/**
 * 巡逻区域管理模块
 */

/**
 * 切换巡逻区域绘制模式
 * @param {Object} map 地图实例
 * @param {Boolean} isDrawing 是否是绘制模式
 * @param {Function} clearPoints 清除点位的回调函数
 */
export const toggleDrawingMode = (map, isDrawing, clearPoints) => {
  if (!map) return

  if (isDrawing) {
    // 进入绘制模式，改变光标样式
    map.getCanvas().style.cursor = 'crosshair'
  } else {
    // 退出绘制模式，恢复光标样式，清除点位
    map.getCanvas().style.cursor = ''
    if (typeof clearPoints === 'function') {
      clearPoints()
    }
  }
}

/**
 * 添加巡逻区域点位
 * @param {Array} points 当前点位数组
 * @param {Number} longitude 经度
 * @param {Number} latitude 纬度
 * @returns {Array} 更新后的点位数组
 */
export const addPatrolPoint = (points, longitude, latitude) => {
  return [...points, [longitude, latitude]]
}

/**
 * 删除最后一个巡逻区域点位
 * @param {Array} points 当前点位数组
 * @returns {Array} 更新后的点位数组
 */
export const removeLastPoint = (points) => {
  if (!points || points.length === 0) return []
  return points.slice(0, -1)
}

/**
 * 完成巡逻区域绘制
 * @param {Array} points 当前点位数组
 * @returns {Array|null} 闭合的多边形点位数组，如果点数不足则返回null
 */
export const completePatrolArea = (points) => {
  if (!points || points.length < 3) return null
  
  // 创建一个闭合的多边形（复制第一个点到最后）
  return [...points, points[0]]
}

/**
 * 计算多边形的凸包（最外围点集合）
 * 使用Graham扫描法
 * @param {Array} points 点位数组 [[lng1, lat1], [lng2, lat2], ...]
 * @returns {Array} 凸包点位数组
 */
export const calculateConvexHull = (points) => {
  if (!points || points.length < 3) return points;
  
  // 首先找到最低且最左的点作为起点
  let start = points[0];
  for (let i = 1; i < points.length; i++) {
    if (points[i][1] < start[1] || (points[i][1] === start[1] && points[i][0] < start[0])) {
      start = points[i];
    }
  }
  
  // 按照相对于起点的极角排序
  const sortedPoints = [...points].sort((a, b) => {
    if (a === start) return -1;
    if (b === start) return 1;
    
    const angleA = Math.atan2(a[1] - start[1], a[0] - start[0]);
    const angleB = Math.atan2(b[1] - start[1], b[0] - start[0]);
    
    if (angleA < angleB) return -1;
    if (angleA > angleB) return 1;
    
    // 如果极角相同，则选择距离更远的点
    const distA = Math.sqrt(Math.pow(a[0] - start[0], 2) + Math.pow(a[1] - start[1], 2));
    const distB = Math.sqrt(Math.pow(b[0] - start[0], 2) + Math.pow(b[1] - start[1], 2));
    
    return distB - distA;
  });
  
  // 执行Graham扫描法构建凸包
  const hull = [sortedPoints[0], sortedPoints[1]];
  
  for (let i = 2; i < sortedPoints.length; i++) {
    while (hull.length > 1 && !isLeftTurn(hull[hull.length - 2], hull[hull.length - 1], sortedPoints[i])) {
      hull.pop();
    }
    hull.push(sortedPoints[i]);
  }
  
  return hull;
}

/**
 * 辅助函数：判断三点是否形成左转
 * @param {Array} p1 第一个点 [lng, lat]
 * @param {Array} p2 第二个点 [lng, lat]
 * @param {Array} p3 第三个点 [lng, lat]
 * @returns {Boolean} 是否左转
 */
const isLeftTurn = (p1, p2, p3) => {
  return (p2[0] - p1[0]) * (p3[1] - p1[1]) - (p2[1] - p1[1]) * (p3[0] - p1[0]) > 0;
}

/**
 * 检查巡逻区域是否有效
 * @param {Array} points 点位数组
 * @returns {Boolean} 是否有效
 */
export const isValidPatrolArea = (points) => {
  return points && points.length >= 3
}

/**
 * 将巡逻区域坐标转换为GeoJSON格式
 * @param {Array} points 点位数组，每个点为[longitude, latitude]
 * @param {Object} properties 附加属性
 * @returns {Object} GeoJSON对象
 */
export const coordsToGeoJSON = (points, properties = {}) => {
  if (!points || points.length < 3) return null;
  
  // 创建GeoJSON对象
  let coords = [...points];
  
  // 确保多边形闭合（首尾点相同）
  if (coords[0][0] !== coords[coords.length - 1][0] || coords[0][1] !== coords[coords.length - 1][1]) {
    coords.push([...coords[0]]);
  }
  
  return {
    type: 'Feature',
    properties,
    geometry: {
      type: 'Polygon',
      coordinates: [coords]
    }
  };
}

/**
 * 计算巡逻区域的面积（平方米）
 * @param {Array} points 点位数组，每个点为[longitude, latitude]
 * @returns {Number} 面积（平方米）
 */
export const calculatePatrolAreaSize = (points) => {
  if (!points || points.length < 3) return 0
  
  // 使用球面多边形面积计算公式
  // 这是一个简化的实现，对于较小的区域足够准确
  const EARTH_RADIUS = 6371000 // 地球半径（米）
  
  let area = 0
  let prev = points[points.length - 1]
  
  for (let i = 0; i < points.length; i++) {
    const current = points[i]
    area += degToRad(current[0] - prev[0]) * (2 + Math.sin(degToRad(prev[1])) + Math.sin(degToRad(current[1])))
    prev = current
  }
  
  area = Math.abs(area * EARTH_RADIUS * EARTH_RADIUS / 2)
  return area
}

/**
 * 角度转弧度
 * @param {Number} deg 角度
 * @returns {Number} 弧度
 */
const degToRad = (deg) => {
  return deg * Math.PI / 180
}
