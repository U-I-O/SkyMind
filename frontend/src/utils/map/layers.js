/**
 * 地图图层相关工具函数
 */
import { ScatterplotLayer, PathLayer, PolygonLayer, IconLayer } from '@deck.gl/layers'

/**
 * 根据无人机状态获取颜色
 * @param {Object} drone 无人机对象
 * @returns {Array} RGBA颜色数组
 */
export const getDroneColor = (drone) => {
  switch (drone.status) {
    case 'idle':
      return [0, 122, 255, 255]  // 蓝色
    case 'flying':
      return [52, 199, 89, 255]  // 绿色
    case 'charging':
      return [255, 149, 0, 255]  // 橙色
    case 'maintenance':
      return [255, 204, 0, 255]  // 黄色
    case 'offline':
      return [210, 210, 210, 180] // 灰色
    case 'error':
      return [255, 59, 48, 255]  // 红色
    default:
      return [128, 128, 128, 255] // 灰色
  }
}

/**
 * 根据电池电量获取电池颜色
 * @param {Number} level 电池电量（百分比）
 * @returns {String} 十六进制颜色值
 */
export const getDroneBatteryColor = (level) => {
  if (level <= 20) return '#ff4d4f'  // 红色（低电量）
  if (level <= 50) return '#faad14'  // 橙色（中等电量）
  return '#52c41a'                   // 绿色（高电量）
}

/**
 * 根据事件类型获取图标
 * @param {Object} event 事件对象
 * @returns {String} 图标名称
 */
export const getEventIcon = (event) => {
  switch (event.type) {
    case 'emergency':
      return 'warning'
    case 'security':
      return 'shield'
    case 'anomaly':
      return 'location'
    case 'logistics':
      return 'package'
    default:
      return 'marker'
  }
}

/**
 * 根据事件等级获取大小
 * @param {Object} event 事件对象
 * @returns {Number} 大小值
 */
export const getEventSize = (event) => {
  switch (event.level) {
    case 'high':
      return 5
    case 'medium':
      return 4
    case 'low':
      return 3
    default:
      return 3
  }
}

/**
 * 根据事件等级获取颜色
 * @param {Object} event 事件对象
 * @returns {Array} RGBA颜色数组
 */
export const getEventColor = (event) => {
  switch (event.level) {
    case 'high':
      return [255, 59, 48, 255]  // 红色
    case 'medium':
      return [255, 149, 0, 255]  // 橙色
    case 'low':
      return [255, 204, 0, 255]  // 黄色
    default:
      return [0, 122, 255, 255]  // 蓝色
  }
}

/**
 * 创建无人机图层
 * @param {Array} drones 无人机数据数组
 * @param {String} selectedDroneId 选中的无人机ID
 * @returns {Object} ScatterplotLayer实例
 */
export const createDronesLayer = (drones, selectedDroneId) => {
  return new ScatterplotLayer({
    id: 'drones-layer',
    data: drones.map(drone => {
      // 标准化数据格式
      if (!drone.current_location) return null
      
      const coordinates = drone.current_location.coordinates
      if (!coordinates || coordinates.length < 2) return null
      
      return {
        ...drone,
        type: 'drone',
        position: [coordinates[0], coordinates[1], coordinates[2] || (drone.current_location.altitude || 100)],
        color: getDroneColor(drone),
        radius: drone.drone_id === selectedDroneId ? 300 : 200
      }
    }).filter(Boolean),
    pickable: true,
    stroked: true,
    filled: true,
    radiusScale: 1,
    radiusMinPixels: 5,
    radiusMaxPixels: 20,
    lineWidthMinPixels: 1,
    getPosition: d => d.position,
    getFillColor: d => d.color,
    getLineColor: d => [255, 255, 255],
    getRadius: d => d.radius,
    getLineWidth: d => d.drone_id === selectedDroneId ? 3 : 1,
    updateTriggers: {
      getFillColor: [drones],
      getLineWidth: [selectedDroneId],
      getRadius: [selectedDroneId]
    }
  })
}

/**
 * 创建飞行路径图层
 * @param {Array} flightPaths 飞行路径数据数组
 * @returns {Object} PathLayer实例
 */
export const createFlightPathsLayer = (flightPaths) => {
  return new PathLayer({
    id: 'flight-paths-layer',
    data: flightPaths,
    pickable: true,
    widthScale: 1,
    widthMinPixels: 2,
    getPath: d => d.path,
    getColor: d => d.color || [30, 144, 255, 200],
    getWidth: d => d.width || 5
  })
}

/**
 * 创建禁飞区图层
 * @param {Array} noFlyZones 禁飞区数据数组
 * @returns {Object} PolygonLayer实例
 */
export const createNoFlyZonesLayer = (noFlyZones) => {
  return new PolygonLayer({
    id: 'no-fly-zones-layer',
    data: noFlyZones,
    pickable: true,
    stroked: true,
    filled: true,
    wireframe: true,
    lineWidthMinPixels: 1,
    getPolygon: d => d.polygon,
    getFillColor: d => d.color || [255, 0, 0, 50],
    getLineColor: [255, 0, 0],
    getLineWidth: 1
  })
}

/**
 * 创建事件图层
 * @param {Array} events 事件数据数组
 * @returns {Object} IconLayer实例
 */
export const createEventsLayer = (events) => {
  return new IconLayer({
    id: 'events-layer',
    data: events.map(event => {
      if (!event.location || !event.location.position) return null
      
      const coordinates = event.location.position.coordinates
      if (!coordinates || coordinates.length < 2) return null
      
      return {
        ...event,
        position: [coordinates[0], coordinates[1], coordinates[2] || 0],
        icon: getEventIcon(event),
        size: getEventSize(event),
        color: getEventColor(event)
      }
    }).filter(Boolean),
    pickable: true,
    sizeScale: 15,
    getPosition: d => d.position,
    getIcon: d => d.icon,
    getSize: d => d.size,
    getColor: d => d.color
  })
}

/**
 * 创建巡逻区域绘制相关图层
 * @param {Boolean} isDrawing 是否处于绘制模式
 * @param {Array} points 点位数组，每个点为[longitude, latitude]
 * @param {Object} geoJson 凸包计算结果的GeoJSON对象
 * @returns {Array} 图层数组
 */
export const createPatrolAreaLayers = (isDrawing, points, geoJson) => {
  const layers = []
  
  if (!isDrawing || points.length === 0) {
    return layers
  }

  // 确定要显示的点 - 如果有凸包，则只显示凸包上的点
  let pointsToShow = points;
  
  // 如果存在凸包数据，则只显示凸包上的点
  if (geoJson && geoJson.geometry && geoJson.geometry.coordinates && geoJson.geometry.coordinates.length > 0) {
    // 从 GeoJSON 中提取凸包上的点
    // 注意：GeoJSON 中的坐标是闭合的(最后一个点与第一个点相同)，所以需要去掉最后一个
    const hullPoints = geoJson.geometry.coordinates[0];
    if (hullPoints.length > 1) {
      // 去掉最后一个点（与第一个点重复）
      pointsToShow = hullPoints.slice(0, -1);
    }
  }

  // 显示凸包上的点
  layers.push(
    new ScatterplotLayer({
      id: 'patrol-area-points-layer',
      data: pointsToShow.map((p, index) => ({ position: p, index })),
      pickable: false,
      stroked: true,
      filled: true,
      radiusScale: 1,
      radiusMinPixels: 4,
      radiusMaxPixels: 8,
      lineWidthMinPixels: 1,
      getPosition: d => d.position,
      getFillColor: [59, 130, 246, 200], // 蓝色
      getLineColor: [255, 255, 255],
      getRadius: 5,
    })
  )

  // 显示凸包边缘连接线
  if (pointsToShow.length > 1) {
    layers.push(
      new PathLayer({
        id: 'patrol-area-path-layer',
        data: [{ path: pointsToShow }],
        pickable: false,
        widthScale: 1,
        widthMinPixels: 2,
        getPath: d => d.path,
        getColor: [59, 130, 246, 255], // 蓝色
        getWidth: 2
      })
    )
  }

  // 如果点数 > 2，显示一个填充的多边形预览
  if (points.length > 2) {
    let polygonData;
    
    // 优先使用凸包计算结果
    if (geoJson && geoJson.geometry && geoJson.geometry.coordinates && geoJson.geometry.coordinates.length > 0) {
      // 使用凸包坐标
      polygonData = [{
        polygon: geoJson.geometry.coordinates, // 使用GeoJSON中的坐标
        color: [59, 130, 246, 80] // 浅蓝色半透明填充
      }];
    } else {
      // 创建一个闭合的多边形（包括最后连回第一个点）
      const closedPolygon = [...points];
      polygonData = [{
        polygon: [closedPolygon], // 注意 PolygonLayer 需要二维数组 [[p1, p2, p3, ...]]
        color: [59, 130, 246, 80] // 浅蓝色半透明填充
      }];
    }
    
    layers.push(
      new PolygonLayer({
        id: 'patrol-area-preview-layer',
        data: polygonData,
        pickable: false,
        stroked: true,
        filled: true,
        wireframe: false,
        lineWidthMinPixels: 2,
        getPolygon: d => d.polygon,
        getFillColor: d => d.color,
        getLineColor: [59, 130, 246, 200],
        getLineWidth: 2
      })
    )
    
    // 不再需要单独的闭合线，因为多边形边界已经是闭合的
  }

  return layers
} 