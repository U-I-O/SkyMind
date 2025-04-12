from fastapi import APIRouter, Depends, HTTPException, Query, status, Body
from typing import Dict, List, Any, Optional
from datetime import datetime

from config.logging_config import get_logger
from database.models import Drone, User, DroneStatus, GeoPoint, Task
from core.security import get_current_active_user
from agents.coordinator import get_coordinator

logger = get_logger("api.drones")

router = APIRouter()

# 获取所有无人机
@router.get("/", response_model=List[Dict[str, Any]])
async def get_all_drones(
    status: Optional[str] = Query(None, description="按状态筛选"),
    current_user: User = Depends(get_current_active_user)
):
    """获取所有无人机"""
    try:
        # 创建查询条件
        query = {}
        if status:
            # Ensure the status string matches the DroneStatus enum values if filtering
            try:
                drone_status = DroneStatus(status)
                query["status"] = drone_status
            except ValueError:
                 raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"无效的状态值: {status}. 可选值: {[s.value for s in DroneStatus]}"
                 )
        
        # 查询数据库
        drones = await Drone.find(query).to_list()
        
        # 格式化结果 - SIMPLIFIED FOR DEBUGGING
        result = []
        for drone in drones:
            try:
                # Return only basic, safe fields
                simplified_drone = {
                    "drone_id": drone.drone_id,
                    "name": drone.name,
                    "status": drone.status.value if drone.status else None, # Ensure status is string
                    # Add other simple fields if needed for basic display
                    "model": drone.model,
                    "battery_level": drone.battery_level 
                }
                result.append(simplified_drone)
            except Exception as e:
                logger.error(f"序列化无人机 (simplified) 失败 {drone.drone_id}: {str(e)}")
                continue # Skip problematic drone

        return result
    except Exception as e:
        logger.error(f"获取无人机列表失败: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取无人机列表时发生服务器内部错误"
        )

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

# Control drone actions
@router.post("/{drone_id}/control", response_model=Dict[str, Any])
async def control_drone(
    drone_id: str,
    command_data: Dict[str, Any] = Body(...),
    current_user: User = Depends(get_current_active_user)
):
    """
    Control a drone with specific commands
    
    Commands:
    - start_task: Start a task execution (requires task_id in params)
    - return_home: Command drone to return to home location
    - emergency_land: Command drone to perform an emergency landing
    - pause: Pause the current operation
    - resume: Resume a paused operation
    """
    # Get the drone
    drone = await Drone.find_one({"drone_id": drone_id})
    if not drone:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Drone not found"
        )
    
    # Extract command and parameters
    command = command_data.get("command")
    params = command_data.get("params", {})
    
    if not command:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Command is required"
        )
    
    # Get the coordinator
    coordinator = await get_coordinator()
    
    # Process different commands
    try:
        if command == "start_task":
            # Check for task_id
            task_id = params.get("task_id")
            if not task_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="task_id is required for start_task command"
                )
            
            # Check if task exists
            task = await Task.find_one({"task_id": task_id})
            if not task:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Task {task_id} not found"
                )
            
            # Execute the command
            result = await coordinator.start_task(drone_id, task_id)
            
            if not result.get("success", False):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=result.get("message", "Failed to start task")
                )
            
            return result
            
        elif command == "return_home":
            # Execute the command
            result = await coordinator.return_home(drone_id)
            
            if not result.get("success", False):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=result.get("message", "Failed to return drone to home")
                )
            
            return result
            
        elif command == "emergency_land":
            # Execute the command
            result = await coordinator.emergency_land(drone_id)
            
            if not result.get("success", False):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=result.get("message", "Failed to initiate emergency landing")
                )
            
            return result
            
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported command: {command}"
            )
            
    except Exception as e:
        logger.error(f"Error executing drone command: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error executing command: {str(e)}"
        )

# Get tasks for a specific drone
@router.get("/{drone_id}/tasks", response_model=List[Dict[str, Any]])
async def get_drone_tasks(
    drone_id: str,
    status: Optional[str] = Query(None, description="Filter by task status"),
    current_user: User = Depends(get_current_active_user)
):
    """Get all tasks assigned to a specific drone"""
    # Check if drone exists
    drone = await Drone.find_one({"drone_id": drone_id})
    if not drone:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Drone not found"
        )
    
    # Build query
    query = {
        "assigned_drones": drone_id
    }
    
    if status:
        query["status"] = status
    
    # Get tasks
    tasks = await Task.find(query).to_list()
    
    return [task.dict() for task in tasks]

# Assign a task to a drone
@router.post("/{drone_id}/tasks", response_model=Dict[str, Any])
async def assign_task_to_drone(
    drone_id: str,
    task_data: Dict[str, Any] = Body(...),
    current_user: User = Depends(get_current_active_user)
):
    """Assign a task to a drone"""
    # Get the drone
    drone = await Drone.find_one({"drone_id": drone_id})
    if not drone:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Drone not found"
        )
    
    # Get the task
    task_id = task_data.get("task_id")
    if not task_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="task_id is required"
        )
    
    task = await Task.find_one({"task_id": task_id})
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {task_id} not found"
        )
    
    # Check if task is already assigned to this drone
    if drone_id in task.assigned_drones:
        return {
            "message": f"Task {task_id} is already assigned to drone {drone_id}",
            "task": task.dict(),
            "drone": drone.dict()
        }
    
    # Assign task to drone
    task.assigned_drones.append(drone_id)
    await task.save()
    
    # Update drone
    if task_id not in drone.assigned_tasks:
        drone.assigned_tasks.append(task_id)
        await drone.save()
    
    logger.info(f"Assigned task {task_id} to drone {drone_id}")
    
    return {
        "message": f"Task {task_id} assigned successfully to drone {drone_id}",
        "task": task.dict(),
        "drone": drone.dict()
    }

# Unassign a task from a drone
@router.delete("/{drone_id}/tasks/{task_id}", response_model=Dict[str, Any])
async def remove_task_from_drone(
    drone_id: str,
    task_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Remove a task assignment from a drone"""
    # Get the drone
    drone = await Drone.find_one({"drone_id": drone_id})
    if not drone:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Drone not found"
        )
    
    # Get the task
    task = await Task.find_one({"task_id": task_id})
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {task_id} not found"
        )
    
    # Check if task is assigned to this drone
    if drone_id not in task.assigned_drones:
        return {
            "message": f"Task {task_id} is not assigned to drone {drone_id}",
            "task": task.dict(),
            "drone": drone.dict()
        }
    
    # Check if task is in progress
    if task.status == "in_progress" and drone.status == "flying":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot unassign an in-progress task. Use return_home command instead."
        )
    
    # Remove task from drone
    if task_id in drone.assigned_tasks:
        drone.assigned_tasks.remove(task_id)
        await drone.save()
    
    # Remove drone from task
    if drone_id in task.assigned_drones:
        task.assigned_drones.remove(drone_id)
        await task.save()
    
    logger.info(f"Removed task {task_id} from drone {drone_id}")
    
    return {
        "message": f"Task {task_id} removed successfully from drone {drone_id}",
        "task": task.dict(),
        "drone": drone.dict()
    }

# Get drone telemetry
@router.get("/{drone_id}/telemetry", response_model=Dict[str, Any])
async def get_drone_telemetry(
    drone_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Get current telemetry data for a drone"""
    # Get the drone
    drone = await Drone.find_one({"drone_id": drone_id})
    if not drone:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Drone not found"
        )
    
    # In a real implementation, this would fetch real-time telemetry data
    # For this simulation, we'll return static data based on drone status
    
    telemetry = {
        "drone_id": drone.drone_id,
        "timestamp": datetime.utcnow().isoformat(),
        "battery_level": drone.battery_level,
        "position": drone.current_location.dict() if drone.current_location else None,
        "status": drone.status,
        "altitude": drone.current_location.altitude if drone.current_location else 0,
        "heading": 0,  # Simulated heading
        "speed": 0,    # Simulated speed
        "signal_strength": 95  # Simulated signal strength
    }
    
    # Add additional telemetry based on status
    if drone.status == DroneStatus.FLYING:
        telemetry["speed"] = 5.0  # Simulated speed in m/s
        telemetry["heading"] = 45.0  # Simulated heading in degrees
        telemetry["altitude"] = 50.0 if not telemetry["altitude"] else telemetry["altitude"]
    
    return telemetry