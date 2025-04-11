from fastapi import APIRouter, Depends, HTTPException, Query, status, Body
from typing import Dict, List, Any, Optional
from datetime import datetime

from config.logging_config import get_logger
from database.models import Drone, User, DroneStatus, GeoPoint, Task
from core.security import get_current_active_user

logger = get_logger("api.drones")

router = APIRouter()

# 获取所有无人机
@router.get("/", response_model=List[Dict[str, Any]])
async def get_all_drones(
    status: Optional[str] = Query(None, description="按状态筛选"),
    current_user: User = Depends(get_current_active_user)
):
    """获取所有无人机"""
    # 创建查询条件
    query = {}
    if status:
        query["status"] = status
    
    # 查询数据库
    drones = await Drone.find(query).to_list()
    
    # 格式化结果
    result = []
    for drone in drones:
        drone_dict = drone.dict()
        
        # 添加关联任务信息
        if drone.assigned_tasks:
            tasks = await Task.find({"task_id": {"$in": drone.assigned_tasks}}).to_list()
            drone_dict["task_details"] = [
                {
                    "task_id": task.task_id,
                    "title": task.title,
                    "status": task.status,
                    "type": task.type
                }
                for task in tasks
            ]
        
        result.append(drone_dict)
    
    return result

# 获取单个无人机详情
@router.get("/{drone_id}", response_model=Dict[str, Any])
async def get_drone(
    drone_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """获取单个无人机详情"""
    drone = await Drone.find_one({"drone_id": drone_id})
    if not drone:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="无人机不存在"
        )
    
    # 格式化结果
    result = drone.dict()
    
    # 添加关联任务信息
    if drone.assigned_tasks:
        tasks = await Task.find({"task_id": {"$in": drone.assigned_tasks}}).to_list()
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

# 创建新无人机
@router.post("/", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
async def create_drone(
    drone_data: Dict[str, Any] = Body(...),
    current_user: User = Depends(get_current_active_user)
):
    """创建新无人机"""
    # 检查必需字段
    required_fields = ["name", "model", "max_flight_time", "max_speed", "max_altitude"]
    for field in required_fields:
        if field not in drone_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"缺少必需字段: {field}"
            )
    
    # 创建无人机对象
    drone = Drone(
        name=drone_data["name"],
        model=drone_data["model"],
        max_flight_time=drone_data["max_flight_time"],
        max_speed=drone_data["max_speed"],
        max_altitude=drone_data["max_altitude"],
        payload_capacity=drone_data.get("payload_capacity", 0.0),
        camera_equipped=drone_data.get("camera_equipped", True)
    )
    
    # 保存到数据库
    await drone.insert()
    
    logger.info(f"创建了新无人机: {drone.drone_id}")
    
    return drone.dict()

# 更新无人机信息
@router.put("/{drone_id}", response_model=Dict[str, Any])
async def update_drone(
    drone_id: str,
    drone_data: Dict[str, Any] = Body(...),
    current_user: User = Depends(get_current_active_user)
):
    """更新无人机信息"""
    # 获取无人机
    drone = await Drone.find_one({"drone_id": drone_id})
    if not drone:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="无人机不存在"
        )
    
    # 更新字段
    update_fields = [
        "name", "model", "status", "battery_level", "max_flight_time",
        "max_speed", "max_altitude", "camera_equipped", "payload_capacity"
    ]
    
    for field in update_fields:
        if field in drone_data:
            setattr(drone, field, drone_data[field])
    
    # 更新位置信息
    if "position" in drone_data:
        pos = drone_data["position"]
        if isinstance(pos, dict) and "coordinates" in pos:
            drone.current_location = GeoPoint(
                type="Point",
                coordinates=pos["coordinates"],
                altitude=pos.get("altitude")
            )
    
    # 更新时间戳
    drone.updated_at = datetime.utcnow()
    
    # 保存更新
    await drone.save()
    
    logger.info(f"更新了无人机信息: {drone_id}")
    
    return drone.dict()

# 删除无人机
@router.delete("/{drone_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_drone(
    drone_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """删除无人机"""
    # 获取无人机
    drone = await Drone.find_one({"drone_id": drone_id})
    if not drone:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="无人机不存在"
        )
    
    # 检查是否有关联任务
    if drone.assigned_tasks:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无人机有关联任务，无法删除"
        )
    
    # 删除无人机
    await drone.delete()
    
    logger.info(f"删除了无人机: {drone_id}")

# 更新无人机位置
@router.put("/{drone_id}/position", response_model=Dict[str, Any])
async def update_drone_position(
    drone_id: str,
    position_data: Dict[str, Any] = Body(...),
    current_user: User = Depends(get_current_active_user)
):
    """更新无人机位置"""
    # 获取无人机
    drone = await Drone.find_one({"drone_id": drone_id})
    if not drone:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="无人机不存在"
        )
    
    # 验证位置数据
    if "coordinates" not in position_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="缺少坐标信息"
        )
    
    # 更新位置
    drone.current_location = GeoPoint(
        type="Point",
        coordinates=position_data["coordinates"],
        altitude=position_data.get("altitude")
    )
    
    # 更新时间戳
    drone.updated_at = datetime.utcnow()
    
    # 保存更新
    await drone.save()
    
    logger.info(f"更新了无人机位置: {drone_id}")
    
    return {
        "drone_id": drone_id,
        "position": drone.current_location.dict(),
        "updated_at": drone.updated_at
    }

# 获取无人机历史轨迹
@router.get("/{drone_id}/trajectory", response_model=List[Dict[str, Any]])
async def get_drone_trajectory(
    drone_id: str,
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    current_user: User = Depends(get_current_active_user)
):
    """获取无人机历史轨迹"""
    # 获取无人机
    drone = await Drone.find_one({"drone_id": drone_id})
    if not drone:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="无人机不存在"
        )
    
    # 在实际应用中，这里应该从轨迹数据库表中查询
    # 由于我们没有实现轨迹存储，这里返回模拟数据
    
    # 返回模拟轨迹数据
    return [
        {
            "timestamp": datetime.utcnow(),
            "position": {
                "type": "Point",
                "coordinates": [116.4074, 39.9042],
                "altitude": 100
            },
            "status": "flying",
            "battery_level": 90
        }
    ]

# 获取无人机状态统计
@router.get("/statistics/status", response_model=Dict[str, int])
async def get_drone_status_statistics(
    current_user: User = Depends(get_current_active_user)
):
    """获取无人机状态统计"""
    # 统计各种状态的无人机数量
    result = {}
    
    for status in DroneStatus:
        count = await Drone.find({"status": status}).count()
        result[status] = count
    
    # 添加总数
    total = await Drone.find_all().count()
    result["total"] = total
    
    return result

# 获取特定状态的无人机列表
@router.get("/filter/status/{status}", response_model=List[Dict[str, Any]])
async def get_drones_by_status(
    status: DroneStatus,
    current_user: User = Depends(get_current_active_user)
):
    """获取特定状态的无人机列表"""
    drones = await Drone.find({"status": status}).to_list()
    
    return [drone.dict() for drone in drones]

# 批量更新无人机状态
@router.post("/batch/status", response_model=Dict[str, Any])
async def batch_update_drone_status(
    batch_data: Dict[str, Any] = Body(...),
    current_user: User = Depends(get_current_active_user)
):
    """批量更新无人机状态"""
    if "drone_ids" not in batch_data or "status" not in batch_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="缺少必需字段: drone_ids 或 status"
        )
    
    drone_ids = batch_data["drone_ids"]
    new_status = batch_data["status"]
    
    # 验证状态值
    if new_status not in [status.value for status in DroneStatus]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"无效的状态值: {new_status}"
        )
    
    # 批量更新
    updated_count = 0
    for drone_id in drone_ids:
        drone = await Drone.find_one({"drone_id": drone_id})
        if drone:
            drone.status = new_status
            drone.updated_at = datetime.utcnow()
            await drone.save()
            updated_count += 1
    
    logger.info(f"批量更新了 {updated_count} 架无人机的状态为: {new_status}")
    
    return {
        "success": True,
        "updated_count": updated_count,
        "status": new_status
    }