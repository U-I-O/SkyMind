from typing import Dict, List, Any, Optional, Union, Tuple, Set
import asyncio
import uuid
import time
from datetime import datetime
import json
import numpy as np
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

from config.logging_config import get_logger
from database.models import (
    Task, Event, Drone, AgentLog, TaskStatus, TaskType,
    EventType, EventLevel, Location, GeoPoint
)
from config.settings import settings
from .base import BaseAgent
from .coordinator import register_agent, get_coordinator

logger = get_logger("agents.response")

# 定义LLM输出模型
class ResponseAction(BaseModel):
    """应急响应行动"""
    action_type: str = Field(..., description="行动类型，如 'deploy_drones', 'notify_authorities', 'evacuate_area', 等")
    priority: int = Field(..., description="优先级，1-10，10为最高优先级")
    description: str = Field(..., description="行动描述")
    resources_needed: List[str] = Field(..., description="所需资源列表")
    estimated_time: Optional[int] = Field(None, description="预计完成时间（分钟）")

class ResponsePlan(BaseModel):
    """应急响应计划"""
    situation_assessment: str = Field(..., description="情况评估")
    severity_level: str = Field(..., description="严重程度，可以是'low', 'medium', 'high'")
    actions: List[ResponseAction] = Field(..., description="响应行动列表")
    additional_notes: Optional[str] = Field(None, description="额外说明")

class ResponseAgent(BaseAgent):
    """
    应急响应智能体使用LLM为各种事件生成智能响应计划
    """
    
    def __init__(self, agent_id: Optional[str] = None, name: str = "应急响应智能体"):
        super().__init__(agent_id, name)
        self.agent_type = "ResponseAgent"
        self.llm = None
        self.response_chain = None
        self.active_tasks: Dict[str, Dict[str, Any]] = {}
        self.memory = {}
        self.llm_lock = asyncio.Lock()
        self.capabilities = {
            "emergency_response": 0.95,
            "situation_assessment": 0.9,
            "resource_allocation": 0.85,
            "risk_analysis": 0.8
        }
    
    async def initialize(self):
        """初始化应急响应智能体"""
        await super().initialize()
        
        # 初始化LLM
        await self._initialize_llm()
        
        # 加载活动任务
        await self._load_active_tasks()
        
        return self
    
    async def _initialize_llm(self):
        """初始化LLM和响应链"""
        try:
            self.logger.info("初始化LLM和响应链")
            
            # 创建LLM
            self.llm = ChatOpenAI(
                model_name=settings.OPENAI_MODEL,
                openai_api_key=settings.OPENAI_API_KEY,
                temperature=0.2
            )
            
            # 创建输出解析器
            parser = PydanticOutputParser(pydantic_object=ResponsePlan)
            
            # 创建响应计划提示模板
            template = """
            你是一个智慧城市低空应急响应系统的AI专家。
            请根据以下事件信息生成一个应急响应计划。
            
            事件信息:
            - 事件ID: {event_id}
            - 标题: {event_title}
            - 描述: {event_description}
            - 类型: {event_type}
            - 级别: {event_level}
            - 位置: {event_location}
            - 检测数据: {detection_data}
            
            可用资源:
            - 无人机: {available_drones}
            - 紧急服务: {emergency_services}
            
            响应计划需要包括：
            1. 情况评估
            2. 严重程度
            3. 响应行动列表（包括优先级、描述、所需资源和预计时间）
            4. 额外说明
            
            请确保你的响应计划考虑到事件的严重性、可用资源和最佳应急实践。
            
            {format_instructions}
            """
            
            # 设置提示模板
            prompt = PromptTemplate(
                template=template,
                input_variables=[
                    "event_id", "event_title", "event_description", "event_type", 
                    "event_level", "event_location", "detection_data", 
                    "available_drones", "emergency_services"
                ],
                partial_variables={"format_instructions": parser.get_format_instructions()}
            )
            
            # 创建LLM链
            self.response_chain = LLMChain(
                llm=self.llm,
                prompt=prompt,
                output_parser=parser,
                verbose=True
            )
            
            self.logger.info("LLM和响应链初始化成功")
        
        except Exception as e:
            self.logger.error(f"初始化LLM和响应链失败: {str(e)}")
            raise
    
    async def _load_active_tasks(self):
        """加载分配给此智能体的活动任务"""
        try:
            tasks = await Task.find({
                "status": {"$in": [TaskStatus.ASSIGNED, TaskStatus.IN_PROGRESS]},
                "assigned_agents": self.agent_id
            }).to_list()
            
            for task in tasks:
                self.active_tasks[task.task_id] = {
                    "task": task,
                    "status": "pending",
                    "response_plan": None,
                    "actions_taken": [],
                    "start_time": datetime.utcnow()
                }
                
                # 创建内存
                self.memory[task.task_id] = ConversationBufferMemory()
            
            self.logger.info(f"加载了 {len(tasks)} 个活动任务")
        except Exception as e:
            self.logger.error(f"加载活动任务失败: {str(e)}")
    
    async def run_cycle(self):
        """应急响应智能体的主循环"""
        # 处理活动任务
        for task_id, task_info in list(self.active_tasks.items()):
            # 检查任务是否已更新
            updated_task = await Task.find_one({"task_id": task_id})
            
            if not updated_task:
                # 任务已被删除
                self.active_tasks.pop(task_id)
                self.memory.pop(task_id, None)
                continue
            
            if updated_task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
                # 任务已完成或取消
                self.active_tasks.pop(task_id)
                self.memory.pop(task_id, None)
                continue
            
            # 更新任务
            task_info["task"] = updated_task
            
            # 处理任务
            if task_info["status"] == "pending":
                await self._process_new_task(task_id, task_info)
            elif task_info["status"] == "generating_plan":
                # 计划正在生成中，无需操作
                pass
            elif task_info["status"] == "executing_plan":
                await self._execute_plan(task_id, task_info)
    
    async def _process_new_task(self, task_id: str, task_info: Dict[str, Any]):
        """处理新任务，生成响应计划"""
        try:
            task = task_info["task"]
            
            # 更新任务状态
            task_info["status"] = "generating_plan"
            
            # 创建异步任务来生成响应计划
            asyncio.create_task(self._generate_response_plan(task_id, task_info))
            
            # 更新任务状态
            task.status = TaskStatus.IN_PROGRESS
            await task.save()
            
            self.logger.info(f"开始为任务 {task_id} 生成响应计划")
        except Exception as e:
            self.logger.error(f"处理新任务失败: {str(e)}")
            task_info["status"] = "error"
    
    async def _generate_response_plan(self, task_id: str, task_info: Dict[str, Any]):
        """异步生成响应计划"""
        try:
            task = task_info["task"]
            
            # 获取相关事件
            if not task.related_events or len(task.related_events) == 0:
                self.logger.warning(f"任务 {task_id} 没有相关事件")
                task_info["status"] = "error"
                return
            
            event_id = task.related_events[0]
            event = await Event.find_one({"event_id": event_id})
            
            if not event:
                self.logger.warning(f"找不到任务 {task_id} 的相关事件 {event_id}")
                task_info["status"] = "error"
                return
            
            # 获取可用无人机
            available_drones = await Drone.find({"status": "idle"}).to_list()
            
            # 准备LLM输入
            llm_input = {
                "event_id": event.event_id,
                "event_title": event.title,
                "event_description": event.description,
                "event_type": event.type,
                "event_level": event.level,
                "event_location": json.dumps(event.location.dict() if event.location else {}),
                "detection_data": json.dumps(event.detection_data or {}),
                "available_drones": json.dumps([{
                    "drone_id": drone.drone_id,
                    "name": drone.name,
                    "model": drone.model,
                    "battery_level": drone.battery_level
                } for drone in available_drones]),
                "emergency_services": json.dumps({
                    "police": {"available": True, "response_time": 10},
                    "fire": {"available": True, "response_time": 15},
                    "medical": {"available": True, "response_time": 12}
                })
            }
            
            # 获取响应计划
            async with self.llm_lock:
                response = await asyncio.to_thread(
                    self.response_chain.run,
                    **llm_input
                )
            
            # 解析响应计划
            if isinstance(response, str):
                # 尝试解析JSON
                try:
                    plan_dict = json.loads(response)
                    response_plan = ResponsePlan.parse_obj(plan_dict)
                except:
                    # 使用输出解析器解析
                    parser = PydanticOutputParser(pydantic_object=ResponsePlan)
                    response_plan = parser.parse(response)
            else:
                response_plan = response
            
            # 保存响应计划
            task_info["response_plan"] = response_plan.dict()
            task_info["status"] = "executing_plan"
            
            # 更新任务
            task.task_data = task.task_data or {}
            task.task_data["response_plan"] = response_plan.dict()
            await task.save()
            
            self.logger.info(f"为任务 {task_id} 生成了响应计划，严重程度: {response_plan.severity_level}，行动数: {len(response_plan.actions)}")
            
            # 记录到内存
            memory = self.memory.get(task_id)
            if memory:
                memory.save_context(
                    {"input": f"生成事件 {event_id} 的响应计划"},
                    {"output": f"已生成响应计划，严重程度: {response_plan.severity_level}，包含 {len(response_plan.actions)} 个行动"}
                )
        
        except Exception as e:
            self.logger.error(f"生成响应计划失败: {str(e)}")
            task_info["status"] = "error"
    
    async def _execute_plan(self, task_id: str, task_info: Dict[str, Any]):
        """执行响应计划"""
        try:
            task = task_info["task"]
            response_plan = task_info["response_plan"]
            
            if not response_plan:
                self.logger.warning(f"任务 {task_id} 没有响应计划")
                task_info["status"] = "error"
                return
            
            # 检查是否所有行动都已执行
            actions = response_plan["actions"]
            actions_taken = task_info["actions_taken"]
            
            all_actions_taken = True
            for action in actions:
                if action["action_type"] not in actions_taken:
                    all_actions_taken = False
                    # 执行行动
                    await self._take_action(task_id, task_info, action)
                    # 每个循环只执行一个行动
                    break
            
            # 如果所有行动都已执行，完成任务
            if all_actions_taken:
                await self._complete_task(task_id, task_info)
        
        except Exception as e:
            self.logger.error(f"执行响应计划失败: {str(e)}")
            task_info["status"] = "error"
    
    async def _take_action(self, task_id: str, task_info: Dict[str, Any], action: Dict[str, Any]):
        """执行响应行动"""
        try:
            action_type = action["action_type"]
            
            self.logger.info(f"执行任务 {task_id} 的行动: {action_type}")
            
            # 记录行动开始
            start_time = datetime.utcnow()
            
            # 根据行动类型执行不同的操作
            if action_type == "deploy_drones":
                await self._action_deploy_drones(task_id, task_info, action)
            elif action_type == "notify_authorities":
                await self._action_notify_authorities(task_id, task_info, action)
            elif action_type == "evacuate_area":
                await self._action_evacuate_area(task_id, task_info, action)
            elif action_type == "monitor_situation":
                await self._action_monitor_situation(task_id, task_info, action)
            elif action_type == "coordinate_resources":
                await self._action_coordinate_resources(task_id, task_info, action)
            else:
                # 对于未识别的行动类型，记录并继续
                self.logger.warning(f"未识别的行动类型: {action_type}")
            
            # 记录行动结束
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()
            
            # 添加到已执行行动
            task_info["actions_taken"].append(action_type)
            
            # 更新内存
            memory = self.memory.get(task_id)
            if memory:
                memory.save_context(
                    {"input": f"执行行动: {action_type}"},
                    {"output": f"已完成行动: {action_type}，耗时: {duration:.2f}秒"}
                )
            
            # 添加任务日志
            await self.log(
                "INFO",
                f"执行行动: {action_type} - {action['description']}",
                task_id=task_id,
                context={"action": action, "duration": duration}
            )
            
            # 更新任务
            task = task_info["task"]
            task.task_data = task.task_data or {}
            actions_log = task.task_data.get("actions_log", [])
            actions_log.append({
                "action_type": action_type,
                "description": action["description"],
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "duration": duration
            })
            task.task_data["actions_log"] = actions_log
            await task.save()
            
        except Exception as e:
            self.logger.error(f"执行行动失败: {str(e)}")
    
    async def _action_deploy_drones(self, task_id: str, task_info: Dict[str, Any], action: Dict[str, Any]):
        """执行部署无人机行动"""
        # 获取可用无人机
        available_drones = await Drone.find({"status": "idle"}).to_list()
        
        if not available_drones:
            self.logger.warning("没有可用的无人机")
            return
        
        # 选择无人机数量（根据严重程度）
        severity = task_info["response_plan"]["severity_level"]
        num_drones = 1
        if severity == "medium":
            num_drones = min(2, len(available_drones))
        elif severity == "high":
            num_drones = min(3, len(available_drones))
        
        selected_drones = available_drones[:num_drones]
        
        # 分配无人机
        task = task_info["task"]
        assigned_drones = []
        
        for drone in selected_drones:
            # 更新无人机状态
            drone.status = "flying"
            drone.assigned_tasks.append(task_id)
            await drone.save()
            assigned_drones.append(drone.drone_id)
        
        # 更新任务
        task.assigned_drones = assigned_drones
        await task.save()
        
        # 等待模拟无人机部署时间
        await asyncio.sleep(2)
        
        self.logger.info(f"为任务 {task_id} 部署了 {len(assigned_drones)} 架无人机")
    
    async def _action_notify_authorities(self, task_id: str, task_info: Dict[str, Any], action: Dict[str, Any]):
        """执行通知当局行动"""
        # 获取事件信息
        task = task_info["task"]
        if not task.related_events or len(task.related_events) == 0:
            return
        
        event_id = task.related_events[0]
        event = await Event.find_one({"event_id": event_id})
        
        if not event:
            return
        
        # 确定需要通知的部门
        departments = []
        if event.type == EventType.SECURITY:
            departments.append("police")
        elif event.type == EventType.EMERGENCY:
            departments.extend(["police", "fire", "medical"])
        elif event.type == EventType.ANOMALY:
            if event.level == EventLevel.HIGH:
                departments.extend(["police", "fire"])
            else:
                departments.append("police")
        
        # 模拟发送通知
        for department in departments:
            # 在实际应用中，这里应该集成真实的通知系统
            self.logger.info(f"向 {department} 发送关于事件 {event_id} 的通知: {event.title}")
            await asyncio.sleep(1)  # 模拟通知延迟
        
        self.logger.info(f"为任务 {task_id} 通知了以下部门: {', '.join(departments)}")
    
    async def _action_evacuate_area(self, task_id: str, task_info: Dict[str, Any], action: Dict[str, Any]):
        """执行疏散区域行动"""
        # 获取事件位置
        task = task_info["task"]
        if not task.related_events or len(task.related_events) == 0:
            return
        
        event_id = task.related_events[0]
        event = await Event.find_one({"event_id": event_id})
        
        if not event or not event.location:
            return
        
        # 计算疏散半径（根据事件级别）
        evacuation_radius = 100  # 默认100米
        if event.level == EventLevel.MEDIUM:
            evacuation_radius = 200
        elif event.level == EventLevel.HIGH:
            evacuation_radius = 500
        
        # 模拟疏散过程
        self.logger.info(f"模拟疏散半径 {evacuation_radius}米 内的区域")
        await asyncio.sleep(3)  # 模拟疏散时间
        
        self.logger.info(f"为任务 {task_id} 完成了区域疏散，半径: {evacuation_radius}米")
    
    async def _action_monitor_situation(self, task_id: str, task_info: Dict[str, Any], action: Dict[str, Any]):
        """执行监控情况行动"""
        # 检查是否有分配的无人机
        task = task_info["task"]
        if not task.assigned_drones:
            self.logger.warning(f"任务 {task_id} 没有分配无人机，无法监控情况")
            return
        
        # 模拟监控过程
        self.logger.info(f"使用 {len(task.assigned_drones)} 架无人机监控情况")
        await asyncio.sleep(5)  # 模拟监控时间
        
        # 生成模拟监控结果
        monitoring_result = {
            "timestamp": datetime.utcnow().isoformat(),
            "status": "ongoing",
            "observations": [
                "区域内人员已大部分疏散",
                "没有观察到明显的危险迹象",
                "情况基本稳定"
            ]
        }
        
        # 更新任务数据
        task.task_data = task.task_data or {}
        monitoring_logs = task.task_data.get("monitoring_logs", [])
        monitoring_logs.append(monitoring_result)
        task.task_data["monitoring_logs"] = monitoring_logs
        await task.save()
        
        self.logger.info(f"为任务 {task_id} 完成了情况监控")
    
    async def _action_coordinate_resources(self, task_id: str, task_info: Dict[str, Any], action: Dict[str, Any]):
        """执行协调资源行动"""
        # 模拟资源协调过程
        self.logger.info("协调应急资源")
        await asyncio.sleep(2)  # 模拟协调时间
        
        # 生成模拟协调结果
        coordination_result = {
            "timestamp": datetime.utcnow().isoformat(),
            "status": "completed",
            "resources_allocated": {
                "police": 3,
                "fire": 2,
                "medical": 1,
                "drones": len(task_info["task"].assigned_drones or [])
            }
        }
        
        # 更新任务数据
        task = task_info["task"]
        task.task_data = task.task_data or {}
        task.task_data["resource_coordination"] = coordination_result
        await task.save()
        
        self.logger.info(f"为任务 {task_id} 完成了资源协调")
    
    async def _complete_task(self, task_id: str, task_info: Dict[str, Any]):
        """完成任务"""
        try:
            self.logger.info(f"完成任务 {task_id}")
            
            task = task_info["task"]
            
            # 如果有相关事件，更新事件状态
            if task.related_events and len(task.related_events) > 0:
                event_id = task.related_events[0]
                event = await Event.find_one({"event_id": event_id})
                
                if event and event.status != "resolved":
                    event.status = "resolved"
                    event.resolved_at = datetime.utcnow()
                    event.resolution_notes = f"由智能体 {self.agent_id} 解决，任务ID: {task_id}"
                    await event.save()
            
            # 释放分配的无人机
            for drone_id in task.assigned_drones:
                drone = await Drone.find_one({"drone_id": drone_id})
                if drone:
                    drone.status = "idle"
                    drone.assigned_tasks = [t for t in drone.assigned_tasks if t != task_id]
                    await drone.save()
            
            # 计算任务执行时间
            start_time = task_info.get("start_time", datetime.utcnow())
            duration = (datetime.utcnow() - start_time).total_seconds()
            
            # 更新任务状态
            task.status = TaskStatus.COMPLETED
            task.end_time = datetime.utcnow()
            task.task_data = task.task_data or {}
            task.task_data["execution_time"] = duration
            task.task_data["completion_summary"] = {
                "actions_taken": task_info["actions_taken"],
                "timestamp": datetime.utcnow().isoformat(),
                "result": "success"
            }
            await task.save()
            
            # 使用基类的方法完成任务
            result = {
                "execution_time": duration,
                "actions_taken": task_info["actions_taken"],
                "response_plan": task_info["response_plan"]
            }
            await self.complete_task(task_id, result)
            
            # 从活动任务中移除
            self.active_tasks.pop(task_id, None)
            self.memory.pop(task_id, None)
            
            # 广播任务完成消息
            await self.broadcast_message({
                "type": "task_completed",
                "task_id": task_id,
                "source_agent_id": self.agent_id
            })
            
            self.logger.info(f"任务 {task_id} 已完成，耗时: {duration:.2f}秒")
        
        except Exception as e:
            self.logger.error(f"完成任务失败: {str(e)}")
    
    async def handle_task_assigned(self, task_id: str):
        """处理分配的任务"""
        await super().handle_task_assigned(task_id)
        
        # 加载任务
        task = await Task.find_one({"task_id": task_id})
        if not task:
            self.logger.warning(f"找不到任务: {task_id}")
            return
        
        # 添加到活动任务
        self.active_tasks[task_id] = {
            "task": task,
            "status": "pending",
            "response_plan": None,
            "actions_taken": [],
            "start_time": datetime.utcnow()
        }
        
        # 创建内存
        self.memory[task_id] = ConversationBufferMemory()
        
        self.logger.info(f"接受了任务分配: {task_id}")
    
    async def handle_task_cancelled(self, task_id: str):
        """处理取消的任务"""
        await super().handle_task_cancelled(task_id)
        
        # 从活动任务中移除
        if task_id in self.active_tasks:
            self.active_tasks.pop(task_id)
            self.memory.pop(task_id, None)
            
            self.logger.info(f"任务已取消: {task_id}")
    
    async def handle_query(self, query: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """处理来自其他智能体的查询"""
        if query == "analyze_event":
            # 分析事件但不创建任务
            event_id = data.get("event_id")
            if not event_id:
                return {"success": False, "error": "Missing event_id"}
            
            event = await Event.find_one({"event_id": event_id})
            if not event:
                return {"success": False, "error": f"Event not found: {event_id}"}
            
            # 获取可用无人机
            available_drones = await Drone.find({"status": "idle"}).to_list()
            
            # 准备LLM输入
            llm_input = {
                "event_id": event.event_id,
                "event_title": event.title,
                "event_description": event.description,
                "event_type": event.type,
                "event_level": event.level,
                "event_location": json.dumps(event.location.dict() if event.location else {}),
                "detection_data": json.dumps(event.detection_data or {}),
                "available_drones": json.dumps([{
                    "drone_id": drone.drone_id,
                    "name": drone.name,
                    "model": drone.model,
                    "battery_level": drone.battery_level
                } for drone in available_drones]),
                "emergency_services": json.dumps({
                    "police": {"available": True, "response_time": 10},
                    "fire": {"available": True, "response_time": 15},
                    "medical": {"available": True, "response_time": 12}
                })
            }
            
            try:
                # 获取响应计划
                async with self.llm_lock:
                    response = await asyncio.to_thread(
                        self.response_chain.run,
                        **llm_input
                    )
                
                # 解析响应计划
                if isinstance(response, str):
                    # 尝试解析JSON
                    try:
                        plan_dict = json.loads(response)
                        response_plan = ResponsePlan.parse_obj(plan_dict)
                    except:
                        # 使用输出解析器解析
                        parser = PydanticOutputParser(pydantic_object=ResponsePlan)
                        response_plan = parser.parse(response)
                else:
                    response_plan = response
                
                return {
                    "success": True,
                    "response_plan": response_plan.dict()
                }
            
            except Exception as e:
                self.logger.error(f"分析事件失败: {str(e)}")
                return {"success": False, "error": str(e)}
        
        elif query == "get_task_status":
            # 获取任务状态
            task_id = data.get("task_id")
            if not task_id:
                return {"success": False, "error": "Missing task_id"}
            
            if task_id not in self.active_tasks:
                return {"success": False, "error": f"Task not active: {task_id}"}
            
            task_info = self.active_tasks[task_id]
            
            return {
                "success": True,
                "status": task_info["status"],
                "actions_taken": task_info["actions_taken"],
                "response_plan": task_info["response_plan"]
            }
        
        return await super().handle_query(query, data)


# 创建应急响应智能体的工厂函数
async def create_response_agent(agent_id: Optional[str] = None, name: Optional[str] = None) -> ResponseAgent:
    """创建并初始化应急响应智能体"""
    agent = ResponseAgent(agent_id, name)
    await agent.initialize()
    register_agent(agent)
    return agent