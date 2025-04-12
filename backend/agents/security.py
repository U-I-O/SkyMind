from typing import Dict, List, Any, Optional, Union, Tuple, Set
import asyncio
import uuid
import time
from datetime import datetime, timedelta
import json
import numpy as np
from pathlib import Path
import random
import math
from shapely.geometry import Point, Polygon
import pymongo

from config.logging_config import get_logger
from database.models import (
    Task, FlightPath, GeoPoint, Location, NoFlyZone, Drone, Event,
    TaskStatus, TaskType, EventType, EventLevel, BoundingBox, VideoSource
)
from config.settings import settings
from .base import BaseAgent
from .coordinator import register_agent, get_coordinator
from .monitor import MonitorAgent

logger = get_logger("agents.security")

class PatrolPattern:
    """巡检模式类型"""
    GRID = "grid"  # 网格巡检
    PERIMETER = "perimeter"  # 周界巡检
    RANDOM = "random"  # 随机巡检
    WAYPOINT = "waypoint"  # 航点巡检
    HOTSPOT = "hotspot"  # 热点巡检
    ADAPTIVE = "adaptive"  # 自适应巡检

class SecurityAgent(BaseAgent):
    """
    安防巡检智能体负责制定和执行安防巡检任务，
    监控城市安全状况和异常活动。
    """
    
    def __init__(self, agent_id: Optional[str] = None, name: str = "安防巡检智能体"):
        super().__init__(agent_id, name)
        self.agent_type = "SecurityAgent"
        self.active_tasks: Dict[str, Dict[str, Any]] = {}
        self.patrol_areas: Dict[str, Dict[str, Any]] = {}
        self.security_zones: List[Dict[str, Any]] = []
        self.patrol_schedules: Dict[str, List[Dict[str, Any]]] = {}
        self.anomaly_history: Dict[str, List[Dict[str, Any]]] = {}
        self.monitor_agent_id: Optional[str] = None
        self.capabilities = {
            "security_patrol": 0.95,
            "anomaly_detection": 0.85,
            "surveillance": 0.9,
            "threat_assessment": 0.8
        }
    
    async def initialize(self):
        """初始化安防巡检智能体"""
        await super().initialize()
        
        # 加载安全区域
        await self._load_security_zones()
        
        # 加载巡检区域
        await self._load_patrol_areas()
        
        # 加载活动任务
        await self._load_active_tasks()
        
        # 查找监控智能体
        await self._find_monitor_agent()
        
        # 初始化巡检计划
        self._initialize_patrol_schedules()
        
        return self
    
    async def _load_security_zones(self):
        """加载安全区域"""
        try:
            # 在实际应用中，这些应该从数据库加载
            # 这里我们创建一些示例区域
            
            # 示例：城市中心区域
            city_center = {
                "id": "zone-city-center",
                "name": "城市中心",
                "type": "high_security",
                "priority": 10,
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [settings.DEFAULT_CITY_CENTER["lon"] - 0.02, settings.DEFAULT_CITY_CENTER["lat"] - 0.02],
                        [settings.DEFAULT_CITY_CENTER["lon"] + 0.02, settings.DEFAULT_CITY_CENTER["lat"] - 0.02],
                        [settings.DEFAULT_CITY_CENTER["lon"] + 0.02, settings.DEFAULT_CITY_CENTER["lat"] + 0.02],
                        [settings.DEFAULT_CITY_CENTER["lon"] - 0.02, settings.DEFAULT_CITY_CENTER["lat"] + 0.02],
                        [settings.DEFAULT_CITY_CENTER["lon"] - 0.02, settings.DEFAULT_CITY_CENTER["lat"] - 0.02]
                    ]]
                }
            }
            
            # 示例：住宅区
            residential = {
                "id": "zone-residential",
                "name": "住宅区",
                "type": "medium_security",
                "priority": 7,
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [settings.DEFAULT_CITY_CENTER["lon"] - 0.04, settings.DEFAULT_CITY_CENTER["lat"] - 0.04],
                        [settings.DEFAULT_CITY_CENTER["lon"] - 0.01, settings.DEFAULT_CITY_CENTER["lat"] - 0.04],
                        [settings.DEFAULT_CITY_CENTER["lon"] - 0.01, settings.DEFAULT_CITY_CENTER["lat"] - 0.01],
                        [settings.DEFAULT_CITY_CENTER["lon"] - 0.04, settings.DEFAULT_CITY_CENTER["lat"] - 0.01],
                        [settings.DEFAULT_CITY_CENTER["lon"] - 0.04, settings.DEFAULT_CITY_CENTER["lat"] - 0.04]
                    ]]
                }
            }
            
            # 示例：商业区
            commercial = {
                "id": "zone-commercial",
                "name": "商业区",
                "type": "high_security",
                "priority": 8,
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [settings.DEFAULT_CITY_CENTER["lon"] + 0.01, settings.DEFAULT_CITY_CENTER["lat"] - 0.04],
                        [settings.DEFAULT_CITY_CENTER["lon"] + 0.04, settings.DEFAULT_CITY_CENTER["lat"] - 0.04],
                        [settings.DEFAULT_CITY_CENTER["lon"] + 0.04, settings.DEFAULT_CITY_CENTER["lat"] - 0.01],
                        [settings.DEFAULT_CITY_CENTER["lon"] + 0.01, settings.DEFAULT_CITY_CENTER["lat"] - 0.01],
                        [settings.DEFAULT_CITY_CENTER["lon"] + 0.01, settings.DEFAULT_CITY_CENTER["lat"] - 0.04]
                    ]]
                }
            }
            
            # 示例：工业区
            industrial = {
                "id": "zone-industrial",
                "name": "工业区",
                "type": "medium_security",
                "priority": 6,
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [settings.DEFAULT_CITY_CENTER["lon"] - 0.04, settings.DEFAULT_CITY_CENTER["lat"] + 0.01],
                        [settings.DEFAULT_CITY_CENTER["lon"] - 0.01, settings.DEFAULT_CITY_CENTER["lat"] + 0.01],
                        [settings.DEFAULT_CITY_CENTER["lon"] - 0.01, settings.DEFAULT_CITY_CENTER["lat"] + 0.04],
                        [settings.DEFAULT_CITY_CENTER["lon"] - 0.04, settings.DEFAULT_CITY_CENTER["lat"] + 0.04],
                        [settings.DEFAULT_CITY_CENTER["lon"] - 0.04, settings.DEFAULT_CITY_CENTER["lat"] + 0.01]
                    ]]
                }
            }
            
            # 示例：公园
            park = {
                "id": "zone-park",
                "name": "公园",
                "type": "low_security",
                "priority": 4,
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [settings.DEFAULT_CITY_CENTER["lon"] + 0.01, settings.DEFAULT_CITY_CENTER["lat"] + 0.01],
                        [settings.DEFAULT_CITY_CENTER["lon"] + 0.04, settings.DEFAULT_CITY_CENTER["lat"] + 0.01],
                        [settings.DEFAULT_CITY_CENTER["lon"] + 0.04, settings.DEFAULT_CITY_CENTER["lat"] + 0.04],
                        [settings.DEFAULT_CITY_CENTER["lon"] + 0.01, settings.DEFAULT_CITY_CENTER["lat"] + 0.04],
                        [settings.DEFAULT_CITY_CENTER["lon"] + 0.01, settings.DEFAULT_CITY_CENTER["lat"] + 0.01]
                    ]]
                }
            }
            
            self.security_zones = [city_center, residential, commercial, industrial, park]
            
            logger.info(f"加载了 {len(self.security_zones)} 个安全区域")
        except Exception as e:
            logger.error(f"加载安全区域失败: {str(e)}")
    
    async def _load_patrol_areas(self):
        """加载巡检区域"""
        try:
            # 根据安全区域创建巡检区域
            for zone in self.security_zones:
                zone_id = zone["id"]
                zone_type = zone["type"]
                
                # 为不同类型的区域选择不同的巡检模式
                if zone_type == "high_security":
                    pattern = PatrolPattern.GRID
                elif zone_type == "medium_security":
                    pattern = PatrolPattern.PERIMETER
                else:  # low_security
                    pattern = PatrolPattern.WAYPOINT
                
                # 创建巡检区域
                self.patrol_areas[zone_id] = {
                    "zone_id": zone_id,
                    "name": f"{zone['name']}巡检区域",
                    "pattern": pattern,
                    "priority": zone["priority"],
                    "geometry": zone["geometry"],
                    "last_patrol": datetime.utcnow() - timedelta(hours=24),  # 初始化为24小时前
                    "patrol_interval": self._get_patrol_interval(zone_type),
                    "waypoints": self._generate_patrol_waypoints(zone["geometry"], pattern)
                }
            
            logger.info(f"创建了 {len(self.patrol_areas)} 个巡检区域")
        except Exception as e:
            logger.error(f"加载巡检区域失败: {str(e)}")
    
    def _get_patrol_interval(self, zone_type: str) -> int:
        """根据区域类型获取巡检间隔（分钟）"""
        if zone_type == "high_security":
            return 60  # 1小时
        elif zone_type == "medium_security":
            return 120  # 2小时
        else:  # low_security
            return 240  # 4小时
    
    def _generate_patrol_waypoints(self, geometry: Dict[str, Any], pattern: str) -> List[Dict[str, Any]]:
        """根据区域几何形状和巡检模式生成巡检航点"""
        coordinates = geometry["coordinates"][0]  # 获取多边形坐标
        
        # 计算区域边界
        lons = [p[0] for p in coordinates]
        lats = [p[1] for p in coordinates]
        min_lon, max_lon = min(lons), max(lons)
        min_lat, max_lat = min(lats), max(lats)
        
        waypoints = []
        
        if pattern == PatrolPattern.GRID:
            # 创建网格巡检点
            grid_size = 0.005  # 大约500米
            
            for lon in np.arange(min_lon, max_lon, grid_size):
                for lat in np.arange(min_lat, max_lat, grid_size):
                    point = Point(lon, lat)
                    polygon = Polygon(coordinates)
                    
                    if polygon.contains(point):
                        waypoints.append({
                            "id": f"wp-{len(waypoints)}",
                            "position": {
                                "type": "Point",
                                "coordinates": [lon, lat]
                            },
                            "altitude": 100  # 默认高度100米
                        })
        
        elif pattern == PatrolPattern.PERIMETER:
            # 创建周界巡检点
            for i in range(len(coordinates) - 1):
                waypoints.append({
                    "id": f"wp-{len(waypoints)}",
                    "position": {
                        "type": "Point",
                        "coordinates": coordinates[i]
                    },
                    "altitude": 100
                })
        
        elif pattern == PatrolPattern.WAYPOINT:
            # 选择区域内的关键点
            # 这里简化为选择四个角点和中心点
            
            # 四个角点
            for i in range(0, len(coordinates) - 1, max(1, (len(coordinates) - 1) // 4)):
                waypoints.append({
                    "id": f"wp-{len(waypoints)}",
                    "position": {
                        "type": "Point",
                        "coordinates": coordinates[i]
                    },
                    "altitude": 100
                })
            
            # 中心点
            center_lon = sum(lons) / len(lons)
            center_lat = sum(lats) / len(lats)
            waypoints.append({
                "id": f"wp-{len(waypoints)}",
                "position": {
                    "type": "Point",
                    "coordinates": [center_lon, center_lat]
                },
                "altitude": 100
            })
        
        else:  # 默认为随机巡检
            # 随机生成10个点
            polygon = Polygon(coordinates)
            count = 0
            while count < 10:
                lon = min_lon + (max_lon - min_lon) * random.random()
                lat = min_lat + (max_lat - min_lat) * random.random()
                point = Point(lon, lat)
                
                if polygon.contains(point):
                    waypoints.append({
                        "id": f"wp-{len(waypoints)}",
                        "position": {
                            "type": "Point",
                            "coordinates": [lon, lat]
                        },
                        "altitude": 100
                    })
                    count += 1
        
        return waypoints
    
    async def _load_active_tasks(self):
        """加载分配给此智能体的活动任务"""
        try:
            tasks = await Task.find({
                "status": {"$in": [TaskStatus.ASSIGNED, TaskStatus.IN_PROGRESS]},
                "assigned_agents": self.agent_id,
                "type": {"$in": [TaskType.SURVEILLANCE, TaskType.INSPECTION]}
            }).to_list()
            
            for task in tasks:
                self.active_tasks[task.task_id] = {
                    "task": task,
                    "status": "in_progress",
                    "start_time": datetime.utcnow(),
                    "drone_id": task.assigned_drones[0] if task.assigned_drones else None,
                    "current_waypoint_index": 0,
                    "completed_waypoints": [],
                    "patrol_results": []
                }
            
            logger.info(f"加载了 {len(tasks)} 个活动任务")
        except Exception as e:
            logger.error(f"加载活动任务失败: {str(e)}")
    
    async def _find_monitor_agent(self):
        """查找监控智能体"""
        from .coordinator import get_agents_by_type
        
        monitor_agents = get_agents_by_type("MonitorAgent")
        if monitor_agents:
            self.monitor_agent_id = monitor_agents[0].agent_id
            logger.info(f"找到监控智能体: {self.monitor_agent_id}")
        else:
            logger.warning("未找到监控智能体")
    
    def _initialize_patrol_schedules(self):
        """初始化巡检计划"""
        try:
            # 为每个时间段创建巡检计划
            # 这里我们简化为每天的几个时间段
            time_slots = ["morning", "afternoon", "evening", "night"]
            
            for time_slot in time_slots:
                self.patrol_schedules[time_slot] = []
                
                # 为每个巡检区域安排巡检计划
                for area_id, area in self.patrol_areas.items():
                    # 根据区域优先级决定是否在此时间段巡检
                    if self._should_patrol_in_timeslot(area["priority"], time_slot):
                        self.patrol_schedules[time_slot].append({
                            "area_id": area_id,
                            "priority": area["priority"],
                            "pattern": area["pattern"]
                        })
            
            logger.info(f"初始化了 {len(time_slots)} 个时间段的巡检计划")
        except Exception as e:
            logger.error(f"初始化巡检计划失败: {str(e)}")
    
    def _should_patrol_in_timeslot(self, priority: int, time_slot: str) -> bool:
        """决定是否在特定时间段巡检"""
        # 高优先级区域在所有时间段都巡检
        if priority >= 8:
            return True
        
        # 中优先级区域在白天巡检
        if priority >= 5:
            return time_slot in ["morning", "afternoon", "evening"]
        
        # 低优先级区域只在白天特定时间段巡检
        return time_slot in ["morning", "afternoon"]
    
    def _get_current_timeslot(self) -> str:
        """获取当前时间段"""
        hour = datetime.utcnow().hour
        
        if 6 <= hour < 12:
            return "morning"
        elif 12 <= hour < 18:
            return "afternoon"
        elif 18 <= hour < 22:
            return "evening"
        else:
            return "night"
    
    async def run_cycle(self):
        """安防巡检智能体的主循环"""
        # 检查需要巡检的区域
        await self._check_patrol_areas()
        
        # 处理活动巡检任务
        await self._process_active_tasks()
        
        # 处理异常事件
        await self._process_anomalies()
    
    async def _check_patrol_areas(self):
        """检查需要巡检的区域，创建巡检任务"""
        try:
            # 获取当前时间段
            current_timeslot = self._get_current_timeslot()
            
            # 获取此时间段的巡检计划
            schedules = self.patrol_schedules.get(current_timeslot, [])
            
            for schedule in schedules:
                area_id = schedule["area_id"]
                area = self.patrol_areas.get(area_id)
                
                if not area:
                    continue
                
                # 检查是否需要巡检（上次巡检时间 + 巡检间隔 < 当前时间）
                if area["last_patrol"] + timedelta(minutes=area["patrol_interval"]) < datetime.utcnow():
                    # 检查是否已有针对此区域的活动任务
                    has_active_task = False
                    for task_info in self.active_tasks.values():
                        task = task_info["task"]
                        task_data = task.task_data or {}
                        if task_data.get("patrol_area_id") == area_id:
                            has_active_task = True
                            break
                    
                    if not has_active_task:
                        # 创建新的巡检任务
                        await self._create_patrol_task(area)
            
        except Exception as e:
            logger.error(f"检查巡检区域失败: {str(e)}")
    
    async def _create_patrol_task(self, area: Dict[str, Any]):
        """创建巡检任务"""
        try:
            # 检查是否已经存在相同的巡检任务
            existing_task = await Task.find_one({
                "title": f"{area['name']}巡检任务",
                "status": {"$in": [TaskStatus.PENDING, TaskStatus.ASSIGNED, TaskStatus.IN_PROGRESS]}
            })
            
            if existing_task:
                self.logger.info(f"已存在相同区域的巡检任务: {existing_task.task_id}")
                return existing_task
            
            # 创建新任务，确保不手动指定_id
            task = Task(
                title=f"{area['name']}巡检任务",
                description=f"对 {area['name']} 进行安防巡检，模式: {area['pattern']}",
                type=TaskType.SURVEILLANCE,
                priority=area["priority"],
                created_by=self.agent_id,
                task_data={
                    "patrol_area_id": area["zone_id"],
                    "patrol_pattern": area["pattern"],
                    "waypoints": area["waypoints"]
                }
            )
            
            # 设置第一个航点作为起点
            if area["waypoints"]:
                first_wp = area["waypoints"][0]
                task.start_location = Location(
                    position=GeoPoint(
                        type="Point",
                        coordinates=first_wp["position"]["coordinates"],
                        altitude=first_wp["altitude"]
                    )
                )
            
            # 设置最后一个航点作为终点
            if len(area["waypoints"]) > 1:
                last_wp = area["waypoints"][-1]
                task.end_location = Location(
                    position=GeoPoint(
                        type="Point",
                        coordinates=last_wp["position"]["coordinates"],
                        altitude=last_wp["altitude"]
                    )
                )
            
            # 使用insert插入新任务，避免可能的_id冲突
            try:
                await task.insert()
            except pymongo.errors.DuplicateKeyError as e:
                self.logger.warning(f"插入任务时出现重复键错误，尝试重新创建: {str(e)}")
                # 如果发生冲突，创建一个新的任务对象（会自动生成新的_id）
                task = Task(
                    task_id=str(uuid.uuid4()),  # 明确指定新的task_id
                    title=f"{area['name']}巡检任务",
                    description=f"对 {area['name']} 进行安防巡检，模式: {area['pattern']}",
                    type=TaskType.SURVEILLANCE,
                    priority=area["priority"],
                    created_by=self.agent_id,
                    task_data={
                        "patrol_area_id": area["zone_id"],
                        "patrol_pattern": area["pattern"],
                        "waypoints": area["waypoints"]
                    }
                )
                # 重新设置位置信息
                if area["waypoints"]:
                    first_wp = area["waypoints"][0]
                    task.start_location = Location(
                        position=GeoPoint(
                            type="Point",
                            coordinates=first_wp["position"]["coordinates"],
                            altitude=first_wp["altitude"]
                        )
                    )
                if len(area["waypoints"]) > 1:
                    last_wp = area["waypoints"][-1]
                    task.end_location = Location(
                        position=GeoPoint(
                            type="Point",
                            coordinates=last_wp["position"]["coordinates"],
                            altitude=last_wp["altitude"]
                        )
                    )
                await task.insert()
            
            # 更新区域最后巡检时间
            area["last_patrol"] = datetime.utcnow()
            
            # 通知协调者
            coordinator = await get_coordinator()
            await coordinator.message_queue.put({
                "type": "new_task",
                "data": task.dict(),
                "sender_id": self.agent_id
            })
            
            self.logger.info(f"创建了巡检任务: {task.task_id} 用于区域 {area['name']}")
            
            return task
        
        except Exception as e:
            self.logger.error(f"创建巡检任务失败: {str(e)}")
            return None
    
    async def _process_active_tasks(self):
        """处理活动巡检任务"""
        for task_id, task_info in list(self.active_tasks.items()):
            # 检查任务是否已完成或取消
            task = task_info["task"]
            updated_task = await Task.find_one({"task_id": task_id})
            
            if not updated_task or updated_task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
                # 任务已结束，从活动任务中移除
                self.active_tasks.pop(task_id, None)
                continue
            
            # 更新任务对象
            task_info["task"] = updated_task
            
            # 处理任务状态
            if task_info["status"] == "in_progress":
                # 模拟巡检过程
                await self._simulate_patrol(task_id, task_info)
            
            # 检查任务是否超时
            if (datetime.utcnow() - task_info["start_time"]).total_seconds() > 3600:  # 1小时超时
                logger.warning(f"任务 {task_id} 已超时")
                
                # 完成任务
                await self._complete_patrol_task(task_id, task_info, success=False, reason="任务超时")
    
    async def _simulate_patrol(self, task_id: str, task_info: Dict[str, Any]):
        """模拟巡检过程"""
        try:
            task = task_info["task"]
            task_data = task.task_data or {}
            waypoints = task_data.get("waypoints", [])
            
            if not waypoints:
                logger.warning(f"任务 {task_id} 没有航点")
                await self._complete_patrol_task(task_id, task_info, success=False, reason="没有航点")
                return
            
            # 获取当前航点索引
            current_idx = task_info["current_waypoint_index"]
            
            # 检查是否已完成所有航点
            if current_idx >= len(waypoints):
                logger.info(f"任务 {task_id} 已完成所有航点")
                await self._complete_patrol_task(task_id, task_info, success=True)
                return
            
            # 获取当前航点
            current_wp = waypoints[current_idx]
            
            # 模拟检测异常
            await self._detect_anomalies_at_waypoint(task_id, task_info, current_wp)
            
            # 标记当前航点为已完成
            task_info["completed_waypoints"].append(current_wp["id"])
            
            # 移动到下一个航点
            task_info["current_waypoint_index"] += 1
            
            # 更新任务数据
            task.task_data = task_data
            task.task_data["progress"] = {
                "current_waypoint": current_idx,
                "total_waypoints": len(waypoints),
                "completed_waypoints": task_info["completed_waypoints"],
                "last_update": datetime.utcnow().isoformat()
            }
            await task.save()
            
        except Exception as e:
            logger.error(f"模拟巡检过程失败: {str(e)}")
    
    async def _detect_anomalies_at_waypoint(self, task_id: str, task_info: Dict[str, Any], waypoint: Dict[str, Any]):
        """在航点检测异常"""
        try:
            # 在实际应用中，这应该从无人机摄像头获取数据
            # 这里我们模拟检测结果
            
            # 随机决定是否检测到异常
            if random.random() < 0.2:  # 20%的概率检测到异常
                # 创建检测结果
                detection_result = {
                    "timestamp": datetime.utcnow().isoformat(),
                    "waypoint_id": waypoint["id"],
                    "position": waypoint["position"],
                    "anomaly_type": random.choice(["unauthorized_person", "suspicious_object", "barrier", "fire"]),
                    "confidence": random.uniform(0.6, 0.95)
                }
                
                # 添加到巡检结果
                task_info["patrol_results"].append(detection_result)
                
                # 创建事件
                await self._create_anomaly_event(task_id, task_info, detection_result)
                
                logger.info(f"在任务 {task_id} 的航点 {waypoint['id']} 检测到异常: {detection_result['anomaly_type']}")
            
        except Exception as e:
            logger.error(f"检测航点异常失败: {str(e)}")
    
    async def _create_anomaly_event(self, task_id: str, task_info: Dict[str, Any], detection: Dict[str, Any]):
        """为检测到的异常创建事件"""
        try:
            # 根据异常类型确定事件级别
            anomaly_type = detection["anomaly_type"]
            event_level = EventLevel.LOW
            
            if anomaly_type in ["fire", "suspicious_object"]:
                event_level = EventLevel.HIGH
            elif anomaly_type in ["unauthorized_person"]:
                event_level = EventLevel.MEDIUM
            
            # 创建事件标题和描述
            title = f"安防巡检检测到异常: {anomaly_type}"
            description = f"在巡检任务 {task_id} 的航点 {detection['waypoint_id']} 处检测到异常：{anomaly_type}，置信度：{detection['confidence']:.2f}"
            
            # 创建位置对象
            position = detection["position"]
            location = Location(
                position=GeoPoint(
                    type="Point",
                    coordinates=position["coordinates"],
                    altitude=100
                )
            )
            
            # 创建边界框（模拟）
            x1, y1 = random.uniform(0.2, 0.4), random.uniform(0.2, 0.4)
            x2, y2 = random.uniform(0.6, 0.8), random.uniform(0.6, 0.8)
            
            bounding_boxes = [
                BoundingBox(
                    x1=x1,
                    y1=y1,
                    x2=x2,
                    y2=y2,
                    confidence=detection["confidence"],
                    class_id=0,
                    class_name=anomaly_type
                )
            ]
            
            # 创建事件
            event = Event(
                type=EventType.SECURITY,
                level=event_level,
                title=title,
                description=description,
                location=location,
                detected_by=self.agent_id,
                detection_data=detection,
                bounding_boxes=bounding_boxes,
                related_tasks=[task_id]
            )
            
            await event.insert()
            
            # 通知协调者
            coordinator = await get_coordinator()
            await coordinator.message_queue.put({
                "type": "new_event",
                "event_id": event.event_id,
                "source_agent_id": self.agent_id
            })
            
            # 保存到异常历史
            area_id = task_info["task"].task_data.get("patrol_area_id", "unknown")
            if area_id not in self.anomaly_history:
                self.anomaly_history[area_id] = []
            
            self.anomaly_history[area_id].append({
                "event_id": event.event_id,
                "anomaly_type": anomaly_type,
                "timestamp": datetime.utcnow().isoformat(),
                "waypoint_id": detection["waypoint_id"],
                "event_level": event_level
            })
            
            logger.info(f"为任务 {task_id} 检测到的异常创建了事件: {event.event_id}")
            
            return event
        
        except Exception as e:
            logger.error(f"创建异常事件失败: {str(e)}")
            return None
    
    async def _complete_patrol_task(self, task_id: str, task_info: Dict[str, Any], success: bool = True, reason: str = None):
        """完成巡检任务"""
        try:
            task = task_info["task"]
            
            # 更新任务状态
            task.status = TaskStatus.COMPLETED if success else TaskStatus.FAILED
            task.end_time = datetime.utcnow()
            
            # 更新任务数据
            task.task_data = task.task_data or {}
            task.task_data["patrol_results"] = task_info["patrol_results"]
            task.task_data["completed_waypoints"] = task_info["completed_waypoints"]
            task.task_data["success"] = success
            
            if not success and reason:
                task.task_data["failure_reason"] = reason
            
            await task.save()
            
            # 如果有分配的无人机，释放它们
            if task.assigned_drones:
                for drone_id in task.assigned_drones:
                    drone = await Drone.find_one({"drone_id": drone_id})
                    if drone:
                        drone.status = "idle"
                        drone.assigned_tasks = [t for t in drone.assigned_tasks if t != task_id]
                        await drone.save()
            
            # 从活动任务中移除
            self.active_tasks.pop(task_id, None)
            
            # 通知任务完成
            await self.broadcast_message({
                "type": "task_completed" if success else "task_failed",
                "task_id": task_id,
                "source_agent_id": self.agent_id
            })
            
            logger.info(f"完成任务 {task_id}，状态: {'成功' if success else '失败'}{f'，原因: {reason}' if reason else ''}")
        
        except Exception as e:
            logger.error(f"完成巡检任务失败: {str(e)}")
    
    async def _process_anomalies(self):
        """处理检测到的异常"""
        try:
            # 分析异常历史，更新巡检优先级和模式
            for area_id, anomalies in self.anomaly_history.items():
                # 只考虑最近24小时的异常
                recent_anomalies = [
                    a for a in anomalies 
                    if datetime.fromisoformat(a["timestamp"]) > datetime.utcnow() - timedelta(hours=24)
                ]
                
                if not recent_anomalies:
                    continue
                
                # 获取区域信息
                area = self.patrol_areas.get(area_id)
                if not area:
                    continue
                
                # 计算异常严重程度
                severity = 0
                for anomaly in recent_anomalies:
                    if anomaly["event_level"] == EventLevel.HIGH:
                        severity += 3
                    elif anomaly["event_level"] == EventLevel.MEDIUM:
                        severity += 2
                    else:
                        severity += 1
                
                # 根据严重程度调整巡检间隔和模式
                if severity >= 5:
                    # 高严重度：减少巡检间隔，使用网格模式
                    area["patrol_interval"] = max(30, area["patrol_interval"] // 2)
                    area["pattern"] = PatrolPattern.GRID
                    
                    # 更新航点
                    area["waypoints"] = self._generate_patrol_waypoints(area["geometry"], PatrolPattern.GRID)
                
                elif severity >= 3:
                    # 中等严重度：稍微减少巡检间隔
                    area["patrol_interval"] = max(60, area["patrol_interval"] * 2 // 3)
                
                # 更新区域信息
                self.patrol_areas[area_id] = area
                
                logger.info(f"更新区域 {area_id} 的巡检策略，严重度: {severity}，新间隔: {area['patrol_interval']}分钟，模式: {area['pattern']}")
        
        except Exception as e:
            logger.error(f"处理异常失败: {str(e)}")
    
    async def handle_task_assigned(self, task_id: str):
        """处理分配的任务"""
        await super().handle_task_assigned(task_id)
        
        task = await Task.find_one({"task_id": task_id})
        if not task:
            logger.warning(f"找不到任务: {task_id}")
            return
        
        # 如果不是巡检或监控任务，忽略
        if task.type not in [TaskType.SURVEILLANCE, TaskType.INSPECTION]:
            return
        
        # 添加到活动任务
        self.active_tasks[task_id] = {
            "task": task,
            "status": "in_progress",
            "start_time": datetime.utcnow(),
            "drone_id": task.assigned_drones[0] if task.assigned_drones else None,
            "current_waypoint_index": 0,
            "completed_waypoints": [],
            "patrol_results": []
        }
        
        logger.info(f"接受了任务: {task_id}")
    
    async def handle_event_detected(self, event_id: str):
        """处理检测到的事件"""
        await super().handle_event_detected(event_id)
        
        # 获取事件详情
        event = await Event.find_one({"event_id": event_id})
        if not event:
            return
        
        # 如果是安全相关事件，创建特殊任务来处理
        if event.type in [EventType.SECURITY, EventType.ANOMALY] and event.level in [EventLevel.MEDIUM, EventLevel.HIGH]:
            # 检查是否已有针对此事件的任务
            existing_task = await Task.find_one({
                "related_events": event_id,
                "status": {"$in": [TaskStatus.PENDING, TaskStatus.ASSIGNED, TaskStatus.IN_PROGRESS]}
            })
            
            if not existing_task:
                # 创建检查任务
                task = Task(
                    title=f"检查事件: {event.title}",
                    description=f"对事件 {event_id} 进行现场检查: {event.description}",
                    type=TaskType.INSPECTION,
                    priority=self._map_event_level_to_priority(event.level),
                    created_by=self.agent_id,
                    related_events=[event_id],
                    start_location=event.location,
                    end_location=event.location
                )
                
                await task.insert()
                
                # 通知协调者
                coordinator = await get_coordinator()
                await coordinator.message_queue.put({
                    "type": "new_task",
                    "task_id": task.task_id,
                    "source_agent_id": self.agent_id
                })
                
                logger.info(f"为事件 {event_id} 创建了检查任务: {task.task_id}")
    
    def _map_event_level_to_priority(self, event_level: EventLevel) -> int:
        """将事件级别映射到任务优先级"""
        if event_level == EventLevel.HIGH:
            return 10
        elif event_level == EventLevel.MEDIUM:
            return 7
        else:
            return 4
    
    async def handle_query(self, query: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """处理来自其他智能体的查询"""
        if query == "get_security_zones":
            # 返回安全区域信息
            return {
                "success": True,
                "zones": self.security_zones
            }
        
        elif query == "get_patrol_areas":
            # 返回巡检区域信息
            area_id = data.get("area_id")
            
            if area_id:
                # 返回特定区域
                area = self.patrol_areas.get(area_id)
                if not area:
                    return {"success": False, "error": f"Area not found: {area_id}"}
                
                return {
                    "success": True,
                    "area": area
                }
            else:
                # 返回所有区域
                return {
                    "success": True,
                    "areas": list(self.patrol_areas.values())
                }
        
        elif query == "get_anomaly_history":
            # 返回异常历史
            area_id = data.get("area_id")
            
            if area_id:
                # 返回特定区域的异常历史
                anomalies = self.anomaly_history.get(area_id, [])
                return {
                    "success": True,
                    "area_id": area_id,
                    "anomalies": anomalies
                }
            else:
                # 返回所有异常历史
                return {
                    "success": True,
                    "anomaly_history": self.anomaly_history
                }
        
        elif query == "create_patrol_task":
            # 创建特定区域的巡检任务
            area_id = data.get("area_id")
            if not area_id:
                return {"success": False, "error": "Missing area_id"}
            
            area = self.patrol_areas.get(area_id)
            if not area:
                return {"success": False, "error": f"Area not found: {area_id}"}
            
            task = await self._create_patrol_task(area)
            if not task:
                return {"success": False, "error": "Failed to create patrol task"}
            
            return {
                "success": True,
                "task_id": task.task_id
            }
        
        return await super().handle_query(query, data)


# 创建安防巡检智能体的工厂函数
async def create_security_agent(agent_id: Optional[str] = None, name: Optional[str] = None) -> SecurityAgent:
    """创建并初始化安防巡检智能体"""
    agent = SecurityAgent(agent_id, name)
    await agent.initialize()
    register_agent(agent)
    return agent