from fastapi import APIRouter, Depends, HTTPException, Query, status, Body, File, UploadFile
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import json
import os
from pathlib import Path

from config.logging_config import get_logger
from database.models import Event, User, EventType, EventLevel, Location, GeoPoint, BoundingBox, Task
from core.security import get_current_active_user
from agents.coordinator import get_coordinator

logger = get_logger("api.events")

router = APIRouter()

# 创建证据图片存储目录
EVIDENCE_DIR = Path("./data/evidence")
EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)

# 获取所有事件
@router.get("/", response_model=List[Dict[str, Any]])
async def get_all_events(
    event_type: Optional[str] = Query(None, description="按事件类型筛选"),
    level: Optional[str] = Query(None, description="按事件级别筛选"),
    status: Optional[str] = Query(None, description="按事件状态筛选"),
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    limit: int = Query(100, ge=1, le=1000),
    skip: int = Query(0, ge=0),
    sort_by: str = Query("detected_at", description="排序字段"),
    sort_order: int = Query(-1, description="排序顺序: 1 升序, -1 降序"),
    current_user: User = Depends(get_current_active_user)
):
    """获取所有事件"""
    # 创建查询条件
    query = {}
    if event_type:
        query["type"] = event_type
    if level:
        query["level"] = level
    if status:
        query["status"] = status
    
    # 添加时间范围查询
    if start_time or end_time:
        time_query = {}
        if start_time:
            time_query["$gte"] = start_time
        if end_time:
            time_query["$lte"] = end_time
        if time_query:
            query["detected_at"] = time_query
    
    # 查询数据库
    events = await Event.find(query).sort(sort_by, sort_order).skip(skip).limit(limit).to_list()
    
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

# 获取单个事件详情
@router.get("/{event_id}", response_model=Dict[str, Any])
async def get_event(
    event_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """获取单个事件详情"""
    event = await Event.find_one({"event_id": event_id})
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="事件不存在"
        )
    
    # 格式化结果
    result = event.dict()
    
    # 添加关联任务信息
    if event.related_tasks:
        tasks = await Task.find({"task_id": {"$in": event.related_tasks}}).to_list()
        result["task_details"] = [
            {
                "task_id": task.task_id,
                "title": task.title,
                "status": task.status,
                "type": task.type
            }
            for task in tasks
        ]
    
    return result

# 创建新事件
@router.post("/", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
async def create_event(
    event_data: Dict[str, Any] = Body(...),
    current_user: User = Depends(get_current_active_user)
):
    """创建新事件"""
    # 检查必需字段
    required_fields = ["type", "level", "title", "description"]
    for field in required_fields:
        if field not in event_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"缺少必需字段: {field}"
            )
    
    # 验证事件类型和级别
    event_type = event_data["type"]
    event_level = event_data["level"]
    
    if event_type not in [t.value for t in EventType]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"无效的事件类型: {event_type}"
        )
    
    if event_level not in [l.value for l in EventLevel]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"无效的事件级别: {event_level}"
        )
    
    # 处理位置信息
    location = None
    if "location" in event_data:
        loc = event_data["location"]
        if isinstance(loc, dict) and "position" in loc:
            pos = loc["position"]
            location = Location(
                position=GeoPoint(
                    type="Point",
                    coordinates=pos["coordinates"],
                    altitude=pos.get("altitude")
                ),
                address=loc.get("address"),
                name=loc.get("name")
            )
    
    # 处理边界框
    bounding_boxes = []
    if "bounding_boxes" in event_data:
        for box in event_data["bounding_boxes"]:
            bounding_boxes.append(BoundingBox(
                x1=box["x1"],
                y1=box["y1"],
                x2=box["x2"],
                y2=box["y2"],
                confidence=box["confidence"],
                class_id=box["class_id"],
                class_name=box["class_name"]
            ))
    
    # 创建事件对象
    event = Event(
        type=event_type,
        level=event_level,
        title=event_data["title"],
        description=event_data["description"],
        location=location,
        detected_by=current_user.username,
        status=event_data.get("status", "new"),
        detection_data=event_data.get("detection_data"),
        video_source=event_data.get("video_source"),
        image_evidence=event_data.get("image_evidence", []),
        bounding_boxes=bounding_boxes
    )
    
    # 处理相关任务
    if "related_tasks" in event_data:
        event.related_tasks = event_data["related_tasks"]
    
    # 保存到数据库
    await event.insert()
    
    logger.info(f"创建了新事件: {event.event_id}")
    
    # 通知协调者
    coordinator = await get_coordinator()
    await coordinator.message_queue.put({
        "type": "new_event",
        "event_id": event.event_id,
        "source_agent_id": "api"
    })
    
    return event.dict()

# 更新事件信息
@router.put("/{event_id}", response_model=Dict[str, Any])
async def update_event(
    event_id: str,
    event_data: Dict[str, Any] = Body(...),
    current_user: User = Depends(get_current_active_user)
):
    """更新事件信息"""
    # 获取事件
    event = await Event.find_one({"event_id": event_id})
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="事件不存在"
        )
    
    # 更新基本字段
    update_fields = ["title", "description", "status", "level", "type"]
    for field in update_fields:
        if field in event_data:
            setattr(event, field, event_data[field])
    
    # 处理位置信息
    if "location" in event_data:
        loc = event_data["location"]
        if isinstance(loc, dict) and "position" in loc:
            pos = loc["position"]
            event.location = Location(
                position=GeoPoint(
                    type="Point",
                    coordinates=pos["coordinates"],
                    altitude=pos.get("altitude")
                ),
                address=loc.get("address"),
                name=loc.get("name")
            )
    
    # 处理边界框
    if "bounding_boxes" in event_data:
        boxes = []
        for box in event_data["bounding_boxes"]:
            boxes.append(BoundingBox(
                x1=box["x1"],
                y1=box["y1"],
                x2=box["x2"],
                y2=box["y2"],
                confidence=box["confidence"],
                class_id=box["class_id"],
                class_name=box["class_name"]
            ))
        event.bounding_boxes = boxes
    
    # 处理检测数据
    if "detection_data" in event_data:
        event.detection_data = event_data["detection_data"]
    
    # 处理视频源
    if "video_source" in event_data:
        event.video_source = event_data["video_source"]
    
    # 处理图像证据
    if "image_evidence" in event_data:
        event.image_evidence = event_data["image_evidence"]
    
    # 处理相关任务
    if "related_tasks" in event_data:
        event.related_tasks = event_data["related_tasks"]
    
    # 如果状态变为resolved，添加解决时间和说明
    if event_data.get("status") == "resolved" and event.status != "resolved":
        event.resolved_at = datetime.utcnow()
        event.resolution_notes = event_data.get("resolution_notes", f"由{current_user.username}解决")
    
    # 保存更新
    await event.save()
    
    logger.info(f"更新了事件信息: {event_id}")
    
    # 通知事件更新
    coordinator = await get_coordinator()
    await coordinator.message_queue.put({
        "type": "event_updated",
        "event_id": event.event_id,
        "source_agent_id": "api"
    })
    
    return event.dict()

# 解决事件
@router.post("/{event_id}/resolve", response_model=Dict[str, Any])
async def resolve_event(
    event_id: str,
    resolve_data: Dict[str, Any] = Body(...),
    current_user: User = Depends(get_current_active_user)
):
    """解决事件"""
    # 获取事件
    event = await Event.find_one({"event_id": event_id})
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="事件不存在"
        )
    
    # 检查状态
    if event.status == "resolved":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="事件已解决"
        )
    
    # 更新状态
    event.status = "resolved"
    event.resolved_at = datetime.utcnow()
    
    # 添加解决说明
    resolution_notes = resolve_data.get("resolution_notes", "")
    if resolution_notes:
        event.resolution_notes = resolution_notes
    else:
        event.resolution_notes = f"由{current_user.username}解决"
    
    # 保存更新
    await event.save()
    
    logger.info(f"解决了事件: {event_id}")
    
    # 通知事件解决
    coordinator = await get_coordinator()
    await coordinator.message_queue.put({
        "type": "event_resolved",
        "event_id": event.event_id,
        "source_agent_id": "api"
    })
    
    return {
        "event_id": event_id,
        "status": "resolved",
        "resolved_at": event.resolved_at.isoformat(),
        "resolution_notes": event.resolution_notes
    }

# 上传事件证据图片
@router.post("/{event_id}/evidence", response_model=Dict[str, str])
async def upload_event_evidence(
    event_id: str,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user)
):
    """上传事件证据图片"""
    # 获取事件
    event = await Event.find_one({"event_id": event_id})
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="事件不存在"
        )
    
    # 验证文件类型
    allowed_types = ["image/jpeg", "image/png", "image/jpg"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="仅支持JPEG和PNG图片"
        )
    
    # 生成文件名
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"{event_id}_{timestamp}_{file.filename}"
    file_path = EVIDENCE_DIR / filename
    
    # 保存文件
    with open(file_path, "wb") as f:
        contents = await file.read()
        f.write(contents)
    
    # 更新事件
    event.image_evidence = event.image_evidence or []
    event.image_evidence.append(str(file_path))
    await event.save()
    
    logger.info(f"上传了事件证据图片: {event_id}, {filename}")
    
    return {
        "event_id": event_id,
        "file_name": filename,
        "file_path": str(file_path)
    }

# 获取事件统计信息
@router.get("/statistics/overall", response_model=Dict[str, Any])
async def get_event_statistics(
    days: int = Query(7, ge=1, le=30, description="统计天数"),
    current_user: User = Depends(get_current_active_user)
):
    """获取事件统计信息"""
    # 计算时间范围
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(days=days)
    
    # 统计总数
    total_count = await Event.find().count()
    
    # 统计指定时间范围内的事件数
    period_count = await Event.find({"detected_at": {"$gte": start_time, "$lte": end_time}}).count()
    
    # 统计各类型事件数量
    type_stats = {}
    for event_type in EventType:
        count = await Event.find({"type": event_type}).count()
        type_stats[event_type] = count
    
    # 统计各级别事件数量
    level_stats = {}
    for level in EventLevel:
        count = await Event.find({"level": level}).count()
        level_stats[level] = count
    
    # 统计状态分布
    status_stats = {
        "new": await Event.find({"status": "new"}).count(),
        "processing": await Event.find({"status": "processing"}).count(),
        "resolved": await Event.find({"status": "resolved"}).count()
    }
    
    # 按日期统计
    date_stats = []
    for i in range(days):
        day_start = end_time - timedelta(days=i+1)
        day_end = end_time - timedelta(days=i)
        count = await Event.find({"detected_at": {"$gte": day_start, "$lte": day_end}}).count()
        date_stats.append({
            "date": day_start.date().isoformat(),
            "count": count
        })
    
    return {
        "total_count": total_count,
        "period_count": period_count,
        "type_stats": type_stats,
        "level_stats": level_stats,
        "status_stats": status_stats,
        "date_stats": date_stats,
        "period_days": days
    }

# 获取热点区域
@router.get("/hotspots", response_model=List[Dict[str, Any]])
async def get_event_hotspots(
    days: int = Query(30, ge=1, le=90, description="统计天数"),
    min_events: int = Query(5, ge=1, description="最少事件数"),
    current_user: User = Depends(get_current_active_user)
):
    """获取事件热点区域"""
    # 计算时间范围
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(days=days)
    
    # 查询有位置信息的事件
    events = await Event.find({
        "detected_at": {"$gte": start_time, "$lte": end_time},
        "location": {"$ne": None}
    }).to_list()
    
    # 分析热点区域
    # 简化版实现：根据经纬度网格化
    grid_size = 0.01  # 约1km网格
    hotspots = {}
    
    for event in events:
        if not event.location or not event.location.position:
            continue
        
        # 获取经纬度
        lon, lat = event.location.position.coordinates
        
        # 计算网格坐标
        grid_lon = round(lon / grid_size) * grid_size
        grid_lat = round(lat / grid_size) * grid_size
        grid_key = f"{grid_lon:.4f},{grid_lat:.4f}"
        
        if grid_key not in hotspots:
            hotspots[grid_key] = {
                "center": [grid_lon, grid_lat],
                "events": [],
                "event_count": 0,
                "event_types": {},
                "severity_score": 0
            }
        
        # 添加事件
        hotspots[grid_key]["events"].append(event.event_id)
        hotspots[grid_key]["event_count"] += 1
        
        # 统计事件类型
        event_type = event.type
        if event_type not in hotspots[grid_key]["event_types"]:
            hotspots[grid_key]["event_types"][event_type] = 0
        hotspots[grid_key]["event_types"][event_type] += 1
        
        # 计算严重程度得分
        severity = 1
        if event.level == EventLevel.MEDIUM:
            severity = 2
        elif event.level == EventLevel.HIGH:
            severity = 3
        
        hotspots[grid_key]["severity_score"] += severity
    
    # 过滤并排序热点
    filtered_hotspots = [
        hotspot for grid_key, hotspot in hotspots.items()
        if hotspot["event_count"] >= min_events
    ]
    
    sorted_hotspots = sorted(
        filtered_hotspots,
        key=lambda h: h["severity_score"],
        reverse=True
    )
    
    return sorted_hotspots

# 批量获取事件
@router.post("/batch", response_model=List[Dict[str, Any]])
async def batch_get_events(
    event_ids: List[str] = Body(..., embed=True),
    current_user: User = Depends(get_current_active_user)
):
    """批量获取事件"""
    events = await Event.find({"event_id": {"$in": event_ids}}).to_list()
    
    return [event.dict() for event in events]