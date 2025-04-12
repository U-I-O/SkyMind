import psutil
import platform
import socket
import time
from fastapi import APIRouter, Depends
from typing import List, Dict, Any
from datetime import datetime, timedelta

from database.models import User
from core.security import get_current_active_user

router = APIRouter()

@router.get("/status")
async def get_system_status(current_user: User = Depends(get_current_active_user)) -> Dict[str, Any]:
    """
    获取系统资源状态
    """
    # 获取CPU信息
    cpu_usage = psutil.cpu_percent(interval=1)
    cpu_count = psutil.cpu_count(logical=True)
    cpu_physical_count = psutil.cpu_count(logical=False)
    cpu_freq = psutil.cpu_freq()
    cpu_stats = psutil.cpu_stats()
    
    # 获取内存信息
    memory = psutil.virtual_memory()
    swap = psutil.swap_memory()
    
    # 获取磁盘信息
    disk = psutil.disk_usage('/')
    disk_io = psutil.disk_io_counters()
    
    # 获取网络信息
    net_io = psutil.net_io_counters()
    
    # 获取系统信息
    boot_time = datetime.fromtimestamp(psutil.boot_time())
    system_uptime = datetime.now() - boot_time
    
    # 获取进程信息
    process_count = len(list(psutil.process_iter()))
    
    # 获取系统负载
    try:
        load_avg = psutil.getloadavg()
    except:
        load_avg = (0, 0, 0)  # Windows可能不支持
    
    # 获取系统信息
    system_info = {
        "system": platform.system(),
        "node": platform.node(),
        "release": platform.release(),
        "version": platform.version(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "hostname": socket.gethostname(),
        "ip_address": socket.gethostbyname(socket.gethostname())
    }
    
    # 模拟其他系统数据（实际项目中应从数据库或其他服务获取）
    online_drones = 8
    total_drones = 12
    active_agents = 5
    total_agents = 5
    pending_events = 3
    active_tasks = 4
    
    return {
        # CPU信息
        "cpu_usage": cpu_usage,
        "cpu_count": cpu_count,
        "cpu_physical_count": cpu_physical_count,
        "cpu_freq": {
            "current": cpu_freq.current if cpu_freq else None,
            "min": cpu_freq.min if cpu_freq and hasattr(cpu_freq, 'min') else None,
            "max": cpu_freq.max if cpu_freq and hasattr(cpu_freq, 'max') else None
        },
        "cpu_stats": {
            "ctx_switches": cpu_stats.ctx_switches,
            "interrupts": cpu_stats.interrupts,
            "soft_interrupts": cpu_stats.soft_interrupts,
            "syscalls": cpu_stats.syscalls
        },
        
        # 内存信息
        "memory_usage": memory.percent,
        "memory_total": memory.total,
        "memory_available": memory.available,
        "memory_used": memory.used,
        "swap_usage": swap.percent,
        "swap_total": swap.total,
        "swap_used": swap.used,
        
        # 磁盘信息
        "storage_usage": disk.percent,
        "storage_total": disk.total,
        "storage_used": disk.used,
        "storage_free": disk.free,
        "disk_io": {
            "read_count": disk_io.read_count,
            "write_count": disk_io.write_count,
            "read_bytes": disk_io.read_bytes,
            "write_bytes": disk_io.write_bytes
        },
        
        # 网络信息
        "network": {
            "bytes_sent": net_io.bytes_sent,
            "bytes_recv": net_io.bytes_recv,
            "packets_sent": net_io.packets_sent,
            "packets_recv": net_io.packets_recv,
            "errin": net_io.errin,
            "errout": net_io.errout,
            "dropin": net_io.dropin,
            "dropout": net_io.dropout
        },
        
        # 系统信息
        "system_info": system_info,
        "boot_time": boot_time.isoformat(),
        "uptime_seconds": system_uptime.total_seconds(),
        "uptime_formatted": str(timedelta(seconds=int(system_uptime.total_seconds()))),
        "process_count": process_count,
        "load_avg": load_avg,
        
        # 业务数据
        "online_drones": online_drones,
        "total_drones": total_drones,
        "active_agents": active_agents,
        "total_agents": total_agents,
        "pending_events": pending_events,
        "active_tasks": active_tasks,
        
        # 时间戳
        "timestamp": datetime.now().isoformat()
    }

@router.get("/agents")
async def get_agents_status(current_user: User = Depends(get_current_active_user)) -> List[Dict[str, Any]]:
    """
    获取智能体状态列表
    """
    # 实际项目中应从数据库获取
    agents = [
        {"id": 1, "name": "监控智能体", "status": "active", "type": "monitor", "cpu_usage": 12.5, "memory_usage": 128.4},
        {"id": 2, "name": "路径规划智能体", "status": "active", "type": "planner", "cpu_usage": 8.2, "memory_usage": 96.7},
        {"id": 3, "name": "应急响应智能体", "status": "active", "type": "response", "cpu_usage": 15.8, "memory_usage": 156.2},
        {"id": 4, "name": "物流调度智能体", "status": "active", "type": "logistics", "cpu_usage": 6.4, "memory_usage": 84.5},
        {"id": 5, "name": "安防巡检智能体", "status": "active", "type": "security", "cpu_usage": 9.1, "memory_usage": 112.3}
    ]
    
    return agents

@router.get("/history/{resource_type}")
async def get_resource_history(
    resource_type: str,
    hours: int = 24,
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    获取资源历史使用数据
    resource_type: cpu, memory, disk, network
    hours: 查询过去多少小时的数据
    """
    # 模拟历史数据
    now = datetime.now()
    data_points = []
    
    # 生成过去hours小时的数据点，每5分钟一个点
    for i in range(hours * 12):
        timestamp = now - timedelta(minutes=i * 5)
        
        if resource_type == "cpu":
            value = 30 + (i % 50)  # 模拟CPU使用率波动
        elif resource_type == "memory":
            value = 50 + (i % 30)  # 模拟内存使用率波动
        elif resource_type == "disk":
            value = 40 + (i % 5)   # 模拟磁盘使用率波动
        elif resource_type == "network":
            value = 20 + (i % 70)  # 模拟网络使用率波动
        else:
            value = 0
            
        data_points.append({
            "timestamp": timestamp.isoformat(),
            "value": value
        })
    
    # 倒序排列，最新的数据在前面
    data_points.reverse()
    
    return {
        "resource_type": resource_type,
        "unit": "percent" if resource_type in ["cpu", "memory", "disk"] else "mbps",
        "data": data_points
    }