from typing import List, Dict, Optional, Union, Any
from datetime import datetime
from beanie import Document, Link, BackLink, Insert, Replace, SaveChanges
from pydantic import BaseModel, Field, validator
from enum import Enum
import uuid


# 枚举定义
class UserRole(str, Enum):
    ADMIN = "admin"
    MANAGER = "manager"
    OPERATOR = "operator"
    VIEWER = "viewer"


class EventLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class TaskStatus(str, Enum):
    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class DroneStatus(str, Enum):
    IDLE = "idle"
    FLYING = "flying"
    CHARGING = "charging"
    MAINTENANCE = "maintenance"
    OFFLINE = "offline"


class EventType(str, Enum):
    ANOMALY = "anomaly"
    EMERGENCY = "emergency"
    LOGISTICS = "logistics"
    SECURITY = "security"
    SYSTEM = "system"


class TaskType(str, Enum):
    EMERGENCY = "emergency"
    DELIVERY = "delivery"
    INSPECTION = "inspection"
    SURVEILLANCE = "surveillance"
    PATROL = "patrol"
    OTHER = "other"


# 地理位置数据类型
class GeoPoint(BaseModel):
    type: str = "Point"
    coordinates: List[float]  # [longitude, latitude]
    altitude: Optional[float] = None


class Location(BaseModel):
    position: GeoPoint
    address: Optional[str] = None
    name: Optional[str] = None


class BoundingBox(BaseModel):
    """YOLO检测结果的边界框"""
    x1: float
    y1: float
    x2: float
    y2: float
    confidence: float
    class_id: int
    class_name: str


class TimeWindow(BaseModel):
    """时间窗口，用于任务调度"""
    start_time: datetime
    end_time: datetime


# 数据库模型定义
class User(Document):
    username: str = Field(..., unique=True, index=True)
    email: str = Field(..., unique=True, index=True)
    hashed_password: str
    full_name: Optional[str] = None
    role: UserRole = UserRole.VIEWER
    is_active: bool = True
    last_login: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "users"
        use_revision = True
        indexes = [
            "username",
            "email",
            "role"
        ]


class Drone(Document):
    """无人机数据模型"""
    drone_id: str = Field(default_factory=lambda: str(uuid.uuid4()), unique=True, index=True)
    name: str
    model: str
    status: DroneStatus = DroneStatus.IDLE
    battery_level: float = 100.0  # 百分比
    current_location: Optional[GeoPoint] = None
    max_flight_time: float  # 分钟
    max_speed: float  # m/s
    max_altitude: float  # 米
    camera_equipped: bool = True
    payload_capacity: float = 0.0  # 千克
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    assigned_tasks: List[str] = []  # 任务ID列表
    
    class Settings:
        name = "drones"
        use_revision = True
        indexes = [
            "drone_id",
            "status"
        ]


class FlightPath(BaseModel):
    """飞行路径"""
    waypoints: List[GeoPoint]
    estimated_duration: float  # 分钟
    distance: float  # 米
    created_by: str  # 创建这个路径的智能体ID


class Event(Document):
    """事件数据模型"""
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()), unique=True, index=True)
    type: EventType
    level: EventLevel = EventLevel.LOW
    title: str
    description: str
    location: Optional[Location] = None
    detected_at: datetime = Field(default_factory=datetime.utcnow)
    detected_by: str  # 检测这个事件的智能体ID
    status: str = "new"  # new, processing, resolved
    detection_data: Optional[Dict[str, Any]] = None  # 存储检测相关的数据
    video_source: Optional[str] = None  # 视频源URL或ID
    image_evidence: Optional[List[str]] = []  # 图像证据URL列表
    bounding_boxes: Optional[List[BoundingBox]] = []  # YOLO检测结果
    assigned_drones: List[str] = []  # 分配的无人机ID
    related_tasks: List[str] = []  # 相关任务ID
    resolved_at: Optional[datetime] = None
    resolution_notes: Optional[str] = None
    
    class Settings:
        name = "events"
        use_revision = True
        indexes = [
            "event_id",
            "type",
            "level",
            "status",
            "detected_at"
        ]


class Task(Document):
    """任务数据模型"""
    task_id: str = Field(default_factory=lambda: str(uuid.uuid4()), unique=True, index=True)
    title: str
    description: str
    type: TaskType = TaskType.PATROL  # 默认巡逻任务
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str  # 用户ID
    assigned_drones: List[str] = []  # 无人机ID列表
    related_events: List[str] = []   # 保留事件关联
    # 巡逻任务特有字段
    rounds: int = 1                  # 巡逻轮次
    altitude: float = 50.0           # 飞行高度（米）
    speed: float = 5.0               # 飞行速度（m/s）
    priority: int = 1                # 优先级
    patrol_area: Dict[str, Any] = Field(default_factory=lambda: {"type": "Polygon", "coordinates": []})
    schedule: Dict[str, Any] = Field(default_factory=lambda: {"type": "once", "date": None, "weekdays": [], "time": None})

    class Settings:
        name = "tasks"
        indexes = [
            "task_id", "type", "status", "created_at"
        ]


class NoFlyZone(Document):
    """禁飞区数据模型"""
    zone_id: str = Field(default_factory=lambda: str(uuid.uuid4()), unique=True, index=True)
    name: str
    description: Optional[str] = None
    geometry: Dict[str, Any]  # GeoJSON Polygon或MultiPolygon
    min_altitude: float = 0.0  # 米
    max_altitude: float = float('inf')  # 米
    permanent: bool = True
    start_time: Optional[datetime] = None  # 临时禁飞区开始时间
    end_time: Optional[datetime] = None  # 临时禁飞区结束时间
    created_by: str  # 用户ID
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "no_fly_zones"
        use_revision = True
        indexes = [
            "zone_id",
            "permanent"
        ]


class DetectionConfig(Document):
    """YOLO检测配置"""
    config_id: str = Field(default_factory=lambda: str(uuid.uuid4()), unique=True, index=True)
    name: str
    description: Optional[str] = None
    model_path: str
    confidence_threshold: float = 0.5
    classes_to_detect: List[int] = []
    enabled: bool = True
    created_by: str  # 用户ID
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "detection_configs"
        indexes = [
            "config_id"
        ]


class VideoSource(Document):
    """视频源数据模型"""
    source_id: str = Field(default_factory=lambda: str(uuid.uuid4()), unique=True, index=True)
    name: str
    description: Optional[str] = None
    url: str
    type: str = "rtsp"  # rtsp, http, file, etc.
    location: Optional[Location] = None
    active: bool = True
    detection_enabled: bool = False
    detection_config_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "video_sources"
        indexes = [
            "source_id",
            "active"
        ]


class AgentLog(Document):
    """智能体日志"""
    log_id: str = Field(default_factory=lambda: str(uuid.uuid4()), unique=True, index=True)
    agent_id: str
    agent_type: str
    level: str  # INFO, WARNING, ERROR, etc.
    message: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    related_task_id: Optional[str] = None
    related_event_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    
    class Settings:
        name = "agent_logs"
        indexes = [
            "agent_id",
            "level",
            "timestamp"
        ]


class AgentState(Document):
    """智能体状态"""
    agent_id: str = Field(..., unique=True, index=True)
    agent_type: str
    status: str = "active"  # active, idle, busy, error
    current_task_id: Optional[str] = None
    capability_scores: Dict[str, float] = {}  # 各种能力的评分
    last_active: datetime = Field(default_factory=datetime.utcnow)
    performance_metrics: Dict[str, Any] = {}
    memory_usage: Dict[str, Any] = {}
    
    class Settings:
        name = "agent_states"
        indexes = [
            "agent_id",
            "agent_type",
            "status"
        ]