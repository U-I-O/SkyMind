import json
import asyncio
import aiohttp
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
import numpy as np

from config.settings import settings
from config.logging_config import get_logger

logger = get_logger("services.beidou")

class BeidouService:
    """北斗导航服务，提供与北斗导航系统的集成"""
    
    def __init__(self, api_url: Optional[str] = None, api_key: Optional[str] = None):
        self.api_url = api_url or settings.BEIDOU_API_URL
        self.api_key = api_key or settings.BEIDOU_API_KEY
        self.is_initialized = False
        self.session = None
        self.request_count = 0
        self.last_request_time = None
    
    async def initialize(self):
        """初始化北斗服务"""
        if self.is_initialized:
            return
        
        try:
            logger.info("初始化北斗导航服务")
            
            # 检查API URL和密钥
            if not self.api_url or not self.api_key:
                logger.warning("未配置北斗API URL或密钥，将启用模拟模式")
                self.is_simulation = True
            else:
                self.is_simulation = False
                # 创建HTTP会话
                self.session = aiohttp.ClientSession()
            
            self.is_initialized = True
            logger.info("北斗导航服务初始化成功")
            
            return True
        except Exception as e:
            logger.error(f"初始化北斗导航服务失败: {str(e)}")
            raise
    
    async def close(self):
        """关闭服务"""
        if self.session:
            await self.session.close()
    
    async def get_location(self, device_id: str) -> Dict[str, Any]:
        """
        获取设备位置
        
        Args:
            device_id: 设备ID
            
        Returns:
            位置信息字典
        """
        if not self.is_initialized:
            await self.initialize()
        
        # 更新统计信息
        self.request_count += 1
        self.last_request_time = datetime.utcnow()
        
        if self.is_simulation:
            # 模拟模式返回模拟数据
            return self._simulate_location(device_id)
        
        try:
            # 构建请求参数
            params = {
                "api_key": self.api_key,
                "device_id": device_id
            }
            
            # 发送请求
            async with self.session.get(f"{self.api_url}/location", params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        "success": True,
                        "location": data,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                else:
                    error_text = await response.text()
                    logger.error(f"获取位置失败: {response.status} - {error_text}")
                    return {
                        "success": False,
                        "error": f"API错误: {response.status}",
                        "timestamp": datetime.utcnow().isoformat()
                    }
        except Exception as e:
            logger.error(f"获取位置失败: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def track_devices(self, device_ids: List[str]) -> Dict[str, Any]:
        """
        跟踪多个设备
        
        Args:
            device_ids: 设备ID列表
            
        Returns:
            跟踪结果字典
        """
        if not self.is_initialized:
            await self.initialize()
        
        # 更新统计信息
        self.request_count += 1
        self.last_request_time = datetime.utcnow()
        
        if self.is_simulation:
            # 模拟模式返回模拟数据
            return self._simulate_tracking(device_ids)
        
        try:
            # 构建请求参数
            params = {
                "api_key": self.api_key,
                "device_ids": ",".join(device_ids)
            }
            
            # 发送请求
            async with self.session.get(f"{self.api_url}/track", params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        "success": True,
                        "devices": data,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                else:
                    error_text = await response.text()
                    logger.error(f"跟踪设备失败: {response.status} - {error_text}")
                    return {
                        "success": False,
                        "error": f"API错误: {response.status}",
                        "timestamp": datetime.utcnow().isoformat()
                    }
        except Exception as e:
            logger.error(f"跟踪设备失败: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def get_trajectory(self, device_id: str, 
                           start_time: datetime,
                           end_time: datetime) -> Dict[str, Any]:
        """
        获取设备轨迹
        
        Args:
            device_id: 设备ID
            start_time: 开始时间
            end_time: 结束时间
            
        Returns:
            轨迹数据字典
        """
        if not self.is_initialized:
            await self.initialize()
        
        # 更新统计信息
        self.request_count += 1
        self.last_request_time = datetime.utcnow()
        
        if self.is_simulation:
            # 模拟模式返回模拟数据
            return self._simulate_trajectory(device_id, start_time, end_time)
        
        try:
            # 构建请求参数
            params = {
                "api_key": self.api_key,
                "device_id": device_id,
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat()
            }
            
            # 发送请求
            async with self.session.get(f"{self.api_url}/trajectory", params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        "success": True,
                        "trajectory": data,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                else:
                    error_text = await response.text()
                    logger.error(f"获取轨迹失败: {response.status} - {error_text}")
                    return {
                        "success": False,
                        "error": f"API错误: {response.status}",
                        "timestamp": datetime.utcnow().isoformat()
                    }
        except Exception as e:
            logger.error(f"获取轨迹失败: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def _simulate_location(self, device_id: str) -> Dict[str, Any]:
        """模拟位置数据"""
        # 使用设备ID生成一个伪随机种子
        seed = int(device_id.replace("-", "")[:8], 16)
        np.random.seed(seed)
        
        # 以默认城市中心为基准生成随机位置
        center_lat = settings.DEFAULT_CITY_CENTER["lat"]
        center_lon = settings.DEFAULT_CITY_CENTER["lon"]
        
        # 随机偏移量（约1公里范围内）
        lat_offset = np.random.uniform(-0.01, 0.01)
        lon_offset = np.random.uniform(-0.01, 0.01)
        
        # 随机高度（50-200米）
        altitude = np.random.uniform(50, 200)
        
        # 随机速度（0-20 m/s）
        speed = np.random.uniform(0, 20)
        
        # 随机方向（0-360度）
        heading = np.random.uniform(0, 360)
        
        return {
            "success": True,
            "location": {
                "device_id": device_id,
                "latitude": center_lat + lat_offset,
                "longitude": center_lon + lon_offset,
                "altitude": altitude,
                "speed": speed,
                "heading": heading,
                "accuracy": np.random.uniform(1, 10),
                "timestamp": datetime.utcnow().isoformat()
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def _simulate_tracking(self, device_ids: List[str]) -> Dict[str, Any]:
        """模拟跟踪数据"""
        devices = []
        
        for device_id in device_ids:
            location = self._simulate_location(device_id)["location"]
            devices.append(location)
        
        return {
            "success": True,
            "devices": devices,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def _simulate_trajectory(self, device_id: str, 
                           start_time: datetime,
                           end_time: datetime) -> Dict[str, Any]:
        """模拟轨迹数据"""
        # 计算需要生成的点数
        time_diff = (end_time - start_time).total_seconds()
        num_points = min(100, max(10, int(time_diff / 60)))  # 每分钟一个点，最少10个，最多100个
        
        # 使用设备ID生成一个伪随机种子
        seed = int(device_id.replace("-", "")[:8], 16)
        np.random.seed(seed)
        
        # 以默认城市中心为基准生成随机起点
        center_lat = settings.DEFAULT_CITY_CENTER["lat"]
        center_lon = settings.DEFAULT_CITY_CENTER["lon"]
        
        # 随机起点偏移量（约1公里范围内）
        start_lat_offset = np.random.uniform(-0.01, 0.01)
        start_lon_offset = np.random.uniform(-0.01, 0.01)
        
        start_lat = center_lat + start_lat_offset
        start_lon = center_lon + start_lon_offset
        
        # 随机终点偏移量（相对于起点再随机偏移约1公里）
        end_lat_offset = np.random.uniform(-0.01, 0.01)
        end_lon_offset = np.random.uniform(-0.01, 0.01)
        
        end_lat = start_lat + end_lat_offset
        end_lon = start_lon + end_lon_offset
        
        # 生成轨迹点
        points = []
        for i in range(num_points):
            # 线性插值
            t = i / (num_points - 1) if num_points > 1 else 0
            lat = start_lat + t * (end_lat - start_lat)
            lon = start_lon + t * (end_lon - start_lon)
            
            # 添加一些随机性
            lat += np.random.uniform(-0.0005, 0.0005)  # 约50米的随机偏移
            lon += np.random.uniform(-0.0005, 0.0005)
            
            # 随机高度（50-200米）
            altitude = np.random.uniform(50, 200)
            
            # 时间点
            point_time = start_time + (end_time - start_time) * t
            
            points.append({
                "latitude": lat,
                "longitude": lon,
                "altitude": altitude,
                "timestamp": point_time.isoformat()
            })
        
        return {
            "success": True,
            "trajectory": {
                "device_id": device_id,
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "points": points
            },
            "timestamp": datetime.utcnow().isoformat()
        }

# 创建全局北斗服务实例
beidou_service = BeidouService()