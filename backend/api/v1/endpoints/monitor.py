from fastapi import APIRouter, Depends, HTTPException, Query, status, Body, File, UploadFile
from fastapi.responses import StreamingResponse
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import json
import os
from pathlib import Path
import cv2
import numpy as np
import asyncio
import base64
from io import BytesIO

from config.logging_config import get_logger
from database.models import User, VideoSource, DetectionConfig, Event
from core.security import get_current_active_user
from agents.monitor import create_monitor_agent
from agents.coordinator import get_coordinator, get_agent_by_id

logger = get_logger("api.monitor")

router = APIRouter()

# 获取所有视频源
@router.get("/sources", response_model=List[Dict[str, Any]])
async def get_video_sources(
    active_only: bool = Query(False, description="仅获取活跃视频源"),
    current_user: User = Depends(get_current_active_user)
):
    """获取所有视频源"""
    query = {}
    if active_only:
        query["active"] = True
    
    sources = await VideoSource.find(query).to_list()
    
    return [source.dict() for source in sources]

# 获取单个视频源
@router.get("/sources/{source_id}", response_model=Dict[str, Any])
async def get_video_source(
    source_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """获取单个视频源"""
    source = await VideoSource.find_one({"source_id": source_id})
    if not source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="视频源不存在"
        )
    
    return source.dict()

# 创建视频源
@router.post("/sources", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
async def create_video_source(
    source_data: Dict[str, Any] = Body(...),
    current_user: User = Depends(get_current_active_user)
):
    """创建视频源"""
    # 检查必需字段
    required_fields = ["name", "url", "type"]
    for field in required_fields:
        if field not in source_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"缺少必需字段: {field}"
            )
    
    # 创建视频源
    source = VideoSource(
        name=source_data["name"],
        url=source_data["url"],
        type=source_data["type"],
        description=source_data.get("description"),
        active=source_data.get("active", True),
        detection_enabled=source_data.get("detection_enabled", False),
        detection_config_id=source_data.get("detection_config_id")
    )
    
    # 处理位置信息
    if "location" in source_data:
        source.location = source_data["location"]
    
    await source.insert()
    
    logger.info(f"创建了新视频源: {source.source_id}")
    
    return source.dict()

# 更新视频源
@router.put("/sources/{source_id}", response_model=Dict[str, Any])
async def update_video_source(
    source_id: str,
    source_data: Dict[str, Any] = Body(...),
    current_user: User = Depends(get_current_active_user)
):
    """更新视频源"""
    source = await VideoSource.find_one({"source_id": source_id})
    if not source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="视频源不存在"
        )
    
    # 更新字段
    update_fields = ["name", "url", "type", "description", "active", "detection_enabled", "detection_config_id"]
    for field in update_fields:
        if field in source_data:
            setattr(source, field, source_data[field])
    
    # 处理位置信息
    if "location" in source_data:
        source.location = source_data["location"]
    
    # 更新时间戳
    source.updated_at = datetime.utcnow()
    
    await source.save()
    
    logger.info(f"更新了视频源: {source_id}")
    
    return source.dict()

# 删除视频源
@router.delete("/sources/{source_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_video_source(
    source_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """删除视频源"""
    source = await VideoSource.find_one({"source_id": source_id})
    if not source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="视频源不存在"
        )
    
    await source.delete()
    
    logger.info(f"删除了视频源: {source_id}")

# 获取所有检测配置
@router.get("/configs", response_model=List[Dict[str, Any]])
async def get_detection_configs(
    enabled_only: bool = Query(False, description="仅获取启用的配置"),
    current_user: User = Depends(get_current_active_user)
):
    """获取所有检测配置"""
    query = {}
    if enabled_only:
        query["enabled"] = True
    
    configs = await DetectionConfig.find(query).to_list()
    
    return [config.dict() for config in configs]

# 获取单个检测配置
@router.get("/configs/{config_id}", response_model=Dict[str, Any])
async def get_detection_config(
    config_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """获取单个检测配置"""
    config = await DetectionConfig.find_one({"config_id": config_id})
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="检测配置不存在"
        )
    
    return config.dict()

# 创建检测配置
@router.post("/configs", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
async def create_detection_config(
    config_data: Dict[str, Any] = Body(...),
    current_user: User = Depends(get_current_active_user)
):
    """创建检测配置"""
    # 检查必需字段
    required_fields = ["name", "model_path"]
    for field in required_fields:
        if field not in config_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"缺少必需字段: {field}"
            )
    
    # 创建配置
    config = DetectionConfig(
        name=config_data["name"],
        model_path=config_data["model_path"],
        description=config_data.get("description"),
        confidence_threshold=config_data.get("confidence_threshold", 0.5),
        classes_to_detect=config_data.get("classes_to_detect", []),
        enabled=config_data.get("enabled", True),
        created_by=current_user.username
    )
    
    await config.insert()
    
    logger.info(f"创建了新检测配置: {config.config_id}")
    
    return config.dict()

# 更新检测配置
@router.put("/configs/{config_id}", response_model=Dict[str, Any])
async def update_detection_config(
    config_id: str,
    config_data: Dict[str, Any] = Body(...),
    current_user: User = Depends(get_current_active_user)
):
    """更新检测配置"""
    config = await DetectionConfig.find_one({"config_id": config_id})
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="检测配置不存在"
        )
    
    # 更新字段
    update_fields = ["name", "model_path", "description", "confidence_threshold", "classes_to_detect", "enabled"]
    for field in update_fields:
        if field in config_data:
            setattr(config, field, config_data[field])
    
    # 更新时间戳
    config.updated_at = datetime.utcnow()
    
    await config.save()
    
    logger.info(f"更新了检测配置: {config_id}")
    
    return config.dict()

# 删除检测配置
@router.delete("/configs/{config_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_detection_config(
    config_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """删除检测配置"""
    config = await DetectionConfig.find_one({"config_id": config_id})
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="检测配置不存在"
        )
    
    # 检查是否有视频源使用此配置
    sources_using_config = await VideoSource.find({"detection_config_id": config_id}).count()
    if sources_using_config > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"有 {sources_using_config} 个视频源使用此配置，无法删除"
        )
    
    await config.delete()
    
    logger.info(f"删除了检测配置: {config_id}")

# 分析图片
@router.post("/analyze-image", response_model=Dict[str, Any])
async def analyze_image(
    file: UploadFile = File(...),
    confidence: float = Query(0.5, ge=0.1, le=1.0),
    current_user: User = Depends(get_current_active_user)
):
    """分析上传的图片"""
    # 检查文件类型
    allowed_types = ["image/jpeg", "image/png", "image/jpg"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="仅支持JPEG和PNG图片"
        )
    
    # 读取图片
    contents = await file.read()
    
    # 保存临时文件
    temp_dir = Path("./temp")
    temp_dir.mkdir(exist_ok=True)
    temp_path = temp_dir / f"temp_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{file.filename}"
    
    with open(temp_path, "wb") as f:
        f.write(contents)
    
    # 获取监控智能体
    coordinator = await get_coordinator()
    monitor_agents = coordinator._get_agents_by_type("MonitorAgent")
    
    if not monitor_agents:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="没有可用的监控智能体"
        )
    
    monitor_agent = monitor_agents[0]
    
    # 查询监控智能体
    response = await coordinator.query_agent(
        monitor_agent.agent_id,
        "analyze_image",
        {"image_path": str(temp_path)}
    )
    
    # 检查响应
    if not response["success"]:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"分析图片失败: {response.get('error', '未知错误')}"
        )
    
    # 读取图片用于标注和返回
    image = cv2.imread(str(temp_path))
    height, width = image.shape[:2]
    
    # 过滤满足置信度的检测结果
    detections = [
        d for d in response["detections"]
        if d["confidence"] >= confidence
    ]
    
    # 在图片上标注检测结果
    for detection in detections:
        # 转换归一化坐标为像素坐标
        x1 = int(detection["x1"] * width)
        y1 = int(detection["y1"] * height)
        x2 = int(detection["x2"] * width)
        y2 = int(detection["y2"] * height)
        
        # 绘制边界框
        cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 2)
        
        # 绘制标签
        label = f"{detection['class_name']} {detection['confidence']:.2f}"
        cv2.putText(image, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
    
    # 将图片编码为base64
    _, buffer = cv2.imencode(".jpg", image)
    img_base64 = base64.b64encode(buffer).decode("utf-8")
    
    # 清理临时文件
    if temp_path.exists():
        os.remove(temp_path)
    
    # 返回检测结果
    return {
        "detections": detections,
        "detection_count": len(detections),
        "annotated_image": img_base64
    }

# 获取监控统计信息
@router.get("/statistics", response_model=Dict[str, Any])
async def get_monitor_statistics(
    current_user: User = Depends(get_current_active_user)
):
    """获取监控统计信息"""
    # 获取监控智能体
    coordinator = await get_coordinator()
    monitor_agents = coordinator._get_agents_by_type("MonitorAgent")
    
    if not monitor_agents:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="没有可用的监控智能体"
        )
    
    monitor_agent = monitor_agents[0]
    
    # 查询监控智能体
    response = await coordinator.query_agent(
        monitor_agent.agent_id,
        "get_detection_status",
        {}
    )
    
    # 检查响应
    if not response["success"]:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取统计信息失败: {response.get('error', '未知错误')}"
        )
    
    # 获取视频源和事件统计
    active_sources_count = response["active_sources"]
    total_sources_count = response["total_sources"]
    
    # 获取今日事件总数
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    today_events_count = await Event.find({"detected_at": {"$gte": today_start}}).count()
    
    # 合并统计信息
    statistics = {
        "active_sources": active_sources_count,
        "total_sources": total_sources_count,
        "today_events": today_events_count,
        "metrics": response["metrics"],
        "timestamp": datetime.utcnow().isoformat()
    }
    
    return statistics