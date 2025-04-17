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
              <n-checkbox v-model:checked="showPatrolAreasLayer">巡逻区域</n-checkbox>
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

          <!-- 绘制巡逻区域 - 仅在任务创建模式下显示 -->
          <n-button 
            v-if="taskStore.isDrawingPatrolArea"
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
      
      <!-- 巡逻区域信息弹窗 -->
      <div v-if="hoveredPatrolArea" class="absolute top-4 left-4 z-20 bg-white rounded-md shadow-md p-3 text-sm max-w-xs">
        <div class="flex items-center justify-between mb-2">
          <div class="font-medium">{{ hoveredPatrolArea.taskName || '巡逻任务' }}</div>
          <n-tag size="small" type="info">巡逻区域</n-tag>
        </div>
        <div v-if="hoveredPatrolArea.taskId" class="text-gray-600 text-xs mb-1">任务ID: {{ hoveredPatrolArea.taskId }}</div>
        <div v-if="hoveredPatrolArea.speed" class="text-gray-600 text-xs mb-1">速度: {{ hoveredPatrolArea.speed }}米/秒</div>
        <div v-if="hoveredPatrolArea.createdAt" class="text-gray-600 text-xs mb-1">
          创建时间: {{ new Date(hoveredPatrolArea.createdAt).toLocaleString() }}
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
  import { useTaskStore } from '@/store/task'
  
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
  import { PolygonLayer, ScatterplotLayer } from '@deck.gl/layers'
  
  // 初始化任务store
  const taskStore = useTaskStore()
  
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
    },
    showPatrolAreas: {
      type: Boolean,
      default: true
    }
  })
  
  const emit = defineEmits([
    'drone-clicked', 
    'map-clicked', 
    'map-loaded', 
    'patrol-area-drawn',
    'patrol-area-clicked'
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
  const hoveredPatrolArea = ref(null)
  const clickedDroneId = ref(null)
  const mapStyle = ref(import.meta.env.VITE_DEFAULT_MAP_STYLE || MAP_STYLES.STREETS)
  const isDarkMode = computed(() => mapStyle.value.includes('dark'))
  
  // 存储已完成的巡逻区域
  const completedPatrolAreas = ref([])
  
  // 临时巡逻区域 - 用于完成绘制但还未正式创建任务时
  const tempPatrolArea = ref(null)
  
  // 巡逻区域绘制相关状态 - 使用计算属性与store联动
  const isDrawingPatrolArea = computed({
    get: () => taskStore.isDrawingPatrolArea,
    set: (value) => {
      if (!value) {
        taskStore.cancelDrawingPatrolArea()
      }
    }
  })
  
  const patrolAreaPoints = computed(() => taskStore.patrolAreaCoordinates)
  
  // Layer controls
  const showBuildingsLayer = ref(true)
  const showTerrainLayer = ref(true)
  const showDronesLayer = ref(props.showDrones)
  const showEventsLayer = ref(true)
  const showPatrolAreasLayer = ref(props.showPatrolAreas)
  
  // Watch for props changes and update layers
  watch(() => [
    props.drones, 
    props.events, 
    props.noFlyZones, 
    props.flightPaths,
    showDronesLayer.value,
    showEventsLayer.value,
    showPatrolAreasLayer.value,
    taskStore.isDrawingPatrolArea,
    taskStore.patrolAreaCoordinates,
    taskStore.patrolAreaGeoJSON,
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
  
  // Watch showPatrolAreas prop change and update internal state
  watch(() => props.showPatrolAreas, (newVal) => {
    showPatrolAreasLayer.value = newVal
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
      if (taskStore.isDrawingPatrolArea) {
        // 使用store添加点位
        taskStore.addPatrolAreaPoint([coordinates.lng, coordinates.lat])
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
            hoveredPatrolArea.value = null
              return null
            }
            
            if (object.type === 'drone') {
              hoveredDroneInfo.value = object
            hoveredPatrolArea.value = null
          } else if (object.taskId || object.taskFormId) {
            // 识别为巡逻区域
            hoveredPatrolArea.value = object
            hoveredDroneInfo.value = null
            }
            
            return null
          },
          onClick: ({ object }) => {
            if (!object) return
            
            if (object.type === 'drone') {
              clickedDroneId.value = object.drone_id
              emit('drone-clicked', object.drone_id)
          } else if (object.taskId || object.taskFormId) {
            // 点击巡逻区域，触发事件通知父组件
            console.log('巡逻区域被点击:', object)
            emit('patrol-area-clicked', object.taskId || object.taskFormId)
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
    
    // 添加事件图层
    if (showEventsLayer.value && props.events.length > 0) {
      layers.push(createEventsLayer(props.events))
    }
    
    // 添加临时巡逻区域图层 - 绘制完成但未创建任务时
    if (showPatrolAreasLayer.value && tempPatrolArea.value && tempPatrolArea.value.geojson && 
        tempPatrolArea.value.geojson.geometry && 
        tempPatrolArea.value.geojson.geometry.coordinates) {
      layers.push(
        new PolygonLayer({
          id: 'temp-patrol-area',
          data: [{
            polygon: tempPatrolArea.value.geojson.geometry.coordinates,
            color: [255, 165, 0, 100], // 橙色半透明填充，表示临时状态
            taskFormId: tempPatrolArea.value.taskFormId
          }],
          pickable: true,
          stroked: true,
          filled: true,
          wireframe: false,
          lineWidthMinPixels: 2,
          getPolygon: d => d.polygon,
          getFillColor: d => d.color,
          getLineColor: [255, 165, 0, 200], // 橙色边框
          getLineWidth: 2
        })
      )
      
      // 显示临时区域的点
      if (tempPatrolArea.value.points && tempPatrolArea.value.points.length > 0) {
      layers.push(
        new ScatterplotLayer({
            id: 'temp-patrol-area-points',
            data: tempPatrolArea.value.points.map((p, index) => ({ position: p, index })),
          pickable: false,
          stroked: true,
          filled: true,
          radiusScale: 1,
          radiusMinPixels: 4,
          radiusMaxPixels: 8,
          lineWidthMinPixels: 1,
          getPosition: d => d.position,
            getFillColor: [255, 165, 0, 200], // 橙色
          getLineColor: [255, 255, 255],
          getRadius: 5,
        })
        )
      }
    }
    
    // 添加已完成的巡逻区域图层
    if (showPatrolAreasLayer.value && completedPatrolAreas.value.length > 0) {
      // 为每个完成的巡逻区域创建一个多边形图层
      completedPatrolAreas.value.forEach((area, index) => {
        if (area.geojson && area.geojson.geometry && area.geojson.geometry.coordinates) {
          // 生成唯一的图层ID
          const layerId = `patrol-area-${area.taskId || area.taskFormId || index}`;
          
          // 使用区域自定义颜色或根据任务状态设置默认颜色
          const fillColor = area.fillColor || [59, 130, 246, 100]; // 默认蓝色
          const strokeColor = area.strokeColor || [59, 130, 246, 200]; // 默认蓝色边框
          
          // 如果是高亮区域，使用更醒目的边框宽度
          const lineWidth = area.isHighlighted ? 4 : 2;
          
          console.debug(`渲染巡逻区域: ${area.taskName || '未命名区域'} (ID: ${layerId})`, 
                       `状态: ${area.status || '未知'}, 颜色: ${fillColor}`,
                       area.isHighlighted ? '高亮显示' : '');
          
          // 创建区域多边形图层
          layers.push(
            new PolygonLayer({
              id: layerId,
              data: [{
                polygon: area.geojson.geometry.coordinates,
                color: fillColor,
                taskId: area.taskId || area.taskFormId,
                taskName: area.taskName || '巡逻任务',
                status: area.status || 'unknown',
                isHighlighted: area.isHighlighted
              }],
              pickable: true,
              stroked: true,
              filled: true,
              wireframe: false,
              lineWidthMinPixels: lineWidth,
              getPolygon: d => d.polygon,
              getFillColor: d => d.color,
              getLineColor: strokeColor,
              getLineWidth: d => d.isHighlighted ? 4 : 2,
              // 使高亮区域的z轴稍高一点，确保边框不被其他区域遮挡
              getElevation: d => d.isHighlighted ? 5 : 0
            })
          );
          
          // 可选：在区域中心添加标签
          if (area.taskName) {
            // 计算区域中心点
            const coords = area.geojson.geometry.coordinates[0];
            if (coords && coords.length > 2) {
              // 简单计算多边形中心点（不是质心，但足够显示标签）
              let centerX = 0, centerY = 0;
              coords.forEach(coord => {
                if (coord && coord.length >= 2) {
                  centerX += coord[0];
                  centerY += coord[1];
                }
              });
              centerX /= coords.length;
              centerY /= coords.length;
              
              // TODO: 添加文字标签图层（如果需要）
            }
          }
        }
      });
    }
    
    // 添加巡逻区域绘制图层 - 使用taskStore中的数据
    if (showPatrolAreasLayer.value && taskStore.isDrawingPatrolArea) {
      const patrolLayers = createPatrolAreaLayers(
        taskStore.isDrawingPatrolArea,
        taskStore.patrolAreaCoordinates,
        taskStore.patrolAreaGeoJSON
      )
      layers.push(...patrolLayers)
    }
    
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
  
  // 切换巡逻区域绘制模式 - 更新为使用store
  const toggleDrawingPatrolArea = () => {
    if (taskStore.isDrawingPatrolArea) {
      // 取消绘制
      taskStore.cancelDrawingPatrolArea()
      // 更新UI
      map.getCanvas().style.cursor = ''
    } else {
      // 不允许从地图直接开始绘制，需要从任务表单触发
      console.warn('必须从巡逻任务表单开始绘制操作')
    }
    renderDeckLayers()
  }
  
  /**
   * 添加巡逻区域到地图
   * @param {Object} patrolArea 巡逻区域对象
   * @param {Boolean} isConfirmed 是否是已确认的任务
   */
  const addPatrolAreaToMap = (patrolArea, isConfirmed = true) => {
    console.log('Map3D.addPatrolAreaToMap 被调用:', JSON.stringify(patrolArea).substring(0, 200) + '...');
    
    if (!map) {
      console.error('地图未初始化，无法添加巡逻区域');
      return;
    }
    
    if (!patrolArea) {
      console.error('巡逻区域参数为空');
      return;
    }
    
    if (!patrolArea.geojson) {
      console.error('巡逻区域缺少geojson属性:', patrolArea);
      return;
    }
    
    try {
      // 检查并处理GeoJSON数据
      let geojsonData = patrolArea.geojson;
      let coordinates = null;
      
      // 尝试解析不同格式的GeoJSON
      if (geojsonData.coordinates) {
        coordinates = geojsonData.coordinates;
        console.log('从geojson.coordinates中获取坐标');
      } else if (geojsonData.geometry && geojsonData.geometry.coordinates) {
        coordinates = geojsonData.geometry.coordinates;
        console.log('从geojson.geometry.coordinates中获取坐标');
      } else if (typeof geojsonData === 'string') {
        // 尝试解析字符串形式的GeoJSON
        try {
          const parsedData = JSON.parse(geojsonData);
          if (parsedData.coordinates) {
            coordinates = parsedData.coordinates;
            console.log('从解析的JSON字符串中获取坐标');
          } else if (parsedData.geometry && parsedData.geometry.coordinates) {
            coordinates = parsedData.geometry.coordinates;
            console.log('从解析的JSON字符串的geometry中获取坐标');
          } else {
            console.error('无法从解析的JSON字符串中获取坐标数据:', parsedData);
            return;
          }
        } catch (parseError) {
          console.error('GeoJSON字符串解析失败:', parseError);
          return;
        }
      } else {
        console.error('无法从GeoJSON中获取坐标数据:', geojsonData);
        return;
      }
      
      // 记录坐标数据类型，便于调试
      console.log('坐标数据类型:', Array.isArray(coordinates) ? 'Array' : typeof coordinates);
      if (Array.isArray(coordinates) && coordinates.length > 0) {
        console.log('第一级元素类型:', Array.isArray(coordinates[0]) ? 'Array' : typeof coordinates[0]);
        if (Array.isArray(coordinates[0]) && coordinates[0].length > 0) {
          console.log('第二级元素类型:', Array.isArray(coordinates[0][0]) ? 'Array' : typeof coordinates[0][0]);
        }
      }
      
      // 确保坐标数据是正确的多边形格式
      let polygonCoordinates = null;
      
      if (Array.isArray(coordinates)) {
        if (Array.isArray(coordinates[0]) && Array.isArray(coordinates[0][0])) {
          // 格式: [[[lng1,lat1], [lng2,lat2], ...]] - 已经是标准多边形格式
          polygonCoordinates = coordinates;
          console.log('坐标已经是标准多边形格式');
        } else if (Array.isArray(coordinates[0]) && typeof coordinates[0][0] === 'number') {
          // 格式: [[lng1,lat1], [lng2,lat2], ...] - 简单坐标数组，需要包装
          polygonCoordinates = [coordinates];
          console.log('将简单坐标数组转换为多边形格式');
        } else if (typeof coordinates[0] === 'number' && coordinates.length >= 6 && coordinates.length % 2 === 0) {
          // 格式: [lng1,lat1,lng2,lat2,...] - 扁平坐标，需要处理
          const pointPairs = [];
          for (let i = 0; i < coordinates.length; i += 2) {
            pointPairs.push([coordinates[i], coordinates[i+1]]);
          }
          polygonCoordinates = [pointPairs];
          console.log('将扁平坐标数组转换为多边形格式');
        } else {
          console.error('无法识别的坐标数组格式:', coordinates);
          return;
        }
      } else {
        console.error('坐标不是有效数组:', coordinates);
        return;
      }
      
      // 打印处理后的坐标
      console.log('处理后的多边形坐标数据:', JSON.stringify(polygonCoordinates).substring(0, 200) + '...');
      
      // 检查坐标是否足够
      if (!polygonCoordinates[0] || polygonCoordinates[0].length < 3) {
        console.error('坐标点不足(至少需要3个点):', polygonCoordinates[0] ? polygonCoordinates[0].length : 0);
        return;
      }
      
      // 检查多边形是否闭合，如果不是，添加闭合点
      const firstPoint = polygonCoordinates[0][0];
      const lastPoint = polygonCoordinates[0][polygonCoordinates[0].length - 1];
      
      if (firstPoint[0] !== lastPoint[0] || firstPoint[1] !== lastPoint[1]) {
        console.log('多边形未闭合，添加闭合点');
        polygonCoordinates[0].push([...firstPoint]);
      }
      
      // 如果是确认的任务，则添加到已完成巡逻区域列表
      if (isConfirmed) {
        // 定义填充颜色和边框颜色
        // 高亮时只改变边框，不改变填充颜色
        let fillColor = patrolArea.color || [59, 130, 246, 100]; // 使用自定义颜色或默认蓝色填充
        let strokeColor = [59, 130, 246, 200]; // 默认蓝色边框
        
        if (patrolArea.isHighlighted) {
          // 只改变边框颜色为白色或亮色，填充颜色保持不变
          strokeColor = [255, 255, 255, 255]; // 高亮时使用白色边框
        }
        
        // 清除临时巡逻区域（不影响已确认的区域）
        tempPatrolArea.value = null;
        
        // 创建完整的patrolArea对象
        const processedArea = {
          ...patrolArea,
          geojson: {
            type: 'Feature',
            geometry: {
              type: 'Polygon',
              coordinates: polygonCoordinates
            },
            properties: {
              taskId: patrolArea.taskId || 'unknown',
              taskName: patrolArea.taskName || '未命名巡逻区域'
            }
          },
          addedAt: new Date(),
          fillColor,
          strokeColor,
          isHighlighted: patrolArea.isHighlighted
        };
        
        console.log('处理后的巡逻区域添加到地图:', JSON.stringify(processedArea.geojson).substring(0, 200) + '...');
        
        // 检查是否已存在相同ID的区域，如果存在则更新而不是添加
        const existingIndex = completedPatrolAreas.value.findIndex(
          area => area.taskId === patrolArea.taskId
        );
        
        if (existingIndex >= 0) {
          console.log(`更新已存在的巡逻区域 ID:${patrolArea.taskId}`);
          // 保留其他属性，只更新高亮状态和边框颜色
          completedPatrolAreas.value[existingIndex] = {
            ...completedPatrolAreas.value[existingIndex],
            strokeColor,
            isHighlighted: patrolArea.isHighlighted
          };
        } else {
          console.log(`添加新巡逻区域 ID:${patrolArea.taskId}`);
          completedPatrolAreas.value.push(processedArea);
        }
        
        // 重新渲染图层
        nextTick(() => {
          renderDeckLayers();
        });
      } else {
        // 如果不是确认的任务，只设置为临时巡逻区域
        tempPatrolArea.value = {
          ...patrolArea,
          geojson: {
            type: 'Feature',
            geometry: {
              type: 'Polygon',
              coordinates: polygonCoordinates
            },
            properties: {
              taskId: patrolArea.taskId || 'temp',
              taskName: patrolArea.taskName || '临时巡逻区域'
            }
          },
          isTemporary: true,
          createdAt: new Date()
        };
        
        console.log('临时巡逻区域已更新');
        
        // 重新渲染图层
        nextTick(() => {
          renderDeckLayers();
        });
      }
    } catch (error) {
      console.error('添加巡逻区域时出错:', error);
    }
  }
  
  /**
   * 清除所有巡逻区域
   */
  const clearPatrolAreas = () => {
    tempPatrolArea.value = null;
    completedPatrolAreas.value = [];
    renderDeckLayers();
  }
  
  // 完成巡逻区域绘制 - 更新为使用store
  const completeDrawingPatrolArea = () => {
    if (taskStore.patrolAreaCoordinates.length >= 3) {
      // 完成绘制，获取GeoJSON结果
      const result = taskStore.completePatrolArea()
      
      // 设置为临时巡逻区域，等待任务创建完成后再永久保存
      tempPatrolArea.value = {
        ...result,
        isTemporary: true,
        createdAt: new Date()
      }
      
      // 派发事件
      emit('patrol-area-drawn', result)
      
      // 恢复光标
      map.getCanvas().style.cursor = ''
    } else {
      console.warn('需要至少3个点来完成绘制')
    }
  }

  // 取消绘制 - 更新为使用store
  const cancelDrawingPatrolArea = () => {
    // 取消绘制
    taskStore.cancelDrawingPatrolArea()
    
    // 清除临时巡逻区域
    tempPatrolArea.value = null
    
    // 恢复光标
    map.getCanvas().style.cursor = ''
    
    // 刷新图层
    renderDeckLayers()
  }
  
  // 撤销上一个点
  const undoLastPatrolPoint = () => {
    if (taskStore.patrolAreaCoordinates.length > 0) {
      // 使用 taskStore 的方法移除最后一个点
      const removed = taskStore.removeLastPatrolAreaPoint();
      if (removed) {
        // 视图更新会通过 watch 自动触发
      }
    }
  }
  
  // 开始绘制巡逻区域 - 由父组件调用
  const startDrawingPatrolArea = (taskFormId) => {
    if (!map) {
      console.warn('地图未初始化，无法开始绘制')
      return
    }
    
    // 使用store开始绘制
    taskStore.startDrawingPatrolArea(taskFormId)
    // 更新光标
    map.getCanvas().style.cursor = 'crosshair'
    // 渲染图层
    renderDeckLayers()
  }
  
  /**
   * 清除临时巡逻区域
   */
  const clearTempPatrolArea = () => {
    tempPatrolArea.value = null;
    renderDeckLayers();
  }
  
  /**
   * 清除所有区域的高亮状态
   */
  const clearHighlightedAreas = () => {
    // 遍历所有巡逻区域，清除高亮标志
    if (completedPatrolAreas.value && completedPatrolAreas.value.length > 0) {
      completedPatrolAreas.value.forEach(area => {
        if (area.isHighlighted) {
          area.isHighlighted = false;
          // 只恢复边框样式，保持填充颜色不变
          area.strokeColor = [59, 130, 246, 200]; // 恢复默认蓝色边框
        }
      });
      
      // 重新渲染图层
      nextTick(() => {
        renderDeckLayers();
      });
      
      console.log('已清除所有区域的高亮状态');
    }
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
    
    // 确保绘制模式被取消
    if (taskStore.isDrawingPatrolArea) {
      taskStore.cancelDrawingPatrolArea()
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
    startDrawingPatrolArea,
    cancelDrawingPatrolArea,
    completeDrawingPatrolArea,
    addPatrolAreaToMap,
    clearTempPatrolArea,
    clearPatrolAreas,
    clearHighlightedAreas
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