from typing import Dict, List, Any, Optional, Union, Set, Callable
import asyncio
import uuid
from datetime import datetime
import json
import camel
from camel.agents import ChatAgent
from camel.societies import RolePlaying
from camel.messages import BaseMessage
import pymongo
import beanie

from config.logging_config import get_logger
from database.models import Task, Event, Drone, AgentState, EventLevel, EventType, TaskType, TaskStatus, DroneStatus
from config.settings import settings
from .base import BaseAgent

logger = get_logger("agents.coordinator")

# 全局智能体注册表
_REGISTERED_AGENTS: Dict[str, BaseAgent] = {}

def register_agent(agent: BaseAgent):
    """注册智能体到全局注册表"""
    _REGISTERED_AGENTS[agent.agent_id] = agent
    logger.info(f"注册智能体: {agent.agent_id} ({agent.agent_type})")
    return agent

def unregister_agent(agent_id: str):
    """从全局注册表中注销智能体"""
    if agent_id in _REGISTERED_AGENTS:
        logger.info(f"注销智能体: {agent_id}")
        del _REGISTERED_AGENTS[agent_id]
        return True
    return False

def get_agent_by_id(agent_id: str) -> Optional[BaseAgent]:
    """根据ID获取智能体"""
    return _REGISTERED_AGENTS.get(agent_id)

def get_agents_by_type(agent_type: str) -> List[BaseAgent]:
    """获取特定类型的所有智能体"""
    return [agent for agent in _REGISTERED_AGENTS.values() if agent.agent_type == agent_type]

def get_all_agents() -> List[BaseAgent]:
    """获取所有注册的智能体"""
    return list(_REGISTERED_AGENTS.values())


class CoordinatorAgent(BaseAgent):
    """
    协调智能体负责管理其他智能体之间的协调和通信。
    它接收系统事件和任务，并将它们分配给适当的智能体。
    """
    
    def __init__(self, agent_id: Optional[str] = None, name: str = "协调智能体"):
        super().__init__(agent_id, name)
        self.agent_type = "CoordinatorAgent"
        self.active_tasks: Dict[str, Task] = {}
        self.active_events: Dict[str, Event] = {}
        self.agent_capabilities: Dict[str, Dict[str, float]] = {}
        self.task_queues: Dict[str, asyncio.Queue] = {}  # 按任务类型的队列
        self.coordination_lock = asyncio.Lock()
        
        # 事件处理器
        self.event_handlers: Dict[str, List[Callable]] = {
            "task": [],
            "event": [],
            "drone": []
        }
        
        # 为不同任务类型创建队列
        for task_type in TaskType:
            self.task_queues[task_type] = asyncio.Queue()
    
    async def initialize(self):
        """初始化协调智能体"""
        await super().initialize()
        
        # 加载现有的活动任务和事件
        await self._load_active_tasks()
        await self._load_active_events()
        
        # 加载所有智能体的能力
        await self._load_agent_capabilities()
        
        # 创建CAMEL角色扮演代理
        self._setup_camel_agents()
        
        return self
    
    def _setup_camel_agents(self):
        """设置CAMEL角色扮演智能体"""
        try:
            logger.info("跳过CAMEL智能体设置，使用贪婪算法代替")
            # 初始化为空字典以避免后续空指针异常
            self.camel_experts = {}
        except Exception as e:
            logger.error(f"设置CAMEL智能体时出错: {str(e)}")
            # 初始化为空字典以避免后续空指针异常
            self.camel_experts = {}
    
    async def _load_active_tasks(self):
        """从数据库加载活动任务"""
        try:
            active_tasks = await Task.find(
                {"status": {"$in": [TaskStatus.PENDING, TaskStatus.ASSIGNED, TaskStatus.IN_PROGRESS]}}
            ).to_list()
            
            for task in active_tasks:
                self.active_tasks[task.task_id] = task
                # 将任务添加到相应的队列
                if task.status == TaskStatus.PENDING:
                    await self.task_queues[task.type].put(task)
            
            logger.info(f"加载了 {len(active_tasks)} 个活动任务")
        except Exception as e:
            logger.error(f"加载活动任务时出错: {str(e)}")
    
    async def _load_active_events(self):
        """从数据库加载活动事件"""
        try:
            active_events = await Event.find(
                {"status": {"$ne": "resolved"}}
            ).to_list()
            
            for event in active_events:
                self.active_events[event.event_id] = event
            
            logger.info(f"加载了 {len(active_events)} 个活动事件")
        except Exception as e:
            logger.error(f"加载活动事件时出错: {str(e)}")
    
    async def _load_agent_capabilities(self):
        """加载所有智能体的能力评分"""
        try:
            agent_states = await AgentState.find_all().to_list()
            
            for state in agent_states:
                self.agent_capabilities[state.agent_id] = state.capability_scores
            
            logger.info(f"加载了 {len(agent_states)} 个智能体的能力评分")
        except Exception as e:
            logger.error(f"加载智能体能力评分时出错: {str(e)}")
    
    async def run_cycle(self):
        """协调者的主循环"""
        await self._process_pending_tasks()
        await self._check_active_tasks()
        await self._process_pending_events()
    
    async def _process_pending_tasks(self):
        """处理待处理的任务"""
        async with self.coordination_lock:
            # 按任务类型处理队列
            for task_type, queue in self.task_queues.items():
                if queue.empty():
                    continue
                
                # 获取任务但不从队列中移除
                task = await queue.get()
                
                # 尝试为任务分配智能体
                assigned = await self._assign_agents_to_task(task)
                
                if assigned:
                    # 任务已分配，将其标记为已完成
                    queue.task_done()
                    logger.info(f"成功分配任务: {task.task_id} ({task_type})")
                else:
                    # 未能分配任务，将其放回队列
                    await queue.put(task)
                    queue.task_done()
                    logger.warning(f"未能分配任务: {task.task_id} ({task_type})")
                    
                    # 为了避免重复处理相同的任务，每次只处理一个任务
                    break
    
    async def _assign_agents_to_task(self, task: Task) -> bool:
        """为任务分配合适的智能体"""
        logger.info(f"尝试为任务分配智能体: {task.task_id} (类型: {task.type})")
        
        # 确定任务所需的能力
        required_capabilities = self._get_required_capabilities(task)
        
        # 获取可用的智能体
        available_agents = self._get_available_agents()
        
        # 使用推理来确定最佳的智能体组合
        best_agents = await self._reason_best_agents(task, available_agents, required_capabilities)
        
        if not best_agents:
            logger.warning(f"找不到适合任务的智能体: {task.task_id}")
            return False
        
        # 分配智能体
        task.assigned_agents = [agent.agent_id for agent in best_agents]
        task.status = TaskStatus.ASSIGNED
        
        # 使用更健壮的保存方式，处理潜在的错误
        try:
            # 首先尝试刷新任务状态
            updated_task = await Task.find_one({"task_id": task.task_id})
            if updated_task:
                # 如果任务存在，更新其属性而不是直接保存
                updated_task.assigned_agents = task.assigned_agents
                updated_task.status = task.status
                await updated_task.save()
                task = updated_task
            else:
                # 如果任务不存在，尝试插入
                await task.save()
                
        except pymongo.errors.DuplicateKeyError as e:
            logger.error(f"保存任务时出现重复键错误: {str(e)}")
            # 尝试重新获取任务并更新
            try:
                updated_task = await Task.find_one({"task_id": task.task_id})
                if updated_task:
                    updated_task.assigned_agents = task.assigned_agents
                    updated_task.status = task.status
                    await updated_task.update({"$set": {
                        "assigned_agents": task.assigned_agents,
                        "status": task.status
                    }})
                    task = updated_task
                else:
                    logger.warning(f"无法找到任务 {task.task_id} 进行更新")
                    return False
            except Exception as update_error:
                logger.error(f"尝试更新任务时出错: {str(update_error)}")
                return False
                
        except beanie.exceptions.RevisionIdWasChanged as e:
            logger.error(f"保存任务时修订ID已更改: {str(e)}")
            # 尝试强制更新任务状态
            try:
                await Task.find_one({"task_id": task.task_id}).update({"$set": {
                    "assigned_agents": task.assigned_agents,
                    "status": task.status
                }})
            except Exception as update_error:
                logger.error(f"尝试强制更新任务时出错: {str(update_error)}")
                return False
                
        except Exception as e:
            logger.error(f"保存任务时出错: {str(e)}")
            return False
        
        # 通知智能体它们被分配了任务
        for agent in best_agents:
            await agent.message_queue.put({
                "type": "task_assigned",
                "task_id": task.task_id,
                "source_agent_id": self.agent_id
            })
        
        # 更新活动任务列表
        self.active_tasks[task.task_id] = task
        
        logger.info(f"为任务 {task.task_id} 分配了 {len(best_agents)} 个智能体")
        return True
    
    async def _reason_best_agents(self, task: Task, available_agents: List[BaseAgent], 
                                required_capabilities: Dict[str, float]) -> List[BaseAgent]:
        """使用推理来确定最佳的智能体组合"""
        try:
            logger.info(f"为任务 {task.task_id} 选择最佳智能体")
            
            # 由于CAMEL库兼容性问题，直接使用贪婪算法选择智能体
            return self._greedy_agent_selection(available_agents, required_capabilities, 3)
            
        except Exception as e:
            logger.error(f"智能体选择出错: {str(e)}")
            # 如果出错，但有可用智能体，分配第一个可用的智能体
            if available_agents:
                fallback_agent = available_agents[0]
                logger.info(f"错误恢复：分配备用智能体 {fallback_agent.agent_id}")
                return [fallback_agent]
            return []
    
    def _greedy_agent_selection(self, available_agents: List[BaseAgent], 
                               required_capabilities: Dict[str, float], max_agents: int) -> List[BaseAgent]:
        """使用贪婪算法选择最合适的智能体组合
        
        对于每个能力，找到具有该能力评分最高的智能体，然后添加到选定的智能体列表中。
        如果已经选择了智能体具有某种能力，则跳过该能力。
        
        Args:
            available_agents: 可用的智能体列表
            required_capabilities: 所需的能力和最低评分
            max_agents: 最多选择的智能体数量
            
        Returns:
            选定的智能体列表
        """
        if not available_agents:
            return []
        
        # 确保我们有智能体能力信息
        agents_with_capabilities = []
        for agent in available_agents:
            agent_capabilities = self.agent_capabilities.get(agent.agent_id, {})
            if agent_capabilities:
                agents_with_capabilities.append((agent, agent_capabilities))
        
        # 如果没有找到带有能力信息的智能体，则返回第一个智能体作为通用处理
        if not agents_with_capabilities and available_agents:
            logger.warning("没有找到带有能力信息的智能体，返回第一个可用智能体")
            return [available_agents[0]]
        
        selected_agents = []
        covered_capabilities = set()
        
        # 确保至少选择一个智能体
        if not agents_with_capabilities:
            logger.warning("没有找到具有指定能力的智能体")
            if available_agents:
                return [available_agents[0]]  # 返回第一个可用智能体
            return []
        
        # 按照总能力得分排序智能体
        scored_agents = []
        for agent, capabilities in agents_with_capabilities:
            total_score = 0
            for cap, required_score in required_capabilities.items():
                if cap in capabilities and capabilities[cap] >= required_score:
                    total_score += capabilities[cap]
            scored_agents.append((agent, total_score))
        
        # 按总得分降序排序
        scored_agents.sort(key=lambda x: x[1], reverse=True)
        
        # 取得分最高的前max_agents个智能体
        selected_agents = [agent for agent, score in scored_agents[:max_agents] if score > 0]
        
        # 如果没有找到合适的智能体但有可用智能体，返回第一个可用智能体
        if not selected_agents and available_agents:
            logger.warning("没有找到足够匹配的智能体，选择第一个可用智能体")
            return [available_agents[0]]
        
        logger.info(f"贪婪算法选择了 {len(selected_agents)} 个智能体")
        return selected_agents
    
    def _get_required_capabilities(self, task: Task) -> Dict[str, float]:
        """根据任务类型确定所需的能力"""
        capabilities = {}
        
        if task.type == TaskType.EMERGENCY:
            capabilities = {
                "emergency_response": 0.9,
                "path_planning": 0.7,
                "object_detection": 0.5,
                "drone_control": 0.8
            }
        elif task.type == TaskType.DELIVERY:
            capabilities = {
                "logistics": 0.9,
                "path_planning": 0.8,
                "drone_control": 0.7,
                "object_detection": 0.3
            }
        elif task.type == TaskType.INSPECTION:
            capabilities = {
                "object_detection": 0.9,
                "drone_control": 0.8,
                "path_planning": 0.6,
                "anomaly_detection": 0.7
            }
        elif task.type == TaskType.SURVEILLANCE:
            capabilities = {
                "object_detection": 0.9,
                "anomaly_detection": 0.8,
                "drone_control": 0.7,
                "path_planning": 0.5
            }
        else:  # TaskType.OTHER
            capabilities = {
                "drone_control": 0.7,
                "path_planning": 0.6,
                "object_detection": 0.5
            }
        

        # 修改后（兼容无 task_data 的情况）：
        if hasattr(task, "task_data") and task.task_data and "required_capabilities" in task.task_data:
            # 合并自定义能力需求
            capabilities.update(task.task_data["required_capabilities"])
        
        return capabilities
    
    def _map_task_to_expert(self, task_type: TaskType) -> str:
        """将任务类型映射到CAMEL专家类型"""
        mapping = {
            TaskType.EMERGENCY: "emergency",
            TaskType.DELIVERY: "logistics",
            TaskType.INSPECTION: "security",
            TaskType.SURVEILLANCE: "security",
            TaskType.OTHER: "logistics"
        }
        return mapping.get(task_type, "emergency")
    
    def _get_available_agents(self) -> List[BaseAgent]:
        """获取所有可用的智能体"""
        return [
            agent for agent in get_all_agents()
            if agent.agent_id != self.agent_id and agent.status != "error" and agent.status != "stopped"
        ]
    
    async def _check_active_tasks(self):
        """检查活动任务的状态"""
        for task_id, task in list(self.active_tasks.items()):
            # 重新从数据库加载任务以获取最新状态
            updated_task = await Task.find_one({"task_id": task_id})
            
            if not updated_task:
                # 任务已被删除
                logger.warning(f"任务已不存在: {task_id}")
                self.active_tasks.pop(task_id)
                continue
            
            if updated_task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
                # 任务已完成或失败或取消
                logger.info(f"任务已结束: {task_id} (状态: {updated_task.status})")
                self.active_tasks.pop(task_id)
                continue
            
            # 更新内部任务记录
            self.active_tasks[task_id] = updated_task
    
    async def _process_pending_events(self):
        """处理待处理的事件"""
        for event_id, event in list(self.active_events.items()):
            # 检查事件是否已解决
            updated_event = await Event.find_one({"event_id": event_id})
            
            if not updated_event:
                # 事件已被删除
                self.active_events.pop(event_id)
                continue
            
            if updated_event.status == "resolved":
                # 事件已解决
                self.active_events.pop(event_id)
                continue
            
            # 对于新事件，创建相应的任务
            if updated_event.status == "new":
                await self._create_task_for_event(updated_event)
                updated_event.status = "processing"
                await updated_event.save()
            
            # 更新内部事件记录
            self.active_events[event_id] = updated_event
    
    async def _create_task_for_event(self, event: Event):
        """根据事件创建任务"""
        task_type = self._map_event_to_task_type(event.type)
        
        # 为事件创建任务
        task = Task(
            title=f"响应事件: {event.title}",
            description=f"自动创建的任务，用于响应事件 {event.event_id}\n\n{event.description}",
            type=task_type,
            priority=self._map_event_level_to_priority(event.level),
            created_by=self.agent_id,
            start_location=event.location,
            end_location=event.location,
            related_events=[event.event_id],
            completion_criteria={
                "event_resolved": True
            },
            task_data={
                "event_data": event.detection_data,
                "video_source": event.video_source,
                "image_evidence": event.image_evidence,
                "bounding_boxes": [box.dict() for box in (event.bounding_boxes or [])]
            }
        )
        
        await task.insert()
        logger.info(f"为事件 {event.event_id} 创建了任务: {task.task_id}")
        
        # 将任务添加到队列
        await self.task_queues[task_type].put(task)
        
        # 更新事件
        event.related_tasks.append(task.task_id)
        await event.save()
        
        return task
    
    def _map_event_to_task_type(self, event_type: EventType) -> TaskType:
        """将事件类型映射到任务类型"""
        mapping = {
            EventType.ANOMALY: TaskType.INSPECTION,
            EventType.EMERGENCY: TaskType.EMERGENCY,
            EventType.LOGISTICS: TaskType.DELIVERY,
            EventType.SECURITY: TaskType.SURVEILLANCE,
            EventType.SYSTEM: TaskType.OTHER
        }
        return mapping.get(event_type, TaskType.OTHER)
    
    def _map_event_level_to_priority(self, event_level: EventLevel) -> int:
        """将事件级别映射到任务优先级"""
        mapping = {
            EventLevel.LOW: 3,
            EventLevel.MEDIUM: 6,
            EventLevel.HIGH: 10
        }
        return mapping.get(event_level, 5)
    
    async def process_message(self, message: Dict[str, Any]):
        """处理来自其他智能体或系统的消息"""
        message_type = message.get("type")
        data = message.get("data", {})
        sender_id = message.get("sender_id")
        
        logger.debug(f"Coordinator received message: Type={message_type}, Sender={sender_id}, Data={data}")
        
        if message_type == "new_task":
            try:
                task_data = data
                # Ensure required fields are present
                if not all(k in task_data for k in ['task_id', 'type', 'priority', 'status']):
                    logger.error(f"Received invalid new_task message: Missing required fields. Data: {task_data}")
                    return
                    
                task = Task(**task_data) # Assuming Task model can be instantiated from dict
                self.active_tasks[task.task_id] = task
                await self.task_queues[task.type].put(task)
                logger.info(f"收到新任务: {task.task_id}")
            except Exception as e:
                logger.error(f"处理 new_task 消息时出错: {e}, Data: {data}")
                
        elif message_type == "new_event":
            try:
                event_data = data
                # Ensure required fields
                if not all(k in event_data for k in ['event_id', 'type', 'level', 'status', 'timestamp']):
                    logger.error(f"Received invalid new_event message: Missing required fields. Data: {event_data}")
                    return
                    
                event = Event(**event_data) # Assuming Event model can be instantiated
                self.active_events[event.event_id] = event
                await self.process_event(event)
                logger.info(f"收到新事件: {event.event_id}")
            except Exception as e:
                logger.error(f"处理 new_event 消息时出错: {e}, Data: {data}")

        elif message_type == "task_update":
            try:
                task_id = data.get("task_id")
                update_data = data.get("update_data")
                if task_id and update_data and task_id in self.active_tasks:
                    task = self.active_tasks[task_id]
                    for key, value in update_data.items():
                        setattr(task, key, value)
                    await task.save() # Save changes to DB
                    logger.info(f"任务更新: {task_id}, Status: {task.status}")
                    # If task is completed or failed, remove from active list?
                    if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
                         del self.active_tasks[task_id]
                         logger.info(f"任务 {task_id} 已结束，从活动列表中移除。")
                else:
                    logger.warning(f"无法更新任务，无效数据: {data}")
            except Exception as e:
                logger.error(f"处理 task_update 消息时出错: {e}, Data: {data}")

        elif message_type == "agent_capability_update":
            try:
                agent_id = data.get("agent_id")
                capabilities = data.get("capabilities")
                if agent_id and capabilities:
                    self.agent_capabilities[agent_id] = capabilities
                    # Persist this? Maybe AgentState update?
                    # await AgentState.find_one(AgentState.agent_id == agent_id).update({"$set": {"capability_scores": capabilities}})
                    logger.info(f"智能体能力更新: {agent_id}")
                else:
                     logger.warning(f"无法更新智能体能力，无效数据: {data}")
            except Exception as e:
                 logger.error(f"处理 agent_capability_update 消息时出错: {e}, Data: {data}")
                 
        # Handle other specific message types...
        # elif message_type == "some_other_type":
        #    # ... specific handling ...

        else:
            # Use base class handler or log unknown type
            # logger.warning(f"收到未知类型的消息: {message_type}") # Keep or remove based on desired strictness
            await super().process_message(message)

    async def handle_query(self, query: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """处理来自其他智能体的查询"""
        if query == "get_task_info":
            task_id = data.get("task_id")
            if not task_id:
                return {"success": False, "error": "Missing task_id"}
            
            task = await Task.find_one({"task_id": task_id})
            if not task:
                return {"success": False, "error": f"Task not found: {task_id}"}
            
            return {
                "success": True,
                "task": task.dict()
            }
        
        elif query == "get_event_info":
            event_id = data.get("event_id")
            if not event_id:
                return {"success": False, "error": "Missing event_id"}
            
            event = await Event.find_one({"event_id": event_id})
            if not event:
                return {"success": False, "error": f"Event not found: {event_id}"}
            
            return {
                "success": True,
                "event": event.dict()
            }
        
        elif query == "get_drone_info":
            drone_id = data.get("drone_id")
            if not drone_id:
                return {"success": False, "error": "Missing drone_id"}
            
            drone = await Drone.find_one({"drone_id": drone_id})
            if not drone:
                return {"success": False, "error": f"Drone not found: {drone_id}"}
            
            return {
                "success": True,
                "drone": drone.dict()
            }
        
        elif query == "get_available_drones":
            drones = await Drone.find({"status": "idle"}).to_list()
            return {
                "success": True,
                "drones": [drone.dict() for drone in drones]
            }
        
        return await super().handle_query(query, data)

    # Add new methods for drone control
    
    async def start_task(self, drone_id: str, task_id: str) -> Dict[str, Any]:
        """
        启动无人机任务执行
        
        该方法启动特定无人机执行特定任务。
        它更新无人机和任务状态，并返回结果。
        
        Args:
            drone_id: 执行任务的无人机ID
            task_id: 要执行的任务ID
            
        Returns:
            包含结果信息的字典
        """
        logger.info(f"为无人机 {drone_id} 启动任务 {task_id}")
        
        try:
            # 获取无人机和任务
            drone = await Drone.find_one({"drone_id": drone_id})
            task = await Task.find_one({"task_id": task_id})
            
            if not drone:
                raise ValueError(f"无人机 {drone_id} 未找到")
            
            if not task:
                raise ValueError(f"任务 {task_id} 未找到")
            
            # 验证无人机是否可以执行此任务
            if drone.status != DroneStatus.IDLE:
                raise ValueError(f"无人机 {drone_id} 不可用（当前状态：{drone.status}）")
            
            if task.status not in [TaskStatus.PENDING, TaskStatus.ASSIGNED]:
                raise ValueError(f"任务 {task_id} 无法启动（当前状态：{task.status}）")
            
            # 更新无人机状态
            drone.status = DroneStatus.FLYING
            if task_id not in drone.assigned_tasks:
                drone.assigned_tasks.append(task_id)
            await drone.save()
            
            # 更新任务状态
            task.status = TaskStatus.IN_PROGRESS
            if drone_id not in task.assigned_drones:
                task.assigned_drones.append(drone_id)
            task.start_time = datetime.utcnow()
            await task.save()
            
            # 保存到活动任务
            self.active_tasks[task_id] = task
            
            # 通知处理程序
            await self._notify_handlers("drone", drone.dict())
            await self._notify_handlers("task", task.dict())
            
            return {
                "success": True,
                "drone": drone.dict(),
                "task": task.dict(),
                "message": f"无人机 {drone_id} 成功启动任务 {task_id}"
            }
            
        except Exception as e:
            logger.error(f"启动任务错误: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "message": f"启动任务失败: {str(e)}"
            }
    
    async def return_home(self, drone_id: str) -> Dict[str, Any]:
        """
        命令无人机返回家位置
        
        Args:
            drone_id: 要返回家的无人机ID
            
        Returns:
            包含结果信息的字典
        """
        logger.info(f"命令无人机 {drone_id} 返回家位置")
        
        try:
            # 获取无人机
            drone = await Drone.find_one({"drone_id": drone_id})
            
            if not drone:
                raise ValueError(f"无人机 {drone_id} 未找到")
            
            # 验证无人机是否可以返回家
            if drone.status not in [DroneStatus.FLYING, DroneStatus.IDLE]:
                raise ValueError(f"无人机 {drone_id} 无法返回家（当前状态：{drone.status}）")
            
            # 在实际实现中，这将向物理无人机发送命令
            # 对于此模拟，我们只更新状态
            
            # 更新无人机状态
            prev_status = drone.status
            drone.status = DroneStatus.FLYING  # 在实际实现中将更新为 RETURNING
            await drone.save()
            
            # 如果无人机正在执行任务，更新任务状态
            if prev_status == DroneStatus.FLYING and drone.assigned_tasks:
                for task_id in drone.assigned_tasks:
                    task = await Task.find_one({"task_id": task_id, "status": TaskStatus.IN_PROGRESS})
                    if task:
                        # 取消或暂停任务
                        task.status = TaskStatus.CANCELLED
                        await task.save()
                        
                        # 更新活动任务
                        self.active_tasks[task_id] = task
                        
                        # 通知处理程序
                        await self._notify_handlers("task", task.dict())
            
            # 通知处理程序
            await self._notify_handlers("drone", drone.dict())
            
            return {
                "success": True,
                "drone": drone.dict(),
                "message": f"无人机 {drone_id} 正在返回家位置"
            }
            
        except Exception as e:
            logger.error(f"命令无人机返回家错误: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "message": f"无人机返回家失败: {str(e)}"
            }
    
    async def emergency_land(self, drone_id: str) -> Dict[str, Any]:
        """
        命令无人机执行紧急降落
        
        Args:
            drone_id: 要执行紧急降落的无人机ID
            
        Returns:
            包含结果信息的字典
        """
        logger.info(f"命令无人机 {drone_id} 执行紧急降落")
        
        try:
            # 获取无人机
            drone = await Drone.find_one({"drone_id": drone_id})
            
            if not drone:
                raise ValueError(f"无人机 {drone_id} 未找到")
            
            # 任何无人机都应能执行紧急降落
            # 在实际实现中，这将向物理无人机发送紧急命令
            
            # 更新无人机状态
            prev_status = drone.status
            drone.status = DroneStatus.FLYING  # 在实际实现中将变为 LANDING
            await drone.save()
            
            # 创建紧急事件
            event = Event(
                event_id=str(uuid.uuid4()),
                type=EventType.EMERGENCY,
                level=EventLevel.HIGH,
                title=f"无人机 {drone.name} 紧急降落",
                description=f"无人机 {drone.name} ({drone_id}) 已启动紧急降落程序",
                location=drone.current_location,
                detected_by=self.agent_id,
                status="new",
                detection_data={"drone_id": drone_id, "prev_status": prev_status}
            )
            await event.save()
            
            # 添加到活动事件
            self.active_events[event.event_id] = event
            
            # 如果无人机正在执行任务，更新任务状态
            if drone.assigned_tasks:
                for task_id in drone.assigned_tasks:
                    task = await Task.find_one({"task_id": task_id, "status": TaskStatus.IN_PROGRESS})
                    if task:
                        # 将任务标记为因紧急情况而失败
                        task.status = TaskStatus.FAILED
                        await task.save()
                        
                        # 更新活动任务
                        self.active_tasks[task_id] = task
                        
                        # 通知处理程序
                        await self._notify_handlers("task", task.dict())
            
            # 通知处理程序
            await self._notify_handlers("drone", drone.dict())
            await self._notify_handlers("event", event.dict())
            
            return {
                "success": True,
                "drone": drone.dict(),
                "event": event.dict(),
                "message": f"无人机 {drone_id} 已启动紧急降落"
            }
            
        except Exception as e:
            logger.error(f"命令无人机紧急降落错误: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "message": f"启动紧急降落失败: {str(e)}"
            }
    
    # 事件处理器注册
    
    def register_handler(self, event_type: str, handler: Callable):
        """为特定事件类型注册处理程序"""
        if event_type in self.event_handlers:
            self.event_handlers[event_type].append(handler)
            logger.debug(f"已注册 {event_type} 事件的处理程序")
        else:
            logger.warning(f"未知事件类型: {event_type}")
    
    def unregister_handler(self, event_type: str, handler: Callable) -> bool:
        """注销特定事件类型的处理程序"""
        if event_type in self.event_handlers and handler in self.event_handlers[event_type]:
            self.event_handlers[event_type].remove(handler)
            logger.debug(f"已注销 {event_type} 事件的处理程序")
            return True
        return False
    
    async def _notify_handlers(self, event_type: str, data: Any):
        """通知特定事件类型的所有注册处理程序"""
        if event_type in self.event_handlers:
            for handler in self.event_handlers[event_type]:
                try:
                    await handler(data)
                except Exception as e:
                    logger.error(f"事件处理程序错误: {str(e)}")

# Singleton coordinator instance
_COORDINATOR_INSTANCE = None

async def get_coordinator() -> CoordinatorAgent:
    """获取或创建协调器实例"""
    global _COORDINATOR_INSTANCE
    if _COORDINATOR_INSTANCE is None:
        _COORDINATOR_INSTANCE = CoordinatorAgent()
        await _COORDINATOR_INSTANCE.initialize()
    return _COORDINATOR_INSTANCE