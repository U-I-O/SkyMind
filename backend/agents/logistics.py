from typing import Dict, List, Any, Optional, Union, Tuple, Set
import asyncio
import uuid
import time
from datetime import datetime, timedelta
import json
import numpy as np
from pathlib import Path
import math
import heapq
from dataclasses import dataclass, field
import random

from config.logging_config import get_logger
from database.models import (
    Task, FlightPath, GeoPoint, Location, Drone,
    TaskStatus, TaskType, TimeWindow
)
from config.settings import settings
from .base import BaseAgent
from .coordinator import register_agent, get_coordinator

logger = get_logger("agents.logistics")


@dataclass(order=True)
class PrioritizedTask:
    """带优先级的任务，用于优先队列"""
    priority: int
    task_id: str = field(compare=False)
    task: Task = field(compare=False)


class LogisticsAgent(BaseAgent):
    """
    物流调度智能体负责管理和优化物流任务，
    包括路径规划、任务分配和调度。
    """
    
    def __init__(self, agent_id: Optional[str] = None, name: str = "物流调度智能体"):
        super().__init__(agent_id, name)
        self.agent_type = "LogisticsAgent"
        self.task_queue: List[PrioritizedTask] = []
        self.scheduled_tasks: Dict[str, Dict[str, Any]] = {}
        self.pending_tasks: Dict[str, Task] = {}
        self.drone_status: Dict[str, Dict[str, Any]] = {}
        self.delivery_statistics: Dict[str, Any] = {}
        self.scheduling_lock = asyncio.Lock()
        self.capabilities = {
            "logistics": 0.95,
            "scheduling": 0.9,
            "optimization": 0.85,
            "resource_management": 0.8
        }
    
    async def initialize(self):
        """初始化物流调度智能体"""
        await super().initialize()
        
        # 加载状态
        await self._load_drone_status()
        await self._load_pending_tasks()
        
        # 初始化统计信息
        self.delivery_statistics = {
            "total_tasks": 0,
            "completed_tasks": 0,
            "failed_tasks": 0,
            "total_distance": 0,
            "average_delivery_time": 0,
            "deliveries_by_hour": {str(h): 0 for h in range(24)},
            "deliveries_by_drone": {},
            "last_updated": datetime.utcnow().isoformat()
        }
        
        return self
    
    async def _load_drone_status(self):
        """加载无人机状态"""
        try:
            drones = await Drone.find_all().to_list()
            
            for drone in drones:
                self.drone_status[drone.drone_id] = {
                    "drone": drone,
                    "current_task": None,
                    "last_updated": datetime.utcnow(),
                    "estimated_available_time": datetime.utcnow(),
                    "total_distance": 0,
                    "total_tasks": 0,
                    "status_history": []
                }
            
            logger.info(f"加载了 {len(drones)} 架无人机的状态")
        except Exception as e:
            logger.error(f"加载无人机状态失败: {str(e)}")
    
    async def _load_pending_tasks(self):
        """加载待处理的物流任务"""
        try:
            # 查找分配给此智能体的物流任务
            tasks = await Task.find({
                "type": TaskType.DELIVERY,
                "status": {"$in": [TaskStatus.PENDING, TaskStatus.ASSIGNED]},
                "assigned_agents": self.agent_id
            }).to_list()
            
            for task in tasks:
                self.pending_tasks[task.task_id] = task
                
                # 计算任务优先级
                priority = self._calculate_task_priority(task)
                
                # 添加到优先队列
                heapq.heappush(
                    self.task_queue,
                    PrioritizedTask(priority=priority, task_id=task.task_id, task=task)
                )
            
            logger.info(f"加载了 {len(tasks)} 个待处理的物流任务")
        except Exception as e:
            logger.error(f"加载待处理的物流任务失败: {str(e)}")
    
    async def run_cycle(self):
        """物流调度智能体的主循环"""
        # 更新无人机状态
        await self._update_drone_status()
        
        # 处理任务队列
        await self._process_task_queue()
        
        # 检查已调度任务的状态
        await self._check_scheduled_tasks()
        
        # 更新统计信息
        await self._update_statistics()
    
    async def _update_drone_status(self):
        """更新无人机状态信息"""
        try:
            # 获取所有无人机的最新状态
            drones = await Drone.find_all().to_list()
            
            for drone in drones:
                if drone.drone_id in self.drone_status:
                    # 更新现有无人机的状态
                    drone_info = self.drone_status[drone.drone_id]
                    
                    # 保存之前的状态
                    prev_status = drone_info["drone"].status
                    
                    # 更新无人机对象
                    drone_info["drone"] = drone
                    
                    # 如果状态发生变化，记录历史
                    if prev_status != drone.status:
                        drone_info["status_history"].append({
                            "timestamp": datetime.utcnow().isoformat(),
                            "from_status": prev_status,
                            "to_status": drone.status
                        })
                    
                    # 更新最后更新时间
                    drone_info["last_updated"] = datetime.utcnow()
                else:
                    # 添加新的无人机
                    self.drone_status[drone.drone_id] = {
                        "drone": drone,
                        "current_task": None,
                        "last_updated": datetime.utcnow(),
                        "estimated_available_time": datetime.utcnow(),
                        "total_distance": 0,
                        "total_tasks": 0,
                        "status_history": []
                    }
            
            # 检查分配任务的无人机
            for drone_id, drone_info in self.drone_status.items():
                drone = drone_info["drone"]
                current_task_id = drone_info["current_task"]
                
                # 检查无人机当前任务是否已完成
                if current_task_id:
                    task = await Task.find_one({"task_id": current_task_id})
                    
                    if not task or task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
                        # 任务已完成或取消，标记无人机为空闲
                        drone_info["current_task"] = None
                        drone_info["estimated_available_time"] = datetime.utcnow()
                        
                        # 如果无人机状态不是空闲，更新状态
                        if drone.status != "idle":
                            drone.status = "idle"
                            await drone.save()
                            
                            # 记录状态变化
                            drone_info["status_history"].append({
                                "timestamp": datetime.utcnow().isoformat(),
                                "from_status": "flying",
                                "to_status": "idle"
                            })
                            
                            logger.info(f"无人机 {drone_id} 已完成任务 {current_task_id}，状态更新为空闲")
            
        except Exception as e:
            logger.error(f"更新无人机状态信息失败: {str(e)}")
    
    async def _process_task_queue(self):
        """处理任务队列"""
        async with self.scheduling_lock:
            # 获取可用的无人机
            available_drones = self._get_available_drones()
            
            # 如果没有可用的无人机，直接返回
            if not available_drones:
                return
            
            # 处理队列中的任务
            while available_drones and self.task_queue:
                # 获取优先级最高的任务
                prioritized_task = heapq.heappop(self.task_queue)
                task_id = prioritized_task.task_id
                task = prioritized_task.task
                
                # 检查任务是否仍然有效
                updated_task = await Task.find_one({"task_id": task_id})
                if not updated_task or updated_task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
                    # 任务已完成或取消，移除
                    self.pending_tasks.pop(task_id, None)
                    continue
                
                # 更新任务对象
                task = updated_task
                self.pending_tasks[task_id] = task
                
                # 选择最合适的无人机
                best_drone = self._select_best_drone(task, available_drones)
                
                if best_drone:
                    # 分配任务给无人机
                    await self._assign_task_to_drone(task, best_drone)
                    
                    # 从可用无人机列表中移除
                    available_drones.remove(best_drone)
                else:
                    # 没有合适的无人机，将任务放回队列
                    heapq.heappush(
                        self.task_queue,
                        PrioritizedTask(priority=prioritized_task.priority, task_id=task_id, task=task)
                    )
                    break
    
    def _get_available_drones(self) -> List[Drone]:
        """获取当前可用的无人机"""
        available_drones = []
        
        for drone_id, drone_info in self.drone_status.items():
            drone = drone_info["drone"]
            current_task = drone_info["current_task"]
            
            # 只选择空闲且电池电量足够的无人机
            if drone.status == "idle" and not current_task and drone.battery_level >= 30:
                available_drones.append(drone)
        
        return available_drones
    
    def _calculate_task_priority(self, task: Task) -> int:
        """计算任务优先级，返回整数值（越小越优先）"""
        base_priority = task.priority
        
        # 如果任务有时间窗口，考虑时间因素
        if task.time_window:
            now = datetime.utcnow()
            start_time = task.time_window.start_time
            end_time = task.time_window.end_time
            
            # 如果已经超过开始时间，提高优先级
            if now > start_time:
                time_factor = (now - start_time).total_seconds() / 60  # 分钟
                base_priority -= min(int(time_factor / 10), 5)  # 每10分钟提高1点优先级，最多提高5点
            
            # 如果接近结束时间，大幅提高优先级
            time_left = (end_time - now).total_seconds() / 60  # 分钟
            if time_left < 30:  # 如果剩余不到30分钟
                base_priority -= 10  # 紧急提高优先级
        
        # 考虑任务状态
        if task.status == TaskStatus.ASSIGNED:
            base_priority -= 2  # 已分配的任务优先级略高
        
        # 确保优先级在有效范围内
        return max(1, min(base_priority, 10))
    
    def _select_best_drone(self, task: Task, available_drones: List[Drone]) -> Optional[Drone]:
        """为任务选择最合适的无人机"""
        if not available_drones:
            return None
        
        # 获取任务的起点和终点
        if not task.start_location or not task.end_location:
            logger.warning(f"任务 {task.task_id} 缺少起点或终点")
            return None
        
        start_point = task.start_location.position.coordinates  # [lon, lat]
        end_point = task.end_location.position.coordinates  # [lon, lat]
        
        best_drone = None
        best_score = float('-inf')
        
        for drone in available_drones:
            # 如果无人机没有当前位置，跳过
            if not drone.current_location:
                continue
            
            # 计算无人机到起点的距离
            drone_point = drone.current_location.coordinates  # [lon, lat]
            distance_to_start = self._calculate_distance(
                drone_point[0], drone_point[1],
                start_point[0], start_point[1]
            )
            
            # 计算任务距离
            task_distance = self._calculate_distance(
                start_point[0], start_point[1],
                end_point[0], end_point[1]
            )
            
            # 估算总飞行距离
            total_distance = distance_to_start + task_distance
            
            # 计算电池充足度（剩余电量与预估需求的比值）
            max_range = drone.max_flight_time * settings.DRONE_MAX_SPEED / 60  # 最大飞行范围（公里）
            battery_adequacy = (drone.battery_level / 100) * max_range / (total_distance / 1000)
            
            # 如果电池不足以完成任务，跳过
            if battery_adequacy < 1.2:  # 需要20%的安全余量
                continue
            
            # 考虑无人机的负载能力
            payload_factor = 1.0
            task_payload = task.task_data.get("payload_weight", 0) if task.task_data else 0
            
            if task_payload > 0:
                if task_payload > drone.payload_capacity:
                    continue  # 超过负载能力
                payload_factor = 1 - (task_payload / drone.payload_capacity)  # 负载因子
            
            # 计算总分数（越大越好）
            # 考虑因素：距离、电池充足度、负载能力
            score = -(distance_to_start * 0.5) + (battery_adequacy * 30) + (payload_factor * 20)
            
            if score > best_score:
                best_score = score
                best_drone = drone
        
        return best_drone
    
    async def _assign_task_to_drone(self, task: Task, drone: Drone):
        """分配任务给无人机"""
        try:
            task_id = task.task_id
            drone_id = drone.drone_id
            
            logger.info(f"将任务 {task_id} 分配给无人机 {drone_id}")
            
            # 更新任务状态
            task.status = TaskStatus.ASSIGNED
            task.assigned_drones = [drone_id]
            await task.save()
            
            # 更新无人机状态
            drone.status = "flying"
            drone.assigned_tasks.append(task_id)
            await drone.save()
            
            # 更新内部状态
            drone_info = self.drone_status.get(drone_id)
            if drone_info:
                drone_info["current_task"] = task_id
                
                # 估算任务完成时间
                completion_time = self._estimate_task_completion_time(task, drone)
                drone_info["estimated_available_time"] = completion_time
                
                # 更新统计信息
                if task.planned_path:
                    drone_info["total_distance"] += task.planned_path.distance
                drone_info["total_tasks"] += 1
                
                # 记录状态变化
                drone_info["status_history"].append({
                    "timestamp": datetime.utcnow().isoformat(),
                    "from_status": "idle",
                    "to_status": "flying",
                    "task_id": task_id
                })
            
            # 将任务添加到已调度任务列表
            self.scheduled_tasks[task_id] = {
                "task": task,
                "drone_id": drone_id,
                "assigned_time": datetime.utcnow(),
                "estimated_completion_time": completion_time,
                "status": "assigned"
            }
            
            # 从待处理任务中移除
            self.pending_tasks.pop(task_id, None)
            
            # 通知任务已分配
            await self.broadcast_message({
                "type": "task_assigned",
                "task_id": task_id,
                "drone_id": drone_id,
                "source_agent_id": self.agent_id
            })
            
            # 启动任务监控
            asyncio.create_task(self._monitor_task(task_id, drone_id))
            
            logger.info(f"成功将任务 {task_id} 分配给无人机 {drone_id}，预计完成时间: {completion_time}")
        
        except Exception as e:
            logger.error(f"分配任务给无人机失败: {str(e)}")
    
    def _estimate_task_completion_time(self, task: Task, drone: Drone) -> datetime:
        """估算任务完成时间"""
        now = datetime.utcnow()
        
        # 如果有规划路径，使用路径信息
        if task.planned_path:
            flight_time = task.planned_path.estimated_duration  # 分钟
            return now + timedelta(minutes=flight_time)
        
        # 否则进行简单估算
        start_point = task.start_location.position.coordinates if task.start_location else None
        end_point = task.end_location.position.coordinates if task.end_location else None
        
        if not start_point or not end_point:
            # 如果没有起点或终点，使用默认时间
            return now + timedelta(minutes=30)
        
        # 计算距离
        distance = self._calculate_distance(
            start_point[0], start_point[1],
            end_point[0], end_point[1]
        )
        
        # 估算飞行时间（分钟）
        speed = settings.DRONE_MAX_SPEED  # m/s
        flight_time = distance / speed / 60
        
        # 添加一些额外时间用于起飞、降落和装卸货物
        total_time = flight_time + 10  # 额外10分钟
        
        return now + timedelta(minutes=total_time)
    
    async def _monitor_task(self, task_id: str, drone_id: str):
        """监控任务执行状态"""
        try:
            # 获取任务信息
            task_info = self.scheduled_tasks.get(task_id)
            if not task_info:
                return
            
            # 获取无人机信息
            drone_info = self.drone_status.get(drone_id)
            if not drone_info:
                return
            
            # 模拟任务执行过程
            task_info["status"] = "in_progress"
            
            # 计算总飞行时间（分钟）
            flight_time = (task_info["estimated_completion_time"] - task_info["assigned_time"]).total_seconds() / 60
            
            # 模拟飞行到起点
            await asyncio.sleep(random.uniform(3, 7))  # 3-7秒模拟飞行到起点
            
            # 模拟装载货物
            await asyncio.sleep(2)  # 2秒模拟装载
            
            # 模拟飞行到目的地
            remaining_time = max(5, min(30, flight_time))  # 最少5秒，最多30秒
            await asyncio.sleep(remaining_time)
            
            # 模拟卸载货物
            await asyncio.sleep(2)  # 2秒模拟卸载
            
            # 更新任务状态
            await self._complete_task(task_id)
        
        except Exception as e:
            logger.error(f"监控任务 {task_id} 失败: {str(e)}")
    
    async def _complete_task(self, task_id: str):
        """完成任务"""
        try:
            # 获取任务信息
            task_info = self.scheduled_tasks.get(task_id)
            if not task_info:
                return
            
            task = task_info["task"]
            drone_id = task_info["drone_id"]
            
            # 更新任务状态
            task.status = TaskStatus.COMPLETED
            task.end_time = datetime.utcnow()
            await task.save()
            
            # 更新无人机状态
            drone = await Drone.find_one({"drone_id": drone_id})
            if drone:
                drone.status = "idle"
                drone.assigned_tasks = [t for t in drone.assigned_tasks if t != task_id]
                
                # 减少电池电量（根据任务距离）
                if task.planned_path:
                    distance_km = task.planned_path.distance / 1000
                    battery_consumption = min(30, max(5, int(distance_km * 2)))  # 每公里消耗2%电量，至少5%，最多30%
                    drone.battery_level = max(0, drone.battery_level - battery_consumption)
                else:
                    # 如果没有规划路径，默认消耗10%电量
                    drone.battery_level = max(0, drone.battery_level - 10)
                
                await drone.save()
            
            # 更新内部状态
            drone_info = self.drone_status.get(drone_id)
            if drone_info:
                drone_info["current_task"] = None
                drone_info["estimated_available_time"] = datetime.utcnow()
                
                # 记录状态变化
                drone_info["status_history"].append({
                    "timestamp": datetime.utcnow().isoformat(),
                    "from_status": "flying",
                    "to_status": "idle",
                    "task_id": task_id,
                    "completed": True
                })
            
            # 更新任务信息
            task_info["status"] = "completed"
            task_info["completion_time"] = datetime.utcnow()
            
            # 更新统计信息
            self.delivery_statistics["total_tasks"] += 1
            self.delivery_statistics["completed_tasks"] += 1
            
            if task.planned_path:
                self.delivery_statistics["total_distance"] += task.planned_path.distance
            
            # 按小时统计
            hour = datetime.utcnow().hour
            self.delivery_statistics["deliveries_by_hour"][str(hour)] = \
                self.delivery_statistics["deliveries_by_hour"].get(str(hour), 0) + 1
            
            # 按无人机统计
            self.delivery_statistics["deliveries_by_drone"][drone_id] = \
                self.delivery_statistics["deliveries_by_drone"].get(drone_id, 0) + 1
            
            # 通知任务完成
            await self.broadcast_message({
                "type": "task_completed",
                "task_id": task_id,
                "drone_id": drone_id,
                "source_agent_id": self.agent_id
            })
            
            logger.info(f"任务 {task_id} 已完成")
        
        except Exception as e:
            logger.error(f"完成任务 {task_id} 失败: {str(e)}")
    
    async def _check_scheduled_tasks(self):
        """检查已调度任务的状态"""
        now = datetime.utcnow()
        
        for task_id, task_info in list(self.scheduled_tasks.items()):
            # 如果任务已完成，从列表中移除
            if task_info["status"] == "completed":
                self.scheduled_tasks.pop(task_id, None)
                continue
            
            # 检查任务是否超时
            if task_info["status"] == "in_progress" and now > task_info["estimated_completion_time"] + timedelta(minutes=30):
                logger.warning(f"任务 {task_id} 已超时")
                
                # 标记任务失败
                task = task_info["task"]
                task.status = TaskStatus.FAILED
                task.task_data = task.task_data or {}
                task.task_data["failure_reason"] = "任务执行超时"
                await task.save()
                
                # 释放无人机
                drone_id = task_info["drone_id"]
                drone = await Drone.find_one({"drone_id": drone_id})
                if drone:
                    drone.status = "idle"
                    drone.assigned_tasks = [t for t in drone.assigned_tasks if t != task_id]
                    await drone.save()
                
                # 更新无人机状态
                drone_info = self.drone_status.get(drone_id)
                if drone_info:
                    drone_info["current_task"] = None
                    drone_info["estimated_available_time"] = datetime.utcnow()
                
                # 更新统计信息
                self.delivery_statistics["total_tasks"] += 1
                self.delivery_statistics["failed_tasks"] += 1
                
                # 从列表中移除
                self.scheduled_tasks.pop(task_id, None)
    
    async def _update_statistics(self):
        """更新统计信息"""
        self.delivery_statistics["last_updated"] = datetime.utcnow().isoformat()
        
        # 计算平均配送时间
        if self.delivery_statistics["completed_tasks"] > 0:
            total_time = 0
            count = 0
            
            for task_id, task_info in self.scheduled_tasks.items():
                if task_info["status"] == "completed" and "completion_time" in task_info:
                    duration = (task_info["completion_time"] - task_info["assigned_time"]).total_seconds() / 60
                    total_time += duration
                    count += 1
            
            if count > 0:
                self.delivery_statistics["average_delivery_time"] = total_time / count
        
        # 更新指标
        await self.update_metrics({
            "delivery_statistics": self.delivery_statistics,
            "scheduled_tasks": len(self.scheduled_tasks),
            "pending_tasks": len(self.pending_tasks),
            "last_update": datetime.utcnow().isoformat()
        })
    
    def _calculate_distance(self, lon1: float, lat1: float, lon2: float, lat2: float) -> float:
        """
        计算两点之间的距离（米）
        """
        # 将坐标转换为弧度
        lon1, lat1, lon2, lat2 = map(math.radians, [lon1, lat1, lon2, lat2])
        
        # Haversine公式
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        r = 6371000  # 地球半径，单位为米
        
        return c * r
    
    async def handle_task_assigned(self, task_id: str):
        """处理分配的任务"""
        await super().handle_task_assigned(task_id)
        
        # 加载任务
        task = await Task.find_one({"task_id": task_id})
        if not task:
            logger.warning(f"找不到任务: {task_id}")
            return
        
        # 如果不是物流任务，忽略
        if task.type != TaskType.DELIVERY:
            return
        
        # 添加到待处理任务
        self.pending_tasks[task_id] = task
        
        # 计算优先级
        priority = self._calculate_task_priority(task)
        
        # 添加到优先队列
        heapq.heappush(
            self.task_queue,
            PrioritizedTask(priority=priority, task_id=task_id, task=task)
        )
        
        logger.info(f"接受了物流任务: {task_id}，优先级: {priority}")
    
    async def handle_query(self, query: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """处理来自其他智能体的查询"""
        if query == "get_delivery_statistics":
            # 返回配送统计信息
            return {
                "success": True,
                "statistics": self.delivery_statistics
            }
        
        elif query == "get_drone_availability":
            # 返回无人机可用性信息
            drone_id = data.get("drone_id")
            
            if drone_id:
                # 返回特定无人机的可用性
                drone_info = self.drone_status.get(drone_id)
                if not drone_info:
                    return {"success": False, "error": f"Drone not found: {drone_id}"}
                
                return {
                    "success": True,
                    "drone_id": drone_id,
                    "available": drone_info["drone"].status == "idle" and not drone_info["current_task"],
                    "current_task": drone_info["current_task"],
                    "estimated_available_time": drone_info["estimated_available_time"].isoformat(),
                    "battery_level": drone_info["drone"].battery_level
                }
            else:
                # 返回所有无人机的可用性
                availability = {}
                
                for drone_id, drone_info in self.drone_status.items():
                    availability[drone_id] = {
                        "available": drone_info["drone"].status == "idle" and not drone_info["current_task"],
                        "current_task": drone_info["current_task"],
                        "estimated_available_time": drone_info["estimated_available_time"].isoformat(),
                        "battery_level": drone_info["drone"].battery_level
                    }
                
                return {
                    "success": True,
                    "availability": availability,
                    "available_count": sum(1 for info in availability.values() if info["available"])
                }
        
        elif query == "estimate_delivery_time":
            # 估算配送时间
            start_point = data.get("start_point")
            end_point = data.get("end_point")
            
            if not start_point or not end_point:
                return {"success": False, "error": "Missing start_point or end_point"}
            
            # 计算距离
            distance = self._calculate_distance(
                start_point[0], start_point[1],
                end_point[0], end_point[1]
            )
            
            # 估算飞行时间（分钟）
            speed = settings.DRONE_MAX_SPEED  # m/s
            flight_time = distance / speed / 60
            
            # 添加一些额外时间用于起飞、降落和装卸货物
            total_time = flight_time + 10  # 额外10分钟
            
            # 查询可用无人机
            available_drones = self._get_available_drones()
            
            return {
                "success": True,
                "distance_meters": distance,
                "estimated_flight_time_minutes": flight_time,
                "estimated_total_time_minutes": total_time,
                "available_drones": len(available_drones)
            }
        
        return await super().handle_query(query, data)


# 创建物流调度智能体的工厂函数
async def create_logistics_agent(agent_id: Optional[str] = None, name: Optional[str] = None) -> LogisticsAgent:
    """创建并初始化物流调度智能体"""
    agent = LogisticsAgent(agent_id, name)
    await agent.initialize()
    register_agent(agent)
    return agent