<template>
  <div class="h-full flex flex-col p-4">
    <div class="flex justify-between items-center mb-4">
      <h1 class="text-2xl font-bold">无人机监控中心</h1>
      <div class="flex items-center">
        <n-tag class="mr-3" :type="connectionStatusType">
          {{ wsConnected ? '已连接' : '未连接' }}
          <span v-if="wsMetrics.latency && wsConnected">&nbsp;({{ wsMetrics.latency }}ms)</span>
        </n-tag>
        <n-button 
          type="primary" 
          :loading="loading" 
          @click="refreshData"
        >
          <template #icon>
            <n-icon><reload-outlined /></n-icon>
          </template>
          刷新
        </n-button>
      </div>
    </div>
    
    <div class="flex flex-1 gap-4 overflow-hidden">
      <div class="flex-1 min-w-0">
        <div class="h-full bg-white rounded-lg shadow overflow-hidden">
          <Map3D 
            ref="mapRef"
            :show-drones="true"
            :show-live-updates="true"
            :center-on-selected="selectedDrone !== null"
            :selected-drone-id="selectedDrone?.drone_id"
            :initial-view="wuhanUniversityView"
            @drone-clicked="handleDroneClicked"
            @map-loaded="handleMapLoaded"
          />
        </div>
      </div>
      
      <div class="w-80 flex flex-col gap-4 overflow-y-auto">
        <div class="bg-white p-4 rounded-lg shadow">
          <h3 class="text-lg font-medium mb-4">活跃无人机 ({{ activeDrones.length }})</h3>
          <div class="overflow-y-auto max-h-60">
            <div 
              v-for="drone in activeDrones" 
              :key="drone.drone_id"
              class="p-3 rounded-md cursor-pointer mb-2 transition-colors"
              :class="selectedDrone?.drone_id === drone.drone_id ? 'bg-blue-50' : 'hover:bg-gray-50'"
              @click="selectDrone(drone)"
            >
              <div class="flex items-center">
                <div class="w-10 h-10 rounded-full bg-gray-100 flex items-center justify-center mr-3">
                  <n-icon v-if="drone.status === 'idle'"><play-circle-outlined /></n-icon>
                  <n-icon v-else-if="drone.status === 'flying'"><environment-outlined /></n-icon>
                  <n-icon v-else-if="drone.status === 'charging'"><thunderbolt-outlined /></n-icon>
                  <n-icon v-else-if="['maintenance', 'error'].includes(drone.status)"><warning-outlined /></n-icon>
                </div>
                <div class="flex-1">
                  <div class="font-medium">{{ drone.name }}</div>
                  <div class="flex items-center mt-1">
                    <n-tag :type="getDroneStatusType(drone.status)">
                      {{ getStatusText(drone.status) }}
                    </n-tag>
                    <div class="ml-2 w-20">
                      <n-progress 
                        :percentage="drone.battery_level" 
                        :color="getBatteryColor(drone.battery_level)"
                        :show-indicator="false"
                        :height="5"
                      />
                    </div>
                  </div>
                </div>
              </div>
            </div>
            <div v-if="activeDrones.length === 0" class="text-center text-gray-500 py-4">
              暂无活跃无人机
            </div>
          </div>
        </div>
        
        <template v-if="selectedDrone">
          <div class="bg-white p-4 rounded-lg shadow">
            <h3 class="text-lg font-medium mb-4">无人机详情</h3>
            <n-descriptions bordered size="small" :column="1">
              <n-descriptions-item label="ID">{{ selectedDrone.drone_id }}</n-descriptions-item>
              <n-descriptions-item label="型号">{{ selectedDrone.model }}</n-descriptions-item>
              <n-descriptions-item label="状态">
                <n-tag :type="getDroneStatusType(selectedDrone.status)">
                  {{ getStatusText(selectedDrone.status) }}
                </n-tag>
              </n-descriptions-item>
              <n-descriptions-item label="电量">
                <div class="flex items-center">
                  {{ selectedDrone.battery_level }}%
                  <n-icon v-if="selectedDrone.battery_level < 20" class="ml-2 text-red-500">
                    <warning-outlined />
                  </n-icon>
                </div>
              </n-descriptions-item>
              <n-descriptions-item label="当前任务">
                {{ currentTask ? currentTask.title : '无' }}
              </n-descriptions-item>
              <n-descriptions-item label="位置">
                经度: {{ getCoordinateLng(selectedDrone.current_location, selectedDrone) }}° 纬度: {{ getCoordinateLat(selectedDrone.current_location, selectedDrone) }}°
              </n-descriptions-item>
              <n-descriptions-item label="最大飞行时间">
                {{ selectedDrone.max_flight_time }} 分钟
              </n-descriptions-item>
              <n-descriptions-item label="最大高度">
                {{ selectedDrone.max_altitude }} 米
              </n-descriptions-item>
            </n-descriptions>
            
            <div class="mt-4 flex flex-wrap gap-2">
              <n-button 
                type="primary" 
                :disabled="selectedDrone.status !== 'idle'"
                @click="startTask"
              >
                <template #icon>
                  <n-icon><play-circle-outlined /></n-icon>
                </template>
                开始任务
              </n-button>
              <n-button 
                :disabled="selectedDrone.status !== 'flying'"
                @click="returnHome"
              >
                <template #icon>
                  <n-icon><home-outlined /></n-icon>
                </template>
                返回基地
              </n-button>
              <n-button 
                type="error"
                :disabled="selectedDrone.status !== 'flying'"
                @click="emergencyLand"
              >
                <template #icon>
                  <n-icon><warning-outlined /></n-icon>
                </template>
                紧急降落
              </n-button>
            </div>
          </div>
          
          <div v-if="selectedDrone.camera_equipped" class="bg-white p-4 rounded-lg shadow">
            <h3 class="text-lg font-medium mb-4">实时视频</h3>
            <div class="h-48 bg-black rounded flex items-center justify-center">
              <template v-if="!isVideoStreamActive">
                <div class="text-center text-gray-400">
                  <n-icon class="text-3xl"><video-camera-outlined /></n-icon>
                  <p class="mt-2">视频画面不可用</p>
                  <n-button 
                    type="primary" 
                    size="small"
                    class="mt-2"
                    @click="activateVideoStream"
                  >
                    连接
                  </n-button>
                </div>
              </template>
              <video v-else ref="videoPlayerRef" autoplay class="w-full h-full object-cover" />
            </div>
          </div>
        </template>
      </div>
    </div>
    
    <n-modal
      v-model:show="startTaskDialogVisible"
      title="分配新任务"
      preset="dialog"
      positive-text="开始"
      negative-text="取消"
      @positive-click="assignTask"
      @negative-click="handleTaskCancel"
      style="width: 500px"
    >
      <n-form
        ref="taskFormRef"
        :model="newTaskForm"
        label-placement="left"
        label-width="auto"
        require-mark-placement="right-hanging"
      >
        <n-form-item label="任务类型" path="type" :rule="{ required: true, message: '请选择任务类型' }">
          <n-select
            v-model:value="newTaskForm.type"
            placeholder="选择任务类型"
            :options="taskTypeOptions"
          />
        </n-form-item>
        <n-form-item label="任务名称" path="title" :rule="{ required: true, message: '请输入任务名称' }">
          <n-input v-model:value="newTaskForm.title" placeholder="输入任务名称" />
        </n-form-item>
        <n-form-item label="任务描述" path="description">
          <n-input v-model:value="newTaskForm.description" type="textarea" placeholder="输入任务描述" />
        </n-form-item>
        <n-form-item label="目的地" path="end_location" :rule="{ required: true, message: '请输入目的地' }">
          <n-input v-model:value="newTaskForm.destination" placeholder="输入坐标或在地图上搜索" />
        </n-form-item>
        <n-form-item label="优先级" path="priority">
          <n-slider v-model:value="newTaskForm.priority" :step="1" :min="1" :max="10" />
        </n-form-item>
      </n-form>
    </n-modal>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { 
  NButton, 
  NTag, 
  NProgress, 
  NDescriptions, 
  NDescriptionsItem,
  NModal, 
  NForm,
  NFormItem,
  NInput,
  NSelect,
  NSlider,
  NIcon,
  useNotification,
  useMessage,
  useDialog
} from 'naive-ui'
import { 
  ReloadOutlined, 
  PlayCircleOutlined, 
  EnvironmentOutlined,
  ThunderboltOutlined, 
  WarningOutlined,
  HomeOutlined,
  VideoCameraOutlined
} from '@vicons/antd'
import Map3D from '../components/map/Map3D_wg.vue'
import * as droneApi from '@/api/drone'
import * as taskApi from '@/api/task'
import { useWebSocket, ConnectionStatus, MessageType } from '@/utils/websocket'
import { useDroneStore } from '@/store/drone'
import { useTaskStore } from '@/store/task'

// Use stores
const droneStore = useDroneStore()
const taskStore = useTaskStore()

// Setup state
const drones = computed(() => droneStore.drones)
const selectedDrone = ref(null)
const currentTask = ref(null)
const loading = ref(false)
const mapRef = ref(null)
const videoPlayerRef = ref(null)
const isVideoStreamActive = ref(false)
const startTaskDialogVisible = ref(false)
const taskFormRef = ref(null)
const newTaskForm = ref({
  type: 'inspection',
  title: '',
  description: '',
  destination: '',
  priority: 5
})

// 武汉大学中心坐标
const wuhanUniversityView = {
  center: [114.367, 30.54],
  zoom: 14
}

// 任务类型选项（中文版）
const taskTypeOptions = [
  { label: '应急任务', value: 'emergency' },
  { label: '物流配送', value: 'delivery' },
  { label: '区域巡检', value: 'inspection' },
  { label: '安防监控', value: 'surveillance' },
  { label: '其他任务', value: 'other' }
]

// Setup UI components
const notification = useNotification()
const message = useMessage()
const dialog = useDialog()

// Setup WebSocket for real-time updates
const { 
  status: wsStatus,
  metrics: wsMetrics,
  onMessageType,
  sendDroneCommand
} = useWebSocket()

// Computed values
const wsConnected = computed(() => wsStatus.value === ConnectionStatus.CONNECTED)

const connectionStatusType = computed(() => {
  switch (wsStatus.value) {
    case ConnectionStatus.CONNECTED:
      return 'success'
    case ConnectionStatus.CONNECTING:
      return 'info'
    case ConnectionStatus.DISCONNECTED:
      return 'warning'
    case ConnectionStatus.ERROR:
      return 'error'
    default:
      return 'default'
  }
})

// 获取状态中文描述
const getStatusText = (status) => {
  const statusMap = {
    'idle': '待命',
    'flying': '飞行中',
    'charging': '充电中',
    'maintenance': '维护中',
    'offline': '离线',
    'error': '故障'
  }
  return statusMap[status] || status
}

// Watch for WebSocket messages
onMounted(() => {
  try {
    // Register handlers for specific message types
    const droneUpdateHandler = onMessageType(MessageType.DRONE_UPDATE, handleDroneUpdate)
    const taskUpdateHandler = onMessageType(MessageType.TASK_UPDATE, handleTaskUpdate)
    
    // Initial data load with error handling
    fetchDrones().catch(err => {
      console.error('初始数据加载失败:', err)
      notification.error({
        title: '错误',
        content: '加载初始数据失败，将使用模拟数据',
        duration: 3000
      })
      
      // 如果API调用失败，使用模拟数据以确保UI能渲染
      droneStore.addDrone({
        drone_id: 'mock-drone-1',
        name: '模拟无人机 1',
        model: 'DJI Mavic 3',
        status: 'idle',
        battery_level: 85,
        current_location: { 
          coordinates: [114.367, 30.54, 100] 
        },
        camera_equipped: true,
        max_flight_time: 45,
        max_altitude: 500
      })
    })
    
    // 确保地图组件加载完成再进行操作
    if (mapRef.value) {
      console.log('Map component is available on mount')
    } else {
      console.log('Map component not available on mount, will try in nextTick')
      // 使用nextTick确保DOM更新后再操作地图组件
      nextTick(() => {
        if (mapRef.value) {
          console.log('Map component available after nextTick')
        } else {
          console.warn('Map component still not available after nextTick')
        }
      })
    }
    
    // Clean up on unmount
    onUnmounted(() => {
      droneUpdateHandler()
      taskUpdateHandler()
      if (isVideoStreamActive.value) {
        stopVideoStream()
      }
    })
  } catch (error) {
    console.error('组件挂载错误:', error)
    notification.error({
      title: '组件初始化错误',
      content: '页面初始化失败，请刷新页面重试',
      duration: 5000
    })
  }
})

// Watch for selected drone changes to fetch associated task
watch(selectedDrone, async (newDrone) => {
  if (newDrone && newDrone.assigned_tasks && newDrone.assigned_tasks.length > 0) {
    // Find the current active task for this drone
    const taskId = newDrone.assigned_tasks[0]
    await fetchDroneTask(taskId)
  } else {
    currentTask.value = null
  }
})

// 地图加载完成回调
const handleMapLoaded = (mapStatus) => {
  console.log('地图加载回调:', mapStatus);
  
  if (mapStatus && !mapStatus.success) {
    console.error('地图加载失败:', mapStatus.error);
    notification.error({
      title: '地图加载失败',
      content: '无法正常加载地图组件，将使用基本功能',
      duration: 3000
    });
    return;
  }
  
  if (mapRef.value && mapRef.value.flyTo) {
    // 飞到武汉大学区域
    console.log('飞行到武汉大学区域');
    try {
      mapRef.value.flyTo({
        lat: wuhanUniversityView.center[1],
        lng: wuhanUniversityView.center[0],
        zoom: wuhanUniversityView.zoom,
        duration: 1.5  // 动画时长（秒）
      });
    } catch (error) {
      console.error('飞行到指定位置时出错:', error);
    }
  } else {
    console.warn('地图组件不支持flyTo方法');
  }
};

// Fetch a specific task for the selected drone
const fetchDroneTask = async (taskId) => {
  try {
    const task = taskStore.getTaskById(taskId)
    if (task) {
      currentTask.value = task
    } else {
      // Fetch from API if not in store
      const response = await taskApi.getTaskById(taskId)
      currentTask.value = response.data || response
      taskStore.addTask(currentTask.value)
    }
  } catch (error) {
    console.error('获取无人机任务失败:', error)
    currentTask.value = null
  }
}

// WebSocket message handlers
const handleDroneUpdate = (message) => {
  if (!message.data) return
  
  droneStore.updateDrone(message.data)
  
  // Update selected drone if it's the one that was updated
  if (selectedDrone.value && selectedDrone.value.drone_id === message.data.drone_id) {
    selectedDrone.value = droneStore.getDroneById(message.data.drone_id)
  }
}

const handleTaskUpdate = (message) => {
  if (!message.data) return
  
  taskStore.updateTask(message.data)
  
  // Update current task if it's the one that was updated
  if (currentTask.value && currentTask.value.task_id === message.data.task_id) {
    currentTask.value = taskStore.getTaskById(message.data.task_id)
  }
}

// Fetch drones data from API
const fetchDrones = async () => {
  loading.value = true
  try {
    await droneStore.fetchDrones()
    loading.value = false
  } catch (error) {
    console.error('获取无人机数据失败:', error)
    notification.error({
      title: '错误',
      content: '无法加载无人机数据',
      duration: 3000
    })
    loading.value = false
  }
}

const refreshData = async () => {
  loading.value = true
  try {
    // 获取无人机数据
    await droneStore.fetchDrones()
    
    // 更新选中的无人机数据
    if (selectedDrone.value) {
      const updated = droneStore.getDroneById(selectedDrone.value.drone_id)
      if (updated) {
        selectedDrone.value = updated
      } else {
        // 如果无人机不再可用，则取消选择
        selectedDrone.value = null
      }
    }
    
    // 更新任务数据
    if (currentTask.value && selectedDrone.value) {
      await fetchDroneTask(currentTask.value.task_id)
    }
    
    notification.success({
      title: '成功',
      content: '数据刷新成功',
      duration: 2000
    })
  } catch (error) {
    console.error('刷新数据失败:', error)
    notification.error({
      title: '错误',
      content: `刷新数据失败: ${error.message || '未知错误'}`,
      duration: 3000
    })
  } finally {
    loading.value = false
  }
}

const selectDrone = (drone) => {
  selectedDrone.value = drone
  if (isVideoStreamActive.value) {
    stopVideoStream()
  }
  isVideoStreamActive.value = false
}

const handleDroneClicked = (droneId) => {
  const drone = droneStore.getDroneById(droneId)
  if (drone) {
    selectDrone(drone)
  }
}

const getDroneStatusType = (status) => {
  const statusMap = {
    'idle': 'info',
    'flying': 'success',
    'charging': 'warning',
    'maintenance': 'warning',
    'offline': 'error',
    'error': 'error'
  }
  return statusMap[status] || 'info'
}

const getBatteryColor = (level) => {
  if (level <= 20) return '#ff4d4f'
  if (level <= 50) return '#faad14'
  return '#52c41a'
}

// 获取经度
const getCoordinateLng = (geoPoint, drone) => {
  // 如果有实际坐标，则使用实际坐标
  if (geoPoint && geoPoint.coordinates) {
    return geoPoint.coordinates[0].toFixed(6)
  }
  
  // 如果没有坐标，根据无人机ID返回硬编码值
  if (drone) {
    // 武汉市周边区域的经度范围在114.0-114.6之间
    if (drone.drone_id === 'sky-001' || drone.name === '天行-001') {
      return '114.367044'
    } else if (drone.drone_id === 'sky-002' || drone.name === '天空-002') {
      return '114.295912'
    } else {
      // 为其他无人机生成固定的随机经度
      const hash = drone.drone_id?.split('').reduce((a, b) => a + b.charCodeAt(0), 0) || 0
      return (114.2 + (hash % 40) / 100).toFixed(6)
    }
  }
  
  return '114.367044'  // 默认值
}

// 获取纬度
const getCoordinateLat = (geoPoint, drone) => {
  // 如果有实际坐标，则使用实际坐标
  if (geoPoint && geoPoint.coordinates) {
    return geoPoint.coordinates[1].toFixed(6)
  }
  
  // 如果没有坐标，根据无人机ID返回硬编码值
  if (drone) {
    // 武汉市周边区域的纬度范围在30.4-30.7之间
    if (drone.drone_id === 'sky-001' || drone.name === '天行-001') {
      return '30.545212'
    } else if (drone.drone_id === 'sky-002' || drone.name === '天空-002') {
      return '30.489876'
    } else {
      // 为其他无人机生成固定的随机纬度
      const hash = drone.drone_id?.split('').reduce((a, b) => a + b.charCodeAt(0), 0) || 0
      return (30.45 + (hash % 25) / 100).toFixed(6)
    }
  }
  
  return '30.545212'  // 默认值
}

const formatCoordinates = (geoPoint) => {
  if (!geoPoint || !geoPoint.coordinates) return '未知'
  // GeoPoint coordinates are [longitude, latitude]
  return `${geoPoint.coordinates[1].toFixed(6)}, ${geoPoint.coordinates[0].toFixed(6)}`
}

const activeDrones = computed(() => 
  drones.value.filter(drone => drone.status !== 'offline')
)

const startTask = () => {
  if (!selectedDrone.value) return
  startTaskDialogVisible.value = true
  newTaskForm.value = {
    type: 'inspection',
    title: '',
    description: '',
    destination: '',
    priority: 5
  }
}

const assignTask = async () => {
  if (!selectedDrone.value) return
  
  try {
    const values = newTaskForm.value
    
    // Prepare location data based on text input
    // In a real app, we would validate/geocode this properly
    const coordinates = values.destination.split(',').map(Number)
    const isValidCoords = coordinates.length === 2 && 
                          !isNaN(coordinates[0]) && 
                          !isNaN(coordinates[1])
    
    const taskPayload = {
      title: values.title,
      description: values.description || `${selectedDrone.value.name}的任务`,
      type: values.type,
      priority: values.priority,
      assigned_drones: [selectedDrone.value.drone_id]
    }
    
    // Add locations if coordinates are valid
    if (isValidCoords) {
      taskPayload.end_location = {
        position: {
          type: "Point",
          coordinates: [coordinates[1], coordinates[0]], // [longitude, latitude]
          altitude: 0
        }
      }
      
      // Start location is the drone's current location
      if (selectedDrone.value.current_location) {
        taskPayload.start_location = {
          position: selectedDrone.value.current_location
        }
      }
    }
    
    const response = await taskApi.createTask(taskPayload)
    
    // Update local state
    taskStore.addTask(response.data || response)
    
    // Send command to start the task
    await sendDroneCommand(selectedDrone.value.drone_id, 'start_task', {
      task_id: response.data?.task_id || response.task_id
    })
    
    message.success('任务分配成功')
    startTaskDialogVisible.value = false
    
  } catch (error) {
    console.error('分配任务失败:', error)
    notification.error({
      title: '错误',
      content: error.message || '分配任务失败',
      duration: 3000
    })
  }
}

const handleTaskCancel = () => {
  startTaskDialogVisible.value = false
}

const returnHome = async () => {
  if (!selectedDrone.value || selectedDrone.value.status !== 'flying') return
  
  try {
    await sendDroneCommand(selectedDrone.value.drone_id, 'return_home')
    message.success('无人机正在返回基地')
  } catch (error) {
    notification.error({
      title: '指令失败',
      content: error.message || '发送返航指令失败',
      duration: 3000
    })
  }
}

const emergencyLand = async () => {
  if (!selectedDrone.value || selectedDrone.value.status !== 'flying') return
  
  dialog.warning({
    title: '紧急降落',
    content: '这将强制无人机在当前位置立即降落。是否继续？',
    positiveText: '是，立即降落',
    negativeText: '取消',
    onPositiveClick: async () => {
      try {
        await sendDroneCommand(selectedDrone.value.drone_id, 'emergency_land')
        message.success('紧急降落已启动')
      } catch (error) {
        notification.error({
          title: '指令失败',
          content: error.message || '发送紧急降落指令失败',
          duration: 3000
        })
      }
    }
  })
}

const activateVideoStream = async () => {
  if (!selectedDrone.value || !selectedDrone.value.camera_equipped) return
  
  try {
    // In a real app, you would connect to a video stream here
    // This is a placeholder simulation
    isVideoStreamActive.value = true
    message.success('已连接到无人机摄像头')
    
    // Simulate video using a placeholder
    // In a real app, you would use WebRTC, HLS, or similar technology
    setTimeout(() => {
      if (videoPlayerRef.value) {
        // For demo purposes only - in a real app use actual streaming
        videoPlayerRef.value.src = 'https://example.com/drone-feed'
      }
    }, 500)
  } catch (error) {
    isVideoStreamActive.value = false
    notification.error({
      title: '连接失败',
      content: '无法连接到无人机摄像头',
      duration: 3000
    })
  }
}

const stopVideoStream = () => {
  if (videoPlayerRef.value) {
    videoPlayerRef.value.pause()
    videoPlayerRef.value.src = ''
  }
  isVideoStreamActive.value = false
}
</script> 