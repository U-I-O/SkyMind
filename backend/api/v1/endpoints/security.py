from fastapi import APIRouter, Depends, HTTPException, Query, status, Body
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

from config.logging_config import get_logger
from database.models import User, Task, TaskType, TaskStatus, Event, EventType
from core.security import get_current_active_user
from agents.coordinator import get_coordinator
from agents.security import create_security_agent

logger = get_logger("api.security")

router = APIRouter()

# 获取安防巡检任务列表
@router.get("/tasks", response_model=List[Dict[str, Any]])
async def get_security_tasks(
    task_type: Optional[str] = Query(None, description="任务类型：surveillance 或 inspection"),
    status: Optional[str] = Query(None, description="任务状态"),
    days: int = Query(7, ge=1, le=30, description="最近天数"),
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(get_current_active_user)
):
    """获取安防巡检任务列表"""
    # 计算时间范围
    now = datetime.utcnow()
    start_time = now - timedelta(days=days)
    
    # 创建查询条件
    query = {
        "created_at": {"$gte": start_time}
    }
    
    # 添加任务类型条件
    if task_type == "surveillance":
        query["type"] = TaskType.SURVEILLANCE
    elif task_type == "inspection":
        query["type"] = TaskType.INSPECTION
    else:
        # 如果未指定类型，则查询所有巡检和监控任务
        query["type"] = {"$in": [TaskType.SURVEILLANCE, TaskType.INSPECTION]}
    
    # 添加状态条件
    if status:
        query["status"] = status
    
    # 执行查询
    tasks = await Task.find(query).sort("created_at", -1).limit(limit).to_list()
    
    # 格式化结果
    result = []
    for task in tasks:
        task_dict = task.dict()
        
        # 添加关联事件信息
        if task.related_events:
            events = await Event.find({"event_id": {"$in": task.related_events}}).to_list()
            task_dict["event_details"] = [
                {
                    "event_id": event.event_id,
                    "title": event.title,
                    "type": event.type,
                    "level": event.level
                }
                for event in events
            ]
        
        result.append(task_dict)
    
    return result

# 获取安防区域列表
@router.get("/zones", response_model=List[Dict[str, Any]])
async def get_security_zones(
    current_user: User = Depends(get_current_active_user)
):
    """获取安防区域列表"""
    # 获取安防巡检智能体
    coordinator = await get_coordinator()
    security_agents = coordinator._get_agents_by_type("SecurityAgent")
    
    if not security_agents:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="没有可用的安防巡检智能体"
        )
    
    security_agent = security_agents[0]
    
    # 查询安防区域
    response = await coordinator.query_agent(
        security_agent.agent_id,
        "get_security_zones",
        {}
    )
    
    # 检查响应
    if not response["success"]:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取安防区域失败: {response.get('error', '未知错误')}"
        )
    
    return response.get("zones", [])

# 获取巡检区域列表
@router.get("/patrol-areas", response_model=List[Dict[str, Any]])
async def get_patrol_areas(
    area_id: Optional[str] = Query(None, description="指定区域ID"),
    current_user: User = Depends(get_current_active_user)
):
    """获取巡检区域列表"""
    # 获取安防巡检智能体
    coordinator = await get_coordinator()
    security_agents = coordinator._get_agents_by_type("SecurityAgent")
    
    if not security_agents:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="没有可用的安防巡检智能体"
        )
    
    security_agent = security_agents[0]
    
    # 查询巡检区域
    response = await coordinator.query_agent(
        security_agent.agent_id,
        "get_patrol_areas",
        {"area_id": area_id} if area_id else {}
    )
    
    # 检查响应
    if not response["success"]:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取巡检区域失败: {response.get('error', '未知错误')}"
        )
    
    # 根据是否指定了区域ID，返回不同的结构
    if area_id:
        if "area" not in response:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"巡检区域不存在: {area_id}"
            )
        return [response["area"]]
    else:
        return response.get("areas", [])

# 创建巡检任务
@router.post("/patrol-tasks", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
async def create_patrol_task(
    task_data: Dict[str, Any] = Body(...),
    current_user: User = Depends(get_current_active_user)
):
    """创建巡检任务"""
    # 检查必需字段
    if "area_id" not in task_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="缺少区域ID"
        )
    
    area_id = task_data["area_id"]
    
    # 获取安防巡检智能体
    coordinator = await get_coordinator()
    security_agents = coordinator._get_agents_by_type("SecurityAgent")
    
    if not security_agents:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="没有可用的安防巡检智能体"
        )
    
    security_agent = security_agents[0]
    
    # 创建巡检任务
    response = await coordinator.query_agent(
        security_agent.agent_id,
        "create_patrol_task",
        {"area_id": area_id}
    )
    
    # 检查响应
    if not response["success"]:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建巡检任务失败: {response.get('error', '未知错误')}"
        )
    
    # 获取任务ID
    task_id = response.get("task_id")
    if not task_id:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="创建任务成功但未返回任务ID"
        )
    
    # 获取任务详情
    task = await Task.find_one({"task_id": task_id})
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"找不到创建的任务: {task_id}"
        )
    
    logger.info(f"为区域 {area_id} 创建了巡检任务: {task_id}")
    
    return task.dict()

# 获取异常历史
@router.get("/anomalies", response_model=Dict[str, List[Dict[str, Any]]])
async def get_anomaly_history(
    area_id: Optional[str] = Query(None, description="指定区域ID"),
    days: int = Query(30, ge=1, le=90, description="最近天数"),
    current_user: User = Depends(get_current_active_user)
):
    """获取异常历史"""
    # 获取安防巡检智能体
    coordinator = await get_coordinator()
    security_agents = coordinator._get_agents_by_type("SecurityAgent")
    
    if not security_agents:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="没有可用的安防巡检智能体"
        )
    
    security_agent = security_agents[0]
    
    # 查询异常历史
    response = await coordinator.query_agent(
        security_agent.agent_id,
        "get_anomaly_history",
        {"area_id": area_id} if area_id else {}
    )
    
    # 检查响应
    if not response["success"]:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取异常历史失败: {response.get('error', '未知错误')}"
        )
    
    # 如果指定了区域，从响应中获取该区域的异常
    if area_id:
        return {"anomalies": response.get("anomalies", [])}
    else:
        return {"anomaly_history": response.get("anomaly_history", {})}

# 获取安防统计信息
@router.get("/statistics", response_model=Dict[str, Any])
async def get_security_statistics(
    days: int = Query(30, ge=1, le=90, description="统计天数"),
    current_user: User = Depends(get_current_active_user)
):
    """获取安防统计信息"""
    # 计算时间范围
    now = datetime.utcnow()
    start_time = now - timedelta(days=days)
    
    # 统计安防事件数量
    security_events_count = await Event.find({
        "type": EventType.SECURITY,
        "detected_at": {"$gte": start_time}
    }).count()
    
    # 按级别统计安防事件
    level_stats = {}
    for level in ["low", "medium", "high"]:
        count = await Event.find({
            "type": EventType.SECURITY,
            "level": level,
            "detected_at": {"$gte": start_time}
        }).count()
        level_stats[level] = count
    
    # 统计巡检任务数量
    patrol_tasks_count = await Task.find({
        "type": TaskType.SURVEILLANCE,
        "created_at": {"$gte": start_time}
    }).count()
    
    # 统计检查任务数量
    inspection_tasks_count = await Task.find({
        "type": TaskType.INSPECTION,
        "created_at": {"$gte": start_time}
    }).count()
    
    # 按日期统计安防事件
    date_stats = []
    for i in range(min(days, 30)):  # 最多统计30天
        day_start = now - timedelta(days=i+1)
        day_end = now - timedelta(days=i)
        
        count = await Event.find({
            "type": EventType.SECURITY,
            "detected_at": {"$gte": day_start, "$lt": day_end}
        }).count()
        
        date_stats.append({
            "date": day_start.date().isoformat(),
            "count": count
        })
    
    # 统计任务状态
    task_status_stats = {}
    for status in ["pending", "assigned", "in_progress", "completed", "failed", "cancelled"]:
        count = await Task.find({
            "type": {"$in": [TaskType.SURVEILLANCE, TaskType.INSPECTION]},
            "status": status,
            "created_at": {"$gte": start_time}
        }).count()
        task_status_stats[status] = count
    
    return {
        "security_events_count": security_events_count,
        "level_stats": level_stats,
        "patrol_tasks_count": patrol_tasks_count,
        "inspection_tasks_count": inspection_tasks_count,
        "date_stats": date_stats,
        "task_status_stats": task_status_stats,
        "period_days": days
    }

# 安防热点区域
@router.get("/hotspots", response_model=List[Dict[str, Any]])
async def get_security_hotspots(
    days: int = Query(30, ge=1, le=90, description="统计天数"),
    min_events: int = Query(3, ge=1, description="最少事件数"),
    current_user: User = Depends(get_current_active_user)
):
    """获取安防热点区域"""
    # 计算时间范围
    now = datetime.utcnow()
    start_time = now - timedelta(days=days)
    
    # 查询安防事件
    security_events = await Event.find({
        "type": EventType.SECURITY,
        "detected_at": {"$gte": start_time},
        "location": {"$ne": None}
    }).to_list()
    
    # 分析热点区域
    # 简化实现：根据位置网格化统计
    grid_size = 0.01  # 约1km
    hotspots = {}
    
    for event in security_events:
        if not event.location or not event.location.position:
            continue
        
        # 获取位置
        coords = event.location.position.coordinates
        if len(coords) < 2:
            continue
        
        lon, lat = coords
        
        # 计算网格坐标
        grid_lon = round(lon / grid_size) * grid_size
        grid_lat = round(lat / grid_size) * grid_size
        grid_key = f"{grid_lon:.4f},{grid_lat:.4f}"
        
        # 添加到热点统计
        if grid_key not in hotspots:
            hotspots[grid_key] = {
                "center": [grid_lon, grid_lat],
                "count": 0,
                "events": [],
                "levels": {"low": 0, "medium": 0, "high": 0}
            }
        
        hotspots[grid_key]["count"] += 1
        hotspots[grid_key]["events"].append(event.event_id)
        hotspots[grid_key]["levels"][event.level] += 1
    
    # 过滤出符合条件的热点
    filtered_hotspots = []
    for grid_key, data in hotspots.items():
        if data["count"] >= min_events:
            # 计算热点得分
            score = data["levels"]["low"] + data["levels"]["medium"] * 2 + data["levels"]["high"] * 3
            
            filtered_hotspots.append({
                "center": data["center"],
                "count": data["count"],
                "score": score,
                "levels": data["levels"],
                "events": data["events"]
            })
    
    # 按热点得分排序
    sorted_hotspots = sorted(filtered_hotspots, key=lambda x: x["score"], reverse=True)
    
    return sorted_hotspots

# 获取最近的安防事件
@router.get("/recent-events", response_model=List[Dict[str, Any]])
async def get_recent_security_events(
    limit: int = Query(10, ge=1, le=100, description="返回数量"),
    level: Optional[str] = Query(None, description="按级别筛选"),
    current_user: User = Depends(get_current_active_user)
):
    """获取最近的安防事件"""
    # 创建查询条件
    query = {"type": EventType.SECURITY}
    if level:
        query["level"] = level
    
    # 查询最近事件
    events = await Event.find(query).sort("detected_at", -1).limit(limit).to_list()
    
    return [event.dict() for event in events]