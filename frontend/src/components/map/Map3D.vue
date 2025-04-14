<template>
    <div class="relative w-full h-full">
      <!-- 3D地图容器 -->
      <div ref="mapContainer" class="w-full h-full"></div>
      
      <!-- 加载指示器 -->
      <div v-if="isLoading" class="absolute inset-0 flex items-center justify-center bg-white bg-opacity-50 z-10">
        <n-spin size="large" />
      </div>
      
      <!-- 控制面板 -->
      <div class="absolute top-4 right-4 z-10">
        <div class="flex flex-col space-y-2">
          <!-- 图层控制 -->
          <n-popover trigger="click" placement="left">
            <template #trigger>
              <n-button circle secondary class="opacity-90">
                <template #icon>
                  <n-icon><layers-icon /></n-icon>
                </template>
              </n-button>
            </template>
            <div class="flex flex-col space-y-2 w-48 p-2">
              <div class="text-sm font-medium text-gray-700 mb-1">图层控制</div>
              <n-checkbox v-model:checked="showBuildings">3D建筑</n-checkbox>
              <n-checkbox v-model:checked="showTerrain">地形</n-checkbox>
              <n-checkbox v-model:checked="showDrones">无人机</n-checkbox>
              <n-checkbox v-model:checked="showEvents">事件标记</n-checkbox>
              <n-checkbox v-model:checked="showNoFlyZones">禁飞区</n-checkbox>
              <n-checkbox v-model:checked="showFlightPaths">飞行路径</n-checkbox>
            </div>
          </n-popover>
          
          <!-- 地图样式切换 -->
          <n-popover trigger="click" placement="left">
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
        </div>
      </div>
      
      <!-- 坐标信息 -->
      <div class="absolute bottom-4 left-4 z-10 bg-white bg-opacity-70 p-2 rounded-md text-xs text-gray-700">
        <div>经度: {{ formatCoordinate(currentPosition.lng) }}</div>
        <div>纬度: {{ formatCoordinate(currentPosition.lat) }}</div>
        <div>海拔: {{ currentPosition.altitude?.toFixed(2) || '未知' }} 米</div>
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

    <!-- Patrol controls -->
    <div class="absolute bottom-4 right-4 z-10 bg-white bg-opacity-70 p-2 rounded-md">
      <n-button-group>
        <n-button @click="startPatrol" :disabled="patrolStatus">
          <template #icon><n-icon><play-icon /></n-icon></template>
          开始巡逻
        </n-button>
        <n-button @click="stopPatrol" :disabled="!patrolStatus">
          <template #icon><n-icon><pause-icon /></n-icon></template>
          停止巡逻
        </n-button>
      </n-button-group>
      <div class="mt-2">
        <n-slider v-model:value="droneSpeedFactor" :step="0.1" :min="0.5" :max="2.0" />
        <div class="text-xs text-center">速度: {{ droneSpeedFactor.toFixed(1) }}x</div>
      </div>
    </div>
    </div>
  </template>
  
  <script setup>
  import { ref, onMounted, onUnmounted, watch, computed, defineProps, defineEmits } from 'vue'
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
  PlayCircleOutlined as PlayIcon,
  PauseCircleOutlined as PauseIcon
  } from '@vicons/antd'
import { NProgress, NSpin, NButton, NIcon, NPopover, NCheckbox, NRadioGroup, NRadio, NSpace, NTag, NSlider, NButtonGroup } from 'naive-ui'
  
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
  
  const emit = defineEmits(['drone-clicked', 'map-clicked', 'coordinates-selected', 'map-loaded'])
  
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
    longitude: props.initialView ? props.initialView.center[0] : 114.33,
    latitude: props.initialView ? props.initialView.center[1] : 30.57,
    zoom: props.initialView ? props.initialView.zoom : 11,
    pitch: 55,
    bearing: 25
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
  
  // Layer controls
  const showBuildings = ref(true)
  const showTerrain = ref(true)
  const showDrones = ref(true)
  const showEvents = ref(true)
  const showNoFlyZones = ref(true)
  const showFlightPaths = ref(true)

// Patrol animation controls
const patrolStatus = ref(false)
const droneSpeedFactor = ref(1.0)
const droneLastKnownPositions = ref(new Map()) // Store last known positions

// Animation frame ID for patrol animation
let animationFrameId = null
  
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
  
  // Watch layers visibility changes
  watch([showBuildings, showTerrain], () => {
    if (map) {
      // Show/hide 3D buildings
      map.setLayoutProperty(
        'building-extrusion',
        'visibility',
        showBuildings.value ? 'visible' : 'none'
      )
      
      // Show/hide terrain
      if (map.getSource('mapbox-dem')) {
        map.setLayoutProperty(
          'sky',
          'visibility',
          showTerrain.value ? 'visible' : 'none'
        )
        // Apply terrain
        if (showTerrain.value) {
          map.setTerrain({ source: 'mapbox-dem', exaggeration: 1.5 })
        } else {
          map.setTerrain(null)
        }
      }
    }
  })
  
  // Watch deck.gl layers visibility changes
  watch([showDrones, showEvents, showNoFlyZones, showFlightPaths], () => {
    if (deck) {
      renderDeckLayers()
    }
  })

// Watch drone speed factor
watch(droneSpeedFactor, () => {
  // Update animation speed if patrol is active
  if (patrolStatus.value && deck) {
      renderDeckLayers()
    }
  })
  
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
      style: mapStyle.value,
        center: [INITIAL_VIEW_STATE.longitude, INITIAL_VIEW_STATE.latitude],
        zoom: INITIAL_VIEW_STATE.zoom,
        pitch: INITIAL_VIEW_STATE.pitch,
        bearing: INITIAL_VIEW_STATE.bearing,
        antialias: true,
      failIfMajorPerformanceCaveat: false,
      });
      
      console.log('地图实例已创建，初始化位置:', [INITIAL_VIEW_STATE.longitude, INITIAL_VIEW_STATE.latitude]);
      
      // 添加错误事件监听器
      map.on('error', (e) => {
        console.error('地图加载错误:', e);
        
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
    if (!map) return;
    
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
      'visibility': showBuildings.value ? 'visible' : 'none'
    });
    
    // 添加地形层
    map.addSource('mapbox-dem', {
      'type': 'raster-dem',
      'url': 'mapbox://mapbox.mapbox-terrain-dem-v1',
      'tileSize': 512,
      'maxzoom': 14
    });
    
    // 设置地形
    map.setTerrain({ 'source': 'mapbox-dem', 'exaggeration': 1.5 });
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
      // 发送点击事件到父组件
      emit('map-clicked', {
        lng: e.lngLat.lng,
        lat: e.lngLat.lat,
        altitude: map.queryTerrainElevation(e.lngLat) || 0
      });
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
      // 确保canvas元素存在
      let deckCanvas = document.getElementById('deck-canvas')
      if (!deckCanvas) {
        console.log('创建deck-canvas元素...')
        deckCanvas = document.createElement('canvas')
        deckCanvas.id = 'deck-canvas'
        deckCanvas.style.position = 'absolute'
        deckCanvas.style.top = '0'
        deckCanvas.style.left = '0'
        deckCanvas.style.width = '100%'
        deckCanvas.style.height = '100%'
        deckCanvas.style.pointerEvents = 'none'
        deckCanvas.style.zIndex = '5'
        mapContainer.value.appendChild(deckCanvas)
        console.log('deck-canvas元素已添加到DOM')
      } else {
        // 确保现有canvas也设置为none
        deckCanvas.style.pointerEvents = 'none'
      }
    
      // 使用更简单的配置初始化Deck
      console.log('使用简化配置初始化Deck.gl...')
      deck = new Deck({
        canvas: deckCanvas,
        initialViewState: {
          longitude: map.getCenter().lng,
          latitude: map.getCenter().lat,
          zoom: map.getZoom(),
          pitch: map.getPitch(),
          bearing: map.getBearing()
        },
        controller: false,
        layers: []
      })
      
      console.log('Deck.gl实例创建成功')
      
      // 先尝试渲染简单的点图层以测试功能
      const testLayer = new ScatterplotLayer({
        id: 'test-layer',
        data: [
          {
            position: [map.getCenter().lng, map.getCenter().lat, 0], 
            color: [255, 0, 0, 255], 
            radius: 200
          }
        ],
        pickable: true,
        stroked: true,
        filled: true,
        radiusScale: 1,
        radiusMinPixels: 10,
        radiusMaxPixels: 100,
        getPosition: d => d.position,
        getFillColor: d => d.color,
        getRadius: d => d.radius,
        getLineColor: [0, 0, 0]
      })
      
      deck.setProps({
        layers: [testLayer]
      })
      
      console.log('测试图层设置成功')
      
      // 确保deck和map视角同步
      map.on('render', () => {
        if (deck) {
          deck.setProps({
            viewState: {
              longitude: map.getCenter().lng,
              latitude: map.getCenter().lat,
              zoom: map.getZoom(),
              pitch: map.getPitch(),
              bearing: map.getBearing()
            }
          })
        }
      })
      
      // 渲染实际图层
      setTimeout(() => renderDeckLayers(), 1000)
      
      // 添加定期刷新
      const refreshInterval = setInterval(() => {
        if (deck && showDrones.value) {
          renderDeckLayers()
        }
      }, 3000)
      
      onUnmounted(() => {
        if (refreshInterval) clearInterval(refreshInterval)
        if (deck) {
          deck.finalize()
          deck = null
        }
      })
    } catch (error) {
      console.error('初始化Deck.gl时出错:', error)
    }
  }
  
// Store drone patrol routes
const dronePatrolRoutes = new Map();

// Get or create a patrol route for a drone
const getOrCreatePatrolRoute = (drone) => {
  if (!dronePatrolRoutes.has(drone.drone_id)) {
    // Get starting position
    const center = drone.current_location?.coordinates || [map.getCenter().lng, map.getCenter().lat];
    const altitude = (drone.current_location?.coordinates && drone.current_location.coordinates[2]) || 200;
    
    // Generate a unique patrol route for this drone
    const patrolRoute = generatePatrolRoute(center[0], center[1], altitude, drone.drone_id);
    dronePatrolRoutes.set(drone.drone_id, patrolRoute);
  }
  
  return dronePatrolRoutes.get(drone.drone_id);
};

// Generate a more complex and natural patrol route
const generatePatrolRoute = (centerLng, centerLat, altitude, droneId) => {
  console.log(`生成无人机 ${droneId} 的巡逻路线`);
  
  // Generate a unique random seed based on drone ID
  const seed = droneId.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0);
  const random = (min, max) => {
    const x = Math.sin(seed * 9999) * 10000;
    const r = x - Math.floor(x);
    return min + r * (max - min);
  };
  
  // Configure patrol route based on drone ID to make each drone behave differently
  const radiusX = 0.05 + random(0.01, 0.08); // 半长轴 - 扩大10倍
  const radiusY = 0.03 + random(0.01, 0.06); // 半短轴 - 扩大10倍
  const points = 40 + Math.floor(random(0, 20)); // 路径点数量
  const altitudeVariation = 30 + Math.floor(random(10, 50)); // 高度变化范围
  const rotationAngle = random(0, Math.PI * 2); // 旋转角度
  
  // 设置共享目的地点 - 增加路径重叠的概率
  const sharedPoints = [
    [114.30, 30.60], // 武汉市中心
    [114.367, 30.540], // 武汉大学
    [114.412, 30.513], // 华中科技大学
    [114.325, 30.57], // 汉口商圈
    [114.264, 30.582], // 江汉路
    [114.306, 30.544], // 黄鹤楼
  ];
  
  // 选择1-2个共享点
  const useSharedPoints = random(0, 1) > 0.3; // 70%概率使用共享点
  const sharedPoint1 = sharedPoints[Math.floor(random(0, sharedPoints.length))];
  const sharedPoint2 = sharedPoints[Math.floor(random(0, sharedPoints.length))];
  
  // Generate route points
  const route = [];
  
  // First, add the starting position
  route.push([centerLng, centerLat, altitude]);
  
  // Add transition to patrol altitude
  const patrolAltitude = altitude + Math.floor(random(-20, 50));
  route.push([centerLng, centerLat, patrolAltitude]);
  
  // Generate core patrol path
  for (let i = 0; i <= points; i++) {
    // Calculate position on ellipse
    const angle = (i / points) * Math.PI * 2;
    const x = radiusX * Math.cos(angle);
    const y = radiusY * Math.sin(angle);
    
    // Apply rotation to create varied paths
    const rotatedX = x * Math.cos(rotationAngle) - y * Math.sin(rotationAngle);
    const rotatedY = x * Math.sin(rotationAngle) + y * Math.cos(rotationAngle);
    
    // Calculate altitude variation with sinusoidal pattern
    const altVariation = altitudeVariation * Math.sin((i / points) * Math.PI * 4);
    const pointAltitude = patrolAltitude + altVariation;
    
    // Add small random variations to make path more natural
    const jitterX = random(-0.0005, 0.0005);
    const jitterY = random(-0.0005, 0.0005);
    
    // Add point to route
    route.push([
      centerLng + rotatedX + jitterX,
      centerLat + rotatedY + jitterY,
      pointAltitude
    ]);
  }
  
  // Connect back to the beginning
  route.push([centerLng, centerLat, patrolAltitude]);
  
  // 添加共享点到路径中 - 创建重叠
  if (useSharedPoints) {
    // 添加前往共享点1的路径
    route.push([
      sharedPoint1[0], 
      sharedPoint1[1], 
      patrolAltitude + random(-30, 30)
    ]);
    
    // 在共享点停留一些点
    const hoverPoints = Math.floor(random(3, 8));
    for (let i = 0; i < hoverPoints; i++) {
      route.push([
        sharedPoint1[0] + random(-0.002, 0.002),
        sharedPoint1[1] + random(-0.002, 0.002),
        patrolAltitude + random(-20, 20)
      ]);
    }
    
    // 有50%概率添加第二个共享点
    if (random(0, 1) > 0.5) {
      route.push([
        sharedPoint2[0], 
        sharedPoint2[1], 
        patrolAltitude + random(-30, 30)
      ]);
      
      // 在第二个共享点停留
      for (let i = 0; i < Math.floor(random(2, 6)); i++) {
        route.push([
          sharedPoint2[0] + random(-0.002, 0.002),
          sharedPoint2[1] + random(-0.002, 0.002),
          patrolAltitude + random(-20, 20)
        ]);
      }
    }
  }
  
  // Generate additional waypoints for figure-8 patterns
  const figure8Points = 20 + Math.floor(random(0, 10));
  const figure8Scale = 0.7 + random(0.5, 0.8); // 增大figure-8的比例
  
  for (let i = 0; i <= figure8Points; i++) {
    const t = (i / figure8Points) * Math.PI * 2;
    
    // Create figure-8 pattern 
    const fx = radiusX * figure8Scale * Math.sin(t);
    const fy = radiusY * figure8Scale * Math.sin(t * 2);
    
    // Apply rotation
    const rotatedFX = fx * Math.cos(rotationAngle) - fy * Math.sin(rotationAngle);
    const rotatedFY = fx * Math.sin(rotationAngle) + fy * Math.cos(rotationAngle);
    
    // Calculate altitude with double frequency
    const faltVariation = altitudeVariation * 0.7 * Math.sin(t * 3);
    const fpointAltitude = patrolAltitude + faltVariation;
    
    // Add minor jitter
    const fjitterX = random(-0.0003, 0.0003);
    const fjitterY = random(-0.0003, 0.0003);
    
    // Add point to route
    route.push([
      centerLng + rotatedFX + fjitterX,
      centerLat + rotatedFY + fjitterY,
      fpointAltitude
    ]);
  }
  
  // Add a second figure-8 pattern at a different angle for variety
  const secondAngle = rotationAngle + Math.PI / 3;
  const secondScale = 0.8 + random(0.4, 0.7); // 增大第二个figure-8的比例
  
  for (let i = 0; i <= figure8Points / 2; i++) {
    const t = (i / (figure8Points / 2)) * Math.PI * 2;
    
    // Create second figure-8 pattern
    const fx = radiusX * secondScale * Math.sin(t);
    const fy = radiusY * secondScale * Math.sin(t * 2);
    
    // Apply second rotation
    const rotatedFX = fx * Math.cos(secondAngle) - fy * Math.sin(secondAngle);
    const rotatedFY = fx * Math.sin(secondAngle) + fy * Math.cos(secondAngle);
    
    // Calculate altitude with triple frequency
    const faltVariation = altitudeVariation * 0.5 * Math.sin(t * 5);
    const fpointAltitude = patrolAltitude - 20 + faltVariation;
    
    // Add minor jitter
    const fjitterX = random(-0.0002, 0.0002);
    const fjitterY = random(-0.0002, 0.0002);
    
    // Add point to route
    route.push([
      centerLng + rotatedFX + fjitterX,
      centerLat + rotatedFY + fjitterY,
      fpointAltitude
    ]);
  }
  
  // Return to start position to complete the loop
  route.push([centerLng, centerLat, patrolAltitude]);
  route.push([centerLng, centerLat, altitude]);
  
  return route;
};

// Calculate position along route with improved interpolation and timing
const calculatePositionAlongRoute = (route, timestamp) => {
  if (!route || route.length < 2) return null;
  
  // 基于速度因子计算持续时间 - 值越大，动画越慢
  const baseDuration = 180000; // 3 minutes
  const speedFactor = droneSpeedFactor.value;
  const duration = baseDuration / speedFactor;
  
  // 计算当前时间在路径中的位置
  const elapsed = timestamp % duration;
  const progress = elapsed / duration;
  
  // 计算在路径上的位置索引
  const totalDistance = route.length - 1;
  const exactIndex = progress * totalDistance;
  const index1 = Math.floor(exactIndex);
  const index2 = Math.min(index1 + 1, route.length - 1);
  
  // 计算两点之间的插值系数
  const fraction = exactIndex - index1;
  
  // 计算当前位置 - 使用三次样条插值使运动更平滑
  const p0 = route[Math.max(0, index1 - 1)];
  const p1 = route[index1];
  const p2 = route[index2];
  const p3 = route[Math.min(route.length - 1, index2 + 1)];
  
  // 立方样条插值系数
  const t = fraction;
  const t2 = t * t;
  const t3 = t2 * t;
  
  // Catmull-Rom 样条插值
  const c0 = 0.5 * (-t3 + 2*t2 - t);
  const c1 = 0.5 * (3*t3 - 5*t2 + 2);
  const c2 = 0.5 * (-3*t3 + 4*t2 + t);
  const c3 = 0.5 * (t3 - t2);
  
  // 计算插值位置
  return [
    c0 * p0[0] + c1 * p1[0] + c2 * p2[0] + c3 * p3[0],
    c0 * p0[1] + c1 * p1[1] + c2 * p2[1] + c3 * p3[1],
    c0 * p0[2] + c1 * p1[2] + c2 * p2[2] + c3 * p3[2]
  ];
};

// Calculate drone heading with smoother transitions
const calculateDroneHeading = (route, timestamp) => {
  if (!route || route.length < 2) return 0;
  
  // 基于速度因子计算持续时间
  const baseDuration = 180000;
  const speedFactor = droneSpeedFactor.value;
  const duration = baseDuration / speedFactor;
  
  // 计算当前时间在路径中的位置
  const elapsed = timestamp % duration;
  const progress = elapsed / duration;
  
  // 获取当前位置和下一个位置
  const totalDistance = route.length - 1;
  const exactIndex = progress * totalDistance;
  const index1 = Math.floor(exactIndex);
  const index2 = Math.min(index1 + 1, route.length - 1);
  
  // 获取当前位置和下一个位置的坐标
  const p1 = route[index1];
  const p2 = route[index2];
  
  // 计算航向角度 - 使用反正切函数获取两点连线与正北方向的夹角
  const dx = p2[0] - p1[0];
  const dy = p2[1] - p1[1];
  let angle = Math.atan2(dy, dx) * (180 / Math.PI);
  
  // 转换为顺时针角度，从北方向开始
  angle = 90 - angle;
  if (angle < 0) angle += 360;
  
  // 添加小幅随机摇摆以模拟自然飞行
  const wobble = Math.sin(timestamp / 500) * 5;
  
  return angle + wobble;
};

// Render deck.gl layers with enhanced drone visualization
  const renderDeckLayers = () => {
    if (!deck) {
      console.error('Deck实例不存在，无法渲染图层')
      return
    }
    
    try {
      console.log('渲染deck.gl图层...')
    
    // Get current timestamp for animations
    const timestamp = Date.now();
    
    // Convert static drone positions to animated positions based on patrol routes
    const animatedDrones = [...props.drones].map(drone => {
      // Create a copy of the drone object to avoid modifying the original
      const animatedDrone = {...drone};
      
      // If drone is in flying status, animate its position
      if (drone.status === 'flying' && patrolStatus.value) {
        // Get or generate patrol route for this drone
        const patrolRoute = getOrCreatePatrolRoute(drone);
        
        // Calculate position along the route based on current time
        const animatedPosition = calculatePositionAlongRoute(patrolRoute, timestamp);
        
        // Update the drone's position and store it
        if (animatedPosition && animatedPosition.length >= 2) {
          animatedDrone.current_location = {
            coordinates: [
              animatedPosition[0], 
              animatedPosition[1], 
              animatedPosition[2] || 200
            ]
          };
          // Store the last known position
          droneLastKnownPositions.value.set(drone.drone_id, animatedDrone.current_location.coordinates);
        }
      } else if (droneLastKnownPositions.value.has(drone.drone_id)) {
        // If patrol is stopped, use the last known position for rendering
        animatedDrone.current_location = {
          coordinates: droneLastKnownPositions.value.get(drone.drone_id)
        };
      }
      
      return animatedDrone;
    });
    
      // 创建测试无人机数据 - 分布在武汉市各个行政区
      const testDrones = [
        // 江岸区 - 更东
        {
          drone_id: 'drone-jiangan-1',
          name: '江岸区无人机',
          status: patrolStatus.value ? 'flying' : 'idle',
          battery_level: 85,
          type: 'surveillance',
          current_location: {
            coordinates: [114.360, 30.650, 650] // 提高高度
          }
        },
        // 江汉区 - 更西
        {
          drone_id: 'drone-jianghan-1',
          name: '江汉商业区无人机',
          status: patrolStatus.value ? 'flying' : 'idle',
          battery_level: 89,
          type: 'transport',
          current_location: {
            coordinates: [114.180, 30.680, 680] // 提高高度
          }
        },
        // 硚口区 - 移到更西
        {
          drone_id: 'drone-qiaokou-1',
          name: '硚口区无人机',
          status: patrolStatus.value ? 'flying' : 'charging',
          battery_level: 68,
          type: 'security',
          current_location: {
            coordinates: [114.195, 30.615, 660] // 提高高度
          }
        },
        // 汉阳区 - 向南偏西
        {
          drone_id: 'drone-hanyang-1',
          name: '汉阳消防无人机',
          status: patrolStatus.value ? 'flying' : 'charging',
          battery_level: 45,
          type: 'emergency',
          current_location: {
            coordinates: [114.180, 30.514, 690] // 提高高度
          }
        },
        // 武昌区 - 黄鹤楼 - 保持中心位置
        {
          drone_id: 'drone-wuchang-1',
          name: '黄鹤楼观光无人机',
          status: patrolStatus.value ? 'flying' : 'idle',
          battery_level: 95,
          type: 'surveillance',
          current_location: {
            coordinates: [114.306, 30.544, 700] // 提高高度
          }
        },
        // 青山区 - 更东北
        {
          drone_id: 'drone-qingshan-1',
          name: '青山工业区无人机',
          status: patrolStatus.value ? 'flying' : 'maintenance',
          battery_level: 35,
          type: 'security',
          current_location: {
            coordinates: [114.440, 30.680, 670] // 提高高度
          }
        },
        // 洪山区 - 武汉大学 - 向东南移动
        {
          drone_id: 'drone-whu-1',
          name: '武大侦察无人机',
          status: patrolStatus.value ? 'flying' : 'idle',
          battery_level: 85,
          type: 'surveillance',
          current_location: {
            coordinates: [114.420, 30.510, 720] // 提高高度
          }
        },
        // 东西湖区 - 更西北方向
        {
          drone_id: 'drone-dongxihu-1',
          name: '东西湖区无人机',
          status: patrolStatus.value ? 'flying' : 'idle',
          battery_level: 78,
          type: 'transport',
          current_location: {
            coordinates: [114.080, 30.670, 680] // 提高高度
          }
        },
        // 汉南区 - 更向南
        {
          drone_id: 'drone-hannan-1',
          name: '汉南区监控无人机',
          status: patrolStatus.value ? 'flying' : 'idle',
          battery_level: 72,
          type: 'surveillance',
          current_location: {
            coordinates: [114.100, 30.250, 660] // 提高高度
          }
        },
        // 蔡甸区 - 更西南
        {
          drone_id: 'drone-caidian-1',
          name: '蔡甸区无人机',
          status: patrolStatus.value ? 'flying' : 'idle',
          battery_level: 88,
          type: 'security',
          current_location: {
            coordinates: [113.980, 30.500, 690] // 提高高度
          }
        },
        // 江夏区 - 更南
        {
          drone_id: 'drone-jiangxia-1',
          name: '江夏区无人机',
          status: patrolStatus.value ? 'flying' : 'idle',
          battery_level: 92,
          type: 'surveillance',
          current_location: {
            coordinates: [114.350, 30.300, 670] // 提高高度
          }
        },
        // 黄陂区 - 更北
        {
          drone_id: 'drone-huangpi-1',
          name: '黄陂区无人机',
          status: patrolStatus.value ? 'flying' : 'maintenance',
          battery_level: 63,
          type: 'emergency',
          current_location: {
            coordinates: [114.320, 30.950, 710] // 提高高度
          }
        },
        // 新洲区 - 更远东北
        {
          drone_id: 'drone-xinzhou-1',
          name: '新洲区无人机',
          status: patrolStatus.value ? 'flying' : 'idle',
          battery_level: 67,
          type: 'security',
          current_location: {
            coordinates: [114.900, 30.950, 700] // 提高高度
          }
        },
        // 华中科技大学区域 - 更东
        {
          drone_id: 'drone-hust-1',
          name: '华科安保无人机',
          status: patrolStatus.value ? 'flying' : 'idle',
          battery_level: 92,
          type: 'security',
          current_location: {
            coordinates: [114.520, 30.513, 690] // 提高高度
          }
        }
      ];
    
    // Animate test drones if patrol is active
    const animatedTestDrones = testDrones.map(drone => {
      const animatedDrone = {...drone};
      
      // If drone is in flying status, animate its position
      if (drone.status === 'flying' && patrolStatus.value) {
        // Get or generate patrol route for this drone
        const patrolRoute = getOrCreatePatrolRoute(drone);
        
        // Calculate position along the route based on current time
        const animatedPosition = calculatePositionAlongRoute(patrolRoute, timestamp);
        
        // Update the drone's position and store it
        if (animatedPosition && animatedPosition.length >= 2) {
          animatedDrone.current_location = {
            coordinates: [
              animatedPosition[0], 
              animatedPosition[1], 
              animatedPosition[2] || 200
            ]
          };
           // Store the last known position for test drones too
          droneLastKnownPositions.value.set(drone.drone_id, animatedDrone.current_location.coordinates);
        }
      } else if (droneLastKnownPositions.value.has(drone.drone_id)) {
        // If patrol is stopped, use the last known position for rendering test drones
         animatedDrone.current_location = {
          coordinates: droneLastKnownPositions.value.get(drone.drone_id)
        };
      }
      
      return animatedDrone;
    });
    
    // Combine all drones
    const allDrones = [...animatedDrones, ...animatedTestDrones];
    
    const layers = [];
    
    // Add drone trail paths for flying drones
    if (showDrones.value && showFlightPaths.value) {
      layers.push(
        new PathLayer({
          id: 'drone-trails',
          data: allDrones.filter(d => d.status === 'flying'),
          pickable: false,
          widthScale: 2,
          widthMinPixels: 2,
          widthMaxPixels: 4,
          getPath: d => {
            const route = getOrCreatePatrolRoute(d);
            return route;
          },
          getColor: d => {
            const color = getDroneColor(d);
            return [color[0], color[1], color[2], 80]; // Semi-transparent trail
          },
          getWidth: 2,
          getDashArray: [3, 2],
          dashJustified: true,
          updateTriggers: {
            getPath: [timestamp]
          }
        })
      );
    }
      
      // 无人机扫描区域层
      if (showDrones.value) {
        // 添加扫描圆锥效果 (PathLayer Version)
        const coneLines = [];
        const segments = 24; // 增加分段数量使圆锥更平滑
        allDrones.filter(d => d.status === 'flying').forEach(drone => {
          const position = drone.current_location?.coordinates;
          if (!position) return;
              const [x, y, z] = position;
          const droneAltitude = z || 450; // Use new default altitude
          
          // Define base radius based on drone type - 缩小10倍
          const scanRadius = drone.type === 'surveillance' ? 0.035 : 
                           drone.type === 'security' ? 0.032 : 
                           drone.type === 'transport' ? 0.028 : 0.038;

          for (let i = 0; i < segments; i++) {
            const angle1 = (i / segments) * Math.PI * 2;
            const angle2 = ((i + 1) / segments) * Math.PI * 2;
            
            const p1x = x + Math.cos(angle1) * scanRadius;
            const p1y = y + Math.sin(angle1) * scanRadius;
            const p2x = x + Math.cos(angle2) * scanRadius;
            const p2y = y + Math.sin(angle2) * scanRadius;

            // Add line from drone to base point
            coneLines.push({
              path: [[x, y, droneAltitude], [p1x, p1y, 0]], // Line from top to base
              drone: drone
            });
            // Add line segment for the base circle
            coneLines.push({
                path: [[p1x, p1y, 0], [p2x, p2y, 0]], // Base circle segment
                drone: drone,
                isBase: true
            });
          }
        });

        layers.push(
          new PathLayer({
            id: 'drone-scan-cone-lines',
            data: coneLines,
            pickable: false,
            widthScale: 1,
            widthMinPixels: 0.7, // 加粗线条
            widthMaxPixels: 2,
            getPath: d => d.path,
            getColor: d => {
              // 颜色更深
              let baseColor;
              if (d.drone.type === 'surveillance') baseColor = [0, 140, 230]; 
              else if (d.drone.type === 'security') baseColor = [230, 10, 70];
              else if (d.drone.type === 'transport') baseColor = [100, 50, 230];
              else baseColor = [230, 40, 0];

              // Pulsing opacity, slightly brighter for base
              const pulseIntensity = 0.6 + 0.4 * Math.sin(timestamp / 700 + (d.isBase ? Math.PI / 2 : 0));
              const opacity = (d.isBase ? 130 : 90) * pulseIntensity; // 稍微增加透明度

              return [...baseColor, opacity];
            },
            getWidth: d => d.isBase ? 2 : 1.2,
            updateTriggers: {
              getColor: [timestamp]
            }
          })
        );
        
        // 添加圆锥体的填充层 - 这是主要的视觉效果
        allDrones.filter(d => d.status === 'flying').forEach((drone, index) => {
          const position = drone.current_location?.coordinates;
          if (!position) return;
          const [x, y, z] = position;
          const droneAltitude = z || 450;
          
          // 根据无人机类型设置扫描半径 - 缩小10倍
          const scanRadius = drone.type === 'surveillance' ? 0.035 : 
                             drone.type === 'security' ? 0.032 : 
                             drone.type === 'transport' ? 0.028 : 0.038;
          
          // 创建圆锥体的填充多边形数据
          const coneSegments = 36; // 更高的分段数使圆锥体更平滑
          const conePolygons = [];
          
          // 生成圆锥体的侧面 - 三角形
          for (let i = 0; i < coneSegments; i++) {
            const angle1 = (i / coneSegments) * Math.PI * 2;
            const angle2 = ((i + 1) / coneSegments) * Math.PI * 2;
            
            const p1x = x + Math.cos(angle1) * scanRadius;
            const p1y = y + Math.sin(angle1) * scanRadius;
            const p2x = x + Math.cos(angle2) * scanRadius;
            const p2y = y + Math.sin(angle2) * scanRadius;
            
            // 每个侧面是一个三角形 (无人机点 -> 底部边缘点1 -> 底部边缘点2)
            conePolygons.push({
              polygon: [[x, y, droneAltitude], [p1x, p1y, 0], [p2x, p2y, 0]],
              drone: drone
            });
          }
          
          // 添加圆锥体填充图层
          layers.push(
            new PolygonLayer({
              id: `drone-cone-fill-${drone.drone_id}`,
              data: conePolygons,
              pickable: false,
              stroked: false,
              filled: true,
              wireframe: false,
              getPolygon: d => d.polygon,
              getFillColor: d => {
                // 根据无人机类型设置基础颜色 - 颜色更深且更饱和
                let baseColor;
                if (d.drone.type === 'surveillance') baseColor = [0, 130, 220]; // 更深的蓝
                else if (d.drone.type === 'security') baseColor = [220, 10, 60]; // 更深的红
                else if (d.drone.type === 'transport') baseColor = [100, 40, 220]; // 更深的紫
                else baseColor = [220, 40, 0]; // 更深的橙
                
                // 添加脉冲效果
                const pulseIntensity = 0.5 + 0.5 * Math.sin(timestamp / 800 + (drone.drone_id.length % 5));
                
                // 透明的填充效果 - 增加透明度
                return [...baseColor, 30 * pulseIntensity]; // 增加填充透明度
              },
              updateTriggers: {
                getFillColor: [timestamp]
              }
            })
          );
          
          // 添加底部圆形填充
          layers.push(
            new PolygonLayer({
              id: `drone-cone-base-${drone.drone_id}`,
              data: [{
                center: [x, y],
                radius: scanRadius,
                drone: drone
              }],
              pickable: false,
              stroked: true,
              filled: true,
              wireframe: false,
              lineWidthMinPixels: 1,
              getPolygon: d => {
                const points = [];
                const segments = 36;
                for (let i = 0; i < segments; i++) {
                  const angle = (i / segments) * Math.PI * 2;
                  points.push([
                    d.center[0] + Math.cos(angle) * d.radius,
                    d.center[1] + Math.sin(angle) * d.radius,
                    0
                  ]);
                }
              return points;
            },
            getFillColor: d => {
                // 根据无人机类型设置基础颜色 - 颜色更深且更饱和
                let baseColor;
                if (d.drone.type === 'surveillance') baseColor = [0, 130, 220];
                else if (d.drone.type === 'security') baseColor = [220, 10, 60];
                else if (d.drone.type === 'transport') baseColor = [100, 40, 220];
                else baseColor = [220, 40, 0];
                
                // 添加脉冲效果
                const pulseIntensity = 0.5 + 0.5 * Math.sin(timestamp / 900 + (drone.drone_id.length % 3));
                
                // 透明的填充效果 - 增加透明度
                return [...baseColor, 50 * pulseIntensity]; // 增加底部填充透明度
              },
              getLineColor: d => {
                // 根据无人机类型设置基础颜色 - 颜色更深且更饱和
                let baseColor;
                if (d.drone.type === 'surveillance') baseColor = [0, 130, 220];
                else if (d.drone.type === 'security') baseColor = [220, 10, 60];
                else if (d.drone.type === 'transport') baseColor = [100, 40, 220];
                else baseColor = [220, 40, 0];
                
                // 添加脉冲效果
                const pulseIntensity = 0.6 + 0.4 * Math.sin(timestamp / 600);
                
                return [...baseColor, 140 * pulseIntensity]; // 增加线条亮度
              },
              getLineWidth: 1.5,
            updateTriggers: {
              getFillColor: [timestamp],
                getLineColor: [timestamp]
            }
          })
        );
        
          // 添加中央光束效果
          layers.push(
            new PathLayer({
              id: `drone-central-beam-${drone.drone_id}`,
              data: [{
                path: [[x, y, droneAltitude], [x, y, 0]],
                drone: drone
              }],
              pickable: false,
              widthScale: 5,
              widthMinPixels: 2,
              widthMaxPixels: 5,
              getPath: d => d.path,
              getColor: d => {
                // 根据无人机类型设置基础颜色 - 颜色更深更亮
                let baseColor;
                if (d.drone.type === 'surveillance') baseColor = [10, 160, 240]; // 更深的亮蓝
                else if (d.drone.type === 'security') baseColor = [240, 30, 90]; // 更深的亮红
                else if (d.drone.type === 'transport') baseColor = [110, 60, 240]; // 更深的亮紫
                else baseColor = [240, 60, 0]; // 更深的亮橙
                
                // 添加闪烁效果
                const pulseIntensity = 0.7 + 0.3 * Math.sin(timestamp / 300);
                
                return [...baseColor, 230 * pulseIntensity]; // 进一步增加亮度
              },
              getWidth: 3,
              updateTriggers: {
                getColor: [timestamp]
              }
            })
          );
        });
        
        // 添加扫描波纹效果 - 新增
        allDrones.filter(d => d.status === 'flying').forEach((drone, index) => {
          const position = drone.current_location?.coordinates;
          if (!position) return;
          
          // 为每个无人机创建2个更快的扫描波纹
          for (let i = 0; i < 2; i++) {
            // 计算当前波纹的半径 (0-1范围)，速度更快
            const seed = (index * 10 + i * 50) % 800;
            const radiusRatio = ((timestamp + seed) % 2000) / 2000;
            
            // 波纹最大范围 - 缩小10倍
            const maxRadius = drone.type === 'surveillance' ? 0.045 : 
                            drone.type === 'security' ? 0.042 : 
                            drone.type === 'transport' ? 0.038 : 0.048;
            
            // 当前波纹半径
            const currentRadius = maxRadius * radiusRatio;
            
            // 波纹透明度 (开始高，然后逐渐消失)
            const opacity = 140 * (1 - radiusRatio * radiusRatio);
            
            if (opacity > 10) { // 只有当波纹足够可见时才添加
              // 根据无人机类型设置波纹颜色
              let waveColor;
              if (drone.type === 'surveillance') waveColor = [50, 200, 255, opacity];
              else if (drone.type === 'security') waveColor = [255, 50, 120, opacity];
              else if (drone.type === 'transport') waveColor = [150, 110, 255, opacity];
              else waveColor = [255, 80, 20, opacity];
              
              // 创建波纹图层
        layers.push(
          new PolygonLayer({
                  id: `drone-wave-${drone.drone_id}-${i}`,
                  data: [{
                    position: position,
                    radius: currentRadius,
                    color: waveColor
                  }],
            pickable: false,
                  stroked: true,
                  filled: false,
            wireframe: true,
            lineWidthMinPixels: 1,
            getPolygon: d => {
                    const [x, y, z] = d.position;
                    const points = [];
                    const segments = 36;
                    
                    for (let j = 0; j < segments; j++) {
                      const angle = (j / segments) * Math.PI * 2;
                      const px = x + Math.cos(angle) * d.radius;
                      const py = y + Math.sin(angle) * d.radius;
                      points.push([px, py, 0]);
                    }
                    
                    return points;
                  },
                  getLineColor: d => d.color,
                  getLineWidth: 1.8 * (1 - radiusRatio),
                  updateTriggers: {
                    getPolygon: [timestamp],
                    getLineColor: [timestamp],
                    getLineWidth: [timestamp]
                  }
                })
              );
            }
          }
        });
        
        // 添加无人机组网连接线
        if (allDrones.length > 1) {
          // 创建无人机之间的连接线以显示组网效果
          const networkConnections = [];
          
          // 为每个无人机找到最近的3个无人机建立连接
          allDrones.forEach(drone => {
            if (drone.status !== 'flying') return;
            
            // 获取当前无人机位置
            const dronePos = drone.current_location?.coordinates;
            if (!dronePos) return;
            
            // 计算与其他无人机的距离
            const connections = allDrones
              .filter(other => other.drone_id !== drone.drone_id && other.status === 'flying')
              .map(other => {
                const otherPos = other.current_location?.coordinates;
                if (!otherPos) return null;
                
                // 计算距离
                const dx = dronePos[0] - otherPos[0];
                const dy = dronePos[1] - otherPos[1];
                const distance = Math.sqrt(dx*dx + dy*dy);
                
                return {
                  drone: drone,
                  other: other,
                  distance: distance
                };
              })
              .filter(conn => conn !== null)
              .sort((a, b) => a.distance - b.distance)
              .slice(0, 5); // 增加到最近的5个连接，强化网络密度
            
            // 添加连接
            connections.forEach(conn => {
              networkConnections.push({
                source: drone,
                target: conn.other,
                distance: conn.distance
              });
            });
          });
          
          // 添加组网连接线 - 增强效果
          layers.push(
            new PathLayer({
              id: 'drone-network-connections',
              data: networkConnections,
              pickable: false,
              widthScale: 2,
              widthMinPixels: 1.5, // 减小线宽
              widthMaxPixels: 3,  // 减小线宽
              getPath: d => {
                const sourcePos = d.source.current_location?.coordinates;
                const targetPos = d.target.current_location?.coordinates;
                
                if (!sourcePos || !targetPos) return [];
                
                // 创建弧形连接线
                const midX = (sourcePos[0] + targetPos[0]) / 2;
                const midY = (sourcePos[1] + targetPos[1]) / 2;
                // 弧线高度与距离相关，距离越远弧度越高
                const dx = sourcePos[0] - targetPos[0];
                const dy = sourcePos[1] - targetPos[1];
                const distance = Math.sqrt(dx*dx + dy*dy);
                const arcHeight = Math.max(sourcePos[2] || 650, targetPos[2] || 650) + distance * 400; // 高度与距离正相关
                
                const midPoint = [midX, midY, arcHeight];
                
                // 生成弧线上的多个点 - 增加点数使弧线更平滑
                const arcPoints = [];
                const segments = 30; // 从10增加到30
                for (let i = 0; i <= segments; i++) {
                  const t = i / segments;
                  let p;
                  // 使用二次贝塞尔曲线插值
                  const t_ = 1 - t;
                  p = [
                    t_*t_*sourcePos[0] + 2*t_*t*midPoint[0] + t*t*targetPos[0],
                    t_*t_*sourcePos[1] + 2*t_*t*midPoint[1] + t*t*targetPos[1],
                    t_*t_*(sourcePos[2] || 650) + 2*t_*t*midPoint[2] + t*t*(targetPos[2] || 650)
                  ];
                  arcPoints.push(p);
                }
                
                return arcPoints;
              },
              getColor: d => {
                // 根据距离设置颜色
                const maxDistance = 0.3; // 最大连接距离
                const ratio = Math.min(d.distance / maxDistance, 1);
                
                // 组网连接颜色 - 使用更加明亮的颜色
                const color = [60, 180, 255]; // 明亮的蓝色基础
                
                // 添加呼吸动画效果
                const pulseIntensity = 0.6 + 0.4 * Math.sin(timestamp / 500);
                const opacity = 220 * pulseIntensity * (1 - ratio * 0.6);
                
                return [...color, opacity];
              },
              getDashArray: [3, 2],
              getWidth: d => {
                // 距离越近，线越粗
                const maxDistance = 0.3;
                const ratio = Math.min(d.distance / maxDistance, 1);
                return 5 * (1 - ratio * 0.6);
              },
              updateTriggers: {
                getPath: [timestamp],
                getColor: [timestamp],
                getWidth: [timestamp]
              }
            })
          );
          
          // 添加网络连接点 - 数据传输效果强化
          const networkNodes = networkConnections.map(conn => {
            const sourcePos = conn.source.current_location?.coordinates;
            const targetPos = conn.target.current_location?.coordinates;
            
            if (!sourcePos || !targetPos) return null;
            
            // 计算连接线中点 - 弧形路径上的点
            const midX = (sourcePos[0] + targetPos[0]) / 2;
            const midY = (sourcePos[1] + targetPos[1]) / 2;
            const midZ = Math.max(sourcePos[2] || 350, targetPos[2] || 350) + 50;
            
            return {
              position: [midX, midY, midZ],
              sourceId: conn.source.drone_id,
              targetId: conn.target.drone_id,
              distance: conn.distance
            };
          }).filter(node => node !== null);
          
          // 添加网络数据流动点
          layers.push(
            new ScatterplotLayer({
              id: 'drone-network-nodes',
              data: networkNodes,
              pickable: false,
              stroked: true,
              filled: true,
              radiusScale: 2,
              radiusMinPixels: 4,
              radiusMaxPixels: 8,
              getPosition: d => d.position,
              getFillColor: d => {
                // 数据传输点脉冲 - 更亮的颜色
                const pulseIntensity = 0.5 + 0.5 * Math.sin(timestamp / 300 + d.position[0] * 10);
                return [120, 220, 255, 255 * pulseIntensity];
              },
              getLineColor: [255, 255, 255, 100],
            getLineWidth: 1,
              getRadius: d => {
                const pulseSize = 1 + 0.7 * Math.sin(timestamp / 300 + d.position[0] * 10);
                return 4 * pulseSize;
            },
            updateTriggers: {
              getFillColor: [timestamp],
                getRadius: [timestamp]
            }
          })
        );

          // 添加数据流动效果 - 沿线移动的粒子
          const flowParticles = [];
          networkConnections.forEach(conn => {
            const sourcePos = conn.source.current_location?.coordinates;
            const targetPos = conn.target.current_location?.coordinates;
            
            if (!sourcePos || !targetPos) return;
            
            // 创建弧形路径上的流动点
            const midPoint = [
              (sourcePos[0] + targetPos[0]) / 2,
              (sourcePos[1] + targetPos[1]) / 2,
              Math.max(sourcePos[2] || 350, targetPos[2] || 350) + 50
            ];
            
            // 创建3-5个沿路径流动的粒子
            const particleCount = 2 + Math.floor(Math.random() * 3);
            for (let i = 0; i < particleCount; i++) {
              // 计算粒子在路径上的位置 (0-1)
              const pathOffset = (timestamp / 2000 + i / particleCount) % 1;
              
              let particlePos;
              if (pathOffset < 0.5) {
                // 前半段路径 (源 -> 中点)
                const segmentPos = pathOffset * 2; // 0-1
                particlePos = [
                  sourcePos[0] + (midPoint[0] - sourcePos[0]) * segmentPos,
                  sourcePos[1] + (midPoint[1] - sourcePos[1]) * segmentPos,
                  sourcePos[2] + (midPoint[2] - sourcePos[2]) * segmentPos
                ];
              } else {
                // 后半段路径 (中点 -> 目标)
                const segmentPos = (pathOffset - 0.5) * 2; // 0-1
                particlePos = [
                  midPoint[0] + (targetPos[0] - midPoint[0]) * segmentPos,
                  midPoint[1] + (targetPos[1] - midPoint[1]) * segmentPos,
                  midPoint[2] + (targetPos[2] - midPoint[2]) * segmentPos
                ];
              }
              
              flowParticles.push({
                position: particlePos,
                sourceId: conn.source.drone_id,
                targetId: conn.target.drone_id,
                pathOffset: pathOffset,
                direction: i % 2 === 0 // 双向数据流动
              });
            }
          });
          
          // 添加数据流动粒子图层
          layers.push(
            new ScatterplotLayer({
              id: 'drone-network-flow-particles',
              data: flowParticles,
              pickable: false,
              stroked: false,
              filled: true,
              radiusScale: 1.5,
              radiusMinPixels: 2,
              radiusMaxPixels: 5,
              getPosition: d => d.position,
              getFillColor: d => {
                // 双向数据流不同颜色
                return d.direction ? 
                  [0, 220, 255, 230] : // 蓝色方向
                  [220, 180, 0, 230];  // 黄色方向
              },
              getRadius: d => {
                // 流动尾部变小效果
                const tailEffect = d.direction ? 
                  d.pathOffset : (1 - d.pathOffset);
                return 3 * (0.6 + 0.4 * tailEffect);
              },
              updateTriggers: {
                getPosition: [timestamp],
                getRadius: [timestamp]
              }
            })
          );
        }
      }
      
      // 无人机图层 - 先添加光晕
      if (showDrones.value) {
        // 添加无人机光晕
        layers.push(
          new ScatterplotLayer({
            id: 'drones-halo',
            data: allDrones,
            pickable: false,
            stroked: false,
            filled: true,
            radiusScale: 4,
            radiusMinPixels: 10,
            radiusMaxPixels: 25,
            lineWidthMinPixels: 1,
            getPosition: d => {
              if (!d.current_location || !d.current_location.coordinates) {
                return [map.getCenter().lng, map.getCenter().lat, 0]
              }
              const coords = d.current_location.coordinates
              return [coords[0], coords[1], (coords[2] || 200) - 10]
            },
            getFillColor: d => {
              const color = getDroneColor(d)
              // Animate glow opacity for flying drones
              const opacityFactor = d.status === 'flying' ? 
                0.2 + 0.1 * Math.sin(timestamp / 500) : 0.2
              return [color[0], color[1], color[2], 30 * opacityFactor]
            },
            getRadius: d => {
              // Animate radius for flying drones
              if (d.status === 'flying') {
                return 80 + 10 * Math.sin(timestamp / 700)
              }
              return 80
            },
            updateTriggers: {
              getFillColor: [timestamp],
              getRadius: [timestamp]
            }
          })
        )
        
      // Main drone layer - using IconLayer for more detailed rendering
        layers.push(
        new IconLayer({
          id: 'drones-icon-layer',
          data: allDrones,
            pickable: true,
          sizeScale: 6, // 进一步减小基础比例
          sizeMinPixels: 30, // 进一步减小最小像素尺寸
          sizeMaxPixels: 60, // 进一步减小最大像素尺寸
            getPosition: d => {
              if (!d.current_location || !d.current_location.coordinates) {
                return [map.getCenter().lng, map.getCenter().lat, 0]
              }
              const coords = d.current_location.coordinates
              return [coords[0], coords[1], coords[2] || 350]
            },
          getIcon: d => getDroneIcon(d),
          getSize: d => {
            // 进一步减小无人机大小，并保持脉动效果
            const baseSize = d.drone_id === props.selectedDroneId ? 35 : 30;
            return baseSize + (d.status === 'flying' ? 3 * Math.sin(timestamp / 500) : 0);
          },
          getAngle: d => {
            // Calculate heading angle for moving drones
            if (d.status === 'flying' && patrolStatus.value) {
              const route = getOrCreatePatrolRoute(d);
              const heading = calculateDroneHeading(route, timestamp);
              return heading;
            }
            return 0;
          },
          onHover: (info) => {
            if (info.object) {
              hoveredDroneInfo.value = info.object;
            } else {
              hoveredDroneInfo.value = null;
            }
          },
          onClick: (info) => {
            if (info.object) {
              emit('drone-clicked', info.object);
            }
          },
          updateTriggers: {
            getAngle: [timestamp],
            getSize: [timestamp]
          }
          })
        );
      }
      
      // 添加锥形扫描区效果 (模拟图中的扫描锥)
      layers.push(
        new PolygonLayer({
          id: 'drone-scan-cone',
          data: allDrones.filter(d => d.status === 'flying'),
          pickable: false,
          extruded: true,
          filled: true,
          wireframe: true,
          lineWidthMinPixels: 0.5,
          getPolygon: d => {
            // 获取无人机位置
            const position = d.current_location?.coordinates || [map.getCenter().lng, map.getCenter().lat, 0];
            const [x, y, z] = position;
            
            // 计算当前扫描方向
            let angle;
            if (patrolStatus.value) {
              // 巡逻模式下，使用实际航向
              const route = getOrCreatePatrolRoute(d);
              angle = calculateDroneHeading(route, timestamp) * (Math.PI / 180);
            } else {
              // 静止模式下，创建旋转扫描效果
              angle = (timestamp / 2000) % (Math.PI * 2);
            }
            
            // 计算锥形顶点和底部四个点
            const coneDistance = d.type === 'surveillance' ? 0.01 : 
                                d.type === 'security' ? 0.008 : 
                                d.type === 'transport' ? 0.006 : 0.012;
            
            // 创建锥形底部的半径
            const baseRadius = coneDistance * 0.5;
            
            // 锥形底部中心点
            const coneX = x + Math.cos(angle) * coneDistance;
            const coneY = y + Math.sin(angle) * coneDistance;
            
            // 创建锥形的底部圆形边缘点
            const numSegments = 12;
            const points = [];
            
            for (let i = 0; i < numSegments; i++) {
              const segmentAngle = (i / numSegments) * Math.PI * 2;
              const px = coneX + Math.cos(segmentAngle) * baseRadius;
              const py = coneY + Math.sin(segmentAngle) * baseRadius;
              points.push([px, py, 0]);
            }
            
            return points;
          },
          getFillColor: d => {
            const baseColor = d.type === 'surveillance' ? [0, 255, 255] : 
                            d.type === 'security' ? [255, 0, 85] : 
                            d.type === 'transport' ? [136, 85, 255] : [255, 0, 0];
            
            // 半透明效果
            return [...baseColor, 60];
          },
          getLineColor: d => {
            const baseColor = d.type === 'surveillance' ? [0, 255, 255] : 
                             d.type === 'security' ? [255, 0, 85] : 
                             d.type === 'transport' ? [136, 85, 255] : [255, 0, 0];
            return [...baseColor, 120];
          },
          getElevation: d => {
            return 0; // 从地面开始
          },
          getLineWidth: 1,
          elevationScale: 1,
          updateTriggers: {
            getFillColor: [timestamp],
            getPolygon: [timestamp]
          }
        })
      );
      
      // 添加光锥连接线
      layers.push(
        new PathLayer({
          id: 'drone-scan-lines',
          data: allDrones.filter(d => d.status === 'flying'),
          pickable: false,
          widthScale: 0.5,
          widthMinPixels: 0.5,
          widthMaxPixels: 2,
          getPath: d => {
            // 获取无人机位置
            const position = d.current_location?.coordinates || [map.getCenter().lng, map.getCenter().lat, 0];
            const [x, y, z] = position;
            
            // 计算当前扫描方向
            let angle;
            if (patrolStatus.value) {
              // 巡逻模式下，使用实际航向
              const route = getOrCreatePatrolRoute(d);
              angle = calculateDroneHeading(route, timestamp) * (Math.PI / 180);
            } else {
              // 静止模式下，创建旋转扫描效果
              angle = (timestamp / 2000) % (Math.PI * 2);
            }
            
            // 计算锥形顶点和底部位置
            const coneDistance = d.type === 'surveillance' ? 0.01 : 
                                d.type === 'security' ? 0.008 : 
                                d.type === 'transport' ? 0.006 : 0.012;
            
            // 锥形底部中心点
            const coneX = x + Math.cos(angle) * coneDistance;
            const coneY = y + Math.sin(angle) * coneDistance;
            
            // 创建从无人机到锥形底部中心的连接线
            return [
              [x, y, z || 450], // Use new default altitude
              [coneX, coneY, 0]
            ];
          },
          getColor: d => {
            const baseColor = d.type === 'surveillance' ? [0, 255, 255] : 
                            d.type === 'security' ? [255, 0, 85] : 
                            d.type === 'transport' ? [136, 85, 255] : [255, 0, 0];
            
            // 添加脉冲动画效果
            const opacity = 120 + 60 * Math.sin(timestamp / 300);
            return [...baseColor, opacity];
          },
          getWidth: 1,
          updateTriggers: {
            getPath: [timestamp],
            getColor: [timestamp]
          }
        })
      );
      
      // 添加投影中心点闪烁效果
      layers.push(
        new ScatterplotLayer({
          id: 'drone-scan-center',
          data: allDrones.filter(d => d.status === 'flying'),
          pickable: false,
          stroked: false,
          filled: true,
          radiusScale: 2,
          radiusMinPixels: 1,
          radiusMaxPixels: 3,
          getPosition: d => {
            // 获取无人机位置
            const position = d.current_location?.coordinates || [map.getCenter().lng, map.getCenter().lat, 0];
            const [x, y, z] = position;
            
            // 计算当前扫描方向
            let angle;
            if (patrolStatus.value) {
              // 巡逻模式下，使用实际航向
              const route = getOrCreatePatrolRoute(d);
              angle = calculateDroneHeading(route, timestamp) * (Math.PI / 180);
            } else {
              // 静止模式下，创建旋转扫描效果
              angle = (timestamp / 2000) % (Math.PI * 2);
            }
            
            // 计算锥形顶点和底部位置
            const coneDistance = d.type === 'surveillance' ? 0.01 : 
                                d.type === 'security' ? 0.008 : 
                                d.type === 'transport' ? 0.006 : 0.012;
            
            // 锥形底部中心点
            const coneX = x + Math.cos(angle) * coneDistance;
            const coneY = y + Math.sin(angle) * coneDistance;
            
            return [coneX, coneY, 0];
          },
          getFillColor: d => {
            const baseColor = d.type === 'surveillance' ? [0, 255, 255] : 
                            d.type === 'security' ? [255, 0, 85] : 
                            d.type === 'transport' ? [136, 85, 255] : [255, 0, 0];
            
            // 添加脉冲动画效果
            const opacity = 180 + 70 * Math.sin(timestamp / 200);
            return [...baseColor, opacity];
          },
          getRadius: d => {
            // 添加脉冲效果
            return 5 + 3 * Math.sin(timestamp / 300);
          },
          updateTriggers: {
            getPosition: [timestamp],
            getFillColor: [timestamp],
            getRadius: [timestamp]
          }
        })
      );
      
      // 设置图层
      deck.setProps({ layers })
    
    // 如果在巡逻模式下，继续动画
    if (patrolStatus.value && !animationFrameId) {
      animationFrameId = requestAnimationFrame(animatePatrol);
    }
    } catch (error) {
      console.error('渲染deck.gl图层时出错:', error)
    }
  }

// Animation function for smooth patrol movement
const animatePatrol = () => {
  if (patrolStatus.value) {
    renderDeckLayers();
    animationFrameId = requestAnimationFrame(animatePatrol);
  } else if (animationFrameId) {
    cancelAnimationFrame(animationFrameId);
    animationFrameId = null;
  }
};
  
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
  
// Helper function to adjust color brightness
const adjustColor = (color, amount) => {
  // Simple implementation - in production this would be more sophisticated
  // Just return the original color for now
  return color;
}

// Get drone SVG icon
const getDroneSvgIcon = (drone) => {
  // Select base color based on drone status with higher saturation
  const statusColor = drone.status === 'flying' ? '#00ff00' :
                  drone.status === 'charging' ? '#ff9500' :
                  drone.status === 'maintenance' ? '#ffcc00' :
                  drone.status === 'offline' ? '#8e8e93' : '#007aff';
  
  // Type-specific colors with higher saturation
  const typeColor = drone.type === 'surveillance' ? '#00ffff' :
                   drone.type === 'security' ? '#ff2d55' : 
                   drone.type === 'transport' ? '#8855ff' : 
                   drone.type === 'emergency' ? '#ff0000' : '#00ffff';
  
  // Battery level visualization
  const batteryLevel = drone.battery_level || 100;
  const batteryColor = batteryLevel > 60 ? '#00ff00' : 
                       batteryLevel > 30 ? '#ffcc00' : '#ff0000';
  
  // Generate unique ID for this drone's animations
  const uniqueId = `drone-${drone.drone_id}`;
  
  // 创建一个简化但更加清晰的3D无人机SVG图标
  return `
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" width="64" height="64">
      <defs>
        <!-- 发光效果 - 增强光晕效果 -->
        <filter id="glow${uniqueId}" x="-50%" y="-50%" width="200%" height="200%">
          <feGaussianBlur stdDeviation="2.5" result="blur" />
          <feFlood flood-color="${typeColor}" flood-opacity="0.95" result="color"/>
          <feComposite in="color" in2="blur" operator="in" result="glow"/>
          <feComposite in="glow" in2="SourceGraphic" operator="over" />
        </filter>
        
        <!-- 无人机机体金属质感 - 增强金属质感 -->
        <linearGradient id="bodyGradient${uniqueId}" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stop-color="#ffffff" />
          <stop offset="50%" stop-color="${typeColor}" />
          <stop offset="100%" stop-color="#111111" />
        </linearGradient>
        
        <!-- 螺旋桨动画 - 更明显的动画效果 -->
        <linearGradient id="propGradient${uniqueId}" x1="0%" y1="0%" x2="100%" y2="0%">
          <stop offset="0%" stop-color="#ffffff" stop-opacity="0.95"/>
          <stop offset="100%" stop-color="#aaaaaa" stop-opacity="0.4"/>
        </linearGradient>
      </defs>
      
      <!-- 机身 -->
      <g filter="url(#glow${uniqueId})">
        <!-- 机身主体 - 中央部分 -->
        <circle cx="32" cy="32" r="10" fill="url(#bodyGradient${uniqueId})" stroke="#555" stroke-width="0.5"/>
        
        <!-- 四个机臂 -->
        <line x1="32" y1="32" x2="15" y2="15" stroke="#333" stroke-width="3" />
        <line x1="32" y1="32" x2="49" y2="15" stroke="#333" stroke-width="3" />
        <line x1="32" y1="32" x2="15" y2="49" stroke="#333" stroke-width="3" />
        <line x1="32" y1="32" x2="49" y2="49" stroke="#333" stroke-width="3" />
        
        <!-- 四个电机和螺旋桨 -->
        <g>
          <!-- 左上电机与螺旋桨 -->
          <circle cx="15" cy="15" r="4" fill="#444" stroke="#222" stroke-width="0.5"/>
          ${drone.status === 'flying' ? `
          <circle cx="15" cy="15" r="8" fill="url(#propGradient${uniqueId})" opacity="0.7">
            <animateTransform attributeName="transform" type="rotate" from="0 15 15" to="360 15 15" dur="0.15s" repeatCount="indefinite"/>
          </circle>` : `
          <line x1="9" y1="15" x2="21" y2="15" stroke="#aaa" stroke-width="1.5"/>
          <line x1="15" y1="9" x2="15" y2="21" stroke="#aaa" stroke-width="1.5"/>`}
          
          <!-- 右上电机与螺旋桨 -->
          <circle cx="49" cy="15" r="4" fill="#444" stroke="#222" stroke-width="0.5"/>
          ${drone.status === 'flying' ? `
          <circle cx="49" cy="15" r="8" fill="url(#propGradient${uniqueId})" opacity="0.7">
            <animateTransform attributeName="transform" type="rotate" from="0 49 15" to="360 49 15" dur="0.17s" repeatCount="indefinite"/>
          </circle>` : `
          <line x1="43" y1="15" x2="55" y2="15" stroke="#aaa" stroke-width="1.5"/>
          <line x1="49" y1="9" x2="49" y2="21" stroke="#aaa" stroke-width="1.5"/>`}
          
          <!-- 左下电机与螺旋桨 -->
          <circle cx="15" cy="49" r="4" fill="#444" stroke="#222" stroke-width="0.5"/>
          ${drone.status === 'flying' ? `
          <circle cx="15" cy="49" r="8" fill="url(#propGradient${uniqueId})" opacity="0.7">
            <animateTransform attributeName="transform" type="rotate" from="0 15 49" to="360 15 49" dur="0.16s" repeatCount="indefinite"/>
          </circle>` : `
          <line x1="9" y1="49" x2="21" y2="49" stroke="#aaa" stroke-width="1.5"/>
          <line x1="15" y1="43" x2="15" y2="55" stroke="#aaa" stroke-width="1.5"/>`}
          
          <!-- 右下电机与螺旋桨 -->
          <circle cx="49" cy="49" r="4" fill="#444" stroke="#222" stroke-width="0.5"/>
          ${drone.status === 'flying' ? `
          <circle cx="49" cy="49" r="8" fill="url(#propGradient${uniqueId})" opacity="0.7">
            <animateTransform attributeName="transform" type="rotate" from="0 49 49" to="360 49 49" dur="0.14s" repeatCount="indefinite"/>
          </circle>` : `
          <line x1="43" y1="49" x2="55" y2="49" stroke="#aaa" stroke-width="1.5"/>
          <line x1="49" y1="43" x2="49" y2="55" stroke="#aaa" stroke-width="1.5"/>`}
        </g>
        
        <!-- 状态指示灯 - 增强亮度 -->
        <circle cx="32" cy="32" r="5" fill="${statusColor}" opacity="0.9">
          ${drone.status === 'flying' || drone.status === 'charging' ? 
          `<animate attributeName="opacity" values="0.6;1;0.6" dur="1s" repeatCount="indefinite"/>` : ''}
        </circle>
        
        <!-- 电池电量指示器 -->
        <rect x="27" y="20" width="10" height="3" rx="1" fill="#222" stroke="#444" stroke-width="0.3"/>
        <rect x="27.5" y="20.5" width="${(batteryLevel/100) * 9}" height="2" rx="0.5" fill="${batteryColor}"/>
        
        <!-- 无人机ID标识 -->
        <text x="32" y="48" text-anchor="middle" font-size="5" fill="white" stroke="black" stroke-width="0.5" font-weight="bold">${drone.name.substring(0, 6)}</text>
      </g>
    </svg>
  `;
};

// Get drone icon for IconLayer
const getDroneIcon = (drone) => {
  // Ensure proper encoding for complex SVGs with special characters
  const svgContent = getDroneSvgIcon(drone);
  const encodedSvg = encodeURIComponent(svgContent)
    .replace(/'/g, '%27')
    .replace(/"/g, '%22');
  
  const dataUrl = `data:image/svg+xml;charset=utf-8,${encodedSvg}`;
  
  return {
    url: dataUrl,
    width: 512,
    height: 512,
    anchorX: 256,
    anchorY: 256,
    mask: false
  };
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
      map.once('style.load', () => {
        map.jumpTo({
          center: currentCenter,
          zoom: currentZoom,
          pitch: currentPitch,
          bearing: currentBearing
        });
        
        // 重新添加3D建筑层
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
      console.log('飞行到武汉市全景');
      
      // 添加动画效果 - 降低缩放级别以显示整个武汉市
      map.flyTo({
        center: [114.33, 30.57], // 武汉市中心位置
        zoom: 10.5, // 更合适的缩放级别以显示武汉核心城区
        pitch: 60, // 增加视角倾斜度以更好地看到扫描效果
        bearing: 25, // 稍微调整视角方向
        duration: 3000, // 较长的动画时间
        essential: true
      });
    } catch (error) {
      console.error('飞行到武汉市时出错:', error);
    }
  };

  // 初始化时添加动态跳转到武汉大学
  const initializeWithAnimation = () => {
    // 首先定位到默认位置的较远视角
    if (map) {
      console.log('初始化动态飞行到武汉市');
      
      // 设置初始视角为较远的视角
      map.jumpTo({
        center: [114.3, 30.62], // 稍微偏北的武汉市位置
        zoom: 10, // 更小的缩放级别以显示更广阔的区域
        pitch: 0,
        bearing: 0
      });
      
      // 延迟一秒后执行飞行动画
      setTimeout(() => {
        flyToWhu();
      }, 1000);
    }
  };
  
// 启动所有无人机巡逻
const startPatrol = () => {
  if (!map) return;
  
  try {
    console.log('开始无人机巡逻');
    patrolStatus.value = true;
    
    // DO NOT Clear existing routes - let animation continue or generate if needed
    // dronePatrolRoutes.clear(); 
    
    // Start animation loop
    if (!animationFrameId) {
      animationFrameId = requestAnimationFrame(animatePatrol);
    }
  } catch (error) {
    console.error('启动巡逻时出错:', error);
  }
};

// 停止所有无人机巡逻
const stopPatrol = () => {
  if (!map) return;
  
  try {
    console.log('停止无人机巡逻');
    patrolStatus.value = false;
    
    // Cancel animation frame
    if (animationFrameId) {
      cancelAnimationFrame(animationFrameId);
      animationFrameId = null;
    }
    
    // Force one last render to capture final positions in droneLastKnownPositions
    renderDeckLayers();
    
  } catch (error) {
    console.error('停止巡逻时出错:', error);
  }
};

  // 修改开始巡逻方法
const startDronePatrol = (drones, speed = 1.0) => {
    if (!map) {
      console.warn('地图实例未初始化，无法开始无人机巡逻');
      return;
    }
    console.log('开始无人机巡逻模拟:', drones);
    
    try {
      // 设置巡逻状态为真
      patrolStatus.value = true;
    droneSpeedFactor.value = speed || 1.0;
    
    // Clear existing routes to generate new ones
    dronePatrolRoutes.clear();
    
    // Set up animation frame for smoother movement
    if (!animationFrameId) {
      animationFrameId = requestAnimationFrame(animatePatrol);
    }
    
    // 刷新图层
    renderDeckLayers();
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
    
    // Cancel animation frame
    if (animationFrameId) {
      cancelAnimationFrame(animationFrameId);
      animationFrameId = null;
    }
    
    // 刷新图层
    renderDeckLayers();
    } catch (error) {
      console.error('停止巡逻时出错:', error);
    }
  };
  
  // 公开巡逻状态
  const getPatrolStatus = () => {
    return patrolStatus.value;
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
          
          // 监听地图加载完成事件，确保map初始化后再初始化deck
          if (map) {
            map.once('load', () => {
              console.log('地图加载完成，准备初始化Deck.gl');
              // 等待一小段时间确保地图完全准备好
              setTimeout(() => {
                initDeck();
              }, 500);
            });
          }
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
  if (animationFrameId) {
    cancelAnimationFrame(animationFrameId);
    animationFrameId = null;
  }
  
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
  startPatrol,
  stopPatrol
  })
  </script>
  
  <style scoped>
  .mapboxgl-canvas {
    outline: none;
  }
  
  /* deck.gl canvas occupies the same position as mapbox */
  #deck-canvas {
    z-index: 5; /* 提高z-index确保在地图上层 */
    pointer-events: none !important; /* 修改为none，让鼠标事件可以穿透到地图 */
  }
  
  /* 添加无人机图标高亮效果 */
  .drone-highlight {
    animation: pulse 1.5s infinite;
  }
  
  @keyframes pulse {
    0% { transform: scale(1); opacity: 1; }
    50% { transform: scale(1.1); opacity: 0.8; }
    100% { transform: scale(1); opacity: 1; }
  }
  </style>