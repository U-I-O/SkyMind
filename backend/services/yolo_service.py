import os
import cv2
import numpy as np
import base64
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime
import asyncio
from ultralytics import YOLO

from config.settings import settings
from config.logging_config import get_logger

logger = get_logger("services.yolo")

class YOLOService:
    """YOLO目标检测服务，封装YOLOv8模型"""
    
    def __init__(self, model_path: Optional[str] = None):
        self.model_path = model_path or settings.YOLO_MODEL
        self.model = None
        self.class_names = []
        self.is_initialized = False
        self.detection_count = 0
        self.last_detection_time = None
    
    async def initialize(self):
        """初始化YOLO模型"""
        if self.is_initialized:
            return
        
        try:
            logger.info(f"加载YOLO模型: {self.model_path}")
            
            # 在后台线程中加载模型
            self.model = await asyncio.to_thread(YOLO, self.model_path)
            
            # 获取类别名称
            self.class_names = self.model.names
            
            self.is_initialized = True
            logger.info(f"YOLO模型加载成功，类别数: {len(self.class_names)}")
            
            return True
        except Exception as e:
            logger.error(f"加载YOLO模型失败: {str(e)}")
            raise
    
    async def detect_image(self, image_data: Union[str, bytes, np.ndarray], 
                          conf_threshold: float = 0.5,
                          classes: Optional[List[int]] = None) -> Dict[str, Any]:
        """
        对图像进行目标检测
        
        Args:
            image_data: 图像数据，可以是base64字符串、字节数据或numpy数组
            conf_threshold: 置信度阈值
            classes: 要检测的类别ID列表
        
        Returns:
            检测结果字典
        """
        if not self.is_initialized:
            await self.initialize()
        
        try:
            # 转换图像数据
            if isinstance(image_data, str) and image_data.startswith("data:image"):
                # 处理base64编码的图像
                image_data = image_data.split(",")[1]
                image_bytes = base64.b64decode(image_data)
                np_arr = np.frombuffer(image_bytes, np.uint8)
                image = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
            elif isinstance(image_data, str) and os.path.exists(image_data):
                # 处理图像文件路径
                image = cv2.imread(image_data)
            elif isinstance(image_data, bytes):
                # 处理字节数据
                np_arr = np.frombuffer(image_data, np.uint8)
                image = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
            elif isinstance(image_data, np.ndarray):
                # 已经是numpy数组
                image = image_data
            else:
                raise ValueError("不支持的图像数据格式")
            
            if image is None:
                raise ValueError("无法解码图像数据")
            
            # 运行YOLOv8检测
            results = await asyncio.to_thread(
                self.model, 
                image, 
                conf=conf_threshold,
                classes=classes,
                verbose=False
            )
            
            # 解析检测结果
            detections = self._parse_detections(results, image.shape)
            
            # 更新统计信息
            self.detection_count += 1
            self.last_detection_time = datetime.utcnow()
            
            return detections
        
        except Exception as e:
            logger.error(f"目标检测失败: {str(e)}")
            raise
    
    def _parse_detections(self, results, image_shape: Tuple[int, int, int]) -> Dict[str, Any]:
        """解析YOLOv8检测结果"""
        if not results or len(results) == 0:
            return {"success": True, "detections": [], "count": 0}
        
        result = results[0]  # 获取第一个结果
        
        height, width = image_shape[:2]
        boxes = []
        
        # 检查是否有检测结果
        if hasattr(result, 'boxes') and len(result.boxes) > 0:
            for i, box in enumerate(result.boxes):
                # 获取边界框坐标
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int)
                
                # 获取置信度和类别ID
                confidence = float(box.conf[0].cpu().numpy())
                class_id = int(box.cls[0].cpu().numpy())
                class_name = self.class_names[class_id]
                
                # 创建检测结果对象
                detection = {
                    "x1": float(x1) / width,  # 归一化坐标
                    "y1": float(y1) / height,
                    "x2": float(x2) / width,
                    "y2": float(y2) / height,
                    "confidence": confidence,
                    "class_id": class_id,
                    "class_name": class_name,
                    "bbox": [int(x1), int(y1), int(x2), int(y2)]  # 像素坐标
                }
                
                boxes.append(detection)
        
        return {
            "success": True,
            "detections": boxes,
            "count": len(boxes),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def detect_video_frame(self, frame: np.ndarray,
                                conf_threshold: float = 0.5,
                                classes: Optional[List[int]] = None) -> Dict[str, Any]:
        """
        对视频帧进行目标检测
        
        Args:
            frame: 视频帧图像
            conf_threshold: 置信度阈值
            classes: 要检测的类别ID列表
        
        Returns:
            检测结果字典
        """
        return await self.detect_image(frame, conf_threshold, classes)
    
    def annotate_image(self, image: np.ndarray, detections: List[Dict[str, Any]]) -> np.ndarray:
        """
        在图像上标注检测结果
        
        Args:
            image: 原始图像
            detections: 检测结果列表
        
        Returns:
            标注后的图像
        """
        annotated_image = image.copy()
        height, width = image.shape[:2]
        
        for detection in detections:
            # 转换归一化坐标为像素坐标
            x1 = int(detection["x1"] * width)
            y1 = int(detection["y1"] * height)
            x2 = int(detection["x2"] * width)
            y2 = int(detection["y2"] * height)
            
            # 获取类别和置信度
            class_name = detection["class_name"]
            confidence = detection["confidence"]
            
            # 设置不同类别的颜色
            class_id = detection["class_id"]
            color = self._get_color(class_id)
            
            # 绘制边界框
            cv2.rectangle(annotated_image, (x1, y1), (x2, y2), color, 2)
            
            # 准备标签
            label = f"{class_name} {confidence:.2f}"
            
            # 获取文本大小
            (label_width, label_height), baseline = cv2.getTextSize(
                label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2
            )
            
            # 绘制标签背景
            cv2.rectangle(
                annotated_image,
                (x1, y1 - label_height - baseline - 5),
                (x1 + label_width, y1),
                color,
                -1
            )
            
            # 绘制标签文本
            cv2.putText(
                annotated_image,
                label,
                (x1, y1 - baseline - 5),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (255, 255, 255),
                2
            )
        
        return annotated_image
    
    def _get_color(self, class_id: int) -> Tuple[int, int, int]:
        """根据类别ID获取颜色"""
        colors = [
            (0, 255, 0),    # 绿色
            (255, 0, 0),    # 蓝色
            (0, 0, 255),    # 红色
            (255, 255, 0),  # 青色
            (255, 0, 255),  # 品红
            (0, 255, 255),  # 黄色
            (128, 128, 0),  # 橄榄
            (128, 0, 128),  # 紫色
            (0, 128, 128),  # 蓝绿
            (0, 165, 255),  # 橙色
        ]
        return colors[class_id % len(colors)]

# 创建全局YOLO服务实例
yolo_service = YOLOService()