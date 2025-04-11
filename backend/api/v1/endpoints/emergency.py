from fastapi import APIRouter, Depends, HTTPException, Query, status, Body
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import json

from config.logging_config import get_logger
from database.models import User, Event, Task, TaskType, TaskStatus, EventType, EventLevel, Location, GeoPoint
from core.security import get_current_active_user
from agents.coordinator import get_coordinator
from agents.response import create_response_agent

logger = get_logger("api.emergency")

router = APIRouter()

# 获取紧急事件
@router.get("/events", response_model=List[Dict[str, Any]])
async def get_emergency_events(
    days: int = Query(7, ge=1, le=30, description="最近天数"),
    level: Optional[str] = Query(None, description="按级别筛选"),
    status: Optional[str] = Query(None, description="按状态筛选"),
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(get_current_active_user)
):
    """获取紧急事件"""
    # 计算时间范围
    now = datetime.utcnow()
    start_time = now - timedelta(days=days)
    
    # 创建查询条件
    query = {
        "type": EventType.EMERGENCY,
        "detected_at": {"$gte": start_time}
    }
    
    if level:
        query["level"] = level
    if status:
        query["status"] = status
    
    # 查询数据库
    events = await Event.find(query).sort("detected_at", -1).limit(limit).to_list()
    
    # 格式化结果
    result = []
    for event in events:
        event_dict = event.dict()
        
        # 添加关联任务信息
        if event.related_tasks:
            tasks = await Task.find({"task_id": {"$in": event.related_tasks}}).to_list()
            event_dict["task_details"] = [
                {
                    "task_id": task.task_id,
                    "title": task.title,
                    "status": task.status,
                    "type": task.type
                }
                for task in tasks
            ]
        
        result.append(event_dict)
    
    return result

# 获取应急任务
@router.get("/tasks", response_model=List[Dict[str, Any]])
async def get_emergency_tasks(
    days: int = Query(7, ge=1, le=30, description="最近天数"),
    status: Optional[str] = Query(None, description="按状态筛选"),
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(get_current_active_user)
):
    """获取应急任务"""
    # 计算时间范围
    now = datetime.utcnow()
    start_time = now - timedelta(days=days)
    
    # 创建查询条件
    query = {
        "type": TaskType.EMERGENCY,
        "created_at": {"$gte": start_time}
    }
    
    if status:
        query["status"] = status
    
    # 查询数据库
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
                    "level": event.level,
                    "status": event.status
                }
                for event in events
            ]
        
        result.append(task_dict)
    
    return result

# 报告紧急事件
@router.post("/report", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
async def report_emergency(
    report_data: Dict[str, Any] = Body(...),
    current_user: User = Depends(get_current_active_user)
):
    """报告紧急事件"""
    # 检查必需字段
    required_fields = ["title", "description", "level"]
    for field in required_fields:
        if field not in report_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"缺少必需字段: {field}"
            )
    
    # 验证级别
    level = report_data["level"]
    if level not in [l.value for l in EventLevel]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"无效的事件级别: {level}"
        )
    
    # 处理位置信息
    location = None
    if "location" in report_data:
        loc_data = report_data["location"]
        if isinstance(loc_data, dict) and "position" in loc_data:
            pos = loc_data["position"]
            location = Location(
                position=GeoPoint(
                    type="Point",
                    coordinates=pos["coordinates"],
                    altitude=pos.get("altitude")
                ),
                address=loc_data.get("address"),
                name=loc_data.get("name")
            )
    
    # 创建紧急事件
    event = Event(
        type=EventType.EMERGENCY,
        level=level,
        title=report_data["title"],
        description=report_data["description"],
        location=location,
        detected_by=current_user.username,
        detection_data=report_data.get("details")
    )
    
    # 保存到数据库
    await event.insert()
    
    logger.info(f"报告了紧急事件: {event.event_id}")
    
    # 通知协调者
    coordinator = await get_coordinator()
    await coordinator.message_queue.put({
        "type": "new_event",
        "event_id": event.event_id,
        "source_agent_id": "api"
    })
    
    # 如果是高级别事件，立即创建应急任务
    if level == EventLevel.HIGH:
        await create_emergency_task(event)
    
    return event.dict()

# 创建应急任务
@router.post("/tasks", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
async def create_emergency_task_endpoint(
    task_data: Dict[str, Any] = Body(...),
    current_user: User = Depends(get_current_active_user)
):
    """创建应急任务"""
    # 检查必需字段
    if "event_id" not in task_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="缺少事件ID"
        )
    
    event_id = task_data["event_id"]
    
    # 获取事件
    event = await Event.find_one({"event_id": event_id})
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="事件不存在"
        )
    
    # 检查是否已有针对此事件的任务
    existing_task = await Task.find_one({
        "related_events": event_id,
        "status": {"$in": [TaskStatus.PENDING, TaskStatus.ASSIGNED, TaskStatus.IN_PROGRESS]}
    })
    
    if existing_task:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"事件 {event_id} 已有正在进行的应急任务"
        )
    
    # 创建应急任务
    task = await create_emergency_task(event)
    
    logger.info(f"手动创建了应急任务: {task.task_id}")
    
    return task.dict()

# 分析紧急事件
@router.post("/analyze/{event_id}", response_model=Dict[str, Any])
async def analyze_emergency_event(
    event_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """分析紧急事件并生成响应计划"""
    # 获取事件
    event = await Event.find_one({"event_id": event_id})
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="事件不存在"
        )
    
    # 获取应急响应智能体
    coordinator = await get_coordinator()
    response_agents = coordinator._get_agents_by_type("ResponseAgent")
    
    if not response_agents:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="没有可用的应急响应智能体"
        )
    
    response_agent = response_agents[0]
    
    # 查询应急响应智能体
    response = await coordinator.query_agent(
        response_agent.agent_id,
        "analyze_event",
        {"event_id": event_id}
    )
    
    # 检查响应
    if not response["success"]:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"分析事件失败: {response.get('error', '未知错误')}"
        )
    
    # 获取响应计划
    response_plan = response.get("response_plan")
    
    return {
        "event_id": event_id,
        "response_plan": response_plan
    }

# 获取应急统计信息
@router.get("/statistics", response_model=Dict[str, Any])
async def get_emergency_statistics(
    days: int = Query(30, ge=1, le=90, description="统计天数"),
    current_user: User = Depends(get_current_active_user)
):
    """获取应急统计信息"""
    # 计算时间范围
    now = datetime.utcnow()
    start_time = now - timedelta(days=days)
    
    # 总紧急事件数
    total_events = await Event.find({
        "type": EventType.EMERGENCY,
        "detected_at": {"$gte": start_time}
    }).count()
    
    # 按级别统计
    level_stats = {}
    for level in EventLevel:
        count = await Event.find({
            "type": EventType.EMERGENCY,
            "level": level,
            "detected_at": {"$gte": start_time}
        }).count()
        level_stats[level] = count
    
    # 按状态统计
    status_stats = {
        "new": await Event.find({
            "type": EventType.EMERGENCY,
            "status": "new",
            "detected_at": {"$gte": start_time}
        }).count(),
        "processing": await Event.find({
            "type": EventType.EMERGENCY,
            "status": "processing",
            "detected_at": {"$gte": start_time}
        }).count(),
        "resolved": await Event.find({
            "type": EventType.EMERGENCY,
            "status": "resolved",
            "detected_at": {"$gte": start_time}
        }).count()
    }
    
    # 应急任务统计
    total_tasks = await Task.find({
        "type": TaskType.EMERGENCY,
        "created_at": {"$gte": start_time}
    }).count()
    
    # 任务状态统计
    task_status_stats = {}
    for status in TaskStatus:
        count = await Task.find({
            "type": TaskType.EMERGENCY,
            "status": status,
            "created_at": {"$gte": start_time}
        }).count()
        task_status_stats[status] = count
    
    # 平均响应时间（从事件创建到任务完成的时间）
    completed_tasks = await Task.find({
        "type": TaskType.EMERGENCY,
        "status": TaskStatus.COMPLETED,
        "created_at": {"$gte": start_time},
        "end_time": {"$ne": None}
    }).to_list()
    
    avg_response_time = None
    if completed_tasks:
        total_time = 0
        for task in completed_tasks:
            # 找出关联的事件
            if task.related_events:
                event_id = task.related_events[0]
                event = await Event.find_one({"event_id": event_id})
                if event:
                    # 计算从事件创建到任务完成的时间（分钟）
                    time_diff = (task.end_time - event.detected_at).total_seconds() / 60
                    total_time += time_diff
        
        if len(completed_tasks) > 0:
            avg_response_time = total_time / len(completed_tasks)
    
    # 按日期统计事件数
    date_stats = []
    for i in range(days):
        day_start = now - timedelta(days=i+1)
        day_end = now - timedelta(days=i)
        count = await Event.find({
            "type": EventType.EMERGENCY,
            "detected_at": {"$gte": day_start, "$lt": day_end}
        }).count()
        date_stats.append({
            "date": day_start.date().isoformat(),
            "count": count
        })
    
    return {
        "total_events": total_events,
        "level_stats": level_stats,
        "status_stats": status_stats,
        "total_tasks": total_tasks,
        "task_status_stats": task_status_stats,
        "avg_response_time_minutes": avg_response_time,
        "date_stats": date_stats,
        "period_days": days
    }

# 辅助函数：创建应急任务
async def create_emergency_task(event: Event) -> Task:
    """根据事件创建应急任务"""
    # 创建任务
    task = Task(
        title=f"应急响应：{event.title}",
        description=f"针对事件 {event.event_id} 的应急响应任务\n\n{event.description}",
        type=TaskType.EMERGENCY,
        priority=_map_event_level_to_priority(event.level),
        created_by="system",
        start_location=event.location,
        end_location=event.location,
        related_events=[event.event_id],
        task_data={
            "event_data": event.detection_data,
            "emergency_level": event.level
        }
    )
    
    await task.insert()
    
    # 更新事件的关联任务
    event.related_tasks = event.related_tasks or []
    event.related_tasks.append(task.task_id)
    event.status = "processing"
    await event.save()
    
    # 通知协调者
    coordinator = await get_coordinator()
    await coordinator.message_queue.put({
        "type": "new_task",
        "task_id": task.task_id,
        "source_agent_id": "api"
    })
    
    logger.info(f"为事件 {event.event_id} 创建了应急任务: {task.task_id}")
    
    return task

# 辅助函数：将事件级别映射到任务优先级
def _map_event_level_to_priority(event_level: str) -> int:
    """将事件级别映射到任务优先级"""
    if event_level == EventLevel.HIGH:
        return 10
    elif event_level == EventLevel.MEDIUM:
        return 7
    else:
        return 4