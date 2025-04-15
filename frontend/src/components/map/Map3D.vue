<template>
    <div class="relative w-full h-full">
      <!-- 3D地图容器 -->
      <div ref="mapContainer" class="w-full h-full"></div>
      
      <!-- 加载指示器 -->
      <div v-if="isLoading" class="absolute inset-0 flex items-center justify-center bg-white bg-opacity-50 z-10">
        <n-spin size="large" />
      </div>
      
      <!-- 控制面板 -->
      <div class="absolute bottom-4 left-1/2 transform -translate-x-1/2 z-10">
        <div class="flex flex-row space-x-2 bg-white bg-opacity-80 rounded-full px-4 py-2 shadow-md">
          <!-- 图层控制 -->
          <n-popover trigger="click" placement="top">
            <template #trigger>
              <n-button circle secondary class="opacity-90">
                <template #icon>
                  <n-icon><layers-icon /></n-icon>
                </template>
              </n-button>
            </template>
            <div class="flex flex-col space-y-2 w-48 p-2">
              <div class="text-sm font-medium text-gray-700 mb-1">图层控制</div>
              <n-checkbox v-model:checked="showBuildingsLayer">3D建筑</n-checkbox>
              <n-checkbox v-model:checked="showTerrainLayer">地形</n-checkbox>
              <n-checkbox v-model:checked="showDronesLayer">无人机</n-checkbox>
              <n-checkbox v-model:checked="showEventsLayer">事件标记</n-checkbox>
              <n-checkbox v-model:checked="showNoFlyZonesLayer">禁飞区</n-checkbox>
              <n-checkbox v-model:checked="showFlightPathsLayer">飞行路径</n-checkbox>
            </div>
          </n-popover>
          
          <!-- 地图样式切换 -->
          <n-popover trigger="click" placement="top">
            <template #trigger>
              <n-button circle secondary class="opacity-90">
                <template #icon>
                  <n-icon>
                    <template v-if="isDarkMode">
                      <moon-icon />
                    </template>
                    <template v-else>
                      <sun-icon />
                    </template>
                  </n-icon>
                </template>
              </n-button>
            </template>
            <div class="flex flex-col space-y-2 w-48 p-2">
              <div class="text-sm font-medium text-gray-700 mb-1">地图样式</div>
              <n-radio-group v-model:value="mapStyle" @update:value="changeMapStyle">
                <n-space vertical>
                  <n-radio :value="MAP_STYLES.DARK">
                    <div class="flex items-center">
                      <moon-icon class="mr-1" />
                      黑夜模式
                    </div>
                  </n-radio>
                  <n-radio :value="MAP_STYLES.LIGHT">
                    <div class="flex items-center">
                      <sun-icon class="mr-1" />
                      白天模式
                    </div>
                  </n-radio>
                  <n-radio :value="MAP_STYLES.STREETS">
                    <div class="flex items-center">
                      <map-icon class="mr-1" />
                      街道模式
                    </div>
                  </n-radio>
                  <n-radio :value="MAP_STYLES.SATELLITE">
                    <div class="flex items-center">
                      <globe-icon class="mr-1" />
                      卫星模式
                    </div>
                  </n-radio>
                </n-space>
              </n-radio-group>
            </div>
          </n-popover>
          
          <!-- 视角控制 -->
          <n-button circle secondary class="opacity-90" @click="toggle3DView">
            <template #icon>
              <n-icon>
                <template v-if="is3DView">
                  <cube-icon />
                </template>
                <template v-else>
                  <map-icon />
                </template>
              </n-icon>
            </template>
          </n-button>
          
          <!-- 回到初始位置 -->
          <n-button circle secondary class="opacity-90" @click="resetView">
            <template #icon>
              <n-icon><home-icon /></n-icon>
            </template>
          </n-button>

          <!-- 跳转到武汉大学 -->
          <n-button circle secondary class="opacity-90" @click="flyToWhu">
            <template #icon>
              <n-icon><environment-icon /></n-icon>
            </template>
          </n-button>

          <!-- 绘制巡逻区域 -->
          <n-button 
            circle 
            :type="isDrawingPatrolArea ? 'primary' : 'default'" 
            secondary 
            class="opacity-90" 
            @click="toggleDrawingPatrolArea"
          >
            <template #icon>
              <n-icon><draw-icon /></n-icon>
            </template>
          </n-button>
        </div>
      </div>
      
      <!-- 坐标信息 -->
      <div class="absolute bottom-16 left-1/2 transform -translate-x-1/2 z-10 bg-opacity-70 p-2 rounded-md text-xs text-gray-700">
        <div>经度: {{ formatCoordinate(currentPosition.lng) }}</div>
        <div>纬度: {{ formatCoordinate(currentPosition.lat) }}</div>
        <div>海拔: {{ currentPosition.altitude?.toFixed(2) || '未知' }} 米</div>
      </div>
      
      <!-- 绘制模式提示与操作 -->
      <div v-if="isDrawingPatrolArea" class="absolute top-4 left-1/2 transform -translate-x-1/2 z-10 bg-white bg-opacity-90 p-3 rounded-md shadow-md text-sm flex flex-col items-center space-y-2">
        <div class="font-medium text-center">绘制巡逻区域</div>
        <div class="text-gray-600 text-xs">点击地图添加顶点，至少需要3个点。</div>
        <div v-if="patrolAreaPoints.length > 0" class="text-xs text-gray-500">已添加 {{ patrolAreaPoints.length }} 个顶点</div>
        <div class="flex space-x-2">
          <n-button size="small" type="primary" :disabled="patrolAreaPoints.length < 3" @click="completeDrawingPatrolArea">
            完成绘制
          </n-button>
          <n-button size="small" @click="cancelDrawingPatrolArea">
            取消
          </n-button>
          <n-button v-if="patrolAreaPoints.length > 0" size="small" tertiary @click="undoLastPatrolPoint">
            撤销上一点
          </n-button>
        </div>
      </div>

      <!-- 无人机信息弹窗 -->
      <div v-if="hoveredDroneInfo" class="absolute top-4 left-4 z-20 bg-white rounded-md shadow-md p-3 text-sm max-w-xs">
        <div class="flex items-center justify-between mb-2">
          <div class="font-medium">{{ hoveredDroneInfo.name }}</div>
          <n-tag size="small" :type="getDroneStatusType(hoveredDroneInfo.status)">
            {{ hoveredDroneInfo.status }}
          </n-tag>
        </div>
        <div class="text-gray-600 text-xs mb-1">ID: {{ hoveredDroneInfo.drone_id }}</div>
        <div class="flex items-center mt-1">
          <div class="text-gray-600 mr-2">Battery:</div>
          <n-progress 
            :percentage="hoveredDroneInfo.battery_level" 
            :color="getDroneBatteryColor(hoveredDroneInfo.battery_level)"
            :height="5"
            :show-indicator="false"
            class="w-24"
          />
          <span class="ml-2 text-xs">{{ hoveredDroneInfo.battery_level }}%</span>
        </div>
      </div>
    </div>
  </template>
  
  <script setup>
  import { ref, onMounted, onUnmounted, watch, computed, defineProps, defineEmits, nextTick } from 'vue'
  import { 
    BuildOutlined as LayersIcon, 
    AppstoreOutlined as CubeIcon, 
    HomeOutlined as HomeIcon, 
    GlobalOutlined as MapIcon,
    EnvironmentOutlined as EnvironmentIcon,
    BulbOutlined as SunIcon,
    CheckOutlined as MoonIcon,
    HighlightOutlined as DrawIcon
  } from '@vicons/antd'
  import { NProgress, NSpin, NButton, NIcon, NPopover, NCheckbox, NRadioGroup, NRadio, NSpace, NTag } from 'naive-ui'
  
  // 导入地图工具函数
  import {
    // 常量配置
    WHU_LOCATION, DEFAULT_VIEW_STATE, MAP_STYLES, DRONE_STATUS_UI_TYPE, MAP_INIT_TIMEOUT,
    // 地图初始化相关
    initializeMapbox, add3DBuildings, addTerrainAndSky, flyTo, setMapStyle, toggle3DView as toggleMapView, formatCoordinate,
    // 图层相关
    getDroneColor, getDroneBatteryColor, createDronesLayer, createFlightPathsLayer, createNoFlyZonesLayer, createEventsLayer, createPatrolAreaLayers,
    // Deck.gl相关
    initializeDeck, createDeckCanvas, updateDeckLayers,
    // 巡逻区域管理
    toggleDrawingMode, addPatrolPoint, removeLastPoint, completePatrolArea, isValidPatrolArea
  } from '@/utils/map'
  
  // Props and emits
  const props = defineProps({
    drones: {
      type: Array,
      default: () => []
    },
    events: {
      type: Array,
      default: () => []
    },
    noFlyZones: {
      type: Array,
      default: () => []
    },
    flightPaths: {
      type: Array,
      default: () => []
    },
    showLiveUpdates: {
      type: Boolean,
      default: true
    },
    centerOnSelected: {
      type: Boolean,
      default: false
    },
    selectedDroneId: {
      type: String,
      default: null
    },
    initialView: {
      type: Object,
      default: () => null
    },
    showDrones: {
      type: Boolean,
      default: true
    }
  })
  
  const emit = defineEmits([
    'drone-clicked', 
    'map-clicked', 
    'map-loaded', 
    'patrol-area-drawn'
  ])
  
  // Map configuration
  const MAPBOX_TOKEN = import.meta.env.VITE_MAPBOX_TOKEN || 'pk.eyJ1IjoibXV0aW5nIiwiYSI6ImNsdGo1OHlkZTAwbmIybHBveHkyNHl6bmgifQ.PtIzPKQRLmLUXIaUqw1XNw'
  
  // 计算初始视图状态
  const initialViewState = computed(() => ({
    longitude: props.initialView ? props.initialView.center[0] : DEFAULT_VIEW_STATE.longitude,
    latitude: props.initialView ? props.initialView.center[1] : DEFAULT_VIEW_STATE.latitude,
    zoom: props.initialView ? props.initialView.zoom : DEFAULT_VIEW_STATE.zoom,
    pitch: DEFAULT_VIEW_STATE.pitch,
    bearing: DEFAULT_VIEW_STATE.bearing
  }))
  
  // Map and deck.gl instances
  let map = null
  let deck = null
  
  // Component state
  const mapContainer = ref(null)
  const isLoading = ref(true)
  const is3DView = ref(true)
  const currentPosition = ref({ 
    lng: initialViewState.value.longitude, 
    lat: initialViewState.value.latitude, 
    altitude: 0 
  })
  const hoveredDroneInfo = ref(null)
  const clickedDroneId = ref(null)
  const mapStyle = ref(import.meta.env.VITE_DEFAULT_MAP_STYLE || MAP_STYLES.STREETS)
  const isDarkMode = computed(() => mapStyle.value.includes('dark'))
  
  // 巡逻区域绘制相关状态
  const isDrawingPatrolArea = ref(false)
  const patrolAreaPoints = ref([])
  
  // Layer controls
  const showBuildingsLayer = ref(true)
  const showTerrainLayer = ref(true)
  const showDronesLayer = ref(props.showDrones)
  const showEventsLayer = ref(true)
  const showNoFlyZonesLayer = ref(true)
  const showFlightPathsLayer = ref(true)
  
  // Watch for props changes and update layers
  watch(() => [
    props.drones, 
    props.events, 
    props.noFlyZones, 
    props.flightPaths,
    showDronesLayer.value,
    showEventsLayer.value,
    showNoFlyZonesLayer.value,
    showFlightPathsLayer.value,
    isDrawingPatrolArea.value,
    patrolAreaPoints.value,
    props.selectedDroneId
  ], () => {
    if (deck) renderDeckLayers()
  }, { deep: true })
  
  // Watch for selected drone changes to center map
  watch(() => props.selectedDroneId, (newVal) => {
    if (newVal && props.centerOnSelected) {
      const drone = props.drones.find(d => d.drone_id === newVal)
      if (drone && drone.current_location && map) {
        centerMapOnDrone(drone)
      }
    }
  })
  
  // Watch showDrones prop change and update internal state
  watch(() => props.showDrones, (newVal) => {
    showDronesLayer.value = newVal
  })
  
  // Watch layers visibility changes
  watch([showBuildingsLayer, showTerrainLayer], () => {
    if (!map) return
    
    // 控制3D建筑层可见性
      if (map.getLayer('building-extrusion')) {
        map.setLayoutProperty(
          'building-extrusion',
          'visibility',
          showBuildingsLayer.value ? 'visible' : 'none'
        )
      }
      
    // 控制地形和天空层可见性
      if (map.getSource('mapbox-dem')) {
      // 更新天空层
        if (map.getLayer('sky')) {
            map.setLayoutProperty(
              'sky',
              'visibility',
              showTerrainLayer.value ? 'visible' : 'none'
            )
        }
      
      // 更新地形
        if (showTerrainLayer.value) {
          map.setTerrain({ source: 'mapbox-dem', exaggeration: 1.5 })
        } else {
          map.setTerrain(null)
      }
    }
  })
  
  // Get drone status tag type
  const getDroneStatusType = (status) => {
    return DRONE_STATUS_UI_TYPE[status] || 'default'
  }
  
  // Center map on a specific drone
  const centerMapOnDrone = (drone) => {
    if (!map || !drone.current_location) return
    
    const coords = drone.current_location.coordinates
    if (coords && coords.length >= 2) {
      flyTo(map, {
        lng: coords[0],
        lat: coords[1],
        zoom: 15,
        pitch: 60,
        bearing: 0,
        duration: 1500
      })
    }
  }
  
  // Initialize map
  const initializeMap = async () => {
    if (!mapContainer.value) {
      console.error('Cannot initialize map: mapContainer ref is not available')
      isLoading.value = false
      return
    }
    
    isLoading.value = true
    let initTimeout
    
    try {
      console.log('Initializing map with token:', MAPBOX_TOKEN)
      
      // 设置超时处理
      initTimeout = setTimeout(() => {
        if (isLoading.value) {
          console.warn('Map initialization timeout')
          isLoading.value = false
          emit('map-loaded', { success: false, error: 'timeout' })
        }
      }, MAP_INIT_TIMEOUT)
      
      // 初始化地图
      map = initializeMapbox(mapContainer.value, {
        mapboxToken: MAPBOX_TOKEN,
        style: mapStyle.value,
        center: [initialViewState.value.longitude, initialViewState.value.latitude],
        zoom: initialViewState.value.zoom,
        pitch: initialViewState.value.pitch,
        bearing: initialViewState.value.bearing
      })
      
      // 监听地图加载事件
      map.on('load', async () => {
        console.log('Map loaded successfully')
        clearTimeout(initTimeout)
        isLoading.value = false
        
        try {
          // 添加3D建筑和地形
          add3DBuildings(map, showBuildingsLayer.value)
          addTerrainAndSky(map, showTerrainLayer.value)
          
          // 设置地图事件
          setupMapEvents()
          
          // 初始化Deck.gl
          setupDeckGL()
          
          // 添加初始动画
          initializeWithAnimation()
          
          // 通知父组件地图已加载
          emit('map-loaded', { success: true })
        } catch (error) {
          console.error('Error initializing map layers:', error)
          emit('map-loaded', { success: false, error: error.message })
        }
      })
      
      // 监听地图错误
      map.on('error', (e) => {
        console.error('Map error:', e)
        
        // 尝试使用备用样式
        if (e.error && e.error.status === 401) {
          console.log('Trying fallback style')
          try {
            map.setStyle(MAP_STYLES.STREETS)
          } catch (styleError) {
            console.error('Failed to set fallback style:', styleError)
          }
        }
      })
    } catch (error) {
      console.error('Map initialization error:', error)
      clearTimeout(initTimeout)
      isLoading.value = false
      emit('map-loaded', { success: false, error: error.message })
    }
  }
  
  // 设置地图事件
  const setupMapEvents = () => {
    if (!map) return
    
    // 鼠标移动更新坐标
    map.on('mousemove', (e) => {
      currentPosition.value = {
        lng: e.lngLat.lng,
        lat: e.lngLat.lat,
        altitude: map.queryTerrainElevation(e.lngLat) || 0
      }
    })
    
    // 地图点击事件
    map.on('click', (e) => {
      const coordinates = {
        lng: e.lngLat.lng,
        lat: e.lngLat.lat,
        altitude: map.queryTerrainElevation(e.lngLat) || 0
      }
      
      // 如果在绘制模式，则添加点位
      if (isDrawingPatrolArea.value) {
        patrolAreaPoints.value = addPatrolPoint(
          patrolAreaPoints.value,
          coordinates.lng,
          coordinates.lat
        )
      } else {
        // 正常点击事件，通知父组件
        emit('map-clicked', coordinates)
      }
    })
  }
  
  // 设置Deck.gl
  const setupDeckGL = () => {
    if (!map || !mapContainer.value) return
    
    try {
      // 创建Deck.gl画布
      createDeckCanvas(mapContainer.value)
      
      // 初始化Deck.gl
      deck = initializeDeck({
        map,
        initialViewState: initialViewState.value,
        onHover: ({ object }) => {
            if (!object) {
              hoveredDroneInfo.value = null
              return null
            }
            
            if (object.type === 'drone') {
              hoveredDroneInfo.value = object
            }
            
            return null
          },
          onClick: ({ object }) => {
            if (!object) return
            
            if (object.type === 'drone') {
              clickedDroneId.value = object.drone_id
              emit('drone-clicked', object.drone_id)
            }
          }
        })
        
      // 渲染初始图层
        renderDeckLayers()
    } catch (error) {
      console.error('Error setting up Deck.gl:', error)
    }
  }
  
  // 渲染Deck.gl图层
  const renderDeckLayers = () => {
    if (!deck) return
    
    const layers = []
    
    // 添加无人机图层
    if (showDronesLayer.value && props.drones.length > 0) {
      layers.push(createDronesLayer(props.drones, props.selectedDroneId))
    }
    
    // 添加飞行路径图层
    if (showFlightPathsLayer.value && props.flightPaths.length > 0) {
      layers.push(createFlightPathsLayer(props.flightPaths))
    }
    
    // 添加禁飞区图层
    if (showNoFlyZonesLayer.value && props.noFlyZones.length > 0) {
      layers.push(createNoFlyZonesLayer(props.noFlyZones))
    }
    
    // 添加事件图层
    if (showEventsLayer.value && props.events.length > 0) {
      layers.push(createEventsLayer(props.events))
    }
    
    // 添加巡逻区域绘制图层
    const patrolLayers = createPatrolAreaLayers(
      isDrawingPatrolArea.value,
      patrolAreaPoints.value
    )
    layers.push(...patrolLayers)
    
    // 更新图层
    updateDeckLayers(deck, layers)
  }
  
  // 重置视图
  const resetView = () => {
    if (!map) return
    
    flyTo(map, {
      lng: DEFAULT_VIEW_STATE.longitude,
      lat: DEFAULT_VIEW_STATE.latitude,
      zoom: DEFAULT_VIEW_STATE.zoom,
      pitch: DEFAULT_VIEW_STATE.pitch,
      bearing: DEFAULT_VIEW_STATE.bearing,
      duration: 1000
    })
  }
  
  // 切换3D视图
  const toggle3DView = () => {
    is3DView.value = !is3DView.value
    if (map) {
      toggleMapView(map, is3DView.value)
    }
  }
  
  // 切换地图样式
  const changeMapStyle = async (style) => {
    if (!map) return
    
    try {
      console.log('Changing map style:', style)
      const updatedMap = await setMapStyle(map, style)
      
      // 重新添加地图图层
      await nextTick()
      add3DBuildings(updatedMap, showBuildingsLayer.value)
      addTerrainAndSky(updatedMap, showTerrainLayer.value)
      
      // 更新黑暗模式状态
      mapStyle.value = style
    } catch (error) {
      console.error('Error changing map style:', error)
    }
  }
  
  // 飞行到武汉大学
  const flyToWhu = () => {
    if (!map) return
    flyTo(map, WHU_LOCATION)
  }
  
  // 初始动画
  const initializeWithAnimation = () => {
    if (!map) return
      
    // 先跳转到远处
      map.jumpTo({
      center: [114.36, 30.52],
      zoom: 10,
        pitch: 0,
        bearing: 0
    })
      
    // 然后飞行到武汉大学
      setTimeout(() => {
      flyToWhu()
    }, 1000)
    }
  
  // 巡逻状态
  const patrolStatus = ref(false)

  // 开始无人机巡逻
  const startDronePatrol = (drones) => {
    if (!map) {
      console.warn('无法开始巡逻：地图未初始化')
      return
    }
    
    console.log('开始无人机巡逻:', drones)
    patrolStatus.value = true
    renderDeckLayers()
  }
  
  // 停止无人机巡逻
  const stopDronePatrol = (droneIds) => {
    if (!map) {
      console.warn('无法停止巡逻：地图未初始化')
      return
    }
    
    console.log('停止无人机巡逻:', droneIds)
    patrolStatus.value = false
    renderDeckLayers()
  }
  
  // 获取巡逻状态
  const getPatrolStatus = () => patrolStatus.value
  
  // 切换巡逻区域绘制模式
  const toggleDrawingPatrolArea = () => {
    isDrawingPatrolArea.value = !isDrawingPatrolArea.value
    toggleDrawingMode(map, isDrawingPatrolArea.value, () => {
      patrolAreaPoints.value = []
    })
  }
  
  // 完成巡逻区域绘制
  const completeDrawingPatrolArea = () => {
    if (isValidPatrolArea(patrolAreaPoints.value)) {
      const finalPolygon = completePatrolArea(patrolAreaPoints.value)
      emit('patrol-area-drawn', finalPolygon)
      isDrawingPatrolArea.value = false
      patrolAreaPoints.value = []
      map.getCanvas().style.cursor = ''
    } else {
      console.warn('需要至少3个点来完成绘制')
    }
  }

  // 取消绘制
  const cancelDrawingPatrolArea = () => {
    isDrawingPatrolArea.value = false
    patrolAreaPoints.value = []
    map.getCanvas().style.cursor = ''
  }
  
  // 撤销上一个点
  const undoLastPatrolPoint = () => {
    patrolAreaPoints.value = removeLastPoint(patrolAreaPoints.value)
    }
  
  // Component lifecycle hooks
  onMounted(() => {
    console.log('Map3D component mounted')
    
    // 延迟初始化确保DOM已准备好
    setTimeout(() => {
      if (mapContainer.value) {
        initializeMap()
      } else {
        console.error('Map container ref not found')
        isLoading.value = false
      }
    }, 100)
  })
  
  onUnmounted(() => {
    // 清理资源
    if (map) {
      map.remove()
      map = null
    }
    
    if (deck) {
      deck.finalize()
      deck = null
    }
  })
  
  // 暴露公共方法
  defineExpose({
    centerOnDrone: centerMapOnDrone,
    resetView,
    toggleView: toggle3DView,
    flyTo: (position) => flyTo(map, position),
    flyToWhu,
    startDronePatrol,
    stopDronePatrol,
    getPatrolStatus,
    changeMapStyle,
    startDrawingPatrolArea: toggleDrawingPatrolArea,
    cancelDrawingPatrolArea
  })
  </script>
  
  <style scoped>
  .mapboxgl-canvas {
    outline: none;
  }
  
  /* deck.gl canvas occupies the same position as mapbox */
  #deck-canvas {
    z-index: 2;
  }
  </style>