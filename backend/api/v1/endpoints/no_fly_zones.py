from fastapi import APIRouter, Depends, HTTPException, Query, status, Body
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import json
from shapely.geometry import Polygon, Point

from config.logging_config import get_logger
from database.models import User, NoFlyZone, Drone, Task
from core.security import get_current_active_user
from config.settings import settings

logger = get_logger("api.no_fly_zones")

router = APIRouter()

# 获取所有禁飞区
@router.get("/", response_model=List[Dict[str, Any]])
async def get_all_no_fly_zones(
    permanent: Optional[bool] = Query(None, description="按永久性筛选"),
    active_only: bool = Query(False, description="仅获取当前有效的禁飞区"),
    current_user: User = Depends(get_current_active_user)
):
    """获取所有禁飞区"""
    # 创建查询条件
    query = {}
    if permanent is not None:
        query["permanent"] = permanent
    
    # 如果只查询当前有效的禁飞区
    if active_only and permanent is not True:
        now = datetime.utcnow()
        query["$or"] = [
            {"permanent": True},
            {
                "permanent": False,
                "start_time": {"$lte": now},
                "end_time": {"$gte": now}
            }
        ]
    
    # 查询数据库
    zones = await NoFlyZone.find(query).to_list()
    
    # 格式化结果
    result = []
    for zone in zones:
        zone_dict = zone.dict()
        
        # 添加禁飞区状态
        if zone.permanent:
            zone_dict["status"] = "permanent"
        else:
            now = datetime.utcnow()
            if zone.start_time > now:
                zone_dict["status"] = "scheduled"
            elif zone.end_time < now:
                zone_dict["status"] = "expired"
            else:
                zone_dict["status"] = "active"
        
        result.append(zone_dict)
    
    return result

# 获取单个禁飞区
@router.get("/{zone_id}", response_model=Dict[str, Any])
async def get_no_fly_zone(
    zone_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """获取单个禁飞区详情"""
    zone = await NoFlyZone.find_one({"zone_id": zone_id})
    if not zone:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="禁飞区不存在"
        )
    
    # 格式化结果
    result = zone.dict()
    
    # 添加禁飞区状态
    if zone.permanent:
        result["status"] = "permanent"
    else:
        now = datetime.utcnow()
        if zone.start_time > now:
            result["status"] = "scheduled"
        elif zone.end_time < now:
            result["status"] = "expired"
        else:
            result["status"] = "active"
    
    return result

# 创建禁飞区
@router.post("/", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
async def create_no_fly_zone(
    zone_data: Dict[str, Any] = Body(...),
    current_user: User = Depends(get_current_active_user)
):
    """创建禁飞区"""
    # 检查必需字段
    required_fields = ["name", "geometry"]
    for field in required_fields:
        if field not in zone_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"缺少必需字段: {field}"
            )
    
    # 验证几何数据
    geometry = zone_data["geometry"]
    if not isinstance(geometry, dict) or "type" not in geometry or "coordinates" not in geometry:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效的几何数据格式"
        )
    
    if geometry["type"] not in ["Polygon", "MultiPolygon"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"不支持的几何类型: {geometry['type']}"
        )
    
    # 检查是否为临时禁飞区
    permanent = zone_data.get("permanent", True)
    if not permanent:
        if "start_time" not in zone_data or "end_time" not in zone_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="临时禁飞区必须指定开始和结束时间"
            )
        
        # 解析时间
        try:
            start_time = datetime.fromisoformat(zone_data["start_time"])
            end_time = datetime.fromisoformat(zone_data["end_time"])
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="无效的时间格式"
            )
        
        # 验证时间范围
        if start_time >= end_time:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="开始时间必须早于结束时间"
            )
    else:
        start_time = None
        end_time = None
    
    # 创建禁飞区
    zone = NoFlyZone(
        name=zone_data["name"],
        description=zone_data.get("description"),
        geometry=geometry,
        min_altitude=zone_data.get("min_altitude", 0.0),
        max_altitude=zone_data.get("max_altitude", float('inf')),
        permanent=permanent,
        start_time=start_time,
        end_time=end_time,
        created_by=current_user.username
    )
    
    # 保存到数据库
    await zone.insert()
    
    logger.info(f"创建了新禁飞区: {zone.zone_id}")
    
    # 检查是否有无人机在该禁飞区内
    await check_drones_in_zone(zone)
    
    return zone.dict()

# 更新禁飞区
@router.put("/{zone_id}", response_model=Dict[str, Any])
async def update_no_fly_zone(
    zone_id: str,
    zone_data: Dict[str, Any] = Body(...),
    current_user: User = Depends(get_current_active_user)
):
    """更新禁飞区"""
    # 获取禁飞区
    zone = await NoFlyZone.find_one({"zone_id": zone_id})
    if not zone:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="禁飞区不存在"
        )
    
    # 更新基本字段
    update_fields = ["name", "description", "min_altitude", "max_altitude"]
    for field in update_fields:
        if field in zone_data:
            setattr(zone, field, zone_data[field])
    
    # 更新几何数据
    if "geometry" in zone_data:
        geometry = zone_data["geometry"]
        if not isinstance(geometry, dict) or "type" not in geometry or "coordinates" not in geometry:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="无效的几何数据格式"
            )
        
        if geometry["type"] not in ["Polygon", "MultiPolygon"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"不支持的几何类型: {geometry['type']}"
            )
        
        zone.geometry = geometry
    
    # 处理临时禁飞区
    if "permanent" in zone_data:
        permanent = zone_data["permanent"]
        zone.permanent = permanent
        
        if not permanent:
            if "start_time" in zone_data and "end_time" in zone_data:
                # 解析时间
                try:
                    start_time = datetime.fromisoformat(zone_data["start_time"])
                    end_time = datetime.fromisoformat(zone_data["end_time"])
                except ValueError:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="无效的时间格式"
                    )
                
                # 验证时间范围
                if start_time >= end_time:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="开始时间必须早于结束时间"
                    )
                
                zone.start_time = start_time
                zone.end_time = end_time
            elif not zone.start_time or not zone.end_time:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="临时禁飞区必须指定开始和结束时间"
                )
        else:
            zone.start_time = None
            zone.end_time = None
    elif not zone.permanent:
        # 更新时间
        if "start_time" in zone_data:
            try:
                zone.start_time = datetime.fromisoformat(zone_data["start_time"])
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="无效的开始时间格式"
                )
        
        if "end_time" in zone_data:
            try:
                zone.end_time = datetime.fromisoformat(zone_data["end_time"])
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="无效的结束时间格式"
                )
        
        # 验证时间范围
        if zone.start_time and zone.end_time and zone.start_time >= zone.end_time:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="开始时间必须早于结束时间"
            )
    
    # 更新时间戳
    zone.updated_at = datetime.utcnow()
    
    # 保存更新
    await zone.save()
    
    logger.info(f"更新了禁飞区: {zone_id}")
    
    # 检查是否有无人机在该禁飞区内
    await check_drones_in_zone(zone)
    
    return zone.dict()

# 删除禁飞区
@router.delete("/{zone_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_no_fly_zone(
    zone_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """删除禁飞区"""
    # 获取禁飞区
    zone = await NoFlyZone.find_one({"zone_id": zone_id})
    if not zone:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="禁飞区不存在"
        )
    
    # 删除禁飞区
    await zone.delete()
    
    logger.info(f"删除了禁飞区: {zone_id}")

# 检查坐标是否在禁飞区内
@router.post("/check", response_model=Dict[str, Any])
async def check_coordinates(
    check_data: Dict[str, Any] = Body(...),
    current_user: User = Depends(get_current_active_user)
):
    """检查坐标是否在禁飞区内"""
    # 检查必需字段
    if "lon" not in check_data or "lat" not in check_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="缺少经纬度坐标"
        )
    
    lon = check_data["lon"]
    lat = check_data["lat"]
    altitude = check_data.get("altitude")
    
    # 创建点
    point = Point(lon, lat)
    
    # 查询所有有效的禁飞区
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
    
    # 检查点是否在禁飞区内
    in_zone = False
    zone_info = None
    
    for zone in zones:
        # 创建多边形
        coordinates = zone.geometry["coordinates"][0]
        polygon = Polygon(coordinates)
        
        if polygon.contains(point):
            # 检查高度
            if altitude:
                if zone.min_altitude <= altitude <= zone.max_altitude:
                    in_zone = True
                    zone_info = zone.dict()
                    break
            else:
                in_zone = True
                zone_info = zone.dict()
                break
    
    return {
        "coordinates": {"lon": lon, "lat": lat, "altitude": altitude},
        "in_no_fly_zone": in_zone,
        "zone_info": zone_info
    }

# 获取活跃禁飞区的GeoJSON
@router.get("/geojson", response_model=Dict[str, Any])
async def get_no_fly_zones_geojson(
    current_user: User = Depends(get_current_active_user)
):
    """获取活跃禁飞区的GeoJSON格式数据"""
    # 查询所有有效的禁飞区
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
    
    # 创建GeoJSON特征集合
    features = []
    
    for zone in zones:
        # 创建特征
        feature = {
            "type": "Feature",
            "geometry": zone.geometry,
            "properties": {
                "zone_id": zone.zone_id,
                "name": zone.name,
                "description": zone.description,
                "permanent": zone.permanent,
                "min_altitude": zone.min_altitude,
                "max_altitude": zone.max_altitude
            }
        }
        
        # 添加临时区域的时间信息
        if not zone.permanent:
            feature["properties"]["start_time"] = zone.start_time.isoformat()
            feature["properties"]["end_time"] = zone.end_time.isoformat()
        
        features.append(feature)
    
    # 创建GeoJSON特征集合
    geojson = {
        "type": "FeatureCollection",
        "features": features
    }
    
    return geojson

# 检查禁飞区内是否有无人机（辅助函数）
async def check_drones_in_zone(zone: NoFlyZone):
    """检查是否有无人机在禁飞区内，并发出警告"""
    try:
        # 检查是否是当前有效的禁飞区
        now = datetime.utcnow()
        is_active = zone.permanent or (zone.start_time <= now <= zone.end_time)
        
        if not is_active:
            return
        
        # 创建多边形
        coordinates = zone.geometry["coordinates"][0]
        polygon = Polygon(coordinates)
        
        # 获取所有飞行中的无人机
        flying_drones = await Drone.find({"status": "flying"}).to_list()
        
        # 检查每个无人机
        for drone in flying_drones:
            if not drone.current_location:
                continue
            
            # 获取无人机位置
            lon, lat = drone.current_location.coordinates
            point = Point(lon, lat)
            
            # 检查是否在禁飞区内
            if polygon.contains(point):
                # 检查高度
                altitude = drone.current_location.altitude
                if altitude and zone.min_altitude <= altitude <= zone.max_altitude:
                    logger.warning(f"无人机 {drone.drone_id} 在禁飞区 {zone.zone_id} 内")
                    
                    # 在实际应用中，这里应该发出警告或通知
                    # 例如通过WebSocket发送警告消息
                    # 或者自动重新规划路径
    
    except Exception as e:
        logger.error(f"检查禁飞区内无人机时出错: {str(e)}")

# 获取与飞行任务冲突的禁飞区
@router.post("/conflicts", response_model=List[Dict[str, Any]])
async def check_task_conflicts(
    task_data: Dict[str, Any] = Body(...),
    current_user: User = Depends(get_current_active_user)
):
    """检查飞行任务是否与禁飞区冲突"""
    # 检查必需字段
    required_fields = ["waypoints"]
    for field in required_fields:
        if field not in task_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"缺少必需字段: {field}"
            )
    
    waypoints = task_data["waypoints"]
    if not isinstance(waypoints, list) or len(waypoints) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="至少需要两个航点"
        )
    
    # 获取时间信息
    start_time = None
    end_time = None
    
    if "time_window" in task_data:
        tw = task_data["time_window"]
        if isinstance(tw, dict) and "start_time" in tw and "end_time" in tw:
            try:
                start_time = datetime.fromisoformat(tw["start_time"])
                end_time = datetime.fromisoformat(tw["end_time"])
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="无效的时间格式"
                )
    
    # 如果没有指定时间，使用当前时间
    if not start_time:
        start_time = datetime.utcnow()
    if not end_time:
        end_time = start_time + timedelta(hours=1)
    
    # 查询相关禁飞区
    zones_query = {
        "$or": [
            {"permanent": True},
            {
                "permanent": False,
                "start_time": {"$lte": end_time},
                "end_time": {"$gte": start_time}
            }
        ]
    }
    
    zones = await NoFlyZone.find(zones_query).to_list()
    
    # 检查每个航点和航段是否与禁飞区冲突
    conflicts = []
    
    for zone in zones:
        # 创建多边形
        coordinates = zone.geometry["coordinates"][0]
        polygon = Polygon(coordinates)
        
        # 检查每个航点
        for i, wp in enumerate(waypoints):
            position = wp.get("position", {})
            coordinates = position.get("coordinates", [])
            
            if len(coordinates) < 2:
                continue
            
            lon, lat = coordinates
            altitude = position.get("altitude")
            point = Point(lon, lat)
            
            # 检查点是否在禁飞区内
            if polygon.contains(point):
                # 检查高度
                if altitude is None or zone.min_altitude <= altitude <= zone.max_altitude:
                    conflicts.append({
                        "zone_id": zone.zone_id,
                        "name": zone.name,
                        "waypoint_index": i,
                        "conflict_type": "waypoint"
                    })
                    break
            
            # 检查航段
            if i < len(waypoints) - 1:
                next_wp = waypoints[i + 1]
                next_position = next_wp.get("position", {})
                next_coordinates = next_position.get("coordinates", [])
                
                if len(next_coordinates) < 2:
                    continue
                
                next_lon, next_lat = next_coordinates
                next_point = Point(next_lon, next_lat)
                
                # 创建线段
                from shapely.geometry import LineString
                line = LineString([(lon, lat), (next_lon, next_lat)])
                
                # 检查线段是否与禁飞区相交
                if line.intersects(polygon):
                    conflicts.append({
                        "zone_id": zone.zone_id,
                        "name": zone.name,
                        "waypoint_index": i,
                        "conflict_type": "segment"
                    })
                    break
    
    return conflicts