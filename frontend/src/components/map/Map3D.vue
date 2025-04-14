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
                  <n-radio value="mapbox://styles/mapbox/dark-v11">
                    <div class="flex items-center">
                      <moon-icon class="mr-1" />
                      黑夜模式
                    </div>
                  </n-radio>
                  <n-radio value="mapbox://styles/mapbox/light-v11">
                    <div class="flex items-center">
                      <sun-icon class="mr-1" />
                      白天模式
                    </div>
                  </n-radio>
                  <n-radio value="mapbox://styles/mapbox/streets-v12">
                    <div class="flex items-center">
                      <map-icon class="mr-1" />
                      街道模式
                    </div>
                  </n-radio>
                  <n-radio value="mapbox://styles/mapbox/satellite-streets-v12">
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

      <!-- Selected drone info popup -->
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
  import mapboxgl from 'mapbox-gl'
  import { Deck } from '@deck.gl/core'
  import { ScatterplotLayer, PathLayer, PolygonLayer, IconLayer } from '@deck.gl/layers'
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
  console.log('Mapbox Token:', MAPBOX_TOKEN)
  
  // 武汉大学位置
  const WHU_LOCATION = {
    longitude: 114.367, 
    latitude: 30.54,
    zoom: 15,
    pitch: 60,
    bearing: 30
  }
  
  const INITIAL_VIEW_STATE = {
    longitude: props.initialView ? props.initialView.center[0] : 114.367,
    latitude: props.initialView ? props.initialView.center[1] : 30.54,
    zoom: props.initialView ? props.initialView.zoom : 14,
    pitch: 45,
    bearing: 0
  }
  
  // Map and deck.gl instances
  let map = null
  let deck = null
  
  // Component state
  const mapContainer = ref(null)
  const isLoading = ref(true)
  const is3DView = ref(true)
  const currentPosition = ref({ lng: INITIAL_VIEW_STATE.longitude, lat: INITIAL_VIEW_STATE.latitude, altitude: 0 })
  const hoveredDroneInfo = ref(null)
  const clickedDroneId = ref(null)
  const mapStyle = ref(import.meta.env.VITE_DEFAULT_MAP_STYLE || 'mapbox://styles/mapbox/streets-v12')
  const isDarkMode = ref(mapStyle.value.includes('dark'))
  
  // 巡逻区域绘制相关状态
  const isDrawingPatrolArea = ref(false)
  const patrolAreaPoints = ref([])
  
  // Layer controls - 使用新名字避免与props冲突
  const showBuildingsLayer = ref(true)
  const showTerrainLayer = ref(true)
  const showDronesLayer = ref(props.showDrones)
  const showEventsLayer = ref(true)
  const showNoFlyZonesLayer = ref(true)
  const showFlightPathsLayer = ref(true)
  
  // Watch for props changes
  watch(() => props.drones, () => {
    if (deck) renderDeckLayers()
  }, { deep: true })
  
  watch(() => props.events, () => {
    if (deck) renderDeckLayers()
  }, { deep: true })
  
  watch(() => props.noFlyZones, () => {
    if (deck) renderDeckLayers()
  }, { deep: true })
  
  watch(() => props.flightPaths, () => {
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
    showDronesLayer.value = newVal;
  })
  
  // Watch layers visibility changes
  watch([showBuildingsLayer, showTerrainLayer], () => {
    if (map) {
      // Show/hide 3D buildings
      if (map.getLayer('building-extrusion')) {
        map.setLayoutProperty(
          'building-extrusion',
          'visibility',
          showBuildingsLayer.value ? 'visible' : 'none'
        )
      }
      
      // Show/hide terrain
      if (map.getSource('mapbox-dem')) {
        // 确保天空层存在
        if (map.getLayer('sky')) {
            map.setLayoutProperty(
              'sky',
              'visibility',
              showTerrainLayer.value ? 'visible' : 'none'
            )
        }
        // Apply terrain
        if (showTerrainLayer.value) {
          map.setTerrain({ source: 'mapbox-dem', exaggeration: 1.5 })
        } else {
          map.setTerrain(null)
        }
      }
    }
  })
  
  // Watch deck.gl layers visibility changes
  watch([showDronesLayer, showEventsLayer, showNoFlyZonesLayer, showFlightPathsLayer, isDrawingPatrolArea, patrolAreaPoints], () => {
    if (deck) {
      renderDeckLayers()
    }
  }, { deep: true })
  
  // Format coordinate display
  const formatCoordinate = (coord) => {
    return coord.toFixed(6)
  }
  
  // Get drone status tag type
  const getDroneStatusType = (status) => {
    const statusMap = {
      'idle': 'info',
      'flying': 'success',
      'charging': 'warning',
      'maintenance': 'warning',
      'offline': 'error',
      'error': 'error'
    }
    return statusMap[status] || 'default'
  }
  
  // Get drone battery color
  const getDroneBatteryColor = (level) => {
    if (level <= 20) return '#ff4d4f'
    if (level <= 50) return '#faad14'
    return '#52c41a'
  }
  
  // Center map on a specific drone
  const centerMapOnDrone = (drone) => {
    if (!map || !drone.current_location) return
    
    const coords = drone.current_location.coordinates
    if (coords && coords.length >= 2) {
      // [longitude, latitude]
      map.flyTo({
        center: [coords[0], coords[1]],
        zoom: 15,
        pitch: 60,
        bearing: 0,
        duration: 1500
      })
    }
  }
  
  // Initialize map
  const initializeMap = () => {
    if (!mapContainer.value) {
      console.error('Cannot initialize map: mapContainer ref is not available');
      isLoading.value = false;
      return;
    }
    
    isLoading.value = true;
    
    try {
      // 确保mapboxgl已加载
      if (!mapboxgl) {
        throw new Error('Mapbox GL JS not loaded');
      }
      
      mapboxgl.accessToken = MAPBOX_TOKEN;
      
      // 尝试创建地图实例
      map = new mapboxgl.Map({
        container: mapContainer.value,
        style: mapStyle.value, // 使用环境变量或默认样式
        center: [INITIAL_VIEW_STATE.longitude, INITIAL_VIEW_STATE.latitude],
        zoom: INITIAL_VIEW_STATE.zoom,
        pitch: INITIAL_VIEW_STATE.pitch,
        bearing: INITIAL_VIEW_STATE.bearing,
        antialias: true,
        failIfMajorPerformanceCaveat: false, // 允许在性能受限的设备上运行
      });
      
      console.log('地图实例已创建，初始化位置:', [INITIAL_VIEW_STATE.longitude, INITIAL_VIEW_STATE.latitude]);
      
      // 添加错误事件监听器
      map.on('error', (e) => {
        console.error('地图加载错误:', e);
        // 不设置isLoading = false，让load事件处理
        
        // 尝试使用备选样式
        if (e.error && e.error.status === 401) {
          console.log('尝试使用备选地图样式');
          try {
            map.setStyle('mapbox://styles/mapbox/streets-v12');
          } catch (styleError) {
            console.error('设置备选样式失败:', styleError);
          }
        }
      });
      
      // 添加加载事件监听器
      map.on('load', () => {
        console.log('地图加载完成');
        isLoading.value = false;
        
        try {
          // 初始化3D建筑层
          add3DBuildings();
          
          // 初始化DeckGL
          if (typeof Deck !== 'undefined') {
            initDeck();
          } else {
            console.warn('Deck.gl未加载，跳过图层初始化');
          }
          
          // 设置地图交互事件
          setupMapEvents();
          
          // 添加初始动画效果
          initializeWithAnimation();
        } catch (error) {
          console.error('地图加载后初始化图层出错:', error);
        }
        
        // 无论如何都通知父组件地图已加载
        emit('map-loaded', { success: true });
      });
      
      // 添加超时处理，防止地图加载卡住
      setTimeout(() => {
        if (isLoading.value) {
          console.warn('地图加载超时，强制完成初始化');
          isLoading.value = false;
          emit('map-loaded', { success: false, error: 'timeout' });
        }
      }, 10000); // 10秒超时
      
    } catch (error) {
      console.error('初始化地图时出错:', error);
      isLoading.value = false;
      emit('map-loaded', { success: false, error: error.message });
    }
  };
  
  // 添加3D建筑方法
  const add3DBuildings = () => {
    if (!map || map.getLayer('building-extrusion')) return; // 防止重复添加
    
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
      'visibility': showBuildingsLayer.value ? 'visible' : 'none'
    });
    
    // 添加地形层
    if (!map.getSource('mapbox-dem')) {
      map.addSource('mapbox-dem', {
        'type': 'raster-dem',
        'url': 'mapbox://mapbox.mapbox-terrain-dem-v1',
        'tileSize': 512,
        'maxzoom': 14
      });
    }
    
    // 设置地形
    if (showTerrainLayer.value) {
        map.setTerrain({ 'source': 'mapbox-dem', 'exaggeration': 1.5 });
    } else {
        map.setTerrain(null);
    }

    // 添加天空层，与地形关联
    if (!map.getLayer('sky')) {
        map.addLayer({
            'id': 'sky',
            'type': 'sky',
            'paint': {
                'sky-type': 'atmosphere',
                'sky-atmosphere-sun': [0.0, 0.0],
                'sky-atmosphere-sun-intensity': 15
            },
           'visibility': showTerrainLayer.value ? 'visible' : 'none'
        });
    }
  };
  
  // 设置地图事件
  const setupMapEvents = () => {
    if (!map) return;
    
    // 鼠标移动事件，更新坐标
    map.on('mousemove', (e) => {
      currentPosition.value = {
        lng: e.lngLat.lng,
        lat: e.lngLat.lat,
        altitude: map.queryTerrainElevation(e.lngLat) || 0
      };
    });
    
    // 点击事件
    map.on('click', (e) => {
      const coordinates = {
        lng: e.lngLat.lng,
        lat: e.lngLat.lat,
        altitude: map.queryTerrainElevation(e.lngLat) || 0
      };
      
      // 如果是绘制巡逻区域模式，添加顶点
      if (isDrawingPatrolArea.value) {
        patrolAreaPoints.value.push([coordinates.lng, coordinates.lat]);
        // deck layer watch 会自动更新视图
      } else {
        // 正常点击事件，发送到父组件
        emit('map-clicked', coordinates);
      }
    });
  };
  
  // 飞行到指定位置
  const flyTo = (position) => {
    if (!map) return;
    
    try {
      console.log('飞行到位置:', position);
      
      // 确保位置对象包含必要的属性
      const lng = position.lng || position.longitude || 114.367;
      const lat = position.lat || position.latitude || 30.54;
      const zoom = position.zoom || 14;
      
      map.flyTo({
        center: [lng, lat],
        zoom: zoom,
        pitch: position.pitch !== undefined ? position.pitch : 45,
        bearing: position.bearing !== undefined ? position.bearing : 0,
        duration: position.duration || 2000,
        essential: true
      });
    } catch (error) {
      console.error('飞行到位置时出错:', error);
    }
  };
  
  // 重置视图到初始状态
  const resetView = () => {
    if (!map) return;
    
    map.flyTo({
      center: [INITIAL_VIEW_STATE.longitude, INITIAL_VIEW_STATE.latitude],
      zoom: INITIAL_VIEW_STATE.zoom,
      pitch: INITIAL_VIEW_STATE.pitch,
      bearing: INITIAL_VIEW_STATE.bearing,
      duration: 1000
    });
  };
  
  // Initialize deck.gl
  const initDeck = () => {
    console.log('Initializing Deck.gl...')
    try {
        // Create deck.gl instance, share map's viewport
        deck = new Deck({
          canvas: 'deck-canvas',
          width: '100%',
          height: '100%',
          initialViewState: INITIAL_VIEW_STATE,
          controller: false,
          onViewStateChange: ({ viewState }) => {
            // Sync view state with map
            map.jumpTo({
              center: [viewState.longitude, viewState.latitude],
              zoom: viewState.zoom,
              bearing: viewState.bearing,
              pitch: viewState.pitch
            })
            return viewState
          },
          layers: [],
          getTooltip: ({ object }) => {
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
        console.log('Deck.gl instance created.')
        
        // Render deck.gl layers
        renderDeckLayers()
        
        // There's a hidden canvas, used for deck.gl rendering
        const deckCanvas = document.createElement('canvas')
        deckCanvas.id = 'deck-canvas'
        deckCanvas.style.position = 'absolute'
        deckCanvas.style.top = '0'
        deckCanvas.style.left = '0'
        deckCanvas.style.width = '100%'
        deckCanvas.style.height = '100%'
        deckCanvas.style.pointerEvents = 'none'
        mapContainer.value.appendChild(deckCanvas)
        
        // Add deck.gl as a map overlay
        map.on('render', () => {
          deck.setProps({
            viewState: {
              longitude: map.getCenter().lng,
              latitude: map.getCenter().lat,
              zoom: map.getZoom(),
              pitch: map.getPitch(),
              bearing: map.getBearing()
            }
          })
        })
    } catch(error) {
        console.error('Error initializing Deck.gl:', error)
    }
  }
  
  // Render deck.gl layers
  const renderDeckLayers = () => {
    if (!deck) return
    
    const layers = []
    
    // Add drone layer
    if (showDronesLayer.value) {
      layers.push(
        new ScatterplotLayer({
          id: 'drones-layer',
          data: props.drones.map(drone => {
            // Standardize data format
            if (!drone.current_location) return null
            
            const coordinates = drone.current_location.coordinates
            if (!coordinates || coordinates.length < 2) return null
            
            return {
              ...drone,
              type: 'drone',
              position: [coordinates[0], coordinates[1], coordinates[2] || (drone.current_location.altitude || 100)],
              color: getDroneColor(drone),
              radius: drone.drone_id === props.selectedDroneId ? 300 : 200
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
          getLineWidth: d => d.drone_id === props.selectedDroneId ? 3 : 1,
          updateTriggers: {
            getFillColor: [props.drones],
            getLineWidth: [props.selectedDroneId],
            getRadius: [props.selectedDroneId]
          }
        })
      )
    }
    
    // Add flight paths layer
    if (showFlightPathsLayer.value && props.flightPaths && props.flightPaths.length > 0) {
      layers.push(
        new PathLayer({
          id: 'flight-paths-layer',
          data: props.flightPaths,
          pickable: true,
          widthScale: 1,
          widthMinPixels: 2,
          getPath: d => d.path,
          getColor: d => d.color || [30, 144, 255, 200],
          getWidth: d => d.width || 5
        })
      )
    }
    
    // Add no-fly zones layer
    if (showNoFlyZonesLayer.value && props.noFlyZones && props.noFlyZones.length > 0) {
      layers.push(
        new PolygonLayer({
          id: 'no-fly-zones-layer',
          data: props.noFlyZones,
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
      )
    }
    
    // Add events layer
    if (showEventsLayer.value && props.events && props.events.length > 0) {
      layers.push(
        new IconLayer({
          id: 'events-layer',
          data: props.events.map(event => {
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
      )
    }

    // Add patrol area drawing layer (if drawing)
    if (isDrawingPatrolArea.value && patrolAreaPoints.value.length > 0) {
      // 显示已绘制的点
      layers.push(
        new ScatterplotLayer({
          id: 'patrol-area-points-layer',
          data: patrolAreaPoints.value.map((p, index) => ({ position: p, index })),
          pickable: false,
          stroked: true,
          filled: true,
          radiusScale: 1,
          radiusMinPixels: 4,
          radiusMaxPixels: 8,
          lineWidthMinPixels: 1,
          getPosition: d => d.position,
          getFillColor: [59, 130, 246, 200], // Blue
          getLineColor: [255, 255, 255],
          getRadius: 5,
        })
      );

      // 显示连接线 (如果点数 > 1)
      if (patrolAreaPoints.value.length > 1) {
        layers.push(
          new PathLayer({
            id: 'patrol-area-path-layer',
            data: [{ path: patrolAreaPoints.value }], // Deck.gl PathLayer 需要 data 是一个数组，每个元素包含一个 path 属性
            pickable: false,
            widthScale: 1,
            widthMinPixels: 2,
            getPath: d => d.path,
            getColor: [59, 130, 246, 255], // Blue
            getWidth: 2,
            dashJustified: true,
            getDashArray: [4, 2] // 虚线效果
          })
        );
      }

      // 预览闭合线 (如果点数 > 2)
      if (patrolAreaPoints.value.length > 2) {
         layers.push(
          new PathLayer({
            id: 'patrol-area-closing-path-layer',
            data: [{ path: [patrolAreaPoints.value[patrolAreaPoints.value.length - 1], patrolAreaPoints.value[0]] }],
            pickable: false,
            widthScale: 1,
            widthMinPixels: 2,
            getPath: d => d.path,
            getColor: [59, 130, 246, 150], // Lighter blue for closing line
            getWidth: 2,
            dashJustified: true,
            getDashArray: [3, 3] // Different dash for closing line
          })
        );
      }
    }
    
    deck.setProps({ layers })
  }
  
  // Get color based on drone status
  const getDroneColor = (drone) => {
    switch (drone.status) {
      case 'idle':
        return [0, 122, 255, 255]  // Blue
      case 'flying':
        return [52, 199, 89, 255]  // Green
      case 'charging':
        return [255, 149, 0, 255]  // Orange
      case 'maintenance':
        return [255, 204, 0, 255]  // Yellow
      case 'offline':
        return [210, 210, 210, 180] // Gray
      case 'error':
        return [255, 59, 48, 255]  // Red
      default:
        return [128, 128, 128, 255] // Gray
    }
  }
  
  // Get icon for event
  const getEventIcon = (event) => {
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
  
  // Get size for event
  const getEventSize = (event) => {
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
  
  // Get color for event
  const getEventColor = (event) => {
    switch (event.level) {
      case 'high':
        return [255, 59, 48, 255]  // Red
      case 'medium':
        return [255, 149, 0, 255]  // Orange
      case 'low':
        return [255, 204, 0, 255]  // Yellow
      default:
        return [0, 122, 255, 255]  // Blue
    }
  }
  
  // Toggle 3D view
  const toggle3DView = () => {
    is3DView.value = !is3DView.value
    if (map) {
      map.easeTo({
        pitch: is3DView.value ? 60 : 0,
        bearing: is3DView.value ? 30 : 0,
        duration: 1000
      })
    }
  }
  
  // 修改地图样式切换方法
  const changeMapStyle = (style) => {
    if (!map) return;
    
    try {
      console.log('切换地图样式:', style);
      // 保存当前视角状态
      const currentCenter = map.getCenter();
      const currentZoom = map.getZoom();
      const currentPitch = map.getPitch();
      const currentBearing = map.getBearing();
      
      // 设置新样式
      map.setStyle(style);
      
      // 样式加载完成后恢复视角
      map.once('style.load', async () => {
        map.jumpTo({
          center: currentCenter,
          zoom: currentZoom,
          pitch: currentPitch,
          bearing: currentBearing
        });
        
        // 重新添加图层和地形
        await nextTick(); // 确保DOM更新
        add3DBuildings();
        
        // 更新isDarkMode状态
        isDarkMode.value = style.includes('dark');
      });
    } catch (error) {
      console.error('切换地图样式时出错:', error);
    }
  };
  
  // 飞行到武汉大学
  const flyToWhu = () => {
    if (!map) return;
    
    try {
      console.log('飞行到武汉大学');
      
      // 添加动画效果
      map.flyTo({
        center: [WHU_LOCATION.longitude, WHU_LOCATION.latitude],
        zoom: WHU_LOCATION.zoom,
        pitch: WHU_LOCATION.pitch,
        bearing: WHU_LOCATION.bearing,
        duration: 3000, // 较长的动画时间
        essential: true
      });
    } catch (error) {
      console.error('飞行到武汉大学时出错:', error);
    }
  };

  // 初始化时添加动态跳转到武汉大学
  const initializeWithAnimation = () => {
    // 首先定位到默认位置的较远视角
    if (map) {
      console.log('初始化动态飞行到武汉大学');
      
      // 设置初始视角为较远的视角
      map.jumpTo({
        center: [114.36, 30.52], // 稍微偏离武汉大学的位置
        zoom: 10, // 较小的缩放级别表示更远的视角
        pitch: 0,
        bearing: 0
      });
      
      // 延迟一秒后执行飞行动画
      setTimeout(() => {
        flyToWhu();
      }, 1000);
    }
  };
  
  // 模拟无人机巡逻状态的标记
  const patrolStatus = ref(false);

  // 修改开始巡逻方法
  const startDronePatrol = (drones) => {
    if (!map) {
      console.warn('地图实例未初始化，无法开始无人机巡逻');
      return;
    }
    console.log('开始无人机巡逻模拟:', drones);
    
    try {
      // 设置巡逻状态为真
      patrolStatus.value = true;
      // 这里可以实现实际的巡逻路径动画
      // 简单实现：为每个无人机创建一个随机巡逻路径
      renderDeckLayers(); // 刷新图层
    } catch (error) {
      console.error('开始巡逻时出错:', error);
    }
  };
  
  // 修改停止巡逻方法
  const stopDronePatrol = (droneIds) => {
    if (!map) {
      console.warn('地图实例未初始化，无法停止无人机巡逻');
      return;
    }
    console.log('停止无人机巡逻:', droneIds);
    
    try {
      // 设置巡逻状态为假
      patrolStatus.value = false;
      // 清除巡逻路径
      renderDeckLayers(); // 刷新图层
    } catch (error) {
      console.error('停止巡逻时出错:', error);
    }
  };
  
  // 公开巡逻状态
  const getPatrolStatus = () => {
    return patrolStatus.value;
  };
  
  // 新增巡逻区域绘制相关方法
  const toggleDrawingPatrolArea = () => {
    isDrawingPatrolArea.value = !isDrawingPatrolArea.value;
    if (!isDrawingPatrolArea.value) {
      // 如果关闭绘制模式，清除当前绘制的点
      patrolAreaPoints.value = [];
    } else {
      // 进入绘制模式，可以添加提示或改变光标样式
      map.getCanvas().style.cursor = 'crosshair';
    }
    if (!isDrawingPatrolArea.value) {
        map.getCanvas().style.cursor = ''; // 恢复默认光标
    }
  };

  const completeDrawingPatrolArea = () => {
    if (patrolAreaPoints.value.length >= 3) {
      const finalPolygon = [...patrolAreaPoints.value, patrolAreaPoints.value[0]]; // 闭合多边形
      emit('patrol-area-drawn', finalPolygon); // 发送包含闭合点的完整路径
      isDrawingPatrolArea.value = false;
      patrolAreaPoints.value = []; // 清空
      map.getCanvas().style.cursor = ''; // 恢复默认光标
    } else {
      console.warn("需要至少3个点来完成绘制");
      // 可以添加用户提示
    }
  };

  const cancelDrawingPatrolArea = () => {
    isDrawingPatrolArea.value = false;
    patrolAreaPoints.value = []; // 清空
    map.getCanvas().style.cursor = ''; // 恢复默认光标
  };

  const undoLastPatrolPoint = () => {
    if (patrolAreaPoints.value.length > 0) {
      patrolAreaPoints.value.pop();
    }
  };
  
  // Mount component
  onMounted(() => {
    console.log('Map3D component mounted.');
    
    // 使用延迟初始化，确保DOM已完全准备好
    setTimeout(() => {
      if (mapContainer.value) {
        console.log('mapContainer is available, initializing map...');
        try {
          initializeMap();
        } catch (error) {
          console.error('Map initialization failed:', error);
          isLoading.value = false;
          
          // 通知父组件地图初始化失败
          emit('map-loaded', { success: false, error: error.message });
        }
      } else {
        console.error('mapContainer ref not found even after delay!');
        isLoading.value = false;
      }
    }, 100);
  })
  
  // Cleanup on unmount
  onUnmounted(() => {
    if (map) {
      map.remove()
      map = null
    }
    if (deck) {
      deck.finalize()
      deck = null
    }
  })
  
  // Methods to expose
  defineExpose({
    centerOnDrone: centerMapOnDrone,
    resetView,
    toggleView: toggle3DView,
    flyTo,
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