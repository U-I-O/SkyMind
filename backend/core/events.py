import asyncio
from typing import Dict, List, Any, Callable, Awaitable, Optional
from datetime import datetime

from config.logging_config import get_logger

logger = get_logger("core.events")

class EventManager:
    """事件管理器，处理系统事件的注册和分发"""
    
    def __init__(self):
        self.event_handlers: Dict[str, List[Callable[[Dict[str, Any]], Awaitable[None]]]] = {}
        self.event_queue = asyncio.Queue()
        self._running = False
    
    def register_handler(self, event_type: str, handler: Callable[[Dict[str, Any]], Awaitable[None]]):
        """注册事件处理器"""
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        
        self.event_handlers[event_type].append(handler)
        logger.debug(f"注册事件处理器: {event_type}")
    
    async def emit(self, event_type: str, data: Optional[Dict[str, Any]] = None):
        """发送事件"""
        if data is None:
            data = {}
        
        # 添加事件元数据
        event = {
            "type": event_type,
            "timestamp": datetime.utcnow().isoformat(),
            "data": data
        }
        
        # 将事件放入队列
        await self.event_queue.put(event)
        logger.debug(f"发送事件: {event_type}")
    
    async def start(self):
        """启动事件处理循环"""
        self._running = True
        logger.info("启动事件处理循环")
        
        while self._running:
            try:
                # 从队列获取事件
                event = await self.event_queue.get()
                event_type = event["type"]
                
                # 调用所有注册的处理器
                if event_type in self.event_handlers:
                    for handler in self.event_handlers[event_type]:
                        try:
                            await handler(event)
                        except Exception as e:
                            logger.error(f"事件处理器出错: {str(e)}")
                
                self.event_queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"事件处理循环出错: {str(e)}")
    
    async def stop(self):
        """停止事件处理循环"""
        self._running = False
        logger.info("停止事件处理循环")


# 全局事件管理器实例
event_manager = EventManager()

# 预定义事件类型
class EventTypes:
    # 系统事件
    SYSTEM_STARTED = "system_started"
    SYSTEM_STOPPING = "system_stopping"
    SYSTEM_ERROR = "system_error"
    
    # 任务事件
    TASK_CREATED = "task_created"
    TASK_ASSIGNED = "task_assigned"
    TASK_UPDATED = "task_updated"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    TASK_CANCELLED = "task_cancelled"
    
    # 事件事件
    EVENT_DETECTED = "event_detected"
    EVENT_UPDATED = "event_updated"
    EVENT_RESOLVED = "event_resolved"
    
    # 无人机事件
    DRONE_REGISTERED = "drone_registered"
    DRONE_STATUS_CHANGED = "drone_status_changed"
    DRONE_TASK_ASSIGNED = "drone_task_assigned"
    DRONE_LOCATION_UPDATED = "drone_location_updated"
    DRONE_BATTERY_LOW = "drone_battery_low"
    
    # 智能体事件
    AGENT_STARTED = "agent_started"
    AGENT_STOPPED = "agent_stopped"
    AGENT_ERROR = "agent_error"


# 辅助函数，添加常用事件处理器
async def setup_default_handlers():
    """设置默认事件处理器"""
    # 系统事件处理器
    event_manager.register_handler(EventTypes.SYSTEM_ERROR, system_error_handler)
    
    # 无人机事件处理器
    event_manager.register_handler(EventTypes.DRONE_BATTERY_LOW, drone_battery_low_handler)
    
    logger.info("设置了默认事件处理器")


# 默认事件处理器实现
async def system_error_handler(event: Dict[str, Any]):
    """系统错误处理器"""
    error_data = event["data"]
    logger.error(f"系统错误: {error_data.get('message', 'Unknown error')}")
    
    # 在这里可以添加告警逻辑，如发送邮件、短信等


async def drone_battery_low_handler(event: Dict[str, Any]):
    """无人机电池低处理器"""
    drone_data = event["data"]
    drone_id = drone_data.get("drone_id")
    battery_level = drone_data.get("battery_level")
    
    logger.warning(f"无人机 {drone_id} 电池电量低: {battery_level}%")
    
    # 在这里可以添加自动返航或降落逻辑