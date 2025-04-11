from typing import Dict, List, Any, Optional, Union, Set
import asyncio
import uuid
from datetime import datetime
import json
import camel
from camel.agents import ChatAgent
from camel.societies import RolePlaying
from camel.messages import BaseMessage

from config.logging_config import get_logger
from database.models import Task, Event, Drone, AgentState, EventLevel, EventType, TaskType, TaskStatus
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
            # 创建CAMEL协调智能体
            self.camel_coordinator = ChatAgent(
                "城市低空系统协调员",
                """你是一个智慧城市低空系统的中央协调员。你负责分析各种事件和任务，并决定如何最有效地分配资源来响应它们。
                你需要考虑事件的优先级、可用资源、地理位置和特殊需求。你擅长协调多个系统和团队协同工作，以确保
                城市的安全和效率。根据各种传感器、摄像头和系统的输入，做出明智的决策并分发适当的指令。"""
            )
            
            # 创建专家智能体角色
            self.camel_experts = {
                "emergency": ChatAgent(
                    "应急响应专家", 
                    """你是一位应急响应专家，负责在紧急情况下提供专业的建议和策略。你擅长分析
                    紧急情况，确定优先级，并提出有效的应对策略。你了解各种紧急情况的标准操作程序，
                    能够迅速评估情况并提出行动建议。"""
                ),
                "logistics": ChatAgent(
                    "物流规划专家",
                    """你是一位物流规划专家，负责优化无人机和车辆的路径和调度。你擅长考虑时间窗口、
                    容量限制、电池寿命和其他因素，以确保物流操作的效率和可靠性。你能够根据实时条件
                    调整路线和调度计划。"""
                ),
                "security": ChatAgent(
                    "安防专家",
                    """你是一位安防专家，负责监控城市的安全状况和检测异常活动。你擅长分析监控数据，
                    识别安全威胁，并提出适当的安全措施。你了解各种安全协议和最佳实践，能够提供有关
                    如何保护关键基础设施和公共区域的建议。"""
                ),
                "detection": ChatAgent(
                    "计算机视觉专家",
                    """你是一位计算机视觉专家，负责解释和分析来自各种摄像头和传感器的视觉数据。
                    你擅长识别图像和视频中的对象、活动和异常情况。你了解各种计算机视觉算法和技术，
                    能够提供有关如何最好地处理和解释视觉数据的建议。"""
                )
            }
            
            logger.info("CAMEL智能体设置完成")
        except Exception as e:
            logger.error(f"设置CAMEL智能体时出错: {str(e)}")
    
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
        # 根据任务类型确定所需的能力
        required_capabilities = self._get_required_capabilities(task)
        
        # 获取可用的智能体
        available_agents = self._get_available_agents()
        
        # 使用CAMEL进行推理，找出最佳的智能体组合
        best_agents = await self._reason_best_agents(task, available_agents, required_capabilities)
        
        if not best_agents:
            logger.warning(f"找不到适合任务的智能体: {task.task_id}")
            return False
        
        # 分配智能体
        task.assigned_agents = [agent.agent_id for agent in best_agents]
        task.status = TaskStatus.ASSIGNED
        await task.save()
        
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
        """使用CAMEL推理来确定最佳的智能体组合"""
        try:
            # 准备输入
            task_json = json.dumps(task.dict(), default=str, ensure_ascii=False)
            agents_json = json.dumps([{
                "agent_id": a.agent_id,
                "agent_type": a.agent_type,
                "status": a.status,
                "capabilities": self.agent_capabilities.get(a.agent_id, {})
            } for a in available_agents], ensure_ascii=False)
            capabilities_json = json.dumps(required_capabilities, ensure_ascii=False)
            
            # 根据任务类型选择专家
            expert_type = self._map_task_to_expert(task.type)
            expert_agent = self.camel_experts.get(expert_type, self.camel_experts["emergency"])
            
            # 创建角色扮演对话
            role_playing = RolePlaying(self.camel_coordinator, expert_agent)
            
            # 用户消息描述任务、可用智能体和所需能力
            user_message = f"""我需要为以下任务选择最合适的智能体组合:
            
            任务详情:
            {task_json}
            
            可用智能体:
            {agents_json}
            
            所需能力:
            {capabilities_json}
            
            请分析任务需求和可用智能体的能力，然后推荐最适合执行此任务的智能体组合。
            你的回答应该是一个JSON格式的列表，包含所选智能体的ID。例如:
            ["agent-id-1", "agent-id-2"]
            只返回JSON，不要有其他文字。最多选择 {settings.MAX_AGENTS_PER_TASK} 个智能体。
            """
            
            # 开始对话
            chat_result = await asyncio.to_thread(
                role_playing.chat, 
                user_message,
                max_turns=1
            )
            
            assistant_response = chat_result[-1].assistant_response
            
            # 从CAMEL响应中提取智能体ID
            try:
                # 提取JSON部分
                json_text = assistant_response
                if "```json" in json_text:
                    json_text = json_text.split("```json")[1].split("```")[0].strip()
                elif "```" in json_text:
                    json_text = json_text.split("```")[1].split("```")[0].strip()
                
                # 解析JSON
                selected_agent_ids = json.loads(json_text)
                
                # 获取对应的智能体对象
                selected_agents = []
                for agent_id in selected_agent_ids:
                    agent = get_agent_by_id(agent_id)
                    if agent and agent in available_agents:
                        selected_agents.append(agent)
                
                logger.info(f"CAMEL推理选择了 {len(selected_agents)} 个智能体用于任务 {task.task_id}")
                return selected_agents
            except json.JSONDecodeError:
                logger.error("无法解析CAMEL响应中的JSON")
                # 回退到简单的贪婪选择
                return self._greedy_agent_selection(available_agents, required_capabilities, settings.MAX_AGENTS_PER_TASK)
        
        except Exception as e:
            logger.error(f"CAMEL推理出错: {str(e)}")
            # 回退到简单的贪婪选择
            return self._greedy_agent_selection(available_agents, required_capabilities, settings.MAX_AGENTS_PER_TASK)
    
    def _greedy_agent_selection(self, available_agents: List[BaseAgent], 
                               required_capabilities: Dict[str, float], max_agents: int) -> List[BaseAgent]:
        """贪婪算法选择智能体（作为CAMEL推理的备选方案）"""
        selected_agents = []
        remaining_capabilities = required_capabilities.copy()
        
        # 按总体匹配度排序智能体
        sorted_agents = sorted(
            available_agents,
            key=lambda a: sum(
                min(self.agent_capabilities.get(a.agent_id, {}).get(cap, 0), score)
                for cap, score in required_capabilities.items()
            ),
            reverse=True
        )
        
        # 贪婪选择
        for agent in sorted_agents:
            if len(selected_agents) >= max_agents:
                break
                
            # 如果所有能力都已满足，结束选择
            if not remaining_capabilities:
                break
                
            # 计算此智能体能够满足多少剩余需求
            agent_capabilities = self.agent_capabilities.get(agent.agent_id, {})
            contribution = sum(
                min(agent_capabilities.get(cap, 0), score)
                for cap, score in remaining_capabilities.items()
            )
            
            if contribution > 0:
                selected_agents.append(agent)
                
                # 更新剩余需求
                for cap, score in list(remaining_capabilities.items()):
                    agent_score = agent_capabilities.get(cap, 0)
                    if agent_score > 0:
                        remaining_score = max(0, score - agent_score)
                        if remaining_score > 0:
                            remaining_capabilities[cap] = remaining_score
                        else:
                            remaining_capabilities.pop(cap)
        
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
        
        # 可以根据任务的具体描述或要求调整能力需求
        if task.task_data and "required_capabilities" in task.task_data:
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
        """处理收到的消息"""
        await super().process_message(message)
        
        message_type = message.get("type")
        
        if message_type == "new_task":
            # 接收新任务
            task_id = message.get("task_id")
            task = await Task.find_one({"task_id": task_id})
            
            if task and task.status == TaskStatus.PENDING:
                logger.info(f"收到新任务: {task_id}")
                # 将任务添加到相应的队列
                await self.task_queues[task.type].put(task)
                
        elif message_type == "new_event":
            # 接收新事件
            event_id = message.get("event_id")
            event = await Event.find_one({"event_id": event_id})
            
            if event and event.status == "new":
                logger.info(f"收到新事件: {event_id}")
                self.active_events[event_id] = event
    
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


# 创建和获取全局协调智能体的函数
_COORDINATOR_INSTANCE = None

async def get_coordinator() -> CoordinatorAgent:
    """获取全局协调智能体实例"""
    global _COORDINATOR_INSTANCE
    
    if not _COORDINATOR_INSTANCE:
        _COORDINATOR_INSTANCE = CoordinatorAgent()
        await _COORDINATOR_INSTANCE.initialize()
        register_agent(_COORDINATOR_INSTANCE)
        
    return _COORDINATOR_INSTANCE