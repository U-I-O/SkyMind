from fastapi import APIRouter, Depends, HTTPException, Query, status, Body
from typing import Dict, List, Any, Optional
from datetime import datetime

from config.logging_config import get_logger
from database.models import Task, User, TaskStatus, TaskType, Location, GeoPoint, TimeWindow, Drone
from core.security import get_current_active_user
from agents.coordinator import get_coordinator

logger = get_logger("api.tasks")

router = APIRouter()

# 获取所有任务
@router.get("/", response_model=List[Dict[str, Any]])
async def get_all_tasks(
    status: Optional[str] = Query(None, description="按状态筛选"),
    task_type: Optional[str] = Query(None, description="按类型筛选"),
    limit: int = Query(100, ge=1, le=1000),
    skip: int = Query(0, ge=0),
    sort_by: str = Query("created_at", description="排序字段"),
    sort_order: int = Query(-1, description="排序顺序: 1 升序, -1 降序"),
    current_user: User = Depends(get_current_active_user)
):
    """获取所有任务"""
    # 创建查询条件
    query = {}
    if status:
        query["status"] = status
    if task_type:
        query["type"] = task_type
    
    # 查询数据库
    tasks = await Task.find(query).sort(sort_by, sort_order).skip(skip).limit(limit).to_list()
    
    # 格式化结果
    result = []
    for task in tasks:
        task_dict = task.dict()
        
        # 添加关联无人机信息
        if task.assigned_drones:
            drones = await Drone.find({"drone_id": {"$in": task.assigned_drones}}).to_list()
            task_dict["drone_details"] = [
                {
                    "drone_id": drone.drone_id,
                    "name": drone.name,
                    "status": drone.status,
                    "battery_level": drone.battery_level
                }
                for drone in drones
            ]
        
        result.append(task_dict)
    
    return result

# 获取单个任务详情
@router.get("/{task_id}", response_model=Dict[str, Any])
async def get_task(
    task_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """获取单个任务详情"""
    task = await Task.find_one({"task_id": task_id})
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在"
        )
    
    # 格式化结果
    result = task.dict()
    
    # 添加关联无人机信息
    if task.assigned_drones:
        drones = await Drone.find({"drone_id": {"$in": task.assigned_drones}}).to_list()
        result["drone_details"] = [
            {
                "drone_id": drone.drone_id,
                "name": drone.name,
                "status": drone.status,
                "battery_level": drone.battery_level
            }
            for drone in drones
        ]
    
    return result

# 创建新任务
@router.post("/", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
async def create_task(
    task_data: Dict[str, Any] = Body(...),
    current_user: User = Depends(get_current_active_user)
):
    """创建新任务"""
    # 检查必需字段
    required_fields = ["title", "description", "type"]
    for field in required_fields:
        if field not in task_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"缺少必需字段: {field}"
            )
    
    # 验证任务类型
    task_type = task_data["type"]
    if task_type not in [t.value for t in TaskType]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"无效的任务类型: {task_type}"
        )
    
    # 处理起点和终点
    start_location = None
    if "start_location" in task_data:
        start_loc = task_data["start_location"]
        if isinstance(start_loc, dict) and "position" in start_loc:
            pos = start_loc["position"]
            start_location = Location(
                position=GeoPoint(
                    type="Point",
                    coordinates=pos["coordinates"],
                    altitude=pos.get("altitude")
                ),
                address=start_loc.get("address"),
                name=start_loc.get("name")
            )
    
    end_location = None
    if "end_location" in task_data:
        end_loc = task_data["end_location"]
        if isinstance(end_loc, dict) and "position" in end_loc:
            pos = end_loc["position"]
            end_location = Location(
                position=GeoPoint(
                    type="Point",
                    coordinates=pos["coordinates"],
                    altitude=pos.get("altitude")
                ),
                address=end_loc.get("address"),
                name=end_loc.get("name")
            )
    
    # 处理时间窗口
    time_window = None
    if "time_window" in task_data:
        tw = task_data["time_window"]
        if isinstance(tw, dict) and "start_time" in tw and "end_time" in tw:
            time_window = TimeWindow(
                start_time=datetime.fromisoformat(tw["start_time"]),
                end_time=datetime.fromisoformat(tw["end_time"])
            )
    
    # 创建任务对象
    task = Task(
        title=task_data["title"],
        description=task_data["description"],
        type=task_type,
        priority=task_data.get("priority", 5),
        created_by=current_user.username,
        start_location=start_location,
        end_location=end_location,
        time_window=time_window,
        task_data=task_data.get("task_data")
    )
    
    # 处理相关事件
    if "related_events" in task_data:
        task.related_events = task_data["related_events"]
    
    # 保存到数据库
    await task.insert()
    
    logger.info(f"创建了新任务: {task.task_id}")
    
    # 通知协调者
    coordinator = await get_coordinator()
    await coordinator.message_queue.put({
        "type": "new_task",
        "task_id": task.task_id,
        "source_agent_id": "api"
    })
    
    return task.dict()

# 更新任务信息
@router.put("/{task_id}", response_model=Dict[str, Any])
async def update_task(
    task_id: str,
    task_data: Dict[str, Any] = Body(...),
    current_user: User = Depends(get_current_active_user)
):
    """更新任务信息"""
    # 获取任务
    task = await Task.find_one({"task_id": task_id})
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在"
        )
    
    # 检查状态
    if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"任务已{task.status}，无法更新"
        )
    
    # 更新基本字段
    update_fields = ["title", "description", "priority", "status"]
    for field in update_fields:
        if field in task_data:
            setattr(task, field, task_data[field])
    
    # 处理起点和终点
    if "start_location" in task_data:
        start_loc = task_data["start_location"]
        if isinstance(start_loc, dict) and "position" in start_loc:
            pos = start_loc["position"]
            task.start_location = Location(
                position=GeoPoint(
                    type="Point",
                    coordinates=pos["coordinates"],
                    altitude=pos.get("altitude")
                ),
                address=start_loc.get("address"),
                name=start_loc.get("name")
            )
    
    if "end_location" in task_data:
        end_loc = task_data["end_location"]
        if isinstance(end_loc, dict) and "position" in end_loc:
            pos = end_loc["position"]
            task.end_location = Location(
                position=GeoPoint(
                    type="Point",
                    coordinates=pos["coordinates"],
                    altitude=pos.get("altitude")
                ),
                address=end_loc.get("address"),
                name=end_loc.get("name")
            )
    
    # 处理时间窗口
    if "time_window" in task_data:
        tw = task_data["time_window"]
        if isinstance(tw, dict) and "start_time" in tw and "end_time" in tw:
            task.time_window = TimeWindow(
                start_time=datetime.fromisoformat(tw["start_time"]),
                end_time=datetime.fromisoformat(tw["end_time"])
            )
    
    # 处理相关事件
    if "related_events" in task_data:
        task.related_events = task_data["related_events"]
    
    # 处理任务数据
    if "task_data" in task_data:
        task.task_data = task_data["task_data"]
    
    # 保存更新
    await task.save()
    
    logger.info(f"更新了任务信息: {task_id}")
    
    # 通知任务更新
    coordinator = await get_coordinator()
    await coordinator.message_queue.put({
        "type": "task_updated",
        "task_id": task.task_id,
        "source_agent_id": "api"
    })
    
    return task.dict()

# 取消任务
@router.post("/{task_id}/cancel", response_model=Dict[str, Any])
async def cancel_task(
    task_id: str,
    cancel_data: Dict[str, Any] = Body(...),
    current_user: User = Depends(get_current_active_user)
):
    """取消任务"""
    # 获取任务
    task = await Task.find_one({"task_id": task_id})
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在"
        )
    
    # 检查状态
    if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"任务已{task.status}，无法取消"
        )
    
    # 更新状态
    task.status = TaskStatus.CANCELLED
    task.end_time = datetime.utcnow()
    
    # 添加取消原因
    reason = cancel_data.get("reason", "用户取消")
    task.task_data = task.task_data or {}
    task.task_data["cancel_reason"] = reason
    task.task_data["cancelled_by"] = current_user.username
    
    # 保存更新
    await task.save()
    
    logger.info(f"取消了任务: {task_id}, 原因: {reason}")
    
    # 通知任务取消
    coordinator = await get_coordinator()
    await coordinator.message_queue.put({
        "type": "task_cancelled",
        "task_id": task.task_id,
        "source_agent_id": "api",
        "reason": reason
    })
    
    # 释放分配的无人机
    if task.assigned_drones:
        for drone_id in task.assigned_drones:
            drone = await Drone.find_one({"drone_id": drone_id})
            if drone:
                drone.assigned_tasks = [t for t in drone.assigned_tasks if t != task_id]
                if not drone.assigned_tasks:
                    drone.status = "idle"
                await drone.save()
    
    return {
        "task_id": task_id,
        "status": "cancelled",
        "reason": reason,
        "cancelled_at": task.end_time.isoformat() if task.end_time else None
    }

# 获取任务统计信息
@router.get("/statistics/status", response_model=Dict[str, int])
async def get_task_status_statistics(
    current_user: User = Depends(get_current_active_user)
):
    """获取任务状态统计信息"""
    # 统计各种状态的任务数量
    result = {}
    
    for status in TaskStatus:
        count = await Task.find({"status": status}).count()
        result[status] = count
    
    # 添加总数
    total = await Task.find_all().count()
    result["total"] = total
    
    return result

# 获取任务类型统计信息
@router.get("/statistics/type", response_model=Dict[str, int])
async def get_task_type_statistics(
    current_user: User = Depends(get_current_active_user)
):
    """获取任务类型统计信息"""
    # 统计各种类型的任务数量
    result = {}
    
    for task_type in TaskType:
        count = await Task.find({"type": task_type}).count()
        result[task_type] = count
    
    # 添加总数
    total = await Task.find_all().count()
    result["total"] = total
    
    return result

# 手动分配无人机到任务
@router.post("/{task_id}/assign", response_model=Dict[str, Any])
async def assign_drone_to_task(
    task_id: str,
    assign_data: Dict[str, Any] = Body(...),
    current_user: User = Depends(get_current_active_user)
):
    """手动分配无人机到任务"""
    # 检查必需字段
    if "drone_ids" not in assign_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="缺少必需字段: drone_ids"
        )
    
    drone_ids = assign_data["drone_ids"]
    
    # 获取任务
    task = await Task.find_one({"task_id": task_id})
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在"
        )
    
    # 检查状态
    if task.status not in [TaskStatus.PENDING, TaskStatus.ASSIGNED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"任务状态为{task.status}，无法分配无人机"
        )
    
    # 验证无人机
    valid_drones = []
    for drone_id in drone_ids:
        drone = await Drone.find_one({"drone_id": drone_id})
        if not drone:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"无人机不存在: {drone_id}"
            )
        valid_drones.append(drone)
    
    # 更新任务
    task.assigned_drones = drone_ids
    task.status = TaskStatus.ASSIGNED
    await task.save()
    
    # 更新无人机
    for drone in valid_drones:
        if task_id not in drone.assigned_tasks:
            drone.assigned_tasks.append(task_id)
        drone.status = "flying"
        await drone.save()
    
    logger.info(f"手动分配了无人机 {drone_ids} 到任务 {task_id}")
    
    # 通知任务更新
    coordinator = await get_coordinator()
    await coordinator.message_queue.put({
        "type": "task_assigned",
        "task_id": task.task_id,
        "drone_ids": drone_ids,
        "source_agent_id": "api"
    })
    
    return {
        "task_id": task_id,
        "status": task.status,
        "assigned_drones": drone_ids
    }

# 批量获取任务
@router.post("/batch", response_model=List[Dict[str, Any]])
async def batch_get_tasks(
    task_ids: List[str] = Body(..., embed=True),
    current_user: User = Depends(get_current_active_user)
):
    """批量获取任务"""
    tasks = await Task.find({"task_id": {"$in": task_ids}}).to_list()
    
    return [task.dict() for task in tasks]