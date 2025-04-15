/**
 * 地图初始化与基础功能模块
 */
import mapboxgl from 'mapbox-gl'

/**
 * 初始化Mapbox地图
 * @param {HTMLElement} container 地图容器元素
 * @param {Object} options 初始化选项
 * @returns {Object} 地图实例
 */
export const initializeMapbox = (container, options = {}) => {
  if (!container) {
    throw new Error('地图容器元素不存在')
  }

  const {
    mapboxToken,
    style = 'mapbox://styles/mapbox/streets-v12',
    center = [114.367, 30.54],
    zoom = 14,
    pitch = 45,
    bearing = 0
  } = options

  // 设置Mapbox访问令牌
  mapboxgl.accessToken = mapboxToken

  // 创建地图实例
  const map = new mapboxgl.Map({
    container,
    style,
    center,
    zoom,
    pitch,
    bearing,
    antialias: true,
    failIfMajorPerformanceCaveat: false
  })

  return map
}

/**
 * 添加3D建筑层
 * @param {Object} map 地图实例
 * @param {Boolean} visible 是否可见
 */
export const add3DBuildings = (map, visible = true) => {
  if (!map || map.getLayer('building-extrusion')) return

  // 添加3D建筑层
  map.addLayer({
    'id': 'building-extrusion',
    'type': 'fill-extrusion',
    'source': 'composite',
    'source-layer': 'building',
    'filter': ['==', 'extrude', 'true'],
    'minzoom': 12,
    'paint': {
      'fill-extrusion-color': '#3b82f6',
      'fill-extrusion-height': [
        'interpolate', ['linear'], ['zoom'],
        12, 0,
        12.5, ['get', 'height']
      ],
      'fill-extrusion-base': [
        'interpolate', ['linear'], ['zoom'],
        12, 0,
        12.5, ['get', 'min_height']
      ],
      'fill-extrusion-opacity': 0.6
    },
    'visibility': visible ? 'visible' : 'none'
  })
}

/**
 * 添加地形和天空层
 * @param {Object} map 地图实例
 * @param {Boolean} visible 是否可见
 * @param {Number} exaggeration 地形夸张程度
 */
export const addTerrainAndSky = (map, visible = true, exaggeration = 1.5) => {
  if (!map) return

  // 添加地形数据源
  if (!map.getSource('mapbox-dem')) {
    map.addSource('mapbox-dem', {
      'type': 'raster-dem',
      'url': 'mapbox://mapbox.mapbox-terrain-dem-v1',
      'tileSize': 512,
      'maxzoom': 14
    })
  }

  // 设置地形
  if (visible) {
    map.setTerrain({ 'source': 'mapbox-dem', 'exaggeration': exaggeration })
  } else {
    map.setTerrain(null)
  }

  // 添加天空层
  if (!map.getLayer('sky')) {
    map.addLayer({
      'id': 'sky',
      'type': 'sky',
      'paint': {
        'sky-type': 'atmosphere',
        'sky-atmosphere-sun': [0.0, 0.0],
        'sky-atmosphere-sun-intensity': 15
      },
      'visibility': visible ? 'visible' : 'none'
    })
  } else {
    map.setLayoutProperty('sky', 'visibility', visible ? 'visible' : 'none')
  }
}

/**
 * 飞行到指定位置
 * @param {Object} map 地图实例
 * @param {Object} position 位置参数
 */
export const flyTo = (map, position = {}) => {
  if (!map) return

  const {
    lng = 114.367,
    lat = 30.54,
    zoom = 14,
    pitch = 45,
    bearing = 0,
    duration = 2000
  } = position

  map.flyTo({
    center: [lng, lat],
    zoom,
    pitch,
    bearing,
    duration,
    essential: true
  })
}

/**
 * 设置地图样式
 * @param {Object} map 地图实例
 * @param {String} style 样式URL
 * @returns {Promise} 样式加载后的Promise
 */
export const setMapStyle = (map, style) => {
  if (!map) return Promise.reject(new Error('地图实例不存在'))

  // 保存当前视角状态
  const currentCenter = map.getCenter()
  const currentZoom = map.getZoom()
  const currentPitch = map.getPitch()
  const currentBearing = map.getBearing()

  // 设置新样式
  map.setStyle(style)

  // 返回Promise，在样式加载完成后恢复视角
  return new Promise((resolve) => {
    map.once('style.load', () => {
      map.jumpTo({
        center: currentCenter,
        zoom: currentZoom,
        pitch: currentPitch,
        bearing: currentBearing
      })
      resolve(map)
    })
  })
}

/**
 * 切换地图3D视图
 * @param {Object} map 地图实例
 * @param {Boolean} enable3D 是否启用3D视图
 * @param {Number} duration 动画持续时间
 */
export const toggle3DView = (map, enable3D, duration = 1000) => {
  if (!map) return

  map.easeTo({
    pitch: enable3D ? 60 : 0,
    bearing: enable3D ? 30 : 0,
    duration
  })
}

/**
 * 格式化坐标数字
 * @param {Number} coord 坐标值
 * @param {Number} precision 精度
 * @returns {String} 格式化后的字符串
 */
export const formatCoordinate = (coord, precision = 6) => {
  return coord.toFixed(precision)
} 