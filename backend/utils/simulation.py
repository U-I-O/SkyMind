import asyncio
import math
import numpy as np
import random
from typing import Dict, List, Any, Optional, Tuple, Set, Callable
from datetime import datetime, timedelta
import json

from config.settings import settings
from config.logging_config import get_logger
from database.models import (
    Drone, DroneStatus, Task, TaskStatus, Event, EventType, EventLevel, 
    Location, GeoPoint, NoFlyZone
)
from core.events import event_manager, EventTypes

logger = get_logger("utils.simulation")

class SimulationConfig:
    """仿真配置"""
    def __init__(self,
                active: bool = True,
                update_interval: float = 1.0,  # 秒
                drone_movement_noise: float = 0.00001,  # 位置噪声
                drone_battery_drain_rate: float = 0.01,  # 每秒电池消耗百分比
                random_events_enabled: bool = True,
                random_event_probability: float = 0.01,  # 每次更新的随机事件概率
                max_random_events: int = 5,  # 单次仿真最大随机事件数
                seed: Optional[int] = None  # 随机种子
                ):
        self.active = active
        self.update_interval = update_interval
        self.drone_movement_noise = drone_movement_noise
        self.drone_battery_drain_rate = drone_battery_drain_rate
        self.random_events_enabled = random_events_enabled
        self.random_event_probability = random_event_probability
        self.max_random_events = max_random_events
        self.seed = seed
    
    def dict(self):
        """返回字典表示"""
        return {
            "active": self.active,
            "update_interval": self.update_interval,
            "drone_movement_noise": self.drone_movement_noise,
            "drone_battery_drain_rate": self.drone_battery_drain_rate,
            "random_events_enabled": self.random_events_enabled,
            "random_event_probability": self.random_event_probability,
            "max_random_events": self.max_random_events,
            "seed": self.seed
        }

class DroneSimulator:
    """无人机仿真器"""
    
    def __init__(self, config: Optional[SimulationConfig] = None):
        self.config = config or SimulationConfig()
        self.running = False
        self.drones: Dict[str, Dict[str, Any]] = {}
        self.tasks: Dict[str, Dict[str, Any]] = {}
        self.events: Dict[str, Dict[str, Any]] = {}
        self.event_count = 0
        self.task_count = 0
        self.update_count = 0
        
        # 设置随机种子
        if self.config.seed is not None:
            random.seed(self.config.seed)
            np.random.seed(self.config.seed)
    
    async def start(self):
        """启动仿真"""
        if self.running:
            return
        
        self.running = True
        logger.info("启动无人机仿真")
        
        # 启动更新循环
        asyncio.create_task(self._update_loop())
        
        # 发布仿真启动事件
        await event_manager.emit("simulation_started", {
            "config": self.config.dict()
        })
    
    async def stop(self):
        """停止仿真"""
        self.running = False
        logger.info("停止无人机仿真")
        
        # 发布仿真停止事件
        await event_manager.emit("simulation_stopped", {})
    
    async def _update_loop(self):
        """仿真更新循环"""
        while self.running:
            try:
                # 更新无人机状态
                await self._update_drones()
                
                # 更新任务状态
                await self._update_tasks()
                
                # 生成随机事件
                if self.config.random_events_enabled:
                    await self._generate_random_events()
                
                # 增加更新计数
                self.update_count += 1
                
                # 等待下一次更新
                await asyncio.sleep(self.config.update_interval)
            
            except Exception as e:
                logger.error(f"仿真更新出错: {str(e)}")
                await asyncio.sleep(1)  # 出错后等待一秒继续
    
    async def _update_drones(self):
        """更新所有无人机状态"""
        # 加载所有无人机
        drones = await Drone.find_all().to_list()
        
        for drone in drones:
            drone_id = drone.drone_id
            
            # 如果没有这个无人机的记录，创建一个
            if drone_id not in self.drones:
                self.drones[drone_id] = {
                    "target_position": None,
                    "waypoints": [],
                    "current_waypoint_index": 0,
                    "speed": 0.0,
                    "start_time": None
                }
            
            drone_sim = self.drones[drone_id]
            
            # 根据无人机状态进行更新
            if drone.status == DroneStatus.FLYING:
                # 更新无人机位置
                await self._update_drone_position(drone, drone_sim)
                
                # 消耗电池
                if drone.battery_level > 0:
                    drone.battery_level -= self.config.drone_battery_drain_rate * self.config.update_interval
                    drone.battery_level = max(0, drone.battery_level)
                    
                    # 如果电池电量过低，触发事件
                    if drone.battery_level < 20 and drone.battery_level % 5 < self.config.drone_battery_drain_rate:
                        await event_manager.emit(EventTypes.DRONE_BATTERY_LOW, {
                            "drone_id": drone_id,
                            "battery_level": drone.battery_level
                        })
                    
                    # 如果电池耗尽，切换到OFFLINE状态
                    if drone.battery_level <= 0:
                        drone.status = DroneStatus.OFFLINE
                        drone.battery_level = 0
                        
                        await event_manager.emit(EventTypes.DRONE_STATUS_CHANGED, {
                            "drone_id": drone_id,
                            "status": drone.status,
                            "previous_status": DroneStatus.FLYING
                        })
            
            elif drone.status == DroneStatus.CHARGING:
                # 充电
                if drone.battery_level < 100:
                    # 每秒充电速度是放电速度的5倍
                    drone.battery_level += self.config.drone_battery_drain_rate * 5 * self.config.update_interval
                    drone.battery_level = min(100, drone.battery_level)
                    
                    # 如果充满电，切换到IDLE状态
                    if drone.battery_level >= 100:
                        drone.status = DroneStatus.IDLE
                        drone.battery_level = 100
                        
                        await event_manager.emit(EventTypes.DRONE_STATUS_CHANGED, {
                            "drone_id": drone_id,
                            "status": drone.status,
                            "previous_status": DroneStatus.CHARGING
                        })
            
            # 保存无人机状态
            await drone.save()
    
    async def _update_drone_position(self, drone: Drone, drone_sim: Dict[str, Any]):
        """更新无人机位置"""
        # 如果没有当前位置，设置一个初始位置
        if not drone.current_location:
            # 使用默认城市中心作为初始位置
            drone.current_location = GeoPoint(
                type="Point",
                coordinates=[
                    settings.DEFAULT_CITY_CENTER["lon"],
                    settings.DEFAULT_CITY_CENTER["lat"]
                ],
                altitude=100.0
            )
        
        # 如果无人机有分配任务，更新航点
        if drone.assigned_tasks and not drone_sim["waypoints"]:
            await self._update_drone_waypoints(drone, drone_sim)
        
        # 如果有目标位置，朝着目标位置移动
        if drone_sim["target_position"]:
            # 获取当前位置和目标位置
            current_pos = drone.current_location.coordinates
            target_pos = drone_sim["target_position"]
            
            # 计算方向和距离
            dx = target_pos[0] - current_pos[0]
            dy = target_pos[1] - current_pos[1]
            distance = math.sqrt(dx*dx + dy*dy)
            
            # 默认速度（度/秒）
            speed = settings.DRONE_MAX_SPEED / 111000  # 转换为度/秒，约111km/度
            
            # 实际移动距离（考虑更新间隔）
            move_distance = speed * self.config.update_interval
            
            # 如果足够接近目标
            if distance <= move_distance:
                # 已到达目标点
                drone.current_location.coordinates = target_pos
                
                # 更新航点索引
                if drone_sim["waypoints"]:
                    drone_sim["current_waypoint_index"] += 1
                    
                    # 如果还有下一个航点
                    if drone_sim["current_waypoint_index"] < len(drone_sim["waypoints"]):
                        next_waypoint = drone_sim["waypoints"][drone_sim["current_waypoint_index"]]
                        drone_sim["target_position"] = next_waypoint["coordinates"]
                    else:
                        # 到达最后一个航点，任务完成
                        drone_sim["waypoints"] = []
                        drone_sim["current_waypoint_index"] = 0
                        drone_sim["target_position"] = None
                        
                        # 如果有关联任务，标记为完成
                        if drone.assigned_tasks:
                            for task_id in drone.assigned_tasks:
                                task = await Task.find_one({"task_id": task_id})
                                if task and task.status == TaskStatus.IN_PROGRESS:
                                    task.status = TaskStatus.COMPLETED
                                    task.end_time = datetime.utcnow()
                                    await task.save()
                                    
                                    # 发布任务完成事件
                                    await event_manager.emit(EventTypes.TASK_COMPLETED, {
                                        "task_id": task_id,
                                        "drone_id": drone.drone_id
                                    })
                            
                            # 清空无人机的任务列表
                            drone.assigned_tasks = []
                            drone.status = DroneStatus.IDLE
            else:
                # 继续移动
                # 计算归一化方向
                norm = distance
                dx /= norm
                dy /= norm
                
                # 更新位置（添加一些随机噪声）
                noise_x = random.uniform(-self.config.drone_movement_noise, self.config.drone_movement_noise)
                noise_y = random.uniform(-self.config.drone_movement_noise, self.config.drone_movement_noise)
                
                new_x = current_pos[0] + dx * move_distance + noise_x
                new_y = current_pos[1] + dy * move_distance + noise_y
                
                drone.current_location.coordinates = [new_x, new_y]
        
        # 如果没有目标位置但有航点
        elif drone_sim["waypoints"] and drone_sim["current_waypoint_index"] < len(drone_sim["waypoints"]):
            # 设置下一个航点为目标
            next_waypoint = drone_sim["waypoints"][drone_sim["current_waypoint_index"]]
            drone_sim["target_position"] = next_waypoint["coordinates"]
    
    async def _update_drone_waypoints(self, drone: Drone, drone_sim: Dict[str, Any]):
        """更新无人机航点"""
        # 获取无人机的第一个任务
        if not drone.assigned_tasks:
            return
        
        task_id = drone.assigned_tasks[0]
        task = await Task.find_one({"task_id": task_id})
        
        if not task:
            return
        
        # 如果任务有规划路径
        if task.planned_path and task.planned_path.waypoints:
            waypoints = []
            
            # 转换航点格式
            for wp in task.planned_path.waypoints:
                waypoints.append({
                    "coordinates": wp.coordinates,
                    "altitude": wp.altitude or 100.0
                })
            
            # 更新无人机仿真信息
            drone_sim["waypoints"] = waypoints
            drone_sim["current_waypoint_index"] = 0
            drone_sim["start_time"] = datetime.utcnow()
            drone_sim["target_position"] = None  # 会在下一次更新中设置
            
            # 更新任务状态
            if task.status == TaskStatus.ASSIGNED:
                task.status = TaskStatus.IN_PROGRESS
                task.start_time = datetime.utcnow()
                await task.save()
                
                # 发布任务更新事件
                await event_manager.emit(EventTypes.TASK_UPDATED, {
                    "task_id": task_id,
                    "status": task.status
                })
        else:
            # 如果没有规划路径但有起点和终点
            if task.start_location and task.end_location:
                # 创建简单的直线路径
                waypoints = [
                    {
                        "coordinates": task.start_location.position.coordinates,
                        "altitude": task.start_location.position.altitude or 100.0
                    },
                    {
                        "coordinates": task.end_location.position.coordinates,
                        "altitude": task.end_location.position.altitude or 100.0
                    }
                ]
                
                # 更新无人机仿真信息
                drone_sim["waypoints"] = waypoints
                drone_sim["current_waypoint_index"] = 0
                drone_sim["start_time"] = datetime.utcnow()
                drone_sim["target_position"] = None  # 会在下一次更新中设置
                
                # 更新任务状态
                if task.status == TaskStatus.ASSIGNED:
                    task.status = TaskStatus.IN_PROGRESS
                    task.start_time = datetime.utcnow()
                    await task.save()
                    
                    # 发布任务更新事件
                    await event_manager.emit(EventTypes.TASK_UPDATED, {
                        "task_id": task_id,
                        "status": task.status
                    })
    
    async def _update_tasks(self):
        """更新任务状态"""
        # 加载所有进行中的任务
        tasks = await Task.find({"status": TaskStatus.IN_PROGRESS}).to_list()
        
        for task in tasks:
            # 检查任务是否超时
            if task.start_time:
                # 计算任务已经运行的时间
                elapsed_time = (datetime.utcnow() - task.start_time).total_seconds() / 60  # 分钟
                
                # 如果有计划路径，检查是否超过预计时间的两倍
                if task.planned_path and task.planned_path.estimated_duration:
                    time_limit = task.planned_path.estimated_duration * 2
                    
                    if elapsed_time > time_limit:
                        # 任务超时
                        task.status = TaskStatus.FAILED
                        task.end_time = datetime.utcnow()
                        task.task_data = task.task_data or {}
                        task.task_data["failure_reason"] = "任务超时"
                        await task.save()
                        
                        # 发布任务失败事件
                        await event_manager.emit(EventTypes.TASK_FAILED, {
                            "task_id": task.task_id,
                            "reason": "任务超时"
                        })
                        
                        # 如果有分配的无人机，释放它们
                        if task.assigned_drones:
                            for drone_id in task.assigned_drones:
                                drone = await Drone.find_one({"drone_id": drone_id})
                                if drone:
                                    drone.assigned_tasks = [t for t in drone.assigned_tasks if t != task.task_id]
                                    if not drone.assigned_tasks:
                                        drone.status = DroneStatus.IDLE
                                    await drone.save()
    
    async def _generate_random_events(self):
        """生成随机事件"""
        # 限制随机事件数量
        if self.event_count >= self.config.max_random_events:
            return
        
        # 随机概率生成事件
        if random.random() > self.config.random_event_probability:
            return
        
        # 选择事件类型
        event_types = [EventType.SECURITY, EventType.EMERGENCY, EventType.ANOMALY]
        event_type = random.choice(event_types)
        
        # 选择事件级别
        if event_type == EventType.EMERGENCY:
            # 紧急事件级别分布: 低60%, 中30%, 高10%
            level_probs = [0.6, 0.3, 0.1]
        else:
            # 其他事件级别分布: 低70%, 中25%, 高5%
            level_probs = [0.7, 0.25, 0.05]
        
        event_level = np.random.choice(
            [EventLevel.LOW, EventLevel.MEDIUM, EventLevel.HIGH],
            p=level_probs
        )
        
        # 生成随机位置（默认城市中心附近）
        center_lat = settings.DEFAULT_CITY_CENTER["lat"]
        center_lon = settings.DEFAULT_CITY_CENTER["lon"]
        
        # 随机偏移（约1公里范围内）
        lat_offset = random.uniform(-0.01, 0.01)
        lon_offset = random.uniform(-0.01, 0.01)
        
        location = Location(
            position=GeoPoint(
                type="Point",
                coordinates=[center_lon + lon_offset, center_lat + lat_offset],
                altitude=random.uniform(50, 200)
            )
        )
        
        # 生成事件标题和描述
        titles = {
            EventType.SECURITY: [
                "检测到可疑活动", "区域入侵警报", "异常行为检测", 
                "安全围栏破坏", "不明人员闯入"
            ],
            EventType.EMERGENCY: [
                "紧急医疗事件", "交通事故", "建筑物火灾", 
                "有害物质泄漏", "自然灾害警报"
            ],
            EventType.ANOMALY: [
                "检测到异常物体", "未识别飞行物", "异常温度读数", 
                "空气质量异常", "水平面异常变化"
            ]
        }
        
        descriptions = {
            EventType.SECURITY: [
                "监控系统检测到区域内的可疑活动，需要进一步调查。",
                "有人员在禁止进入的区域内活动，请立即派遣无人机前往查看。",
                "检测到异常行为模式，可能存在安全隐患。",
                "安全围栏受到破坏，需要进行安全检查。",
                "不明人员在限制区域内活动，请核实身份。"
            ],
            EventType.EMERGENCY: [
                "接收到紧急医疗求助信号，需要立即响应。",
                "发生交通事故，需要评估现场情况并协调救援。",
                "建筑物发生火灾，需要确定火势范围和疏散路线。",
                "检测到有害物质泄漏，需要确定影响范围并发布警报。",
                "自然灾害警报触发，需要评估受影响区域。"
            ],
            EventType.ANOMALY: [
                "传感器检测到区域内存在异常物体，需要确认。",
                "探测到未识别的飞行物，需要跟踪并确定性质。",
                "区域温度读数异常，可能表明设备故障或火灾隐患。",
                "空气质量监测显示污染物浓度异常升高，需要确定来源。",
                "水平面传感器显示异常变化，可能存在洪水或泄漏风险。"
            ]
        }
        
        title = random.choice(titles[event_type])
        description = random.choice(descriptions[event_type])
        
        # 创建事件
        event = Event(
            type=event_type,
            level=event_level,
            title=title,
            description=description,
            location=location,
            detected_by="simulation",
            detection_data={
                "simulation": True,
                "generation_time": datetime.utcnow().isoformat()
            }
        )
        
        # 保存事件
        await event.insert()
        
        # 增加事件计数
        self.event_count += 1
        
        # 发布事件检测事件
        await event_manager.emit(EventTypes.EVENT_DETECTED, {
            "event_id": event.event_id,
            "event_type": event.type,
            "event_level": event.level,
            "title": event.title
        })
        
        logger.info(f"生成随机事件: {event.event_id} - {event.title} ({event.type}, {event.level})")
        
        return event
    
    def collision_check(self, drone_id: str, other_drone_id: str) -> bool:
        """检查两个无人机是否可能发生碰撞"""
        if drone_id not in self.drones or other_drone_id not in self.drones:
            return False
        
        # 在实际应用中，这里应该实现更复杂的碰撞检测算法
        # 这里只是一个简化的示例
        return False
    
    async def check_no_fly_zones(self, drone: Drone) -> List[NoFlyZone]:
        """检查无人机是否在禁飞区内"""
        if not drone.current_location:
            return []
        
        # 获取无人机位置
        location = drone.current_location.coordinates
        
        # 查询包含该位置的禁飞区
        now = datetime.utcnow()
        zones = await NoFlyZone.find({
            "$or": [
                {"permanent": True},
                {
                    "permanent": False,
                    "start_time": {"$lte": now},
                    "end_time": {"$gte": now}
                }
            ]
        }).to_list()
        
        # 检查每个禁飞区
        violated_zones = []
        
        for zone in zones:
            # 检查禁飞区几何形状是否包含无人机位置
            # 这里需要实现点在多边形内的检测
            # 简化实现，实际应用中应使用更精确的算法
            coords = zone.geometry["coordinates"][0]
            if self._point_in_polygon(location[1], location[0], coords):
                violated_zones.append(zone)
        
        return violated_zones
    
    def _point_in_polygon(self, x, y, poly):
        """判断点是否在多边形内（射线法）"""
        n = len(poly)
        inside = False
        
        p1x, p1y = poly[0]
        for i in range(1, n + 1):
            p2x, p2y = poly[i % n]
            if y > min(p1y, p2y):
                if y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        if p1y != p2y:
                            xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or x <= xinters:
                            inside = not inside
            p1x, p1y = p2x, p2y
        
        return inside


# 创建全局仿真器实例
simulator = DroneSimulator()