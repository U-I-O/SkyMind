from fastapi import APIRouter, Depends, HTTPException, Query, status, Body
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import json

from config.logging_config import get_logger
from database.models import (
    User, Task, TaskType, TaskStatus, Drone, Location,
    GeoPoint, TimeWindow, FlightPath
)
from core.security import get_current_active_user
from agents.coordinator import get_coordinator
from agents.logistics import create_logistics_agent

logger = get_logger("api.logistics")

router = APIRouter()

# 获取物流任务
@router.get("/tasks", response_model=List[Dict[str, Any]])
async def get_logistics_tasks(
    status: Optional[str] = Query(None, description="按状态筛选"),
    days: int = Query(7, ge=1, le=30, description="最近天数"),
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(get_current_active_user)
):
    """获取物流任务"""
    # 计算时间范围
    now = datetime.utcnow()
    start_time = now - timedelta(days=days)
    
    # 创建查询条件
    query = {
        "type": TaskType.DELIVERY,
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

# 创建物流任务
@router.post("/tasks", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
async def create_logistics_task(
    task_data: Dict[str, Any] = Body(...),
    current_user: User = Depends(get_current_active_user)
):
    """创建物流任务"""
    # 检查必需字段
    required_fields = ["title", "description", "start_location", "end_location"]
    for field in required_fields:
        if field not in task_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"缺少必需字段: {field}"
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
            try:
                time_window = TimeWindow(
                    start_time=datetime.fromisoformat(tw["start_time"]),
                    end_time=datetime.fromisoformat(tw["end_time"])
                )
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="无效的时间格式"
                )
    
    # 创建任务
    task = Task(
        title=task_data["title"],
        description=task_data["description"],
        type=TaskType.DELIVERY,
        priority=task_data.get("priority", 5),
        created_by=current_user.username,
        start_location=start_location,
        end_location=end_location,
        time_window=time_window
    )
    
    # 处理负载信息
    if "payload" in task_data:
        payload = task_data["payload"]
        task.task_data = task.task_data or {}
        task.task_data["payload"] = payload
        
        # 提取负载重量
        if isinstance(payload, dict) and "weight" in payload:
            task.task_data["payload_weight"] = payload["weight"]
    
    await task.insert()
    
    logger.info(f"创建了物流任务: {task.task_id}")
    
    # 通知协调者
    coordinator = await get_coordinator()
    await coordinator.message_queue.put({
        "type": "new_task",
        "task_id": task.task_id,
        "source_agent_id": "api"
    })
    
    return task.dict()

# 获取配送统计信息
@router.get("/statistics", response_model=Dict[str, Any])
async def get_logistics_statistics(
    current_user: User = Depends(get_current_active_user)
):
    """获取配送统计信息"""
    # 获取物流智能体
    coordinator = await get_coordinator()
    logistics_agents = coordinator._get_agents_by_type("LogisticsAgent")
    
    if not logistics_agents:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="没有可用的物流智能体"
        )
    
    logistics_agent = logistics_agents[0]
    
    # 查询物流智能体
    response = await coordinator.query_agent(
        logistics_agent.agent_id,
        "get_delivery_statistics",
        {}
    )
    
    # 检查响应
    if not response["success"]:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取统计信息失败: {response.get('error', '未知错误')}"
        )
    
    statistics = response.get("statistics", {})
    
    # 补充其他统计信息
    # 计算时间范围
    now = datetime.utcnow()
    last_month = now - timedelta(days=30)
    
    # 月度任务数
    monthly_tasks = await Task.find({
        "type": TaskType.DELIVERY,
        "created_at": {"$gte": last_month}
    }).count()
    
    # 月度完成任务数
    monthly_completed = await Task.find({
        "type": TaskType.DELIVERY,
        "status": TaskStatus.COMPLETED,
        "created_at": {"$gte": last_month}
    }).count()
    
    # 按日期统计
    date_stats = []
    for i in range(30):
        day_start = now - timedelta(days=i+1)
        day_end = now - timedelta(days=i)
        
        count = await Task.find({
            "type": TaskType.DELIVERY,
            "created_at": {"$gte": day_start, "$lt": day_end}
        }).count()
        
        completed = await Task.find({
            "type": TaskType.DELIVERY,
            "status": TaskStatus.COMPLETED,
            "created_at": {"$gte": day_start, "$lt": day_end}
        }).count()
        
        date_stats.append({
            "date": day_start.date().isoformat(),
            "total": count,
            "completed": completed
        })
    
    # 合并统计信息
    if "monthly_tasks" not in statistics:
        statistics["monthly_tasks"] = monthly_tasks
    if "monthly_completed" not in statistics:
        statistics["monthly_completed"] = monthly_completed
    if "date_stats" not in statistics:
        statistics["date_stats"] = date_stats
    
    # 添加完成率
    if "total_tasks" in statistics and statistics["total_tasks"] > 0:
        statistics["completion_rate"] = statistics["completed_tasks"] / statistics["total_tasks"]
    
    return statistics

# 估算配送时间
@router.post("/estimate-delivery", response_model=Dict[str, Any])
async def estimate_delivery_time(
    delivery_data: Dict[str, Any] = Body(...),
    current_user: User = Depends(get_current_active_user)
):
    """估算配送时间"""
    # 检查必需字段
    required_fields = ["start_point", "end_point"]
    for field in required_fields:
        if field not in delivery_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"缺少必需字段: {field}"
            )
    
    # 获取物流智能体
    coordinator = await get_coordinator()
    logistics_agents = coordinator._get_agents_by_type("LogisticsAgent")
    
    if not logistics_agents:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="没有可用的物流智能体"
        )
    
    logistics_agent = logistics_agents[0]
    
    # 查询物流智能体
    response = await coordinator.query_agent(
        logistics_agent.agent_id,
        "estimate_delivery_time",
        {
            "start_point": delivery_data["start_point"],
            "end_point": delivery_data["end_point"]
        }
    )
    
    # 检查响应
    if not response["success"]:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"估算配送时间失败: {response.get('error', '未知错误')}"
        )
    
    return response

# 规划路径
@router.post("/plan-path", response_model=Dict[str, Any])
async def plan_delivery_path(
    path_data: Dict[str, Any] = Body(...),
    current_user: User = Depends(get_current_active_user)
):
    """规划配送路径"""
    # 检查必需字段
    required_fields = ["start_point", "end_point"]
    for field in required_fields:
        if field not in path_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"缺少必需字段: {field}"
            )
    
    # 获取路径规划智能体
    coordinator = await get_coordinator()
    planner_agents = coordinator._get_agents_by_type("PathPlanningAgent")
    
    if not planner_agents:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="没有可用的路径规划智能体"
        )
    
    planner_agent = planner_agents[0]
    
    # 查询路径规划智能体
    response = await coordinator.query_agent(
        planner_agent.agent_id,
        "plan_path",
        {
            "start_point": path_data["start_point"],
            "end_point": path_data["end_point"]
        }
    )
    
    # 检查响应
    if not response["success"]:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"规划路径失败: {response.get('error', '未知错误')}"
        )
    
    return response

# 检查无人机可用性
@router.get("/drone-availability", response_model=Dict[str, Any])
async def check_drone_availability(
    drone_id: Optional[str] = Query(None, description="指定无人机ID"),
    current_user: User = Depends(get_current_active_user)
):
    """检查无人机可用性"""
    # 获取物流智能体
    coordinator = await get_coordinator()
    logistics_agents = coordinator._get_agents_by_type("LogisticsAgent")
    
    if not logistics_agents:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="没有可用的物流智能体"
        )
    
    logistics_agent = logistics_agents[0]
    
    # 查询物流智能体
    response = await coordinator.query_agent(
        logistics_agent.agent_id,
        "get_drone_availability",
        {"drone_id": drone_id} if drone_id else {}
    )
    
    # 检查响应
    if not response["success"]:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"检查无人机可用性失败: {response.get('error', '未知错误')}"
        )
    
    return response

# 批量创建物流任务
@router.post("/batch-tasks", response_model=List[Dict[str, Any]])
async def create_batch_logistics_tasks(
    tasks_data: List[Dict[str, Any]] = Body(...),
    current_user: User = Depends(get_current_active_user)
):
    """批量创建物流任务"""
    if not tasks_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="任务列表为空"
        )
    
    created_tasks = []
    
    for task_data in tasks_data:
        # 检查必需字段
        required_fields = ["title", "description", "start_location", "end_location"]
        for field in required_fields:
            if field not in task_data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"缺少必需字段: {field}"
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
                try:
                    time_window = TimeWindow(
                        start_time=datetime.fromisoformat(tw["start_time"]),
                        end_time=datetime.fromisoformat(tw["end_time"])
                    )
                except ValueError:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="无效的时间格式"
                    )
        
        # 创建任务
        task = Task(
            title=task_data["title"],
            description=task_data["description"],
            type=TaskType.DELIVERY,
            priority=task_data.get("priority", 5),
            created_by=current_user.username,
            start_location=start_location,
            end_location=end_location,
            time_window=time_window
        )
        
        # 处理负载信息
        if "payload" in task_data:
            payload = task_data["payload"]
            task.task_data = task.task_data or {}
            task.task_data["payload"] = payload
            
            # 提取负载重量
            if isinstance(payload, dict) and "weight" in payload:
                task.task_data["payload_weight"] = payload["weight"]
        
        await task.insert()
        
        logger.info(f"批量创建物流任务: {task.task_id}")
        
        # 通知协调者
        coordinator = await get_coordinator()
        await coordinator.message_queue.put({
            "type": "new_task",
            "task_id": task.task_id,
            "source_agent_id": "api"
        })
        
        created_tasks.append(task.dict())
    
    return created_tasks