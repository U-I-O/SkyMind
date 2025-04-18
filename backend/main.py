import asyncio
import uvicorn
import os
from fastapi import FastAPI, Depends, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.security import OAuth2PasswordBearer
from typing import Dict, List, Any, Optional, Set
import json
from datetime import datetime, timedelta

from config.settings import settings
from config.logging_config import get_logger
from database.mongodb import init_db, create_initial_data
from database.models import Task, Event, Drone
from agents.coordinator import get_coordinator
from agents.monitor import create_monitor_agent
from agents.planner import create_planner_agent
from agents.response import create_response_agent
from agents.logistics import create_logistics_agent
# from agents.security import create_security_agent
from api.v1.router import api_router

# 设置日志
logger = get_logger("main")

# 创建FastAPI应用
app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    description="SkyMind低空智慧城市AI平台",
    openapi_url=f"{settings.API_PREFIX}/openapi.json"
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应该限制为特定域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 包含API路由
app.include_router(api_router, prefix=settings.API_PREFIX)

# WebSocket连接管理器
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.connection_type: Dict[str, str] = {}  # 连接类型: "admin", "user", "drone"
        self.pending_commands: Dict[str, asyncio.Future] = {}  # command_id -> Future for responses

    async def connect(self, websocket: WebSocket, client_id: str, connection_type: str = "user"):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        self.connection_type[client_id] = connection_type
        logger.info(f"WebSocket客户端连接: {client_id} ({connection_type})")

    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            self.active_connections.pop(client_id)
            self.connection_type.pop(client_id, None)
            
            # Cancel any pending command futures for this client
            commands_to_cancel = [cmd_id for cmd_id, future in self.pending_commands.items() 
                                if not future.done() and future.get_name() == client_id]
            for cmd_id in commands_to_cancel:
                future = self.pending_commands.pop(cmd_id, None)
                if future and not future.done():
                    future.set_exception(ConnectionError("Client disconnected"))
            
            logger.info(f"WebSocket客户端断开连接: {client_id}")

    async def send_message(self, client_id: str, message: Dict[str, Any]):
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_json(message)

    async def broadcast(self, message: Dict[str, Any], connection_type: Optional[str] = None):
        for client_id, connection in list(self.active_connections.items()):
            if connection_type is None or self.connection_type.get(client_id) == connection_type:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"向客户端 {client_id} 广播消息失败: {str(e)}")
                    self.disconnect(client_id)
    
    def register_command(self, command_id: str, client_id: str) -> asyncio.Future:
        """Register a command and return a future that will be resolved when the command completes"""
        future = asyncio.Future()
        future.set_name(client_id)  # Store client_id in the future for cleanup
        self.pending_commands[command_id] = future
        return future
    
    def resolve_command(self, command_id: str, result: Any, is_success: bool = True):
        """Resolve a pending command with result data"""
        future = self.pending_commands.pop(command_id, None)
        if future and not future.done():
            if is_success:
                future.set_result(result)
            else:
                future.set_exception(Exception(str(result)))

manager = ConnectionManager()

# WebSocket接口
@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    connection_type = websocket.query_params.get("type", "user")
    connection_version = websocket.query_params.get("version", "1.0")
    auth_token = websocket.query_params.get("token", None)
    
    # In a real app, validate auth_token here
    # For now, we'll accept any connection
    
    await manager.connect(websocket, client_id, connection_type)
    try:
        while True:
            data = await websocket.receive_json()
            # 处理接收到的消息
            if "type" in data:
                message_type = data["type"]
                
                if message_type == "ping":
                    # 心跳消息
                    await manager.send_message(client_id, {
                        "type": "pong", 
                        "timestamp": datetime.utcnow().isoformat()
                    })
                
                elif message_type == "subscribe":
                    # 处理订阅请求
                    await handle_subscription(client_id, data)
                
                elif message_type == "drone_status":
                    # 处理无人机状态更新
                    await handle_drone_status(client_id, data)
                
                elif message_type == "drone_command":
                    # 处理无人机命令
                    await handle_drone_command(client_id, data)
                
                else:
                    # 其他消息类型
                    await handle_message(client_id, data)
    except WebSocketDisconnect:
        manager.disconnect(client_id)
    except Exception as e:
        logger.error(f"WebSocket错误: {str(e)}")
        manager.disconnect(client_id)

async def handle_subscription(client_id: str, data: Dict[str, Any]):
    """处理WebSocket订阅请求"""
    topic = data.get("topic")
    if not topic:
        return
    
    # 根据订阅主题发送初始数据
    if topic == "tasks":
        # 发送任务列表
        tasks = await Task.find_all().to_list()
        await manager.send_message(client_id, {
            "type": "initial_data",
            "topic": "tasks",
            "data": [task.dict() for task in tasks]
        })
    
    elif topic == "events":
        # 发送事件列表
        events = await Event.find_all().to_list()
        await manager.send_message(client_id, {
            "type": "initial_data",
            "topic": "events",
            "data": [event.dict() for event in events]
        })
    
    elif topic == "drones":
        # 发送无人机列表
        drones = await Drone.find_all().to_list()
        await manager.send_message(client_id, {
            "type": "initial_data",
            "topic": "drones",
            "data": [drone.dict() for drone in drones]
        })

async def handle_drone_status(client_id: str, data: Dict[str, Any]):
    """处理无人机状态更新"""
    drone_id = data.get("drone_id")
    status = data.get("status")
    position = data.get("position")
    
    if not drone_id or not status:
        return
    
    # 更新无人机状态
    drone = await Drone.find_one({"drone_id": drone_id})
    if drone:
        if status:
            drone.status = status
        
        if position:
            drone.current_location = position
        
        # 更新电池电量
        if "battery_level" in data:
            drone.battery_level = data["battery_level"]
        
        await drone.save()
        
        # 广播无人机状态更新
        await manager.broadcast({
            "type": "drone_update",
            "data": {
                "drone_id": drone_id,
                "status": drone.status,
                "current_location": drone.current_location.dict() if drone.current_location else None,
                "battery_level": drone.battery_level,
                "timestamp": datetime.utcnow().isoformat()
            }
        })

async def handle_drone_command(client_id: str, data: Dict[str, Any]):
    """处理无人机命令执行"""
    drone_id = data.get("droneId")
    command = data.get("command")
    params = data.get("params", {})
    command_id = data.get("commandId")
    
    if not drone_id or not command or not command_id:
        await manager.send_message(client_id, {
            "type": "command_response",
            "commandId": command_id if command_id else "unknown",
            "status": "error",
            "error": "Missing required parameters: droneId, command, or commandId",
            "timestamp": datetime.utcnow().isoformat()
        })
        return
    
    try:
        # 获取无人机
        drone = await Drone.find_one({"drone_id": drone_id})
        if not drone:
            raise ValueError(f"无人机 {drone_id} 未找到")
        
        # 处理命令
        result = await process_drone_command(drone, command, params)
        
        # 发送成功响应
        await manager.send_message(client_id, {
            "type": "command_response",
            "commandId": command_id,
            "status": "success",
            "data": result,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # 广播无人机更新到所有连接的客户端
        updated_drone = await Drone.find_one({"drone_id": drone_id})
        if updated_drone:
            await manager.broadcast({
                "type": "drone_update",
                "data": updated_drone.dict()
            })
        
    except Exception as e:
        logger.error(f"处理无人机命令失败: {str(e)}")
        await manager.send_message(client_id, {
            "type": "command_response",
            "commandId": command_id,
            "status": "error",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        })

async def process_drone_command(drone: Drone, command: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """处理无人机命令并返回结果"""
    coordinator = await get_coordinator()
    
    # 根据命令类型执行命令
    if command == "start_task":
        task_id = params.get("task_id")
        if not task_id:
            raise ValueError("Missing task_id parameter")
        
        task = await Task.find_one({"task_id": task_id})
        if not task:
            raise ValueError(f"任务 {task_id} 未找到")
        
        # 将任务分配给无人机
        if task_id not in drone.assigned_tasks:
            drone.assigned_tasks.append(task_id)
            await drone.save()
            
        # 更新任务状态
        task.status = "assigned"
        await task.save()
        
        # 命令无人机开始执行任务
        # 在实际实现中，这将通过与无人机的通信来完成
        result = await coordinator.start_task(drone.drone_id, task_id)
        
        return {
            "message": f"任务 {task_id} 启动成功",
            "drone": drone.dict(),
            "task": task.dict()
        }
    
    elif command == "return_home":
        # 命令无人机返回至家位置
        drone.status = "flying"  # 更新状态为飞行
        await drone.save()
        
        # 在实际实现中，这将通过向无人机发送命令来完成
        result = await coordinator.return_home(drone.drone_id)
        
        return {
            "message": f"无人机 {drone.drone_id} 返回至家",
            "drone": drone.dict()
        }
    
    elif command == "emergency_land":
        # 命令无人机立即降落
        drone.status = "flying"  # 更新状态为飞行（在实际实现中将变为降落）
        await drone.save()
        
        # 在实际实现中，这将通过向无人机发送紧急降落命令来完成
        result = await coordinator.emergency_land(drone.drone_id)
        
        return {
            "message": f"紧急降落已启动，无人机 {drone.drone_id}",
            "drone": drone.dict()
        }
    
    else:
        # 处理其他命令类型
        raise ValueError(f"不支持的命令: {command}")

async def handle_message(client_id: str, data: Dict[str, Any]):
    """处理其他WebSocket消息"""
    # 处理各种消息类型
    message_type = data.get("type")
    
    # 回复客户端
    await manager.send_message(client_id, {
        "type": "ack",
        "original_type": message_type,
        "status": "received",
        "timestamp": datetime.utcnow().isoformat()
    })

# 启动事件
@app.on_event("startup")
async def startup_event():
    logger.info("启动SkyMind低空智慧城市AI平台")
    
    # 初始化数据库
    await init_db()
    
    # 创建初始数据
    await create_initial_data()
    
    # 启动智能体系统
    asyncio.create_task(start_agent_system())
    
    logger.info("系统初始化完成")

# 关闭事件
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("关闭SkyMind低空智慧城市AI平台")
    
    # 停止智能体
    coordinator = await get_coordinator()
    if coordinator:
        await coordinator.stop()
    
    logger.info("系统已关闭")

async def start_agent_system():
    """启动智能体系统"""
    try:
        logger.info("启动智能体系统")
        
        # 启动协调智能体
        coordinator = await get_coordinator()
        asyncio.create_task(coordinator.start())
        
        # 等待协调智能体完全启动
        await asyncio.sleep(1)
        
        # 启动其他智能体
        agents = []
        
        # 监控智能体
        monitor_agent = await create_monitor_agent()
        agents.append(monitor_agent)
        
        # 路径规划智能体
        planner_agent = await create_planner_agent()
        agents.append(planner_agent)
        
        # 应急响应智能体
        response_agent = await create_response_agent()
        agents.append(response_agent)
        
        # 物流调度智能体
        logistics_agent = await create_logistics_agent()
        agents.append(logistics_agent)
        
        # 安防巡检智能体
        # security_agent = await create_security_agent()
        # agents.append(security_agent)
        
        # 启动所有智能体
        for agent in agents:
            asyncio.create_task(agent.start())
        
        # 启动事件监听器
        asyncio.create_task(event_listener())
        
        logger.info(f"成功启动 {len(agents) + 1} 个智能体")
    except Exception as e:
        logger.error(f"启动智能体系统失败: {str(e)}")

async def event_listener():
    """监听系统事件并通过WebSocket广播"""
    coordinator = await get_coordinator()
    
    # 注册不同类型事件的处理程序
    async def handle_task_event(data):
        await manager.broadcast({"type": "task_update", "data": data})
    
    async def handle_event_event(data):
        await manager.broadcast({"type": "event_update", "data": data})
    
    async def handle_drone_event(data):
        await manager.broadcast({"type": "drone_update", "data": data})
    
    # 注册处理程序与协调者
    coordinator.register_handler("task", handle_task_event)
    coordinator.register_handler("event", handle_event_event)
    coordinator.register_handler("drone", handle_drone_event)
    
    # 保持监听器活动
    while True:
        await asyncio.sleep(1)

# 挂载静态文件
try:
    app.mount("/static", StaticFiles(directory="static"), name="static")
except RuntimeError:
    logger.warning("静态文件目录不存在，跳过挂载")

# 主函数
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )