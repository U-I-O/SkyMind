import math
import numpy as np
import heapq
from typing import Dict, List, Any, Optional, Tuple, Set, Callable
from shapely.geometry import Point, Polygon, LineString
import random
from datetime import datetime

from config.settings import settings
from config.logging_config import get_logger

logger = get_logger("services.path_planning")

class PathPlanningService:
    """路径规划服务，实现多种路径规划算法"""
    
    def __init__(self):
        self.default_algorithm = settings.PATH_PLANNING_ALGORITHM
        self.no_fly_zones: List[Dict[str, Any]] = []
        self.last_updated = datetime.utcnow()
    
    def set_no_fly_zones(self, zones: List[Dict[str, Any]]):
        """设置禁飞区"""
        self.no_fly_zones = zones
        self.last_updated = datetime.utcnow()
        logger.info(f"更新了 {len(zones)} 个禁飞区")
    
    def plan_path(self, start_point: List[float], end_point: List[float], 
                  algorithm: Optional[str] = None, altitude: float = 100.0,
                  options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        规划路径
        
        Args:
            start_point: 起点坐标 [lon, lat]
            end_point: 终点坐标 [lon, lat]
            algorithm: 路径规划算法，默认使用配置中的算法
            altitude: 飞行高度，默认100米
            options: 算法选项
        
        Returns:
            路径规划结果
        """
        if options is None:
            options = {}
        
        # 确定使用的算法
        algo = algorithm or self.default_algorithm
        
        # 根据算法选择规划方法
        if algo == "astar":
            return self._plan_path_astar(start_point, end_point, altitude, options)
        elif algo == "rrt":
            return self._plan_path_rrt(start_point, end_point, altitude, options)
        elif algo == "dijkstra":
            return self._plan_path_dijkstra(start_point, end_point, altitude, options)
        else:
            # 默认使用A*算法
            return self._plan_path_astar(start_point, end_point, altitude, options)
    
    def _plan_path_astar(self, start_point: List[float], end_point: List[float],
                        altitude: float, options: Dict[str, Any]) -> Dict[str, Any]:
        """使用A*算法规划路径"""
        # 解析选项
        grid_size = options.get("grid_size", 0.0005)  # 约50米网格
        max_iterations = options.get("max_iterations", 10000)
        
        # 创建网格范围
        min_lon = min(start_point[0], end_point[0]) - 0.01
        max_lon = max(start_point[0], end_point[0]) + 0.01
        min_lat = min(start_point[1], end_point[1]) - 0.01
        max_lat = max(start_point[1], end_point[1]) + 0.01
        
        # 将经纬度坐标转换为网格坐标
        start_grid = self._point_to_grid(start_point, min_lon, min_lat, grid_size)
        end_grid = self._point_to_grid(end_point, min_lon, min_lat, grid_size)
        
        # A*搜索
        open_set = [(0, start_grid, [])]  # (f_score, position, path)
        closed_set = set()
        
        iterations = 0
        while open_set and iterations < max_iterations:
            iterations += 1
            
            # 获取f_score最小的节点
            f_score, current, path = heapq.heappop(open_set)
            
            # 如果到达终点
            if current == end_grid:
                # 构建路径
                final_path = path + [current]
                waypoints = [
                    self._grid_to_point(grid, min_lon, min_lat, grid_size, altitude)
                    for grid in final_path
                ]
                
                # 计算距离和时间
                distance = self._calculate_path_distance(waypoints)
                duration = distance / settings.DRONE_MAX_SPEED / 1000 * 60  # 分钟
                
                logger.info(f"A*算法找到路径，航点数: {len(waypoints)}, 距离: {distance:.2f}米")
                
                return {
                    "success": True,
                    "algorithm": "astar",
                    "waypoints": waypoints,
                    "distance": distance,
                    "duration": duration,
                    "iterations": iterations
                }
            
            # 将当前节点添加到已访问集合
            if current in closed_set:
                continue
            closed_set.add(current)
            
            # 扩展相邻节点
            for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0), (1, 1), (1, -1), (-1, 1), (-1, -1)]:
                neighbor = (current[0] + dx, current[1] + dy)
                
                # 检查是否越界
                if not self._is_valid_grid(neighbor, min_lon, max_lon, min_lat, max_lat, grid_size):
                    continue
                
                # 检查是否已访问
                if neighbor in closed_set:
                    continue
                
                # 检查是否在禁飞区内
                neighbor_point = self._grid_to_point(neighbor, min_lon, min_lat, grid_size, altitude)
                if self._is_in_no_fly_zone(neighbor_point[:2]):
                    continue
                
                # 计算路径代价
                g_score = len(path) + 1
                h_score = self._heuristic(neighbor, end_grid)
                f_score = g_score + h_score
                
                # 添加到开放集合
                new_path = path + [current]
                heapq.heappush(open_set, (f_score, neighbor, new_path))
        
        logger.warning(f"A*算法未找到路径，已达到最大迭代次数: {max_iterations}")
        
        # 如果未找到路径，返回直线路径
        return self._generate_direct_path(start_point, end_point, altitude)
    
    def _plan_path_rrt(self, start_point: List[float], end_point: List[float],
                      altitude: float, options: Dict[str, Any]) -> Dict[str, Any]:
        """使用RRT算法规划路径"""
        # 解析选项
        max_iterations = options.get("max_iterations", 5000)
        step_size = options.get("step_size", 0.0005)  # 约50米
        goal_sample_rate = options.get("goal_sample_rate", 0.1)  # 10%的概率直接采样目标点
        
        # 计算区域边界
        min_lon = min(start_point[0], end_point[0]) - 0.01
        max_lon = max(start_point[0], end_point[0]) + 0.01
        min_lat = min(start_point[1], end_point[1]) - 0.01
        max_lat = max(start_point[1], end_point[1]) + 0.01
        
        # 初始化节点列表
        class RRTNode:
            def __init__(self, x, y):
                self.x = x
                self.y = y
                self.parent = None
        
        # 创建起点和终点节点
        start_node = RRTNode(start_point[0], start_point[1])
        end_node = RRTNode(end_point[0], end_point[1])
        
        # 初始化节点列表
        nodes = [start_node]
        
        # RRT主循环
        for i in range(max_iterations):
            # 随机采样
            if random.random() < goal_sample_rate:
                # 直接使用目标点
                random_node = RRTNode(end_node.x, end_node.y)
            else:
                # 随机采样
                random_lon = min_lon + random.random() * (max_lon - min_lon)
                random_lat = min_lat + random.random() * (max_lat - min_lat)
                random_node = RRTNode(random_lon, random_lat)
            
            # 找到最近的节点
            nearest_node = self._find_nearest_node(nodes, random_node)
            
            # 沿着方向移动step_size距离
            new_node = self._steer(nearest_node, random_node, step_size)
            
            # 检查是否有效
            if new_node and not self._is_in_no_fly_zone([new_node.x, new_node.y]):
                # 设置父节点并添加到列表
                new_node.parent = nearest_node
                nodes.append(new_node)
                
                # 检查是否可以连接到目标
                dist_to_goal = self._distance(new_node.x, new_node.y, end_node.x, end_node.y)
                
                if dist_to_goal < step_size * 2:
                    # 检查连接是否穿过禁飞区
                    if not self._path_intersects_no_fly_zone(
                        [new_node.x, new_node.y], [end_node.x, end_node.y]
                    ):
                        # 可以连接到目标
                        end_node.parent = new_node
                        nodes.append(end_node)
                        
                        # 构建路径
                        path = self._extract_path(end_node)
                        waypoints = [
                            [node.x, node.y, altitude]
                            for node in path
                        ]
                        
                        # 计算距离和时间
                        distance = self._calculate_path_distance(waypoints)
                        duration = distance / settings.DRONE_MAX_SPEED / 1000 * 60  # 分钟
                        
                        logger.info(f"RRT算法找到路径，航点数: {len(waypoints)}, 距离: {distance:.2f}米")
                        
                        return {
                            "success": True,
                            "algorithm": "rrt",
                            "waypoints": waypoints,
                            "distance": distance,
                            "duration": duration,
                            "iterations": i + 1
                        }
        
        logger.warning(f"RRT算法未找到路径，已达到最大迭代次数: {max_iterations}")
        
        # 如果未找到路径，返回直线路径
        return self._generate_direct_path(start_point, end_point, altitude)
    
    def _plan_path_dijkstra(self, start_point: List[float], end_point: List[float],
                           altitude: float, options: Dict[str, Any]) -> Dict[str, Any]:
        """使用Dijkstra算法规划路径"""
        # 解析选项
        grid_size = options.get("grid_size", 0.0005)  # 约50米网格
        max_iterations = options.get("max_iterations", 10000)
        
        # 创建网格范围
        min_lon = min(start_point[0], end_point[0]) - 0.01
        max_lon = max(start_point[0], end_point[0]) + 0.01
        min_lat = min(start_point[1], end_point[1]) - 0.01
        max_lat = max(start_point[1], end_point[1]) + 0.01
        
        # 将经纬度坐标转换为网格坐标
        start_grid = self._point_to_grid(start_point, min_lon, min_lat, grid_size)
        end_grid = self._point_to_grid(end_point, min_lon, min_lat, grid_size)
        
        # Dijkstra搜索
        # 距离，节点位置，路径
        open_set = [(0, start_grid, [])]
        closed_set = set()
        
        iterations = 0
        while open_set and iterations < max_iterations:
            iterations += 1
            
            # 获取距离最小的节点
            distance, current, path = heapq.heappop(open_set)
            
            # 如果到达终点
            if current == end_grid:
                # 构建路径
                final_path = path + [current]
                waypoints = [
                    self._grid_to_point(grid, min_lon, min_lat, grid_size, altitude)
                    for grid in final_path
                ]
                
                # 计算距离和时间
                total_distance = self._calculate_path_distance(waypoints)
                duration = total_distance / settings.DRONE_MAX_SPEED / 1000 * 60  # 分钟
                
                logger.info(f"Dijkstra算法找到路径，航点数: {len(waypoints)}, 距离: {total_distance:.2f}米")
                
                return {
                    "success": True,
                    "algorithm": "dijkstra",
                    "waypoints": waypoints,
                    "distance": total_distance,
                    "duration": duration,
                    "iterations": iterations
                }
            
            # 将当前节点添加到已访问集合
            if current in closed_set:
                continue
            closed_set.add(current)
            
            # 扩展相邻节点
            for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0), (1, 1), (1, -1), (-1, 1), (-1, -1)]:
                neighbor = (current[0] + dx, current[1] + dy)
                
                # 检查是否越界
                if not self._is_valid_grid(neighbor, min_lon, max_lon, min_lat, max_lat, grid_size):
                    continue
                
                # 检查是否已访问
                if neighbor in closed_set:
                    continue
                
                # 检查是否在禁飞区内
                neighbor_point = self._grid_to_point(neighbor, min_lon, min_lat, grid_size, altitude)
                if self._is_in_no_fly_zone(neighbor_point[:2]):
                    continue
                
                # 计算移动代价
                move_cost = 1
                if dx != 0 and dy != 0:
                    move_cost = 1.414  # 对角线移动的代价
                
                # 计算新的距离
                new_distance = distance + move_cost
                
                # 添加到开放集合
                new_path = path + [current]
                heapq.heappush(open_set, (new_distance, neighbor, new_path))
        
        logger.warning(f"Dijkstra算法未找到路径，已达到最大迭代次数: {max_iterations}")
        
        # 如果未找到路径，返回直线路径
        return self._generate_direct_path(start_point, end_point, altitude)
    
    def _generate_direct_path(self, start_point: List[float], end_point: List[float],
                             altitude: float) -> Dict[str, Any]:
        """生成直线路径"""
        # 创建航点列表
        waypoints = [
            [start_point[0], start_point[1], altitude],
            [end_point[0], end_point[1], altitude]
        ]
        
        # 计算距离
        distance = self._haversine(
            start_point[1], start_point[0],
            end_point[1], end_point[0]
        )
        
        # 计算持续时间
        duration = distance / settings.DRONE_MAX_SPEED / 1000 * 60  # 分钟
        
        logger.info(f"生成直线路径，距离: {distance:.2f}米")
        
        return {
            "success": True,
            "algorithm": "direct",
            "waypoints": waypoints,
            "distance": distance,
            "duration": duration,
            "iterations": 0
        }
    
    def _point_to_grid(self, point: List[float], min_lon: float, min_lat: float,
                      grid_size: float) -> Tuple[int, int]:
        """将经纬度坐标转换为网格坐标"""
        lon, lat = point
        grid_x = int((lon - min_lon) / grid_size)
        grid_y = int((lat - min_lat) / grid_size)
        return (grid_x, grid_y)
    
    def _grid_to_point(self, grid: Tuple[int, int], min_lon: float, min_lat: float,
                      grid_size: float, altitude: float) -> List[float]:
        """将网格坐标转换为经纬度坐标"""
        grid_x, grid_y = grid
        lon = min_lon + grid_x * grid_size
        lat = min_lat + grid_y * grid_size
        return [lon, lat, altitude]
    
    def _is_valid_grid(self, grid: Tuple[int, int], min_lon: float, max_lon: float,
                      min_lat: float, max_lat: float, grid_size: float) -> bool:
        """检查网格坐标是否在范围内"""
        grid_x, grid_y = grid
        lon = min_lon + grid_x * grid_size
        lat = min_lat + grid_y * grid_size
        
        return min_lon <= lon <= max_lon and min_lat <= lat <= max_lat
    
    def _heuristic(self, a: Tuple[int, int], b: Tuple[int, int]) -> float:
        """曼哈顿距离启发式函数"""
        return abs(a[0] - b[0]) + abs(a[1] - b[1])
    
    def _is_in_no_fly_zone(self, point: List[float]) -> bool:
        """检查点是否在禁飞区内"""
        lon, lat = point
        point_obj = Point(lon, lat)
        
        for zone in self.no_fly_zones:
            # 获取禁飞区几何形状
            if "geometry" in zone and "coordinates" in zone["geometry"]:
                coordinates = zone["geometry"]["coordinates"][0]
                polygon = Polygon(coordinates)
                
                if polygon.contains(point_obj):
                    return True
        
        return False
    
    def _path_intersects_no_fly_zone(self, point1: List[float], point2: List[float]) -> bool:
        """检查路径是否与禁飞区相交"""
        line = LineString([(point1[0], point1[1]), (point2[0], point2[1])])
        
        for zone in self.no_fly_zones:
            # 获取禁飞区几何形状
            if "geometry" in zone and "coordinates" in zone["geometry"]:
                coordinates = zone["geometry"]["coordinates"][0]
                polygon = Polygon(coordinates)
                
                if polygon.intersects(line):
                    return True
        
        return False
    
    def _haversine(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        计算两点之间的大圆距离（Haversine公式）
        
        Args:
            lat1, lon1: 第一个点的纬度和经度
            lat2, lon2: 第二个点的纬度和经度
            
        Returns:
            距离（米）
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
    
    def _calculate_path_distance(self, waypoints: List[List[float]]) -> float:
        """计算路径总距离"""
        if len(waypoints) < 2:
            return 0
        
        total_distance = 0
        for i in range(len(waypoints) - 1):
            lon1, lat1 = waypoints[i][0], waypoints[i][1]
            lon2, lat2 = waypoints[i+1][0], waypoints[i+1][1]
            
            distance = self._haversine(lat1, lon1, lat2, lon2)
            total_distance += distance
        
        return total_distance
    
    def _find_nearest_node(self, nodes: List[Any], target: Any) -> Any:
        """找到最近的节点"""
        min_dist = float('inf')
        nearest = None
        
        for node in nodes:
            dist = self._distance(node.x, node.y, target.x, target.y)
            if dist < min_dist:
                min_dist = dist
                nearest = node
        
        return nearest
    
    def _distance(self, x1: float, y1: float, x2: float, y2: float) -> float:
        """计算欧几里得距离"""
        return math.sqrt((x1 - x2)**2 + (y1 - y2)**2)
    
    def _steer(self, from_node: Any, to_node: Any, step_size: float) -> Any:
        """从一个节点向另一个节点移动一个步长"""
        dist = self._distance(from_node.x, from_node.y, to_node.x, to_node.y)
        
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

# 创建全局路径规划服务实例
path_planning_service = PathPlanningService()