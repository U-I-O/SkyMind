import asyncio
import math
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
from io import BytesIO
import base64
from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime, timedelta
import colorsys
import imageio
import os
from pathlib import Path

from config.settings import settings
from config.logging_config import get_logger
from database.models import (
    Drone, DroneStatus, Task, TaskStatus, Event, EventType, EventLevel, 
    Location, GeoPoint, NoFlyZone, FlightPath
)

logger = get_logger("utils.visualization")

class MapVisualizer:
    """地图可视化工具，用于生成地图可视化"""
    
    def __init__(self, width: int = 800, height: int = 600, dpi: int = 100):
        self.width = width
        self.height = height
        self.dpi = dpi
        self.fig = None
        self.ax = None
        self.city_center = (settings.DEFAULT_CITY_CENTER["lon"], settings.DEFAULT_CITY_CENTER["lat"])
        self.default_radius = 0.05  # 约5公里
        self.temp_dir = Path("./temp")
        self.temp_dir.mkdir(exist_ok=True)
    
    def _setup_plot(self, title: str = "智慧城市地图", zoom_level: float = None):
        """设置绘图"""
        # 创建图形和坐标轴
        plt.close('all')  # 关闭之前的图形
        self.fig, self.ax = plt.subplots(figsize=(self.width/self.dpi, self.height/self.dpi), dpi=self.dpi)
        
        # 设置标题和坐标标签
        self.ax.set_title(title, fontsize=16)
        self.ax.set_xlabel("经度", fontsize=12)
        self.ax.set_ylabel("纬度", fontsize=12)
        
        # 设置网格
        self.ax.grid(True, linestyle='--', alpha=0.7)
        
        # 如果没有指定缩放级别，使用默认半径
        if zoom_level is None:
            radius = self.default_radius
        else:
            # 将缩放级别转换为半径
            # 缩放级别越大，半径越小
            radius = self.default_radius / (zoom_level / 10)
        
        # 设置坐标轴范围
        lon, lat = self.city_center
        self.ax.set_xlim(lon - radius, lon + radius)
        self.ax.set_ylim(lat - radius, lat + radius)
    
    def _add_drones(self, drones: List[Drone]):
        """添加无人机标记"""
        if not self.ax:
            raise ValueError("需要先调用_setup_plot初始化绘图")
        
        # 状态对应的颜色和标记
        status_color = {
            DroneStatus.IDLE: "blue",
            DroneStatus.FLYING: "green",
            DroneStatus.CHARGING: "orange",
            DroneStatus.MAINTENANCE: "purple",
            DroneStatus.OFFLINE: "red"
        }
        
        status_marker = {
            DroneStatus.IDLE: "o",  # 圆形
            DroneStatus.FLYING: "^", # 三角形
            DroneStatus.CHARGING: "s", # 方形
            DroneStatus.MAINTENANCE: "p", # 五角形
            DroneStatus.OFFLINE: "x"  # 叉号
        }
        
        # 绘制无人机
        for drone in drones:
            if not drone.current_location:
                continue
            
            # 获取无人机位置
            lon, lat = drone.current_location.coordinates
            
            # 获取状态对应的颜色和标记
            color = status_color.get(drone.status, "gray")
            marker = status_marker.get(drone.status, "o")
            
            # 绘制无人机
            self.ax.scatter(lon, lat, s=100, color=color, marker=marker, edgecolors='black', linewidths=1, zorder=10)
            
            # 添加无人机ID标签
            short_id = drone.drone_id.split('-')[0]
            self.ax.annotate(
                short_id,
                (lon, lat),
                xytext=(5, 5),
                textcoords='offset points',
                fontsize=8,
                bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="black", alpha=0.7)
            )
    
    def _add_flight_paths(self, paths: List[Dict[str, Any]]):
        """添加飞行路径"""
        if not self.ax:
            raise ValueError("需要先调用_setup_plot初始化绘图")
        
        # 为每条路径分配不同颜色
        num_paths = len(paths)
        colors = [self._get_color(i, num_paths) for i in range(num_paths)]
        
        for i, path_data in enumerate(paths):
            path = path_data["path"]
            drone_id = path_data.get("drone_id", f"路径{i+1}")
            
            # 绘制路径
            waypoints = path.waypoints
            if waypoints and len(waypoints) >= 2:
                # 提取坐标
                coords = [wp.coordinates for wp in waypoints]
                lons = [c[0] for c in coords]
                lats = [c[1] for c in coords]
                
                # 绘制路径线
                self.ax.plot(lons, lats, '-', color=colors[i], linewidth=2, alpha=0.7, zorder=5)
                
                # 添加起点和终点标记
                self.ax.scatter(lons[0], lats[0], s=80, color=colors[i], marker='o', edgecolors='black', linewidths=1, zorder=8)
                self.ax.scatter(lons[-1], lats[-1], s=80, color=colors[i], marker='s', edgecolors='black', linewidths=1, zorder=8)
                
                # 绘制航点
                if len(waypoints) > 2:
                    self.ax.scatter(lons[1:-1], lats[1:-1], s=40, color=colors[i], marker='o', alpha=0.6, zorder=6)
                
                # 添加路径标签
                mid_idx = len(waypoints) // 2
                mid_lon, mid_lat = coords[mid_idx]
                self.ax.annotate(
                    drone_id,
                    (mid_lon, mid_lat),
                    xytext=(5, 5),
                    textcoords='offset points',
                    fontsize=8,
                    bbox=dict(boxstyle="round,pad=0.3", fc="white", ec=colors[i], alpha=0.7)
                )
    
    def _add_events(self, events: List[Event]):
        """添加事件标记"""
        if not self.ax:
            raise ValueError("需要先调用_setup_plot初始化绘图")
        
        # 事件类型对应的标记
        event_marker = {
            EventType.SECURITY: "s", # 方形
            EventType.EMERGENCY: "*", # 星形
            EventType.ANOMALY: "D", # 菱形
            EventType.LOGISTICS: "o", # 圆形
            EventType.SYSTEM: "+"  # 加号
        }
        
        # 事件级别对应的颜色
        level_color = {
            EventLevel.LOW: "yellow",
            EventLevel.MEDIUM: "orange",
            EventLevel.HIGH: "red"
        }
        
        # 绘制事件
        for event in events:
            if not event.location or not event.location.position:
                continue
            
            # 获取事件位置
            lon, lat = event.location.position.coordinates
            
            # 获取事件类型和级别对应的标记和颜色
            marker = event_marker.get(event.type, "o")
            color = level_color.get(event.level, "gray")
            
            # 绘制事件
            self.ax.scatter(lon, lat, s=150, color=color, marker=marker, edgecolors='black', linewidths=1, alpha=0.8, zorder=9)
            
            # 添加事件ID标签
            short_id = event.event_id.split('-')[0]
            self.ax.annotate(
                short_id,
                (lon, lat),
                xytext=(5, -15),
                textcoords='offset points',
                fontsize=8,
                bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="black", alpha=0.7)
            )
    
    def _add_no_fly_zones(self, zones: List[NoFlyZone]):
        """添加禁飞区"""
        if not self.ax:
            raise ValueError("需要先调用_setup_plot初始化绘图")
        
        for zone in zones:
            # 获取禁飞区几何形状
            if "geometry" in zone.__dict__ and "coordinates" in zone.geometry:
                coords = zone.geometry["coordinates"][0]
                
                # 提取经纬度坐标
                lons = [c[0] for c in coords]
                lats = [c[1] for c in coords]
                
                # 是否为永久禁飞区
                if zone.permanent:
                    color = "red"
                    alpha = 0.3
                else:
                    color = "orange"
                    alpha = 0.2
                
                # 绘制禁飞区多边形
                self.ax.fill(lons, lats, color=color, alpha=alpha, edgecolor='black', linewidth=1, zorder=2)
                
                # 添加禁飞区名称
                center_lon = sum(lons) / len(lons)
                center_lat = sum(lats) / len(lats)
                
                self.ax.annotate(
                    zone.name,
                    (center_lon, center_lat),
                    fontsize=9,
                    ha='center',
                    va='center',
                    bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="black", alpha=0.7),
                    zorder=3
                )
    
    def _add_legend(self):
        """添加图例"""
        if not self.ax:
            raise ValueError("需要先调用_setup_plot初始化绘图")
        
        # 无人机状态图例
        drone_status_elements = [
            patches.Patch(color="blue", label="空闲"),
            patches.Patch(color="green", label="飞行中"),
            patches.Patch(color="orange", label="充电中"),
            patches.Patch(color="purple", label="维护中"),
            patches.Patch(color="red", label="离线")
        ]
        
        # 事件类型图例
        event_elements = [
            patches.Patch(color="yellow", label="低级别事件"),
            patches.Patch(color="orange", label="中级别事件"),
            patches.Patch(color="red", label="高级别事件")
        ]
        
        # 禁飞区图例
        zone_elements = [
            patches.Patch(color="red", alpha=0.3, label="永久禁飞区"),
            patches.Patch(color="orange", alpha=0.2, label="临时禁飞区")
        ]
        
        # 添加图例
        self.ax.legend(
            handles=drone_status_elements + event_elements + zone_elements,
            loc='upper right',
            fontsize=8,
            title="图例",
            title_fontsize=10,
            framealpha=0.7
        )
    
    async def generate_map(self, include_drones: bool = True, include_events: bool = True,
                         include_paths: bool = True, include_zones: bool = True,
                         title: str = "智慧城市地图", zoom_level: float = None) -> str:
        """
        生成地图可视化
        
        Args:
            include_drones: 是否包含无人机
            include_events: 是否包含事件
            include_paths: 是否包含飞行路径
            include_zones: 是否包含禁飞区
            title: 地图标题
            zoom_level: 缩放级别
            
        Returns:
            base64编码的PNG图像
        """
        try:
            # 设置绘图
            self._setup_plot(title, zoom_level)
            
            # 添加禁飞区
            if include_zones:
                # 获取当前有效的禁飞区
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
                
                self._add_no_fly_zones(zones)
            
            # 添加飞行路径
            if include_paths:
                # 获取正在进行的任务
                tasks = await Task.find({
                    "status": TaskStatus.IN_PROGRESS,
                    "planned_path": {"$ne": None}
                }).to_list()
                
                paths = []
                for task in tasks:
                    if task.planned_path and task.assigned_drones:
                        drone_id = task.assigned_drones[0] if task.assigned_drones else None
                        paths.append({
                            "path": task.planned_path,
                            "drone_id": drone_id
                        })
                
                self._add_flight_paths(paths)
            
            # 添加事件
            if include_events:
                # 获取未解决的事件
                events = await Event.find({
                    "status": {"$ne": "resolved"},
                    "location": {"$ne": None}
                }).to_list()
                
                self._add_events(events)
            
            # 添加无人机
            if include_drones:
                # 获取所有无人机
                drones = await Drone.find_all().to_list()
                
                self._add_drones(drones)
            
            # 添加图例
            self._add_legend()
            
            # 保存图像到内存
            buf = BytesIO()
            plt.tight_layout()
            self.fig.savefig(buf, format='png', bbox_inches='tight')
            buf.seek(0)
            
            # 转换为base64
            data = base64.b64encode(buf.getvalue()).decode()
            
            # 关闭图形
            plt.close(self.fig)
            
            return data
        except Exception as e:
            logger.error(f"生成地图可视化失败: {str(e)}")
            raise
    
    async def generate_heat_map(self, data_type: str = "events", days: int = 30,
                              title: str = "事件热力图") -> str:
        """
        生成热力图
        
        Args:
            data_type: 数据类型，可以是"events"或"drones"
            days: 统计天数
            title: 热力图标题
            
        Returns:
            base64编码的PNG图像
        """
        try:
            # 设置绘图
            self._setup_plot(title)
            
            # 获取数据
            if data_type == "events":
                # 计算时间范围
                now = datetime.utcnow()
                start_time = now - timedelta(days=days)
                
                # 获取时间范围内的事件
                events = await Event.find({
                    "detected_at": {"$gte": start_time},
                    "location": {"$ne": None}
                }).to_list()
                
                # 提取坐标
                points = []
                intensities = []
                
                for event in events:
                    if event.location and event.location.position:
                        lon, lat = event.location.position.coordinates
                        intensity = 0.5  # 默认强度
                        
                        # 根据事件级别调整强度
                        if event.level == EventLevel.HIGH:
                            intensity = 1.0
                        elif event.level == EventLevel.MEDIUM:
                            intensity = 0.7
                        
                        points.append((lon, lat))
                        intensities.append(intensity)
                
                # 如果没有事件，返回空地图
                if not points:
                    self.ax.set_title(f"{title} (没有数据)")
                    buf = BytesIO()
                    plt.tight_layout()
                    self.fig.savefig(buf, format='png', bbox_inches='tight')
                    buf.seek(0)
                    data = base64.b64encode(buf.getvalue()).decode()
                    plt.close(self.fig)
                    return data
                
                # 生成热力图
                x = [p[0] for p in points]
                y = [p[1] for p in points]
                
                # 创建密度图
                self.ax.hexbin(
                    x, y, 
                    gridsize=20, 
                    cmap='hot', 
                    alpha=0.7, 
                    zorder=2
                )
                
                # 添加颜色条
                cbar = plt.colorbar(ax=self.ax)
                cbar.set_label("事件密度")
                
                # 添加事件点
                self.ax.scatter(x, y, s=30, color='white', edgecolors='black', alpha=0.5, zorder=3)
            
            elif data_type == "drones":
                # 获取所有无人机的轨迹数据
                # 在实际应用中，这应该从数据库获取
                # 这里使用模拟数据
                
                # 设置随机种子以获得一致的结果
                np.random.seed(42)
                
                # 模拟多条轨迹
                num_drones = 5
                num_points = 100
                
                # 为每个无人机生成随机轨迹
                for i in range(num_drones):
                    # 生成起点（城市中心附近）
                    lon, lat = self.city_center
                    start_lon = lon + np.random.uniform(-0.02, 0.02)
                    start_lat = lat + np.random.uniform(-0.02, 0.02)
                    
                    # 生成随机轨迹
                    trajectory = []
                    
                    # 随机运动参数
                    angle = np.random.uniform(0, 2 * np.pi)
                    speed = np.random.uniform(0.001, 0.002)
                    
                    current_lon, current_lat = start_lon, start_lat
                    
                    for j in range(num_points):
                        # 随机更改方向
                        if j % 10 == 0:
                            angle += np.random.uniform(-np.pi/4, np.pi/4)
                        
                        # 计算新位置
                        current_lon += speed * np.cos(angle)
                        current_lat += speed * np.sin(angle)
                        
                        trajectory.append((current_lon, current_lat))
                    
                    # 绘制轨迹
                    traj_lons, traj_lats = zip(*trajectory)
                    self.ax.plot(traj_lons, traj_lats, '-', linewidth=1, alpha=0.3, zorder=2)
                
                # 将所有轨迹点合并用于热力图
                all_points = []
                for i in range(num_drones):
                    all_points.extend(trajectory)
                
                # 生成热力图
                x = [p[0] for p in all_points]
                y = [p[1] for p in all_points]
                
                # 创建密度图
                self.ax.hexbin(
                    x, y, 
                    gridsize=30, 
                    cmap='Blues', 
                    alpha=0.7, 
                    zorder=1
                )
                
                # 添加颜色条
                cbar = plt.colorbar(ax=self.ax)
                cbar.set_label("无人机活动密度")
            
            else:
                raise ValueError(f"未知的数据类型: {data_type}")
            
            # 设置标题
            self.ax.set_title(f"{title} (最近{days}天)")
            
            # 保存图像到内存
            buf = BytesIO()
            plt.tight_layout()
            self.fig.savefig(buf, format='png', bbox_inches='tight')
            buf.seek(0)
            
            # 转换为base64
            data = base64.b64encode(buf.getvalue()).decode()
            
            # 关闭图形
            plt.close(self.fig)
            
            return data
        except Exception as e:
            logger.error(f"生成热力图失败: {str(e)}")
            raise
    
    async def generate_statistics_chart(self, chart_type: str = "events_by_type",
                                     days: int = 30, title: str = None) -> str:
        """
        生成统计图表
        
        Args:
            chart_type: 图表类型
            days: 统计天数
            title: 图表标题
            
        Returns:
            base64编码的PNG图像
        """
        try:
            # 计算时间范围
            now = datetime.utcnow()
            start_time = now - timedelta(days=days)
            
            # 关闭之前的图形
            plt.close('all')
            
            if chart_type == "events_by_type":
                # 统计不同类型的事件数量
                events = await Event.find({
                    "detected_at": {"$gte": start_time}
                }).to_list()
                
                # 统计每种类型的事件数量
                type_counts = {}
                for event in events:
                    event_type = event.type
                    type_counts[event_type] = type_counts.get(event_type, 0) + 1
                
                # 设置图表标题
                if title is None:
                    title = f"事件类型分布 (最近{days}天)"
                
                # 创建饼图
                self.fig, self.ax = plt.subplots(figsize=(self.width/self.dpi, self.height/self.dpi), dpi=self.dpi)
                self.ax.set_title(title, fontsize=16)
                
                # 准备数据
                labels = list(type_counts.keys())
                sizes = list(type_counts.values())
                
                # 如果没有数据，显示空图
                if not sizes:
                    self.ax.text(
                        0.5, 0.5, 
                        "没有数据", 
                        horizontalalignment='center',
                        verticalalignment='center',
                        transform=self.ax.transAxes,
                        fontsize=14
                    )
                else:
                    # 生成颜色
                    colors = [self._get_color(i, len(labels)) for i in range(len(labels))]
                    
                    # 绘制饼图
                    wedges, texts, autotexts = self.ax.pie(
                        sizes,
                        labels=labels,
                        colors=colors,
                        autopct='%1.1f%%',
                        startangle=90,
                        wedgeprops={'edgecolor': 'w','linewidth': 1}
                    )
                    
                    # 设置字体大小
                    for text in texts:
                        text.set_fontsize(10)
                    for autotext in autotexts:
                        autotext.set_fontsize(10)
                    
                    # 添加标题
                    plt.suptitle(title, fontsize=16)
                    
                    # 添加图例
                    self.ax.legend(
                        wedges, 
                        labels,
                        title="事件类型",
                        loc="center left",
                        bbox_to_anchor=(1, 0, 0.5, 1)
                    )
            
            elif chart_type == "events_by_level":
                # 统计不同级别的事件数量
                events = await Event.find({
                    "detected_at": {"$gte": start_time}
                }).to_list()
                
                # 统计每种级别的事件数量
                level_counts = {}
                for event in events:
                    event_level = event.level
                    level_counts[event_level] = level_counts.get(event_level, 0) + 1
                
                # 设置图表标题
                if title is None:
                    title = f"事件级别分布 (最近{days}天)"
                
                # 创建饼图
                self.fig, self.ax = plt.subplots(figsize=(self.width/self.dpi, self.height/self.dpi), dpi=self.dpi)
                self.ax.set_title(title, fontsize=16)
                
                # 准备数据
                labels = list(level_counts.keys())
                sizes = list(level_counts.values())
                
                # 如果没有数据，显示空图
                if not sizes:
                    self.ax.text(
                        0.5, 0.5, 
                        "没有数据", 
                        horizontalalignment='center',
                        verticalalignment='center',
                        transform=self.ax.transAxes,
                        fontsize=14
                    )
                else:
                    # 级别对应的颜色
                    level_colors = {
                        EventLevel.LOW: "yellow",
                        EventLevel.MEDIUM: "orange",
                        EventLevel.HIGH: "red"
                    }
                    
                    colors = [level_colors.get(level, "gray") for level in labels]
                    
                    # 绘制饼图
                    wedges, texts, autotexts = self.ax.pie(
                        sizes,
                        labels=labels,
                        colors=colors,
                        autopct='%1.1f%%',
                        startangle=90,
                        wedgeprops={'edgecolor': 'w','linewidth': 1}
                    )
                    
                    # 设置字体大小
                    for text in texts:
                        text.set_fontsize(10)
                    for autotext in autotexts:
                        autotext.set_fontsize(10)
                    
                    # 添加标题
                    plt.suptitle(title, fontsize=16)
                    
                    # 添加图例
                    self.ax.legend(
                        wedges, 
                        labels,
                        title="事件级别",
                        loc="center left",
                        bbox_to_anchor=(1, 0, 0.5, 1)
                    )
            
            elif chart_type == "events_timeline":
                # 生成事件时间线图
                events = await Event.find({
                    "detected_at": {"$gte": start_time}
                }).to_list()
                
                # 设置图表标题
                if title is None:
                    title = f"事件时间线 (最近{days}天)"
                
                # 创建时间线图
                self.fig, self.ax = plt.subplots(figsize=(self.width/self.dpi, self.height/self.dpi), dpi=self.dpi)
                self.ax.set_title(title, fontsize=16)
                
                # 准备数据
                # 按天统计事件数量
                day_counts = {}
                for event in events:
                    day = event.detected_at.date()
                    day_counts[day] = day_counts.get(day, 0) + 1
                
                # 如果没有数据，显示空图
                if not day_counts:
                    self.ax.text(
                        0.5, 0.5, 
                        "没有数据", 
                        horizontalalignment='center',
                        verticalalignment='center',
                        transform=self.ax.transAxes,
                        fontsize=14
                    )
                else:
                    # 排序天数
                    sorted_days = sorted(day_counts.keys())
                    counts = [day_counts[day] for day in sorted_days]
                    
                    # 绘制柱状图
                    bars = self.ax.bar(sorted_days, counts, width=0.8, color="skyblue", edgecolor="navy")
                    
                    # 设置x轴标签格式
                    self.ax.xaxis.set_major_formatter(plt.matplotlib.dates.DateFormatter('%m-%d'))
                    
                    # 自动旋转日期标签
                    plt.gcf().autofmt_xdate()
                    
                    # 设置轴标签
                    self.ax.set_xlabel("日期", fontsize=12)
                    self.ax.set_ylabel("事件数量", fontsize=12)
                    
                    # 添加数据标签
                    for bar in bars:
                        height = bar.get_height()
                        self.ax.text(
                            bar.get_x() + bar.get_width()/2., 
                            height + 0.1,
                            '%d' % int(height),
                            ha='center', 
                            va='bottom',
                            fontsize=9
                        )
            
            elif chart_type == "drone_status":
                # 统计无人机状态
                drones = await Drone.find_all().to_list()
                
                # 统计每种状态的无人机数量
                status_counts = {}
                for drone in drones:
                    status = drone.status
                    status_counts[status] = status_counts.get(status, 0) + 1
                
                # 设置图表标题
                if title is None:
                    title = "无人机状态分布"
                
                # 创建饼图
                self.fig, self.ax = plt.subplots(figsize=(self.width/self.dpi, self.height/self.dpi), dpi=self.dpi)
                self.ax.set_title(title, fontsize=16)
                
                # 准备数据
                labels = list(status_counts.keys())
                sizes = list(status_counts.values())
                
                # 如果没有数据，显示空图
                if not sizes:
                    self.ax.text(
                        0.5, 0.5, 
                        "没有数据", 
                        horizontalalignment='center',
                        verticalalignment='center',
                        transform=self.ax.transAxes,
                        fontsize=14
                    )
                else:
                    # 状态对应的颜色
                    status_colors = {
                        DroneStatus.IDLE: "blue",
                        DroneStatus.FLYING: "green",
                        DroneStatus.CHARGING: "orange",
                        DroneStatus.MAINTENANCE: "purple",
                        DroneStatus.OFFLINE: "red"
                    }
                    
                    colors = [status_colors.get(status, "gray") for status in labels]
                    
                    # 绘制饼图
                    wedges, texts, autotexts = self.ax.pie(
                        sizes,
                        labels=labels,
                        colors=colors,
                        autopct='%1.1f%%',
                        startangle=90,
                        wedgeprops={'edgecolor': 'w','linewidth': 1}
                    )
                    
                    # 设置字体大小
                    for text in texts:
                        text.set_fontsize(10)
                    for autotext in autotexts:
                        autotext.set_fontsize(10)
                    
                    # 添加标题
                    plt.suptitle(title, fontsize=16)
                    
                    # 添加图例
                    self.ax.legend(
                        wedges, 
                        labels,
                        title="无人机状态",
                        loc="center left",
                        bbox_to_anchor=(1, 0, 0.5, 1)
                    )
            
            elif chart_type == "task_status":
                # 统计任务状态
                tasks = await Task.find_all().to_list()
                
                # 统计每种状态的任务数量
                status_counts = {}
                for task in tasks:
                    status = task.status
                    status_counts[status] = status_counts.get(status, 0) + 1
                
                # 设置图表标题
                if title is None:
                    title = "任务状态分布"
                
                # 创建饼图
                self.fig, self.ax = plt.subplots(figsize=(self.width/self.dpi, self.height/self.dpi), dpi=self.dpi)
                self.ax.set_title(title, fontsize=16)
                
                # 准备数据
                labels = list(status_counts.keys())
                sizes = list(status_counts.values())
                
                # 如果没有数据，显示空图
                if not sizes:
                    self.ax.text(
                        0.5, 0.5, 
                        "没有数据", 
                        horizontalalignment='center',
                        verticalalignment='center',
                        transform=self.ax.transAxes,
                        fontsize=14
                    )
                else:
                    # 状态对应的颜色
                    status_colors = {
                        TaskStatus.PENDING: "lightblue",
                        TaskStatus.ASSIGNED: "yellow",
                        TaskStatus.IN_PROGRESS: "green",
                        TaskStatus.COMPLETED: "blue",
                        TaskStatus.FAILED: "red",
                        TaskStatus.CANCELLED: "gray"
                    }
                    
                    colors = [status_colors.get(status, "lightgray") for status in labels]
                    
                    # 绘制饼图
                    wedges, texts, autotexts = self.ax.pie(
                        sizes,
                        labels=labels,
                        colors=colors,
                        autopct='%1.1f%%',
                        startangle=90,
                        wedgeprops={'edgecolor': 'w','linewidth': 1}
                    )
                    
                    # 设置字体大小
                    for text in texts:
                        text.set_fontsize(10)
                    for autotext in autotexts:
                        autotext.set_fontsize(10)
                    
                    # 添加标题
                    plt.suptitle(title, fontsize=16)
                    
                    # 添加图例
                    self.ax.legend(
                        wedges, 
                        labels,
                        title="任务状态",
                        loc="center left",
                        bbox_to_anchor=(1, 0, 0.5, 1)
                    )
            
            else:
                raise ValueError(f"未知的图表类型: {chart_type}")
            
            # 保存图像到内存
            buf = BytesIO()
            plt.tight_layout()
            self.fig.savefig(buf, format='png', bbox_inches='tight')
            buf.seek(0)
            
            # 转换为base64
            data = base64.b64encode(buf.getvalue()).decode()
            
            # 关闭图形
            plt.close(self.fig)
            
            return data
        except Exception as e:
            logger.error(f"生成统计图表失败: {str(e)}")
            raise
    
    async def generate_animation(self, drone_id: str, duration: int = 60,
                              fps: int = 10, zoom_level: float = None) -> str:
        """
        生成无人机飞行动画
        
        Args:
            drone_id: 无人机ID
            duration: 持续时间（秒）
            fps: 帧率
            zoom_level: 缩放级别
            
        Returns:
            生成的gif文件路径
        """
        try:
            # 获取无人机
            drone = await Drone.find_one({"drone_id": drone_id})
            if not drone:
                raise ValueError(f"找不到无人机: {drone_id}")
            
            # 获取无人机的任务
            task = None
            if drone.assigned_tasks:
                task_id = drone.assigned_tasks[0]
                task = await Task.find_one({"task_id": task_id})
            
            # 如果没有任务或没有规划路径，无法生成动画
            if not task or not task.planned_path or not task.planned_path.waypoints:
                raise ValueError(f"无人机 {drone_id} 没有活动任务或规划路径")
            
            # 获取路径
            waypoints = task.planned_path.waypoints
            if len(waypoints) < 2:
                raise ValueError("路径至少需要两个航点")
            
            # 提取坐标
            coords = [wp.coordinates for wp in waypoints]
            
            # 估算飞行时间
            distance = 0
            for i in range(len(coords) - 1):
                lon1, lat1 = coords[i]
                lon2, lat2 = coords[i+1]
                dist = self._haversine(lat1, lon1, lat2, lon2)
                distance += dist
            
            flight_time = distance / settings.DRONE_MAX_SPEED  # 秒
            
            # 如果飞行时间太短，至少设置为10秒
            flight_time = max(10, flight_time)
            
            # 每秒的移动距离
            speed = distance / flight_time
            
            # 计算插值点
            total_frames = fps * duration
            
            # 每个航点段的距离占总距离的比例
            segment_distances = []
            for i in range(len(coords) - 1):
                lon1, lat1 = coords[i]
                lon2, lat2 = coords[i+1]
                dist = self._haversine(lat1, lon1, lat2, lon2)
                segment_distances.append(dist)
            
            total_distance = sum(segment_distances)
            segment_ratios = [d / total_distance for d in segment_distances]
            
            # 每个航点段的帧数
            segment_frames = [int(ratio * total_frames) for ratio in segment_ratios]
            
            # 确保总帧数一致
            while sum(segment_frames) < total_frames:
                segment_frames[0] += 1
            
            # 生成插值点
            interp_coords = []
            
            for i in range(len(coords) - 1):
                lon1, lat1 = coords[i]
                lon2, lat2 = coords[i+1]
                frames = segment_frames[i]
                
                for j in range(frames):
                    t = j / frames
                    lon = lon1 + t * (lon2 - lon1)
                    lat = lat1 + t * (lat2 - lat1)
                    interp_coords.append((lon, lat))
            
            # 添加最后一个点
            interp_coords.append(coords[-1])
            
            # 确保帧数正确
            interp_coords = interp_coords[:total_frames]
            
            # 准备生成动画
            temp_dir = Path("./temp/frames")
            temp_dir.mkdir(parents=True, exist_ok=True)
            
            # 清理旧文件
            for file in temp_dir.glob("*.png"):
                os.remove(file)
            
            # 生成每一帧
            for i, (lon, lat) in enumerate(interp_coords):
                # 设置绘图
                self._setup_plot(f"无人机 {drone_id} 飞行轨迹", zoom_level)
                
                # 添加禁飞区
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
                
                self._add_no_fly_zones(zones)
                
                # 添加路径
                path_lons = [c[0] for c in coords]
                path_lats = [c[1] for c in coords]
                self.ax.plot(path_lons, path_lats, '-', color="blue", linewidth=2, alpha=0.7, zorder=5)
                
                # 添加航点
                self.ax.scatter(path_lons[1:-1], path_lats[1:-1], s=40, color="blue", marker='o', alpha=0.6, zorder=6)
                
                # 添加起点和终点标记
                self.ax.scatter(path_lons[0], path_lats[0], s=80, color="green", marker='o', edgecolors='black', linewidths=1, zorder=8)
                self.ax.scatter(path_lons[-1], path_lats[-1], s=80, color="red", marker='s', edgecolors='black', linewidths=1, zorder=8)
                
                # 添加无人机位置
                self.ax.scatter(lon, lat, s=150, color="yellow", marker='^', edgecolors='black', linewidths=2, zorder=10)
                
                # 添加当前位置标签
                self.ax.annotate(
                    drone_id,
                    (lon, lat),
                    xytext=(10, 10),
                    textcoords='offset points',
                    fontsize=12,
                    bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="black", alpha=0.7),
                    arrowprops=dict(arrowstyle="->")
                )
                
                # 添加完成百分比
                progress = (i + 1) / len(interp_coords) * 100
                self.ax.set_title(f"无人机 {drone_id} 飞行轨迹 - 完成: {progress:.1f}%", fontsize=16)
                
                # 保存帧
                frame_path = temp_dir / f"frame_{i:04d}.png"
                plt.tight_layout()
                self.fig.savefig(frame_path, format='png', bbox_inches='tight')
                plt.close(self.fig)
            
            # 生成动画
            frames = []
            for i in range(total_frames):
                frame_path = temp_dir / f"frame_{i:04d}.png"
                if frame_path.exists():
                    frames.append(imageio.imread(str(frame_path)))
            
            # 保存为GIF
            output_path = self.temp_dir / f"drone_{drone_id}_animation.gif"
            imageio.mimsave(str(output_path), frames, fps=fps)
            
            # 清理临时文件
            for file in temp_dir.glob("*.png"):
                os.remove(file)
            
            return str(output_path)
        except Exception as e:
            logger.error(f"生成动画失败: {str(e)}")
            raise
    
    def _get_color(self, index: int, total: int) -> str:
        """根据索引生成颜色"""
        hue = index / total
        rgb = colorsys.hsv_to_rgb(hue, 0.8, 0.9)
        return (rgb[0], rgb[1], rgb[2])
    
    def _haversine(self, lat1, lon1, lat2, lon2):
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
        r = 6371000  # 地球半径，单位为米
        
        # 返回距离，单位为米
        return c * r


# 创建全局地图可视化工具实例
map_visualizer = MapVisualizer()