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
 * 检查巡逻区域是否有效
 * @param {Array} points 点位数组
 * @returns {Boolean} 是否有效
 */
export const isValidPatrolArea = (points) => {
  return points && points.length >= 3
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