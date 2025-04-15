/**
 * 地图相关常量配置
 */

// 武汉大学位置
export const WHU_LOCATION = {
  longitude: 114.367, 
  latitude: 30.54,
  zoom: 15,
  pitch: 60,
  bearing: 30
}

// 地图默认视图状态
export const DEFAULT_VIEW_STATE = {
  longitude: 114.367,
  latitude: 30.54,
  zoom: 14,
  pitch: 45,
  bearing: 0
}

// Mapbox样式配置
export const MAP_STYLES = {
  DARK: 'mapbox://styles/mapbox/dark-v11',
  LIGHT: 'mapbox://styles/mapbox/light-v11',
  STREETS: 'mapbox://styles/mapbox/streets-v12',
  SATELLITE: 'mapbox://styles/mapbox/satellite-streets-v12'
}

// 无人机状态类型
export const DRONE_STATUS = {
  IDLE: 'idle',
  FLYING: 'flying',
  CHARGING: 'charging',
  MAINTENANCE: 'maintenance',
  OFFLINE: 'offline',
  ERROR: 'error'
}

// 无人机状态对应的UI类型
export const DRONE_STATUS_UI_TYPE = {
  idle: 'info',
  flying: 'success',
  charging: 'warning',
  maintenance: 'warning',
  offline: 'error',
  error: 'error'
}

// 事件级别
export const EVENT_LEVELS = {
  HIGH: 'high',
  MEDIUM: 'medium',
  LOW: 'low'
}

// 巡逻区域默认设置
export const PATROL_AREA_SETTINGS = {
  MIN_POINTS: 3,
  POINT_COLOR: [59, 130, 246, 200],  // 蓝色，半透明
  LINE_COLOR: [59, 130, 246, 255],   // 蓝色，不透明
  FILL_COLOR: [59, 130, 246, 80],    // 蓝色，高透明
  LINE_WIDTH: 2,
  POINT_RADIUS: 5
}

// 地图初始化超时时间（毫秒）
export const MAP_INIT_TIMEOUT = 10000 