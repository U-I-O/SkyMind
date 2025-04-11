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
        </div>
      </div>
      
      <!-- 坐标信息 -->
      <div class="absolute bottom-4 left-4 z-10 bg-white bg-opacity-70 p-2 rounded-md text-xs text-gray-700">
        <div>经度: {{ formatCoordinate(currentPosition.lng) }}</div>
        <div>纬度: {{ formatCoordinate(currentPosition.lat) }}</div>
        <div>海拔: {{ currentPosition.altitude?.toFixed(2) || '未知' }} 米</div>
      </div>
    </div>
  </template>
  
  <script setup>
  import { ref, onMounted, onUnmounted, watch } from 'vue'
  import mapboxgl from 'mapbox-gl'
  import { Deck } from '@deck.gl/core'
  import { ScatterplotLayer, PathLayer, PolygonLayer, IconLayer } from '@deck.gl/layers'
  import { BuildOutlined as LayersIcon, AppstoreOutlined as CubeIcon, HomeOutlined as HomeIcon, GlobalOutlined as MapIcon } from '@vicons/antd'
  
  // 地图配置
  const MAPBOX_TOKEN = import.meta.env.VITE_MAPBOX_TOKEN // 从环境变量读取Token
  console.log('Mapbox Token:', MAPBOX_TOKEN); // <-- 添加日志
  if (!MAPBOX_TOKEN) {
    console.error("Mapbox token not configured. Please set VITE_MAPBOX_TOKEN in your .env file.")
    // 可以选择在这里添加用户提示或阻止地图加载
  }
  const INITIAL_VIEW_STATE = {
    longitude: 116.3833,  // 北京坐标
    latitude: 39.9,
    zoom: 11,
    pitch: 45,
    bearing: 0
  }
  
  // 地图和deck.gl实例
  let map = null
  let deck = null
  
  // 组件状态
  const mapContainer = ref(null)
  const isLoading = ref(true)
  const is3DView = ref(true)
  const currentPosition = ref({ lng: INITIAL_VIEW_STATE.longitude, lat: INITIAL_VIEW_STATE.latitude, altitude: 0 })
  
  // 图层控制
  const showBuildings = ref(true)
  const showTerrain = ref(true)
  const showDrones = ref(true)
  const showEvents = ref(true)
  const showNoFlyZones = ref(true)
  const showFlightPaths = ref(true)
  
  // 监听图层变化
  watch([showBuildings, showTerrain], () => {
    if (map) {
      // 显示/隐藏3D建筑
      map.setLayoutProperty(
        'building-extrusion',
        'visibility',
        showBuildings.value ? 'visible' : 'none'
      )
      
      // 显示/隐藏地形
      if (map.getSource('mapbox-dem')) {
        map.setLayoutProperty(
          'sky',
          'visibility',
          showTerrain.value ? 'visible' : 'none'
        )
        // 应用地形
        if (showTerrain.value) {
          map.setTerrain({ source: 'mapbox-dem', exaggeration: 1.5 })
        } else {
          map.setTerrain(null)
        }
      }
    }
  })
  
  // 监听deck.gl图层变化
  watch([showDrones, showEvents, showNoFlyZones, showFlightPaths], () => {
    if (deck) {
      renderDeckLayers()
    }
  })
  
  // 格式化坐标显示
  const formatCoordinate = (coord) => {
    return coord.toFixed(6)
  }
  
  // 初始化地图
  const initMap = () => {
    console.log('Initializing Mapbox...'); // <-- 添加日志
    if (!MAPBOX_TOKEN) {
        console.error("Cannot initialize map: Mapbox token is missing.");
        isLoading.value = false; // Hide loading indicator
        // Optionally show an error message to the user
        return;
    }
    if (!mapContainer.value) {
        console.error("Cannot initialize map: mapContainer ref is not available.");
        isLoading.value = false;
        return;
    }
    
    mapboxgl.accessToken = MAPBOX_TOKEN
    
    try {
      // 创建地图实例
      map = new mapboxgl.Map({
        container: mapContainer.value,
        style: 'mapbox://styles/mapbox/satellite-streets-v12',
        ...INITIAL_VIEW_STATE,
        antialias: true
      })
      console.log('Mapbox instance created.'); // <-- 添加日志
      
      // 添加导航控件
      map.addControl(new mapboxgl.NavigationControl(), 'bottom-right')
      map.addControl(new mapboxgl.ScaleControl(), 'bottom-left')
      
      // 地图加载完成后初始化3D图层和deck.gl
      map.on('load', () => {
        console.log('Map loaded.'); // <-- 添加日志
        isLoading.value = false
        
        // 添加DEM地形源
        map.addSource('mapbox-dem', {
          'type': 'raster-dem',
          'url': 'mapbox://mapbox.mapbox-terrain-dem-v1',
          'tileSize': 512,
          'maxzoom': 14
        })
        
        // 设置地形
        if (showTerrain.value) {
          map.setTerrain({ source: 'mapbox-dem', exaggeration: 1.5 })
        }
        
        // 添加天空图层
        map.addLayer({
          'id': 'sky',
          'type': 'sky',
          'paint': {
            'sky-type': 'atmosphere',
            'sky-atmosphere-sun': [0.0, 0.0],
            'sky-atmosphere-sun-intensity': 15
          }
        })
        
        // 添加3D建筑图层
        map.addLayer({
          'id': 'building-extrusion',
          'type': 'fill-extrusion',
          'source': 'composite',
          'source-layer': 'building',
          'minzoom': 15,
          'filter': ['==', 'extrude', 'true'],
          'paint': {
            'fill-extrusion-color': [
              'interpolate',
              ['linear'],
              ['get', 'height'],
              0, 'rgba(9, 37, 67, 0.85)',
              50, 'rgba(12, 52, 110, 0.85)',
              100, 'rgba(28, 71, 138, 0.85)',
              200, 'rgba(44, 111, 183, 0.85)',
              400, 'rgba(67, 148, 238, 0.85)'
            ],
            'fill-extrusion-height': [
              'interpolate',
              ['linear'],
              ['zoom'],
              15, 0,
              16, ['get', 'height']
            ],
            'fill-extrusion-base': [
              'interpolate',
              ['linear'],
              ['zoom'],
              15, 0,
              16, ['get', 'min_height']
            ],
            'fill-extrusion-opacity': 0.8
          }
        })
        
        // 初始化deck.gl
        initDeck()
      })
      
      map.on('error', (e) => {
        console.error('Mapbox error:', e); // <-- 添加错误处理日志
        isLoading.value = false;
        // Optionally show an error message to the user
      });
      
      // 鼠标移动时更新坐标
      map.on('mousemove', (e) => {
        currentPosition.value = {
          lng: e.lngLat.lng,
          lat: e.lngLat.lat,
          altitude: map.queryTerrainElevation(e.lngLat) || 0
        }
      })
    } catch (error) {
        console.error('Error initializing Mapbox:', error); // <-- 添加错误捕获
        isLoading.value = false;
    }
  }
  
  // 初始化deck.gl
  const initDeck = () => {
    console.log('Initializing Deck.gl...'); // <-- 添加日志
    try {
        // 创建deck.gl实例，共享地图的视口
        deck = new Deck({
          canvas: 'deck-canvas',
          width: '100%',
          height: '100%',
          initialViewState: INITIAL_VIEW_STATE,
          controller: false,
          onViewStateChange: ({ viewState }) => {
            // 与地图同步视图状态
            map.jumpTo({
              center: [viewState.longitude, viewState.latitude],
              zoom: viewState.zoom,
              bearing: viewState.bearing,
              pitch: viewState.pitch
            })
            return viewState
          },
          layers: [],
          getTooltip: ({ object }) => object && {
            html: `<div>${object.name || 'Unnamed'}</div><div>${object.description || ''}</div>`,
            style: {
              backgroundColor: 'rgba(255, 255, 255, 0.9)',
              fontSize: '12px',
              padding: '5px',
              borderRadius: '3px',
              color: '#333'
            }
          }
        })
        console.log('Deck.gl instance created.'); // <-- 添加日志
        
        // 渲染deck.gl图层
        renderDeckLayers()
        
        // 有一个隐藏的canvas，用于deck.gl渲染
        const deckCanvas = document.createElement('canvas')
        deckCanvas.id = 'deck-canvas'
        deckCanvas.style.position = 'absolute'
        deckCanvas.style.top = '0'
        deckCanvas.style.left = '0'
        deckCanvas.style.width = '100%'
        deckCanvas.style.height = '100%'
        deckCanvas.style.pointerEvents = 'none'
        mapContainer.value.appendChild(deckCanvas)
        
        // 将deck.gl添加为地图的覆盖层
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
        console.error('Error initializing Deck.gl:', error); // <-- 添加错误捕获
    }
  }
  
  // 渲染deck.gl图层
  const renderDeckLayers = () => {
    if (!deck) return
    
    const layers = []
    
    // 无人机图层
    if (showDrones.value) {
      layers.push(
        new IconLayer({
          id: 'drone-layer',
          data: [], // 后续从API获取数据
          pickable: true,
          iconAtlas: '/images/drone-icon.png',
          iconMapping: {
            drone: { x: 0, y: 0, width: 128, height: 128, mask: true }
          },
          getIcon: d => 'drone',
          getPosition: d => [d.longitude, d.latitude, d.altitude || 150],
          getSize: d => 24,
          getColor: d => {
            // 根据无人机状态设置颜色
            const status = d.status || 'idle'
            if (status === 'flying') return [46, 204, 113, 255]
            if (status === 'idle') return [52, 152, 219, 255]
            if (status === 'error') return [231, 76, 60, 255]
            return [255, 255, 255, 255]
          }
        })
      )
    }
    
    // 事件标记图层
    if (showEvents.value) {
      layers.push(
        new ScatterplotLayer({
          id: 'event-layer',
          data: [], // 后续从API获取数据
          pickable: true,
          opacity: 0.8,
          stroked: true,
          filled: true,
          radiusScale: 6,
          radiusMinPixels: 3,
          radiusMaxPixels: 30,
          lineWidthMinPixels: 1,
          getPosition: d => [d.longitude, d.latitude, d.altitude || 0],
          getRadius: d => Math.sqrt(d.severity || 1) * 10,
          getFillColor: d => {
            // 根据事件类型和级别设置颜色
            const type = d.type || 'anomaly'
            if (type === 'emergency') return [231, 76, 60, 200]
            if (type === 'security') return [241, 196, 15, 200]
            return [52, 152, 219, 200]
          },
          getLineColor: d => [255, 255, 255]
        })
      )
    }
    
    // 禁飞区图层
    if (showNoFlyZones.value) {
      layers.push(
        new PolygonLayer({
          id: 'no-fly-zone-layer',
          data: [], // 后续从API获取数据
          pickable: true,
          stroked: true,
          filled: true,
          wireframe: true,
          lineWidthMinPixels: 1,
          getPolygon: d => d.coordinates,
          getElevation: d => 0,
          getFillColor: d => [255, 0, 0, 50],
          getLineColor: [255, 0, 0, 200],
          getLineWidth: 2,
          extruded: true,
          getExtrusionHeight: d => d.max_altitude || 500
        })
      )
    }
    
    // 飞行路径图层
    if (showFlightPaths.value) {
      layers.push(
        new PathLayer({
          id: 'flight-path-layer',
          data: [], // 后续从API获取数据
          pickable: true,
          widthScale: 10,
          widthMinPixels: 2,
          getPath: d => d.path,
          getColor: d => {
            // 根据任务类型设置颜色
            const type = d.type || 'regular'
            if (type === 'emergency') return [231, 76, 60, 200]
            if (type === 'inspection') return [241, 196, 15, 200]
            return [52, 152, 219, 200]
          },
          getWidth: d => 2
        })
      )
    }
    
    deck.setProps({ layers })
  }
  
  // 切换2D/3D视图
  const toggle3DView = () => {
    is3DView.value = !is3DView.value
    if (map) {
      map.easeTo({
        pitch: is3DView.value ? 45 : 0,
        bearing: is3DView.value ? 0 : 0,
        duration: 1000
      })
    }
  }
  
  // 重置视图到初始状态
  const resetView = () => {
    if (map) {
      map.flyTo({
        center: [INITIAL_VIEW_STATE.longitude, INITIAL_VIEW_STATE.latitude],
        zoom: INITIAL_VIEW_STATE.zoom,
        pitch: is3DView.value ? 45 : 0,
        bearing: 0,
        duration: 1500
      })
    }
  }
  
  // 组件挂载
  onMounted(() => {
    console.log('Map3D component mounted.'); // <-- 添加日志
    if (mapContainer.value) {
      console.log('mapContainer is available.'); // <-- 添加日志
      initMap()
    } else {
      console.error('mapContainer ref not found on mount!'); // <-- 添加日志
    }
  })
  
  // 组件卸载
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
  </script>
  
  <style scoped>
  .mapboxgl-canvas {
    outline: none;
  }
  
  /* deck.gl canvas占据与mapbox相同的位置 */
  #deck-canvas {
    z-index: 2;
  }
  </style>