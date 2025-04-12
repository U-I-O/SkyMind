from typing import Dict, List, Any, Optional, Union, Tuple, Set
import asyncio
import uuid
import time
from datetime import datetime
import json
import numpy as np
import networkx as nx
from shapely.geometry import Point, Polygon, LineString
import osmnx as ox
import gymnasium as gym
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv
import torch
import pickle
from pathlib import Path
import math
import heapq

from config.logging_config import get_logger
from database.models import (
    Task, FlightPath, GeoPoint, Location, NoFlyZone, Drone,
    TaskStatus, TaskType
)
from config.settings import settings
from .base import BaseAgent
from .coordinator import register_agent, get_coordinator

logger = get_logger("agents.planner")

# 路径规划算法类型
class PlanningAlgorithm:
    A_STAR = "a_star"
    RRT = "rrt"
    RL = "reinforcement_learning"
    DIJKSTRA = "dijkstra"
    GENETIC = "genetic"

class PathPlanningAgent(BaseAgent):
    """
    路径规划智能体负责为无人机任务计划最优路径，
    考虑障碍物、禁飞区和其他约束。
    """
    
    def __init__(self, agent_id: Optional[str] = None, name: str = "路径规划智能体"):
        super().__init__(agent_id, name)
        self.agent_type = "PathPlanningAgent"
        self.active_tasks: Dict[str, Task] = {}
        self.no_fly_zones: List[NoFlyZone] = []
        self.city_graph = None
        self.rl_model = None
        self.cache_dir = Path("./data/path_cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.path_cache: Dict[str, Any] = {}
        self.planning_lock = asyncio.Lock()
        self.capabilities = {
            "path_planning": 0.95,
            "obstacle_avoidance": 0.9,
            "optimization": 0.85,
            "route_analysis": 0.8
        }
    
    async def initialize(self):
        """初始化路径规划智能体"""
        await super().initialize()
        
        # 加载禁飞区
        await self._load_no_fly_zones()
        
        # 初始化城市图
        await self._initialize_city_graph()
        
        # 初始化强化学习模型（如果配置）
        if settings.PATH_PLANNING_ALGORITHM == PlanningAlgorithm.RL:
            await self._initialize_rl_model()
        
        # 加载路径缓存
        await self._load_path_cache()
        
        # 加载活动任务
        await self._load_active_tasks()
        
        return self
    
    async def _load_no_fly_zones(self):
        """从数据库加载禁飞区"""
        try:
            # 加载永久禁飞区
            permanent_zones = await NoFlyZone.find({"permanent": True}).to_list()
            self.no_fly_zones.extend(permanent_zones)
            
            # 加载当前有效的临时禁飞区
            now = datetime.utcnow()
            temp_zones = await NoFlyZone.find({
                "permanent": False,
                "start_time": {"$lte": now},
                "end_time": {"$gte": now}
            }).to_list()
            self.no_fly_zones.extend(temp_zones)
            
            self.logger.info(f"加载了 {len(self.no_fly_zones)} 个禁飞区")
        except Exception as e:
            self.logger.error(f"加载禁飞区失败: {str(e)}")
    
    async def _initialize_city_graph(self):
        """初始化城市路网图，用于路径规划"""
        try:
            # 检查是否有缓存的城市图
            graph_path = self.cache_dir / "city_graph.pkl"
            
            if graph_path.exists():
                self.logger.info("从缓存加载城市图")
                with open(graph_path, "rb") as f:
                    self.city_graph = pickle.load(f)
            else:
                self.logger.info("创建新的城市图")
                # 使用OpenStreetMap数据创建城市图
                # 使用设置中的默认城市中心
                lat = settings.DEFAULT_CITY_CENTER["lat"]
                lon = settings.DEFAULT_CITY_CENTER["lon"]
                
                # 在后台线程中下载和处理图
                self.city_graph = await asyncio.to_thread(
                    ox.graph_from_point,
                    (lat, lon),
                    dist=5000,  # 5公里半径
                    network_type="drive",
                    simplify=True
                )
                
                # 将图转换为无向图，以便于寻路
                self.city_graph = self.city_graph.to_undirected()
                
                # 保存图到缓存
                with open(graph_path, "wb") as f:
                    pickle.dump(self.city_graph, f)
            
            self.logger.info(f"城市图初始化成功，节点数: {len(self.city_graph.nodes)}, 边数: {len(self.city_graph.edges)}")
        except Exception as e:
            self.logger.error(f"初始化城市图失败: {str(e)}")
            # 创建一个简单的后备图
            self.city_graph = nx.grid_2d_graph(100, 100)
            self.logger.warning("使用简单网格图作为后备")
    
    async def _initialize_rl_model(self):
        """初始化强化学习模型，用于路径规划"""
        try:
            # 检查是否有预训练模型
            model_path = self.cache_dir / "rl_path_model.zip"
            
            if model_path.exists():
                self.logger.info("加载预训练的强化学习模型")
                # 在后台线程中加载模型
                self.rl_model = await asyncio.to_thread(PPO.load, model_path)
            else:
                self.logger.warning("没有找到预训练的强化学习模型，将使用A*算法替代")
                # 设置后备为A*算法
                settings.PATH_PLANNING_ALGORITHM = PlanningAlgorithm.A_STAR
        except Exception as e:
            self.logger.error(f"初始化强化学习模型失败: {str(e)}")
            # 设置后备为A*算法
            settings.PATH_PLANNING_ALGORITHM = PlanningAlgorithm.A_STAR
    
    async def _load_path_cache(self):
        """加载路径缓存"""
        try:
            cache_file = self.cache_dir / "path_cache.json"
            
            if cache_file.exists():
                with open(cache_file, "r") as f:
                    self.path_cache = json.load(f)
                self.logger.info(f"加载了 {len(self.path_cache)} 条路径缓存")
        except Exception as e:
            self.logger.error(f"加载路径缓存失败: {str(e)}")
            self.path_cache = {}
    
    async def _save_path_cache(self):
        """保存路径缓存"""
        try:
            cache_file = self.cache_dir / "path_cache.json"
            
            with open(cache_file, "w") as f:
                json.dump(self.path_cache, f)
            
            self.logger.info(f"保存了 {len(self.path_cache)} 条路径缓存")
        except Exception as e:
            self.logger.error(f"保存路径缓存失败: {str(e)}")
    
    async def _load_active_tasks(self):
        """加载需要路径规划的活动任务"""
        try:
            tasks = await Task.find({
                "status": {"$in": [TaskStatus.ASSIGNED, TaskStatus.PENDING]},
                "assigned_agents": self.agent_id
            }).to_list()
            
            for task in tasks:
                self.active_tasks[task.task_id] = task
            
            self.logger.info(f"加载了 {len(tasks)} 个活动任务")
        except Exception as e:
            self.logger.error(f"加载活动任务失败: {str(e)}")
    
    async def run_cycle(self):
        """路径规划智能体的主循环"""
        # 处理活动任务
        await self._process_active_tasks()
        
        # 更新禁飞区（定期检查新的禁飞区）
        if time.time() % 60 < 1:  # 大约每分钟检查一次
            await self._load_no_fly_zones()
        
        # 每小时保存一次路径缓存
        if time.time() % 3600 < 1:  # 大约每小时保存一次
            await self._save_path_cache()
    
    async def _process_active_tasks(self):
        """处理需要路径规划的活动任务"""
        for task_id, task in list(self.active_tasks.items()):
            # 检查任务是否已完成或取消
            updated_task = await Task.find_one({"task_id": task_id})
            if not updated_task or updated_task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
                self.active_tasks.pop(task_id, None)
                continue
            
            # 更新任务
            self.active_tasks[task_id] = updated_task
            
            # 如果任务需要路径规划且尚未规划
            if not updated_task.planned_path:
                async with self.planning_lock:
                    # 规划路径
                    await self._plan_path_for_task(updated_task)
    
    async def _plan_path_for_task(self, task: Task):
        """为任务规划路径"""
        try:
            self.logger.info(f"为任务规划路径: {task.task_id}")
            
            # 检查起点和终点
            if not task.start_location or not task.end_location:
                self.logger.warning(f"任务缺少起点或终点: {task.task_id}")
                return
            
            # 提取起点和终点坐标
            start_point = task.start_location.position.coordinates  # [lon, lat]
            end_point = task.end_location.position.coordinates  # [lon, lat]
            
            # 检查是否有缓存的路径
            cache_key = f"{start_point[0]:.5f},{start_point[1]:.5f}_{end_point[0]:.5f},{end_point[1]:.5f}"
            
            if cache_key in self.path_cache:
                self.logger.info(f"使用缓存的路径: {cache_key}")
                planned_path = self._restore_path_from_cache(self.path_cache[cache_key])
            else:
                # 根据设置选择算法
                algorithm = settings.PATH_PLANNING_ALGORITHM
                
                if algorithm == PlanningAlgorithm.A_STAR:
                    planned_path = await self._plan_path_astar(start_point, end_point, task)
                elif algorithm == PlanningAlgorithm.RRT:
                    planned_path = await self._plan_path_rrt(start_point, end_point, task)
                elif algorithm == PlanningAlgorithm.RL and self.rl_model:
                    planned_path = await self._plan_path_rl(start_point, end_point, task)
                else:
                    # 默认使用A*
                    planned_path = await self._plan_path_astar(start_point, end_point, task)
                
                # 缓存路径
                if planned_path:
                    self.path_cache[cache_key] = self._cache_path(planned_path)
            
            if planned_path:
                # 更新任务的规划路径
                task.planned_path = planned_path
                await task.save()
                
                self.logger.info(f"成功为任务 {task.task_id} 规划路径，航点数: {len(planned_path.waypoints)}")
                
                # 通知任务已更新
                await self.broadcast_message({
                    "type": "task_updated",
                    "task_id": task.task_id,
                    "source_agent_id": self.agent_id
                })
            else:
                self.logger.warning(f"无法为任务 {task.task_id} 规划路径")
                
                # 任务失败
                task.status = TaskStatus.FAILED
                task.task_data = task.task_data or {}
                task.task_data["failure_reason"] = "无法规划有效路径"
                await task.save()
                
                # 通知任务失败
                await self.broadcast_message({
                    "type": "task_failed",
                    "task_id": task.task_id,
                    "reason": "无法规划有效路径",
                    "source_agent_id": self.agent_id
                })
        except Exception as e:
            self.logger.error(f"规划路径出错: {str(e)}")
    
    async def _plan_path_astar(self, start_point: List[float], end_point: List[float], task: Task) -> Optional[FlightPath]:
        """使用A*算法规划路径"""
        try:
            # 将经纬度转换为图中的节点
            start_node = await self._get_nearest_node(start_point)
            end_node = await self._get_nearest_node(end_point)
            
            if not start_node or not end_node:
                self.logger.warning(f"无法找到起点或终点对应的节点: {task.task_id}")
                return None
            
            # 使用A*算法寻找路径
            self.logger.info(f"使用A*算法规划路径: {start_node} -> {end_node}")
            
            # 定义启发式函数
            def heuristic(n1, n2):
                # 使用大圆距离（Haversine公式）作为启发式
                n1_lat, n1_lon = self.city_graph.nodes[n1]['y'], self.city_graph.nodes[n1]['x']
                n2_lat, n2_lon = self.city_graph.nodes[n2]['y'], self.city_graph.nodes[n2]['x']
                return self._haversine(n1_lat, n1_lon, n2_lat, n2_lon)
            
            # 在后台线程中运行A*算法
            try:
                path_nodes = await asyncio.to_thread(
                    nx.astar_path,
                    self.city_graph,
                    start_node,
                    end_node,
                    heuristic=heuristic,
                    weight='length'
                )
                
                # 检查禁飞区
                valid_path = await self._validate_path_with_no_fly_zones(path_nodes)
                if not valid_path:
                    self.logger.warning(f"路径穿过禁飞区，尝试重新规划: {task.task_id}")
                    # 实现绕过禁飞区的逻辑
                    path_nodes = await self._plan_path_avoiding_no_fly_zones(start_node, end_node)
                
                # 将路径转换为航点列表
                waypoints = await self._nodes_to_waypoints(path_nodes)
                
                # 计算路径信息
                distance = sum(self._haversine(
                    waypoints[i].coordinates[1], waypoints[i].coordinates[0],
                    waypoints[i+1].coordinates[1], waypoints[i+1].coordinates[0]
                ) for i in range(len(waypoints) - 1))
                
                estimated_duration = distance / settings.DRONE_MAX_SPEED / 1000 * 60  # 分钟
                
                return FlightPath(
                    waypoints=waypoints,
                    estimated_duration=estimated_duration,
                    distance=distance,
                    created_by=self.agent_id
                )
            
            except nx.NetworkXNoPath:
                self.logger.warning(f"A*算法未找到路径: {task.task_id}")
                return None
        
        except Exception as e:
            self.logger.error(f"A*路径规划出错: {str(e)}")
            return None
    
    async def _plan_path_rrt(self, start_point: List[float], end_point: List[float], task: Task) -> Optional[FlightPath]:
        """使用RRT(Rapidly-exploring Random Tree)算法规划路径"""
        try:
            self.logger.info(f"使用RRT算法规划路径: {start_point} -> {end_point}")
            
            # 定义地图边界
            bounds = self._get_map_bounds(start_point, end_point)
            
            # 创建RRT参数
            max_iterations = 1000
            goal_sample_rate = 0.1
            step_size = 0.001  # 大约100米
            
            class RRTNode:
                def __init__(self, x, y):
                    self.x = x
                    self.y = y
                    self.parent = None
            
            # 初始化起点和终点节点
            start_node = RRTNode(start_point[1], start_point[0])  # lat, lon
            goal_node = RRTNode(end_point[1], end_point[0])       # lat, lon
            
            # 节点列表
            nodes = [start_node]
            
            # RRT主循环
            for i in range(max_iterations):
                # 随机采样
                if np.random.random() < goal_sample_rate:
                    random_node = goal_node
                else:
                    random_point = self._get_random_point(bounds)
                    random_node = RRTNode(random_point[0], random_point[1])
                
                # 找到最近的节点
                nearest_node_idx = self._find_nearest_node_idx(nodes, random_node)
                nearest_node = nodes[nearest_node_idx]
                
                # 生成新节点
                new_node = self._steer(nearest_node, random_node, step_size)
                
                # 检查新节点是否有效
                if not new_node or await self._is_in_no_fly_zone(new_node.x, new_node.y):
                    continue
                
                # 检查新节点与最近节点之间的路径是否穿过禁飞区
                if await self._is_path_in_no_fly_zone(nearest_node.x, nearest_node.y, new_node.x, new_node.y):
                    continue
                
                # 添加新节点
                new_node.parent = nearest_node
                nodes.append(new_node)
                
                # 检查是否接近目标
                dist_to_goal = self._euclidean_distance(new_node.x, new_node.y, goal_node.x, goal_node.y)
                if dist_to_goal < step_size:
                    # 连接到目标
                    goal_node.parent = new_node
                    nodes.append(goal_node)
                    
                    # 生成路径
                    path = self._extract_path(goal_node)
                    
                    # 转换为航点
                    waypoints = [GeoPoint(
                        type="Point",
                        coordinates=[node.y, node.x],  # lon, lat
                        altitude=settings.DRONE_MAX_ALTITUDE / 2
                    ) for node in path]
                    
                    # 计算路径信息
                    distance = sum(self._haversine(
                        waypoints[i].coordinates[1], waypoints[i].coordinates[0],
                        waypoints[i+1].coordinates[1], waypoints[i+1].coordinates[0]
                    ) for i in range(len(waypoints) - 1))
                    
                    estimated_duration = distance / settings.DRONE_MAX_SPEED / 1000 * 60  # 分钟
                    
                    return FlightPath(
                        waypoints=waypoints,
                        estimated_duration=estimated_duration,
                        distance=distance,
                        created_by=self.agent_id
                    )
            
            self.logger.warning(f"RRT算法未找到路径 (已达到最大迭代次数): {task.task_id}")
            return None
            
        except Exception as e:
            self.logger.error(f"RRT路径规划出错: {str(e)}")
            return None
    
    def _get_map_bounds(self, start_point: List[float], end_point: List[float]) -> Tuple[float, float, float, float]:
        """获取地图边界"""
        min_lon = min(start_point[0], end_point[0]) - 0.05
        max_lon = max(start_point[0], end_point[0]) + 0.05
        min_lat = min(start_point[1], end_point[1]) - 0.05
        max_lat = max(start_point[1], end_point[1]) + 0.05
        return (min_lat, max_lat, min_lon, max_lon)
    
    def _get_random_point(self, bounds: Tuple[float, float, float, float]) -> Tuple[float, float]:
        """获取随机点"""
        min_lat, max_lat, min_lon, max_lon = bounds
        lat = min_lat + (max_lat - min_lat) * np.random.random()
        lon = min_lon + (max_lon - min_lon) * np.random.random()
        return (lat, lon)
    
    def _find_nearest_node_idx(self, nodes: List[Any], target: Any) -> int:
        """找到最近的节点索引"""
        distances = [self._euclidean_distance(node.x, node.y, target.x, target.y) for node in nodes]
        return distances.index(min(distances))
    
    def _euclidean_distance(self, x1: float, y1: float, x2: float, y2: float) -> float:
        """欧几里得距离（简化版，不考虑地球曲率）"""
        return ((x1 - x2) ** 2 + (y1 - y2) ** 2) ** 0.5
    
    def _steer(self, from_node: Any, to_node: Any, step_size: float) -> Optional[Any]:
        """从一个节点向另一个节点移动一个步长"""
        dist = self._euclidean_distance(from_node.x, from_node.y, to_node.x, to_node.y)
        
        if dist < step_size:
            return to_node
        
        # 计算方向
        theta = math.atan2(to_node.y - from_node.y, to_node.x - from_node.x)
        
        # 计算新节点坐标
        new_x = from_node.x + step_size * math.cos(theta)
        new_y = from_node.y + step_size * math.sin(theta)
        
        new_node = type(from_node)(new_x, new_y)
        return new_node
    
    def _extract_path(self, goal_node: Any) -> List[Any]:
        """从目标节点回溯提取路径"""
        path = []
        current = goal_node
        
        while current:
            path.append(current)
            current = current.parent
        
        return path[::-1]  # 反转路径
    
    async def _plan_path_rl(self, start_point: List[float], end_point: List[float], task: Task) -> Optional[FlightPath]:
        """使用强化学习模型规划路径"""
        try:
            self.logger.info(f"使用强化学习模型规划路径: {start_point} -> {end_point}")
            
            # 由于强化学习需要训练环境，这里我们使用一个简化的实现
            # 在实际应用中，应该使用预训练的RL模型
            
            # 首先尝试使用A*获取基础路径
            base_path = await self._plan_path_astar(start_point, end_point, task)
            
            if not base_path:
                return None
            
            # 使用RL模型优化路径
            # ...这里应该使用RL模型，但为简化实现，我们只对A*路径做简单优化
            
            # 简化路径（移除不必要的节点）
            simplified_waypoints = self._simplify_path(base_path.waypoints)
            
            # 计算新路径信息
            distance = sum(self._haversine(
                simplified_waypoints[i].coordinates[1], simplified_waypoints[i].coordinates[0],
                simplified_waypoints[i+1].coordinates[1], simplified_waypoints[i+1].coordinates[0]
            ) for i in range(len(simplified_waypoints) - 1))
            
            estimated_duration = distance / settings.DRONE_MAX_SPEED / 1000 * 60  # 分钟
            
            return FlightPath(
                waypoints=simplified_waypoints,
                estimated_duration=estimated_duration,
                distance=distance,
                created_by=self.agent_id
            )
            
        except Exception as e:
            self.logger.error(f"强化学习路径规划出错: {str(e)}")
            return None
    
    def _simplify_path(self, waypoints: List[GeoPoint]) -> List[GeoPoint]:
        """简化路径，移除不必要的节点"""
        if len(waypoints) <= 2:
            return waypoints
        
        # 使用道格拉斯-普克算法简化路径
        coords = [(wp.coordinates[1], wp.coordinates[0]) for wp in waypoints]  # (lat, lon)
        line = LineString(coords)
        
        # 简化参数（越小越精确）
        tolerance = 0.0001  # 约10米
        simplified = line.simplify(tolerance, preserve_topology=True)
        
        # 创建新的航点
        new_waypoints = []
        for lon, lat in [(p[1], p[0]) for p in list(simplified.coords)]:
            new_waypoints.append(GeoPoint(
                type="Point",
                coordinates=[lon, lat],
                altitude=settings.DRONE_MAX_ALTITUDE / 2
            ))
        
        return new_waypoints
    
    async def _get_nearest_node(self, point: List[float]) -> Optional[Any]:
        """获取最接近给定点的图节点"""
        try:
            # 提取经纬度
            lon, lat = point  # [lon, lat]
            
            # 使用OSMnx在后台线程中查找最近节点
            nearest_node = await asyncio.to_thread(
                ox.distance.nearest_nodes,
                self.city_graph, X=[lon], Y=[lat]
            )
            
            if nearest_node:
                return nearest_node[0]
            return None
        except Exception as e:
            self.logger.error(f"获取最近节点失败: {str(e)}")
            return None
    
    async def _validate_path_with_no_fly_zones(self, path_nodes: List[Any]) -> bool:
        """验证路径是否穿过禁飞区"""
        # 如果没有禁飞区，路径有效
        if not self.no_fly_zones:
            return True
        
        # 获取路径上的所有点
        path_points = []
        for node in path_nodes:
            lat = self.city_graph.nodes[node]['y']
            lon = self.city_graph.nodes[node]['x']
            path_points.append((lat, lon))
        
        # 检查每段路径是否穿过禁飞区
        for i in range(len(path_points) - 1):
            lat1, lon1 = path_points[i]
            lat2, lon2 = path_points[i + 1]
            
            if await self._is_path_in_no_fly_zone(lat1, lon1, lat2, lon2):
                return False
        
        return True
    
    async def _is_in_no_fly_zone(self, lat: float, lon: float) -> bool:
        """检查点是否在禁飞区内"""
        point = Point(lon, lat)
        
        for zone in self.no_fly_zones:
            try:
                # 获取禁飞区多边形
                polygon = Polygon(zone.geometry["coordinates"][0])
                
                # 检查点是否在多边形内
                if polygon.contains(point):
                    return True
            except Exception as e:
                self.logger.error(f"检查禁飞区出错: {str(e)}")
        
        return False
    
    async def _is_path_in_no_fly_zone(self, lat1: float, lon1: float, lat2: float, lon2: float) -> bool:
        """检查路径是否穿过禁飞区"""
        path = LineString([(lon1, lat1), (lon2, lat2)])
        
        for zone in self.no_fly_zones:
            try:
                # 获取禁飞区多边形
                polygon = Polygon(zone.geometry["coordinates"][0])
                
                # 检查路径是否与多边形相交
                if polygon.intersects(path):
                    return True
            except Exception as e:
                self.logger.error(f"检查路径与禁飞区相交出错: {str(e)}")
        
        return False
    
    async def _plan_path_avoiding_no_fly_zones(self, start_node: Any, end_node: Any) -> List[Any]:
        """规划绕过禁飞区的路径"""
        # 这里实现一个更复杂的路径规划算法，考虑禁飞区
        # 为简化实现，我们使用修改后的Dijkstra算法
        
        try:
            # 创建一个队列
            queue = [(0, start_node, [])]  # (cost, node, path)
            visited = set()
            
            while queue:
                # 弹出成本最低的路径
                cost, node, path = heapq.heappop(queue)
                
                # 如果到达终点
                if node == end_node:
                    return path + [node]
                
                # 如果节点已访问
                if node in visited:
                    continue
                
                # 标记为已访问
                visited.add(node)
                
                # 遍历所有邻居
                for neighbor in self.city_graph.neighbors(node):
                    if neighbor in visited:
                        continue
                    
                    # 获取边的长度
                    edge_data = self.city_graph.get_edge_data(node, neighbor)
                    length = edge_data.get('length', 1)
                    
                    # 检查路径是否穿过禁飞区
                    node_lat = self.city_graph.nodes[node]['y']
                    node_lon = self.city_graph.nodes[node]['x']
                    neighbor_lat = self.city_graph.nodes[neighbor]['y']
                    neighbor_lon = self.city_graph.nodes[neighbor]['x']
                    
                    if await self._is_path_in_no_fly_zone(node_lat, node_lon, neighbor_lat, neighbor_lon):
                        # 如果穿过禁飞区，增加成本惩罚
                        length *= 10
                    
                    # 添加邻居到队列
                    new_cost = cost + length
                    new_path = path + [node]
                    heapq.heappush(queue, (new_cost, neighbor, new_path))
            
            # 如果找不到路径
            return []
        
        except Exception as e:
            self.logger.error(f"规划绕过禁飞区的路径出错: {str(e)}")
            return []
    
    async def _nodes_to_waypoints(self, path_nodes: List[Any]) -> List[GeoPoint]:
        """将图节点转换为航点"""
        waypoints = []
        
        for node in path_nodes:
            lat = self.city_graph.nodes[node]['y']
            lon = self.city_graph.nodes[node]['x']
            
            waypoint = GeoPoint(
                type="Point",
                coordinates=[lon, lat],  # [lon, lat]
                altitude=settings.DRONE_MAX_ALTITUDE / 2  # 默认飞行高度
            )
            
            waypoints.append(waypoint)
        
        return waypoints
    
    def _haversine(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        计算两点之间的大圆距离（Haversine公式）
        返回距离，单位为米
        """
        # 将角度转换为弧度
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        
        # Haversine公式
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        r = 6371  # 地球半径，单位为公里
        
        # 返回距离，单位为米
        return c * r * 1000
    
    def _cache_path(self, path: FlightPath) -> Dict[str, Any]:
        """将路径转换为可缓存的格式"""
        return {
            "waypoints": [[wp.coordinates[0], wp.coordinates[1], wp.altitude] for wp in path.waypoints],
            "estimated_duration": path.estimated_duration,
            "distance": path.distance,
            "created_by": path.created_by
        }
    
    def _restore_path_from_cache(self, cached_path: Dict[str, Any]) -> FlightPath:
        """从缓存格式恢复路径"""
        waypoints = []
        for wp in cached_path["waypoints"]:
            waypoints.append(GeoPoint(
                type="Point",
                coordinates=[wp[0], wp[1]],
                altitude=wp[2]
            ))
        
        return FlightPath(
            waypoints=waypoints,
            estimated_duration=cached_path["estimated_duration"],
            distance=cached_path["distance"],
            created_by=cached_path["created_by"]
        )
    
    async def handle_query(self, query: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """处理来自其他智能体的查询"""
        if query == "plan_path":
            # 快速计划两点之间的路径
            start_point = data.get("start_point")
            end_point = data.get("end_point")
            
            if not start_point or not end_point:
                return {"success": False, "error": "Missing start_point or end_point"}
            
            # 简单验证坐标
            if (len(start_point) != 2 or len(end_point) != 2 or
                not all(isinstance(x, (int, float)) for x in start_point + end_point)):
                return {"success": False, "error": "Invalid coordinates"}
            
            # 创建一个临时任务
            temp_task = Task(
                task_id=f"temp_{str(uuid.uuid4())[:8]}",
                title="临时路径规划",
                description="由查询触发的临时路径规划",
                type=TaskType.OTHER,
                created_by=self.agent_id,
                start_location=Location(
                    position=GeoPoint(
                        type="Point",
                        coordinates=start_point
                    )
                ),
                end_location=Location(
                    position=GeoPoint(
                        type="Point",
                        coordinates=end_point
                    )
                )
            )
            
            # 规划路径
            path = await self._plan_path_astar(start_point, end_point, temp_task)
            
            if not path:
                return {"success": False, "error": "Could not plan path"}
            
            return {
                "success": True,
                "path": {
                    "waypoints": [[wp.coordinates[0], wp.coordinates[1], wp.altitude] for wp in path.waypoints],
                    "distance": path.distance,
                    "duration": path.estimated_duration
                }
            }
        
        elif query == "check_no_fly_zones":
            # 检查特定位置是否在禁飞区内
            lat = data.get("lat")
            lon = data.get("lon")
            
            if lat is None or lon is None:
                return {"success": False, "error": "Missing lat or lon"}
            
            in_no_fly_zone = await self._is_in_no_fly_zone(lat, lon)
            
            return {
                "success": True,
                "in_no_fly_zone": in_no_fly_zone
            }
        
        return await super().handle_query(query, data)


# 创建路径规划智能体的工厂函数
async def create_planner_agent(agent_id: Optional[str] = None, name: Optional[str] = None) -> PathPlanningAgent:
    """创建并初始化路径规划智能体"""
    agent = PathPlanningAgent(agent_id, name)
    await agent.initialize()
    register_agent(agent)
    return agent