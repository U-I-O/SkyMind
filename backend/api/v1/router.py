from fastapi import APIRouter
from .endpoints import auth, monitor, emergency, logistics, security, drones, tasks, events, no_fly_zones

api_router = APIRouter()

# 认证相关路由
api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["认证"]
)

# 监控相关路由
api_router.include_router(
    monitor.router,
    prefix="/monitor",
    tags=["监控"]
)

# 应急相关路由
api_router.include_router(
    emergency.router,
    prefix="/emergency",
    tags=["应急"]
)

# 物流相关路由
api_router.include_router(
    logistics.router,
    prefix="/logistics",
    tags=["物流"]
)

# 安防相关路由
api_router.include_router(
    security.router,
    prefix="/security",
    tags=["安防"]
)

# 无人机相关路由
api_router.include_router(
    drones.router,
    prefix="/drones",
    tags=["无人机"]
)

# 任务相关路由
api_router.include_router(
    tasks.router,
    prefix="/tasks",
    tags=["任务"]
)

# 事件相关路由
api_router.include_router(
    events.router,
    prefix="/events",
    tags=["事件"]
)

# 禁飞区相关路由
api_router.include_router(
    no_fly_zones.router,
    prefix="/no-fly-zones",
    tags=["禁飞区"]
)