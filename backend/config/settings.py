from pydantic_settings import BaseSettings
from typing import Dict, List, Optional, Union
import os
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    # 基本配置
    PROJECT_NAME: str = "SkyMind低空智慧城市AI平台"
    API_VERSION: str = "v1"
    API_PREFIX: str = f"/api/{API_VERSION}"
    DEBUG: bool = bool(int(os.getenv("DEBUG", "1")))
    
    # 安全配置
    SECRET_KEY: str = os.getenv("SECRET_KEY", "supersecretkey")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7天
    
    # 数据库配置
    MONGODB_URL: str = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    DATABASE_NAME: str = os.getenv("DATABASE_NAME", "skymind_db")
    
    # LLM配置
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4")
    
    # YOLO配置
    YOLO_MODEL: str = os.getenv("YOLO_MODEL", "yolov8n.pt")
    CUSTOM_YOLO_MODEL: Optional[str] = os.getenv("CUSTOM_YOLO_MODEL", None)
    DETECTION_CONFIDENCE: float = float(os.getenv("DETECTION_CONFIDENCE", "0.5"))
    DETECTION_CLASSES: List[int] = [0, 1, 2, 3, 5, 6, 7, 8, 9]  # 默认检测类别（人、自行车、汽车等）
    
    # 视频流配置
    MAX_VIDEO_STREAMS: int = int(os.getenv("MAX_VIDEO_STREAMS", "10"))
    VIDEO_STREAM_TIMEOUT: int = int(os.getenv("VIDEO_STREAM_TIMEOUT", "30"))
    
    # 地理空间配置
    DEFAULT_CITY_CENTER: Dict[str, float] = {
        "lat": float(os.getenv("DEFAULT_CITY_LAT", "39.9042")),  # 北京
        "lon": float(os.getenv("DEFAULT_CITY_LON", "116.4074"))
    }
    DEFAULT_ZOOM_LEVEL: int = int(os.getenv("DEFAULT_ZOOM_LEVEL", "12"))
    
    # 路径规划配置
    PATH_PLANNING_ALGORITHM: str = os.getenv("PATH_PLANNING_ALGORITHM", "astar")  # 可选: astar, rrt, rl
    DRONE_MAX_SPEED: float = float(os.getenv("DRONE_MAX_SPEED", "15.0"))  # m/s
    DRONE_MAX_ALTITUDE: float = float(os.getenv("DRONE_MAX_ALTITUDE", "120.0"))  # m
    
    # 北斗配置
    BEIDOU_API_URL: Optional[str] = os.getenv("BEIDOU_API_URL")
    BEIDOU_API_KEY: Optional[str] = os.getenv("BEIDOU_API_KEY")
    
    # 异常事件配置
    ANOMALY_EVENT_LEVELS: Dict[str, Dict] = {
        "low": {"color": "yellow", "response_time": 300},  # 5分钟响应
        "medium": {"color": "orange", "response_time": 120},  # 2分钟响应
        "high": {"color": "red", "response_time": 60}  # 1分钟响应
    }
    
    # WebSocket配置
    WS_PING_INTERVAL: int = int(os.getenv("WS_PING_INTERVAL", "30"))  # 秒
    
    # 智能体配置
    AGENT_COMMUNICATION_INTERVAL: int = int(os.getenv("AGENT_COMMUNICATION_INTERVAL", "5"))  # 秒
    MAX_AGENTS_PER_TASK: int = int(os.getenv("MAX_AGENTS_PER_TASK", "5"))
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()