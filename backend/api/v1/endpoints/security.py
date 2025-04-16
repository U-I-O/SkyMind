from fastapi import APIRouter, Depends, HTTPException, Query, status, Body, Request
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import uuid  # 添加uuid库，用于生成唯一ID

from config.logging_config import get_logger
from database.models import User, Task, TaskType, TaskStatus, Event, EventType, UserRole
from core.security import get_current_active_user
# 暂时注释掉agent导入
# from agents.coordinator import get_coordinator
# from agents.security import create_security_agent

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
    elif task_type == "patrol":
        query["type"] = TaskType.PATROL
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
    # 屏蔽掉原有的agent代码
    # coordinator = await get_coordinator()
    # security_agents = coordinator._get_agents_by_type("SecurityAgent")
    
    # 使用模拟数据
    logger.info("使用模拟数据替代安防区域API")
    
    # 返回模拟数据
    return [
        {
            "zone_id": str(uuid.uuid4()),
            "name": "示例安防区域1",
            "description": "这是一个模拟的安防区域",
            "type": "高安全区",
            "coordinates": [
                [114.3637, 30.5336],
                [114.3657, 30.5350],
                [114.3621, 30.5360],
                [114.3637, 30.5336]
            ]
        }
    ]

# 获取巡检区域列表
@router.get("/patrol-areas", response_model=List[Dict[str, Any]])
async def get_patrol_areas(
    area_id: Optional[str] = Query(None, description="指定区域ID"),
    current_user: User = Depends(get_current_active_user)
):
    """获取巡检区域列表"""
    # 屏蔽掉原有的agent代码
    # coordinator = await get_coordinator()
    # security_agents = coordinator._get_agents_by_type("SecurityAgent")
    
    # 使用模拟数据
    logger.info("使用模拟数据替代巡检区域API")
    
    # 返回模拟数据
    mock_area = {
        "area_id": area_id or str(uuid.uuid4()),
        "name": "示例巡检区域",
        "description": "这是一个模拟的巡检区域",
        "coordinates": [
            [114.3637, 30.5336],
            [114.3657, 30.5350],
            [114.3621, 30.5360],
            [114.3637, 30.5336]
        ]
    }
    
    if area_id:
        return [mock_area]
    else:
        return [
            mock_area,
            {
                "area_id": str(uuid.uuid4()),
                "name": "示例巡检区域2",
                "description": "这是另一个模拟的巡检区域",
                "coordinates": [
                    [114.3537, 30.5236],
                    [114.3557, 30.5250],
                    [114.3521, 30.5260],
                    [114.3537, 30.5236]
                ]
            }
        ]

@router.get("/patrol-tasks", response_model=List[Dict[str, Any]])
async def get_all_surveillance_tasks(
    current_user: User = Depends(get_current_active_user)
):
    """获取所有巡逻任务，不带任何过滤条件"""
    
    logger.info(f"用户 {current_user.username} 请求获取所有巡逻任务")
    
    # 只过滤任务类型
    query = {
        "type": TaskType.SURVEILLANCE
    }
    
    # 执行查询并记录结果
    tasks = await Task.find(query).sort([("created_at", -1)]).to_list()
    
    # 记录详细的任务信息
    logger.info(f"查询到 {len(tasks)} 个巡逻任务")    
    result = [task.model_dump(mode='json') for task in tasks]
    return result

# 创建巡检任务
@router.post("/patrol-tasks", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
async def create_patrol_task(
    task_data: Dict[str, Any] = Body(...),
    current_user: User = Depends(get_current_active_user),
    request: Request = None
):
    """创建巡检任务"""
    # 记录详细的请求信息
    if request:
        all_headers = dict(request.headers.items())
        logger.info(f"所有请求头: {all_headers}")
        
        # 专门检查授权头
        auth_header = request.headers.get("Authorization", "None")
        logger.info(f"接收到创建巡检任务请求，认证头: {auth_header}")
        logger.info(f"认证头长度: {len(auth_header) if auth_header != 'None' else 0}")
        
        # 记录请求来源信息
        client_host = request.client.host if request.client else "unknown"
        logger.info(f"客户端: {client_host}")
    else:
        logger.warning("无法获取请求对象")
    
    # 记录请求体（去除敏感信息）
    task_data_log = {k: v for k, v in task_data.items() if k not in ['token']}
    logger.info(f"请求体数据: {task_data_log}")
    
    # 获取巡逻区域 - 兼容两种可能的字段名
    patrol_area = task_data.get("patrol_area") or task_data.get("patrolArea")
    
    # 获取无人机ID列表 - 兼容两种可能的字段名
    assigned_drones = task_data.get("assigned_drones") or task_data.get("droneIds") or []
    
    # 获取调度信息 - 兼容可能缺失的情况
    schedule = task_data.get("schedule") or {"type": "once"}
    schedule_type = schedule.get("type", "once")
    
    # 检查必需字段
    if not patrol_area:
        logger.error("请求缺少巡逻区域信息")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="缺少巡逻区域信息"
        )
    
    # 记录关键字段
    logger.info(f"巡逻区域: {patrol_area}")
    logger.info(f"关联无人机: {assigned_drones}")
    logger.info(f"调度信息: {schedule}")
    
    # 记录当前用户信息
    try:
        logger.info(f"当前用户: {current_user.username} (ID: {current_user.id})")
        logger.info(f"用户角色: {getattr(current_user, 'role', 'unknown')}")
    except Exception as e:
        logger.error(f"记录用户信息时出错: {str(e)}")
    
    logger.info("使用模拟数据创建巡检任务")
    
    # 创建任务
    try:
        # 生成任务ID
        task_id = str(uuid.uuid4())
        
        # 处理日期和时间
        scheduled_datetime = None
        schedule_type = schedule.get("type", "once")
        
        # 根据调度类型处理日期
        if schedule_type == "date" and schedule.get("date"):
            # 处理ISO格式日期字符串
            try:
                # 尝试解析ISO格式日期
                date_str = schedule.get("date")
                if isinstance(date_str, str):
                    # 解析ISO日期字符串
                    date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                    scheduled_datetime = date_obj
                else:
                    # 如果是时间戳（数字）
                    scheduled_datetime = datetime.fromtimestamp(int(date_str) / 1000)
            except Exception as e:
                logger.error(f"日期解析错误: {e}, 使用默认日期")
                scheduled_datetime = datetime.utcnow() + timedelta(hours=1)
        
        # 如果有时间字段，合并到日期中
        time_str = schedule.get("time")
        if time_str and isinstance(time_str, str) and scheduled_datetime:
            try:
                # 解析时间字符串 "HH:MM"
                hour, minute = map(int, time_str.split(':'))
                scheduled_datetime = scheduled_datetime.replace(hour=hour, minute=minute)
            except Exception as e:
                logger.error(f"时间解析错误: {e}, 保持原有时间")
        
        # 如果未设置scheduled_datetime，使用默认值
        if not scheduled_datetime:
            scheduled_datetime = datetime.utcnow() + timedelta(hours=1)
        
        # 创建任务数据
        task = Task(
            task_id=task_id,
            title=task_data.get("title", "新巡检任务"),
            description=task_data.get("description", f"于{datetime.utcnow().strftime('%Y-%m-%d %H:%M')}创建的巡检任务"),
            type=TaskType.SURVEILLANCE,
            status=TaskStatus.PENDING,
            created_by=str(current_user.id),
            created_at=datetime.utcnow(),
            
            # 使用处理后的日期时间
            scheduled_at=scheduled_datetime,
            
            # 保存完整的调度信息
            schedule=schedule,
            
            # 保存关联的无人机ID
            assigned_drones=assigned_drones,
            
            patrol_area=patrol_area,
            priority=task_data.get("priority", 1),
            rounds=task_data.get("rounds", 1),
            altitude=task_data.get("altitude", 50),
            speed=task_data.get("speed", 5)
        )
        
        # 保存到数据库
        await task.insert()
        
        # 返回创建的任务
        logger.info(f"成功创建巡检任务: {task_id}")
        return task.model_dump(mode='json')
        
    except Exception as e:
        logger.error(f"创建任务失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建巡检任务失败: {str(e)}"
        )

# 获取巡逻任务详情
@router.get("/patrol-tasks/{task_id}", response_model=Dict[str, Any])
async def get_patrol_task(
    task_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """获取巡逻任务详情"""
    task = await Task.find_one({"task_id": task_id, "type": TaskType.SURVEILLANCE})
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="巡逻任务不存在"
        )
    
    # 格式化任务信息
    task_dict = task.dict()
    
    # 添加创建者信息
    if task.created_by:
        try:
            creator = await User.find_one({"id": task.created_by})
            if creator:
                task_dict["creator"] = {
                    "username": creator.username,
                    "role": creator.role
                }
        except Exception as e:
            logger.error(f"获取创建者信息失败: {str(e)}")
    
    return task_dict

# 更新巡逻任务
@router.put("/patrol-tasks/{task_id}", response_model=Dict[str, Any])
async def update_patrol_task(
    task_id: str,
    task_data: Dict[str, Any] = Body(...),
    current_user: User = Depends(get_current_active_user)
):
    """更新巡逻任务"""
    # 记录操作信息
    logger.info(f"用户 {current_user.username} 正在更新任务 {task_id}")
    logger.info(f"更新数据: {task_data}")
    
    # 获取任务
    task = await Task.find_one({"task_id": task_id, "type": TaskType.SURVEILLANCE})
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="巡逻任务不存在"
        )
    
    # 检查权限 (只有任务创建者或管理员可以更新)
    if str(task.created_by) != str(current_user.id) and current_user.role != UserRole.ADMIN:
        logger.warning(f"用户 {current_user.username} 无权更新任务 {task_id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权更新此任务"
        )
    
    # 可更新的字段列表
    updatable_fields = [
        "title", "description", "status", "priority", 
        "rounds", "altitude", "speed", "assigned_drones",
        "schedule", "patrol_area"
    ]
    
    # 过滤有效的更新字段
    update_data = {k: v for k, v in task_data.items() if k in updatable_fields}
    
    # 特殊处理 schedule 字段
    if "schedule" in update_data:
        schedule = update_data["schedule"]
        # 确保schedule包含必要的字段
        if not isinstance(schedule, dict):
            schedule = {"type": "once"}
        if "type" not in schedule:
            schedule["type"] = "once"
        if "weekdays" not in schedule:
            schedule["weekdays"] = []
            
        # 处理日期时间
        if schedule["type"] == "date" and schedule.get("date"):
            try:
                # 更新任务的scheduled_at字段
                date_str = schedule.get("date")
                if isinstance(date_str, str):
                    date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                    task.scheduled_at = date_obj
                else:
                    # 如果是时间戳
                    task.scheduled_at = datetime.fromtimestamp(int(date_str) / 1000)
                    
                # 处理时间部分
                time_str = schedule.get("time")
                if time_str and isinstance(time_str, str):
                    hour, minute = map(int, time_str.split(':'))
                    task.scheduled_at = task.scheduled_at.replace(hour=hour, minute=minute)
            except Exception as e:
                logger.error(f"处理调度日期时出错: {e}")
    
    # 更新任务字段
    for field, value in update_data.items():
        setattr(task, field, value)
    
    # 保存更新
    try:
        await task.save()
        logger.info(f"任务 {task_id} 更新成功")
        return task.model_dump(mode='json')
    except Exception as e:
        logger.error(f"保存任务更新时出错: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新任务失败: {str(e)}"
        )

# 删除巡逻任务
@router.delete("/patrol-tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_patrol_task(
    task_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """删除巡逻任务"""
    # 记录操作
    logger.info(f"用户 {current_user.username} 尝试删除任务 {task_id}")
    
    # 查找任务
    task = await Task.find_one({"task_id": task_id, "type": TaskType.SURVEILLANCE})
    if not task:
        logger.warning(f"任务 {task_id} 不存在")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="巡逻任务不存在"
        )
    
    # 检查权限 (只有任务创建者或管理员可以删除)
    if str(task.created_by) != str(current_user.id) and current_user.role != UserRole.ADMIN:
        logger.warning(f"用户 {current_user.username} 无权删除任务 {task_id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="没有权限删除此任务"
        )
    
    # 检查任务状态 (不能删除正在执行的任务)
    if task.status == TaskStatus.IN_PROGRESS:
        logger.warning(f"无法删除正在执行的任务 {task_id}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无法删除正在执行的任务，请先停止任务"
        )
    
    # 删除任务
    try:
        await task.delete()
        logger.info(f"任务 {task_id} 已成功删除")
        return None
    except Exception as e:
        logger.error(f"删除任务 {task_id} 时出错: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除任务失败: {str(e)}"
        )

# 获取异常历史
@router.get("/anomalies", response_model=Dict[str, List[Dict[str, Any]]])
async def get_anomaly_history(
    area_id: Optional[str] = Query(None, description="指定区域ID"),
    days: int = Query(30, ge=1, le=90, description="最近天数"),
    current_user: User = Depends(get_current_active_user)
):
    """获取异常历史"""
    # 屏蔽掉原有的agent代码
    # coordinator = await get_coordinator()
    # security_agents = coordinator._get_agents_by_type("SecurityAgent")
    
    logger.info("使用模拟数据替代异常历史API")
    
    # 使用模拟数据
    mock_anomalies = [
        {
            "anomaly_id": str(uuid.uuid4()),
            "type": "intrusion",
            "level": "medium",
            "detected_at": (datetime.utcnow() - timedelta(days=i)).isoformat(),
            "location": [114.3637 + i*0.001, 30.5336 + i*0.001],
            "description": f"模拟异常事件 {i+1}"
        }
        for i in range(5)
    ]
    
    if area_id:
        return {"anomalies": mock_anomalies}
    else:
        return {"anomaly_history": {"area1": mock_anomalies[:2], "area2": mock_anomalies[2:]}}

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
    # 直接使用模拟数据
    logger.info("使用模拟数据替代热点区域API")
    
    # 返回模拟热点数据
    return [
        {
            "center": [114.3637, 30.5336],
            "count": 8,
            "score": 14,
            "levels": {"low": 2, "medium": 4, "high": 2},
            "events": [str(uuid.uuid4()) for _ in range(8)]
        },
        {
            "center": [114.3437, 30.5136],
            "count": 5,
            "score": 9,
            "levels": {"low": 1, "medium": 3, "high": 1},
            "events": [str(uuid.uuid4()) for _ in range(5)]
        },
        {
            "center": [114.3837, 30.5236],
            "count": 3,
            "score": 4,
            "levels": {"low": 2, "medium": 1, "high": 0},
            "events": [str(uuid.uuid4()) for _ in range(3)]
        }
    ]

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