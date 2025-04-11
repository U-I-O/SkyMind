from typing import Dict, List, Any, Optional, Union, Set, Tuple
import asyncio
import uuid
import os
import time
from datetime import datetime
import json
import threading
import cv2
import numpy as np
from ultralytics import YOLO
import base64
from pathlib import Path
from collections import defaultdict
import queue

from config.logging_config import get_logger
from database.models import (
    Event, VideoSource, DetectionConfig, BoundingBox, 
    EventType, EventLevel, Location, GeoPoint
)
from config.settings import settings
from .base import BaseAgent
from .coordinator import register_agent, get_coordinator

logger = get_logger("agents.monitor")

class MonitorAgent(BaseAgent):
    """
    监控智能体使用YOLOv8进行实时视频分析和异常事件检测
    """
    
    def __init__(self, agent_id: Optional[str] = None, name: str = "监控智能体"):
        super().__init__(agent_id, name)
        self.agent_type = "MonitorAgent"
        self.yolo_model = None
        self.detection_configs: Dict[str, DetectionConfig] = {}
        self.video_sources: Dict[str, Dict[str, Any]] = {}
        self.video_threads: Dict[str, threading.Thread] = {}
        self.frame_queues: Dict[str, queue.Queue] = {}
        self.result_queues: Dict[str, asyncio.Queue] = {}
        self.detection_stats: Dict[str, Dict[str, Any]] = {}
        self.event_cooldowns: Dict[str, Dict[str, float]] = {}  # 事件冷却时间
        self.saved_images_dir = Path("./data/detected_images")
        self.saved_images_dir.mkdir(parents=True, exist_ok=True)
        self.capabilities = {
            "object_detection": 0.95,
            "anomaly_detection": 0.8,
            "video_processing": 0.9,
            "event_classification": 0.85
        }
    
    async def initialize(self):
        """初始化监控智能体"""
        await super().initialize()
        
        # 加载YOLOv8模型
        await self._load_yolo_model()
        
        # 加载检测配置
        await self._load_detection_configs()
        
        # 加载视频源
        await self._load_video_sources()
        
        return self
    
    async def _load_yolo_model(self):
        """加载YOLOv8模型"""
        try:
            # 确定使用哪个模型
            model_path = settings.CUSTOM_YOLO_MODEL or settings.YOLO_MODEL
            
            self.logger.info(f"加载YOLOv8模型: {model_path}")
            
            # 在单独的线程中加载模型，避免阻塞事件循环
            self.yolo_model = await asyncio.to_thread(YOLO, model_path)
            
            self.logger.info(f"YOLOv8模型加载成功: {model_path}")
            
            # 记录模型信息
            model_info = {
                "model_path": model_path,
                "model_type": self.yolo_model.task,
                "model_version": self.yolo_model.model.yaml_file if hasattr(self.yolo_model.model, 'yaml_file') else "unknown"
            }
            await self.update_metrics({"yolo_model": model_info})
            
        except Exception as e:
            self.logger.error(f"加载YOLOv8模型失败: {str(e)}")
            raise
    
    async def _load_detection_configs(self):
        """从数据库加载检测配置"""
        try:
            configs = await DetectionConfig.find({"enabled": True}).to_list()
            
            for config in configs:
                self.detection_configs[config.config_id] = config
            
            self.logger.info(f"加载了 {len(configs)} 个检测配置")
        except Exception as e:
            self.logger.error(f"加载检测配置失败: {str(e)}")
    
    async def _load_video_sources(self):
        """从数据库加载视频源"""
        try:
            sources = await VideoSource.find({"active": True}).to_list()
            
            for source in sources:
                self.video_sources[source.source_id] = {
                    "source": source,
                    "active": False,
                    "last_frame_time": None,
                    "frames_processed": 0,
                    "detections": 0,
                    "events_detected": 0,
                    "fps": 0
                }
            
            self.logger.info(f"加载了 {len(sources)} 个视频源")
        except Exception as e:
            self.logger.error(f"加载视频源失败: {str(e)}")
    
    async def run_cycle(self):
        """监控智能体的主循环"""
        # 处理视频源
        await self._process_video_sources()
        
        # 处理检测结果
        await self._process_detection_results()
        
        # 更新统计信息
        await self._update_statistics()
    
    async def _process_video_sources(self):
        """处理所有活动的视频源"""
        for source_id, source_info in list(self.video_sources.items()):
            source = source_info["source"]
            
            # 跳过未启用检测的视频源
            if not source.detection_enabled:
                continue
            
            # 如果视频源不活跃，启动它
            if not source_info["active"]:
                await self._start_video_source(source_id)
    
    async def _start_video_source(self, source_id: str):
        """启动视频源的处理"""
        source_info = self.video_sources.get(source_id)
        if not source_info:
            self.logger.warning(f"找不到视频源: {source_id}")
            return False
        
        source = source_info["source"]
        
        try:
            # 创建帧队列和结果队列
            self.frame_queues[source_id] = queue.Queue(maxsize=30)  # 限制队列大小，防止内存溢出
            self.result_queues[source_id] = asyncio.Queue()
            
            # 创建事件冷却时间字典
            self.event_cooldowns[source_id] = {}
            
            # 启动视频处理线程
            thread = threading.Thread(
                target=self._video_processing_thread,
                args=(source_id, source.url),
                daemon=True
            )
            thread.start()
            
            self.video_threads[source_id] = thread
            self.video_sources[source_id]["active"] = True
            
            self.logger.info(f"启动视频源处理: {source_id} ({source.name})")
            return True
        
        except Exception as e:
            self.logger.error(f"启动视频源处理失败 {source_id}: {str(e)}")
            return False
    
    def _video_processing_thread(self, source_id: str, url: str):
        """视频处理线程，在后台运行"""
        # 获取相应的配置
        source_info = self.video_sources.get(source_id)
        if not source_info:
            logger.error(f"找不到视频源信息: {source_id}")
            return
        
        source = source_info["source"]
        config_id = source.detection_config_id
        config = self.detection_configs.get(config_id)
        
        # 如果没有专门的配置，使用默认配置
        confidence_threshold = (
            config.confidence_threshold if config else 
            settings.DETECTION_CONFIDENCE
        )
        classes_to_detect = (
            config.classes_to_detect if config else 
            settings.DETECTION_CLASSES
        )
        
        try:
            # 打开视频流
            cap = cv2.VideoCapture(url)
            if not cap.isOpened():
                logger.error(f"无法打开视频源: {url}")
                return
            
            frame_count = 0
            start_time = time.time()
            fps_update_interval = 10  # 每10帧更新一次FPS
            
            while not self._stop_event.is_set():
                ret, frame = cap.read()
                if not ret:
                    logger.warning(f"无法从视频源读取帧: {url}")
                    time.sleep(1)  # 暂停一秒后重试
                    continue
                
                # 更新FPS
                frame_count += 1
                if frame_count % fps_update_interval == 0:
                    end_time = time.time()
                    elapsed_time = end_time - start_time
                    fps = fps_update_interval / elapsed_time if elapsed_time > 0 else 0
                    source_info["fps"] = fps
                    start_time = time.time()
                
                # 将帧放入队列等待处理
                # 如果队列已满，跳过这一帧
                try:
                    self.frame_queues[source_id].put_nowait({
                        "frame": frame,
                        "timestamp": datetime.utcnow(),
                        "frame_id": frame_count
                    })
                except queue.Full:
                    # 队列已满，跳过这一帧
                    pass
                
                # 运行YOLOv8检测
                try:
                    results = self.yolo_model(
                        frame, 
                        conf=confidence_threshold,
                        classes=classes_to_detect,
                        verbose=False
                    )
                    
                    # 解析结果并放入结果队列
                    detections = self._parse_yolo_results(results, frame, source_id, frame_count)
                    if detections and len(detections["boxes"]) > 0:
                        asyncio.run_coroutine_threadsafe(
                            self.result_queues[source_id].put(detections),
                            asyncio.get_event_loop()
                        )
                    
                except Exception as e:
                    logger.error(f"YOLOv8检测出错: {str(e)}")
                
                # 控制处理速率，避免CPU过载
                time.sleep(0.01)
            
            # 关闭视频流
            cap.release()
            logger.info(f"视频处理线程结束: {source_id}")
        
        except Exception as e:
            logger.error(f"视频处理线程出错: {str(e)}")
    
    def _parse_yolo_results(self, results, frame, source_id: str, frame_id: int) -> Dict[str, Any]:
        """解析YOLOv8检测结果"""
        if not results or len(results) == 0:
            return None
        
        result = results[0]  # 获取第一个结果
        if not hasattr(result, 'boxes') or len(result.boxes) == 0:
            return None
        
        # 获取类别名称
        class_names = result.names
        
        height, width = frame.shape[:2]
        
        boxes = []
        for i, box in enumerate(result.boxes):
            # 获取边界框坐标
            x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int)
            
            # 获取置信度和类别ID
            confidence = float(box.conf[0].cpu().numpy())
            class_id = int(box.cls[0].cpu().numpy())
            class_name = class_names[class_id]
            
            # 创建边界框对象
            bounding_box = {
                "x1": float(x1) / width,  # 归一化坐标
                "y1": float(y1) / height,
                "x2": float(x2) / width,
                "y2": float(y2) / height,
                "confidence": confidence,
                "class_id": class_id,
                "class_name": class_name
            }
            boxes.append(bounding_box)
        
        # 如果检测到物体，保存图像
        if boxes:
            # 裁剪图像在边界框范围内
            save_path = None
            try:
                # 只保存第一个检测到的物体
                box = boxes[0]
                x1 = int(box["x1"] * width)
                y1 = int(box["y1"] * height)
                x2 = int(box["x2"] * width)
                y2 = int(box["y2"] * height)
                
                # 确保坐标有效
                x1 = max(0, x1)
                y1 = max(0, y1)
                x2 = min(width, x2)
                y2 = min(height, y2)
                
                if x1 < x2 and y1 < y2:
                    # 裁剪图像
                    cropped_img = frame[y1:y2, x1:x2]
                    
                    # 生成文件名
                    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f")
                    filename = f"{source_id}_{timestamp}_{box['class_name']}.jpg"
                    save_path = str(self.saved_images_dir / filename)
                    
                    # 保存图像
                    cv2.imwrite(save_path, cropped_img)
            except Exception as e:
                logger.error(f"保存检测图像失败: {str(e)}")
        
        return {
            "source_id": source_id,
            "frame_id": frame_id,
            "timestamp": datetime.utcnow(),
            "boxes": boxes,
            "image_path": save_path
        }
    
    async def _process_detection_results(self):
        """处理检测结果并生成事件"""
        for source_id, result_queue in self.result_queues.items():
            # 处理队列中的所有结果
            while not result_queue.empty():
                try:
                    detection = result_queue.get_nowait()
                    
                    if detection:
                        # 分析检测结果是否构成事件
                        events = await self._analyze_detection(detection)
                        
                        # 如果检测到事件，创建事件并通知协调者
                        for event in events:
                            await self._create_event(event)
                            
                        # 更新统计信息
                        source_info = self.video_sources.get(source_id, {})
                        source_info["detections"] = source_info.get("detections", 0) + len(detection["boxes"])
                        source_info["events_detected"] = source_info.get("events_detected", 0) + len(events)
                        source_info["last_frame_time"] = detection["timestamp"]
                        source_info["frames_processed"] = source_info.get("frames_processed", 0) + 1
                    
                    result_queue.task_done()
                except asyncio.QueueEmpty:
                    break
                except Exception as e:
                    self.logger.error(f"处理检测结果出错: {str(e)}")
    
    async def _analyze_detection(self, detection: Dict[str, Any]) -> List[Dict[str, Any]]:
        """分析检测结果，确定是否构成事件"""
        events = []
        source_id = detection["source_id"]
        timestamp = detection["timestamp"]
        boxes = detection["boxes"]
        
        # 获取视频源信息
        source_info = self.video_sources.get(source_id)
        if not source_info:
            return events
        
        source = source_info["source"]
        
        # 检查是否存在异常事件
        # 1. 人群聚集检测
        person_boxes = [box for box in boxes if box["class_name"] == "person"]
        if len(person_boxes) >= 5:  # 如果检测到5个以上的人
            event_key = f"crowd_{source_id}"
            if self._check_event_cooldown(source_id, event_key, 60):  # 1分钟冷却时间
                events.append({
                    "type": EventType.SECURITY,
                    "level": EventLevel.MEDIUM,
                    "title": "检测到人群聚集",
                    "description": f"在视频源 {source.name} 中检测到 {len(person_boxes)} 人聚集",
                    "location": source.location,
                    "source_id": source_id,
                    "boxes": person_boxes,
                    "image_path": detection.get("image_path")
                })
        
        # 2. 异常物体检测
        # 定义异常物体类别
        anomaly_classes = {"knife", "gun", "scissors", "fire", "smoke"}
        anomaly_boxes = [box for box in boxes if box["class_name"].lower() in anomaly_classes]
        
        for box in anomaly_boxes:
            event_key = f"anomaly_{box['class_name']}_{source_id}"
            if self._check_event_cooldown(source_id, event_key, 120):  # 2分钟冷却时间
                events.append({
                    "type": EventType.ANOMALY,
                    "level": EventLevel.HIGH,
                    "title": f"检测到异常物体: {box['class_name']}",
                    "description": f"在视频源 {source.name} 中检测到异常物体: {box['class_name']}，置信度: {box['confidence']:.2f}",
                    "location": source.location,
                    "source_id": source_id,
                    "boxes": [box],
                    "image_path": detection.get("image_path")
                })
        
        # 3. 车辆异常停放检测
        vehicle_classes = {"car", "truck", "bus", "motorcycle"}
        vehicle_boxes = [box for box in boxes if box["class_name"].lower() in vehicle_classes]
        
        # 检查是否有车辆在禁停区域
        # 这里简化为检测是否有车辆，在实际应用中应该结合地理位置判断
        if vehicle_boxes and source.location and hasattr(source, 'no_parking_zone') and source.no_parking_zone:
            for box in vehicle_boxes:
                event_key = f"illegal_parking_{source_id}"
                if self._check_event_cooldown(source_id, event_key, 300):  # 5分钟冷却时间
                    events.append({
                        "type": EventType.SECURITY,
                        "level": EventLevel.LOW,
                        "title": "检测到车辆异常停放",
                        "description": f"在视频源 {source.name} 中检测到车辆异常停放",
                        "location": source.location,
                        "source_id": source_id,
                        "boxes": [box],
                        "image_path": detection.get("image_path")
                    })
        
        return events
    
    def _check_event_cooldown(self, source_id: str, event_key: str, cooldown_seconds: int) -> bool:
        """检查事件是否在冷却时间内"""
        now = time.time()
        
        # 确保冷却字典存在
        if source_id not in self.event_cooldowns:
            self.event_cooldowns[source_id] = {}
        
        # 检查事件是否在冷却时间内
        if event_key in self.event_cooldowns[source_id]:
            last_time = self.event_cooldowns[source_id][event_key]
            if now - last_time < cooldown_seconds:
                return False
        
        # 更新事件最后触发时间
        self.event_cooldowns[source_id][event_key] = now
        return True
    
    async def _create_event(self, event_data: Dict[str, Any]):
        """创建事件并通知协调者"""
        try:
            # 创建边界框对象
            bounding_boxes = []
            for box in event_data.get("boxes", []):
                bounding_boxes.append(BoundingBox(
                    x1=box["x1"],
                    y1=box["y1"],
                    x2=box["x2"],
                    y2=box["y2"],
                    confidence=box["confidence"],
                    class_id=box["class_id"],
                    class_name=box["class_name"]
                ))
            
            # 创建事件
            event = Event(
                type=event_data["type"],
                level=event_data["level"],
                title=event_data["title"],
                description=event_data["description"],
                location=event_data["location"],
                detected_by=self.agent_id,
                detection_data={
                    "source_id": event_data["source_id"]
                },
                video_source=event_data["source_id"],
                bounding_boxes=bounding_boxes
            )
            
            # 如果有图像证据，添加到事件中
            if "image_path" in event_data and event_data["image_path"]:
                event.image_evidence = [event_data["image_path"]]
            
            # 保存事件
            await event.insert()
            self.logger.info(f"创建了新事件: {event.event_id} - {event.title}")
            
            # 通知协调者
            coordinator = await get_coordinator()
            await coordinator.message_queue.put({
                "type": "new_event",
                "event_id": event.event_id,
                "source_agent_id": self.agent_id
            })
            
            # 广播事件
            await self.broadcast_message({
                "type": "event_detected",
                "event_id": event.event_id,
                "event_level": event.level,
                "event_type": event.type,
                "source_agent_id": self.agent_id
            })
            
        except Exception as e:
            self.logger.error(f"创建事件出错: {str(e)}")
    
    async def _update_statistics(self):
        """更新智能体统计信息"""
        total_frames = 0
        total_detections = 0
        total_events = 0
        active_sources = 0
        
        for source_id, source_info in self.video_sources.items():
            if source_info["active"]:
                active_sources += 1
                total_frames += source_info.get("frames_processed", 0)
                total_detections += source_info.get("detections", 0)
                total_events += source_info.get("events_detected", 0)
        
        # 更新指标
        metrics = {
            "active_sources": active_sources,
            "total_frames_processed": total_frames,
            "total_detections": total_detections,
            "total_events_detected": total_events,
            "last_update": datetime.utcnow().isoformat()
        }
        
        await self.update_metrics(metrics)
    
    async def handle_query(self, query: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """处理来自其他智能体的查询"""
        if query == "get_detection_status":
            # 返回检测状态信息
            return {
                "success": True,
                "active_sources": sum(1 for info in self.video_sources.values() if info["active"]),
                "total_sources": len(self.video_sources),
                "metrics": self.metrics
            }
        
        elif query == "analyze_image":
            # 分析单个图像
            image_path = data.get("image_path")
            if not image_path or not os.path.exists(image_path):
                return {"success": False, "error": "Image not found"}
            
            try:
                # 读取图像
                image = cv2.imread(image_path)
                if image is None:
                    return {"success": False, "error": "Could not read image"}
                
                # 运行YOLOv8检测
                results = self.yolo_model(
                    image,
                    conf=settings.DETECTION_CONFIDENCE,
                    classes=settings.DETECTION_CLASSES,
                    verbose=False
                )
                
                # 解析结果
                detection = self._parse_yolo_results(
                    results, image, "query", 0
                )
                
                if not detection:
                    return {"success": True, "detections": []}
                
                return {
                    "success": True,
                    "detections": detection["boxes"]
                }
            
            except Exception as e:
                self.logger.error(f"分析图像出错: {str(e)}")
                return {"success": False, "error": str(e)}
        
        return await super().handle_query(query, data)
    
    async def stop(self):
        """停止监控智能体"""
        self.logger.info("停止监控智能体")
        
        # 设置停止事件
        self._stop_event.set()
        
        # 等待线程结束
        for source_id, thread in self.video_threads.items():
            self.logger.info(f"等待视频线程结束: {source_id}")
            thread.join(timeout=2)
        
        await super().stop()


# 创建监控智能体的工厂函数
async def create_monitor_agent(agent_id: Optional[str] = None, name: Optional[str] = None) -> MonitorAgent:
    """创建并初始化监控智能体"""
    agent = MonitorAgent(agent_id, name)
    await agent.initialize()
    register_agent(agent)
    return agent