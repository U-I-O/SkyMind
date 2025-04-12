from abc import ABC, abstractmethod
import uuid
import asyncio
import time
from typing import Dict, List, Any, Optional, Union, Callable
from datetime import datetime
import json

from config.logging_config import get_logger
from database.models import AgentLog, AgentState, Task, TaskStatus
from config.settings import settings

logger = get_logger("agents")

class BaseAgent(ABC):
    """所有智能体的基类，定义通用接口和功能"""
    
    def __init__(self, agent_id: Optional[str] = None, name: str = None):
        self.agent_id = agent_id or f"{self.__class__.__name__.lower()}-{str(uuid.uuid4())[:8]}"
        self.name = name or self.__class__.__name__
        self.agent_type = self.__class__.__name__
        self.status = "initializing"
        self.current_task_id = None
        self.capabilities = {}
        self.metrics = {}
        self.logger = get_logger(f"agent.{self.agent_type.lower()}")
        self.message_queue = asyncio.Queue()
        self.event_listeners = {}
        self.last_active = datetime.utcnow()
        self._stop_event = asyncio.Event()
        self._initialized = False
        
    async def initialize(self):
        """初始化智能体，在子类中可以重写此方法以添加特定初始化逻辑"""
        self.logger.info(f"初始化智能体: {self.agent_id}")
        self.status = "idle"
        
        # 创建或更新智能体状态
        await self._update_agent_state()
        
        self._initialized = True
        return self
    
    async def _update_agent_state(self):
        """更新智能体状态到数据库"""
        try:
            # 尝试找到现有的状态
            agent_state = await AgentState.find_one({"agent_id": self.agent_id})
            
            if agent_state:
                # 更新现有状态
                agent_state.status = self.status
                agent_state.current_task_id = self.current_task_id
                agent_state.last_active = datetime.utcnow()
                agent_state.capability_scores = self.capabilities
                agent_state.performance_metrics = self.metrics
                await agent_state.save()
            else:
                # 创建新状态
                agent_state = AgentState(
                    agent_id=self.agent_id,
                    agent_type=self.agent_type,
                    status=self.status,
                    current_task_id=self.current_task_id,
                    capability_scores=self.capabilities,
                    performance_metrics=self.metrics,
                    last_active=datetime.utcnow()
                )
                await agent_state.insert()
        except Exception as e:
            self.logger.error(f"更新智能体状态失败: {str(e)}")
    
    async def log(self, level: str, message: str, task_id: Optional[str] = None, 
                 event_id: Optional[str] = None, context: Optional[Dict[str, Any]] = None):
        """记录智能体日志到数据库"""
        try:
            agent_log = AgentLog(
                agent_id=self.agent_id,
                agent_type=self.agent_type,
                level=level,
                message=message,
                related_task_id=task_id or self.current_task_id,
                related_event_id=event_id,
                context=context or {}
            )
            await agent_log.insert()
            
            # 同时使用Python日志库记录
            log_method = getattr(self.logger, level.lower(), self.logger.info)
            log_method(message)
        except Exception as e:
            self.logger.error(f"记录智能体日志失败: {str(e)}")
    
    async def start(self):
        """启动智能体的主循环"""
        if not self._initialized:
            await self.initialize()
        
        self.logger.info(f"启动智能体: {self.agent_id}")
        self.status = "active"
        await self._update_agent_state()
        
        try:
            # 启动消息处理循环
            asyncio.create_task(self._process_messages())
            
            # 启动智能体主循环
            await self._main_loop()
        except Exception as e:
            self.logger.error(f"智能体运行出错: {str(e)}")
            self.status = "error"
            await self._update_agent_state()
    
    async def stop(self):
        """停止智能体"""
        self.logger.info(f"停止智能体: {self.agent_id}")
        self._stop_event.set()
        self.status = "stopped"
        await self._update_agent_state()
    
    async def _main_loop(self):
        """智能体主循环，可在子类中重写"""
        while not self._stop_event.is_set():
            try:
                # 执行智能体的主要逻辑
                await self.run_cycle()
                
                # 更新状态
                self.last_active = datetime.utcnow()
                await self._update_agent_state()
                
                # 避免过于频繁的循环
                await asyncio.sleep(settings.AGENT_COMMUNICATION_INTERVAL)
            except Exception as e:
                import traceback
                error_trace = traceback.format_exc()
                self.logger.error(f"智能体循环出错: {str(e)}\n{error_trace}")
                await asyncio.sleep(5)  # 出错后等待一段时间再继续
    
    @abstractmethod
    async def run_cycle(self):
        """智能体的一个工作周期，必须在子类中实现"""
        pass
    
    async def _process_messages(self):
        """处理接收到的消息"""
        while not self._stop_event.is_set():
            try:
                message = await self.message_queue.get()
                await self.process_message(message)
                self.message_queue.task_done()
            except Exception as e:
                self.logger.error(f"处理消息出错: {str(e)}")
                await asyncio.sleep(1)
    
    async def process_message(self, message: Dict[str, Any]):
        """处理接收到的消息，可在子类中重写"""
        message_type = message.get("type")
        
        if message_type == "task_assigned":
            await self.handle_task_assigned(message.get("task_id"))
        elif message_type == "task_updated":
            await self.handle_task_updated(message.get("task_id"))
        elif message_type == "task_cancelled":
            await self.handle_task_cancelled(message.get("task_id"))
        elif message_type == "event_detected":
            await self.handle_event_detected(message.get("event_id"))
        elif message_type == "agent_query":
            response = await self.handle_query(message.get("query"), message.get("data", {}))
            if "callback_queue" in message:
                await message["callback_queue"].put({
                    "type": "query_response",
                    "query_id": message.get("query_id"),
                    "response": response,
                    "agent_id": self.agent_id
                })
        else:
            self.logger.warning(f"收到未知类型的消息: {message_type}")
    
    async def send_message(self, target_agent_id: str, message: Dict[str, Any]):
        """向另一个智能体发送消息"""
        from agents.coordinator import get_agent_by_id
        
        target_agent = get_agent_by_id(target_agent_id)
        if target_agent:
            await target_agent.message_queue.put(message)
            return True
        else:
            self.logger.warning(f"找不到目标智能体: {target_agent_id}")
            return False
    
    async def query_agent(self, target_agent_id: str, query: str, data: Dict[str, Any] = None) -> Dict[str, Any]:
        """向另一个智能体发送查询并等待响应"""
        from agents.coordinator import get_agent_by_id
        
        target_agent = get_agent_by_id(target_agent_id)
        if not target_agent:
            self.logger.warning(f"找不到目标智能体: {target_agent_id}")
            return {"success": False, "error": "Agent not found"}
        
        # 创建回调队列和查询ID
        callback_queue = asyncio.Queue()
        query_id = str(uuid.uuid4())
        
        # 发送查询
        await target_agent.message_queue.put({
            "type": "agent_query",
            "query": query,
            "data": data or {},
            "query_id": query_id,
            "callback_queue": callback_queue,
            "source_agent_id": self.agent_id
        })
        
        # 等待响应，设置超时
        try:
            response = await asyncio.wait_for(callback_queue.get(), timeout=30)
            return response
        except asyncio.TimeoutError:
            self.logger.warning(f"查询智能体 {target_agent_id} 超时")
            return {"success": False, "error": "Query timeout"}
    
    async def broadcast_message(self, message: Dict[str, Any], agent_type: Optional[str] = None):
        """广播消息给所有智能体或特定类型的智能体"""
        from agents.coordinator import get_all_agents
        
        agents = get_all_agents()
        if agent_type:
            agents = [a for a in agents if a.agent_type == agent_type]
        
        for agent in agents:
            if agent.agent_id != self.agent_id:  # 不给自己发送
                await agent.message_queue.put(message)
    
    async def handle_task_assigned(self, task_id: str):
        """处理分配的任务"""
        self.logger.info(f"收到任务分配: {task_id}")
        self.current_task_id = task_id
        self.status = "busy"
        await self._update_agent_state()
    
    async def handle_task_updated(self, task_id: str):
        """处理更新的任务"""
        self.logger.info(f"任务已更新: {task_id}")
    
    async def handle_task_cancelled(self, task_id: str):
        """处理取消的任务"""
        self.logger.info(f"任务已取消: {task_id}")
        if self.current_task_id == task_id:
            self.current_task_id = None
            self.status = "idle"
            await self._update_agent_state()
    
    async def handle_event_detected(self, event_id: str):
        """处理检测到的事件"""
        self.logger.info(f"检测到事件: {event_id}")
    
    async def handle_query(self, query: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """处理来自其他智能体的查询"""
        self.logger.info(f"收到查询: {query}")
        # 默认实现仅返回基本信息，子类应该重写此方法以提供有意义的响应
        return {
            "success": True,
            "agent_id": self.agent_id,
            "agent_type": self.agent_type,
            "status": self.status,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def on_event(self, event_type: str, callback: Callable):
        """注册事件监听器"""
        if event_type not in self.event_listeners:
            self.event_listeners[event_type] = []
        self.event_listeners[event_type].append(callback)
    
    async def emit_event(self, event_type: str, data: Dict[str, Any] = None):
        """触发事件并调用监听器"""
        if event_type in self.event_listeners:
            for callback in self.event_listeners[event_type]:
                try:
                    await callback(data or {})
                except Exception as e:
                    self.logger.error(f"事件监听器出错: {str(e)}")
    
    async def update_capabilities(self, capabilities: Dict[str, float]):
        """更新智能体的能力评分"""
        self.capabilities.update(capabilities)
        await self._update_agent_state()
    
    async def update_metrics(self, metrics: Dict[str, Any]):
        """更新智能体的性能指标"""
        self.metrics.update(metrics)
        await self._update_agent_state()
    
    async def complete_task(self, task_id: str, result: Dict[str, Any] = None, success: bool = True):
        """完成任务并更新状态"""
        if not task_id:
            self.logger.warning("尝试完成空任务ID")
            return False
        
        try:
            task = await Task.find_one({"task_id": task_id})
            if not task:
                self.logger.warning(f"找不到任务: {task_id}")
                return False
            
            # 更新任务状态
            task.status = TaskStatus.COMPLETED if success else TaskStatus.FAILED
            task.end_time = datetime.utcnow()
            if result:
                task.task_data = task.task_data or {}
                task.task_data["result"] = result
            await task.save()
            
            # 更新智能体状态
            if self.current_task_id == task_id:
                self.current_task_id = None
                self.status = "idle"
                await self._update_agent_state()
            
            # 记录日志
            await self.log(
                "INFO",
                f"{'完成' if success else '失败'} 任务: {task_id}",
                task_id=task_id,
                context={"result": result}
            )
            
            # 发出事件
            await self.emit_event(
                "task_completed" if success else "task_failed",
                {"task_id": task_id, "result": result}
            )
            
            return True
        except Exception as e:
            self.logger.error(f"完成任务时出错: {str(e)}")
            return False