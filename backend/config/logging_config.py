import os
import sys
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
import json
import time
from loguru import logger

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = "{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} - {message}"

# 创建日志目录
log_dir = Path("./logs")
log_dir.mkdir(exist_ok=True)

# 为不同模块配置不同的日志文件
log_files = {
    "default": log_dir / "skymind.log",
    "api": log_dir / "api.log",
    "agents": log_dir / "agents.log",
    "yolo": log_dir / "yolo.log",
    "planner": log_dir / "planner.log",
    "llm": log_dir / "llm.log",
    "error": log_dir / "error.log",
}

# 移除默认配置
logger.remove()

# 添加控制台输出
logger.add(sys.stderr, format=LOG_FORMAT, level=LOG_LEVEL, diagnose=True)

# 添加文件输出
for name, file_path in log_files.items():
    logger.add(
        file_path,
        format=LOG_FORMAT,
        level=LOG_LEVEL if name != "error" else "ERROR",
        rotation="50 MB",  # 日志文件达到50MB时轮转
        compression="zip",  # 压缩旧日志
        retention="30 days",  # 保留30天的日志
        enqueue=True,  # 多进程安全
        diagnose=True,  # 异常跟踪
        filter=lambda record: record["extra"].get("module", "default") == name if name != "default" else True
    )

# 创建具名日志器
def get_logger(module_name="default"):
    """获取指定模块的日志器"""
    return logger.bind(module=module_name)


# 创建一个JSON格式的日志处理器（用于日志分析系统）
class JsonLogFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            "timestamp": int(time.time()),
            "datetime": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(record.created)),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.name,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        if hasattr(record, "agent_id"):
            log_data["agent_id"] = record.agent_id
            
        if hasattr(record, "event_id"):
            log_data["event_id"] = record.event_id
            
        if hasattr(record, "task_id"):
            log_data["task_id"] = record.task_id
            
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
            
        return json.dumps(log_data)

# 为分析系统创建JSON日志文件
json_handler = RotatingFileHandler(
    log_dir / "json_logs.json",
    maxBytes=50 * 1024 * 1024,  # 50MB
    backupCount=10
)
json_handler.setFormatter(JsonLogFormatter())

# 配置标准库日志系统以便与外部库集成
logging.basicConfig(handlers=[json_handler], level=getattr(logging, LOG_LEVEL))

# 拦截常见的Python警告
import warnings
warnings.filterwarnings("always", category=UserWarning)
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=FutureWarning)