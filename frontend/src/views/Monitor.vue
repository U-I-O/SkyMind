<template>
  <div class="h-full flex flex-col p-4">
    <div class="flex justify-between items-center mb-4">
      <h1 class="text-2xl font-bold">Drone Monitoring Center</h1>
      <div>
        <n-button 
          type="primary" 
          :loading="loading" 
          @click="refreshData"
        >
          <template #icon>
            <n-icon><reload-outlined /></n-icon>
          </template>
          Refresh
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
            :selected-drone-id="selectedDrone?.id"
          />
        </div>
      </div>
      
      <div class="w-80 flex flex-col gap-4 overflow-y-auto">
        <div class="bg-white p-4 rounded-lg shadow">
          <h3 class="text-lg font-medium mb-4">Active Drones ({{ activeDrones.length }})</h3>
          <div class="overflow-y-auto max-h-60">
            <div 
              v-for="drone in activeDrones" 
              :key="drone.id"
              class="p-3 rounded-md cursor-pointer mb-2 transition-colors"
              :class="selectedDrone?.id === drone.id ? 'bg-blue-50' : 'hover:bg-gray-50'"
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
                      {{ drone.status }}
                    </n-tag>
                    <div class="ml-2 w-20">
                      <n-progress 
                        :percentage="drone.batteryLevel" 
                        :color="getBatteryColor(drone.batteryLevel)"
                        :show-indicator="false"
                        :height="5"
                      />
                    </div>
                  </div>
                </div>
              </div>
            </div>
            <div v-if="activeDrones.length === 0" class="text-center text-gray-500 py-4">
              No active drones found
            </div>
          </div>
        </div>
        
        <template v-if="selectedDrone">
          <div class="bg-white p-4 rounded-lg shadow">
            <h3 class="text-lg font-medium mb-4">Drone Details</h3>
            <n-descriptions bordered size="small" :column="1">
              <n-descriptions-item label="ID">{{ selectedDrone.id }}</n-descriptions-item>
              <n-descriptions-item label="Model">{{ selectedDrone.model }}</n-descriptions-item>
              <n-descriptions-item label="Status">
                <n-tag :type="getDroneStatusType(selectedDrone.status)">
                  {{ selectedDrone.status }}
                </n-tag>
              </n-descriptions-item>
              <n-descriptions-item label="Battery">
                <div class="flex items-center">
                  {{ selectedDrone.batteryLevel }}%
                  <n-icon v-if="selectedDrone.batteryLevel < 20" class="ml-2 text-red-500">
                    <warning-outlined />
                  </n-icon>
                </div>
              </n-descriptions-item>
              <n-descriptions-item label="Current Task">
                {{ selectedDrone.currentTask?.name || 'None' }}
              </n-descriptions-item>
              <n-descriptions-item label="Location">
                {{ formatCoordinates(selectedDrone.location) }}
              </n-descriptions-item>
              <n-descriptions-item label="Speed">
                {{ selectedDrone.speed }} km/h
              </n-descriptions-item>
              <n-descriptions-item label="Altitude">
                {{ selectedDrone.altitude }} m
              </n-descriptions-item>
            </n-descriptions>
            
            <div class="mt-4 flex">
              <n-button 
                type="primary" 
                :disabled="selectedDrone.status !== 'idle'"
                @click="startTask"
              >
                <template #icon>
                  <n-icon><play-circle-outlined /></n-icon>
                </template>
                Start Task
              </n-button>
              <n-button 
                class="ml-2"
                :disabled="selectedDrone.status !== 'flying'"
                @click="returnHome"
              >
                <template #icon>
                  <n-icon><home-outlined /></n-icon>
                </template>
                Return Home
              </n-button>
              <n-button 
                class="ml-2"
                type="error"
                :disabled="selectedDrone.status !== 'flying'"
                @click="emergencyLand"
              >
                <template #icon>
                  <n-icon><warning-outlined /></n-icon>
                </template>
                Emergency Land
              </n-button>
            </div>
          </div>
          
          <div v-if="selectedDrone.hasCamera" class="bg-white p-4 rounded-lg shadow">
            <h3 class="text-lg font-medium mb-4">Live Feed</h3>
            <div class="h-48 bg-black rounded flex items-center justify-center">
              <template v-if="!isVideoStreamActive">
                <div class="text-center text-gray-400">
                  <n-icon class="text-3xl"><video-camera-outlined /></n-icon>
                  <p class="mt-2">Video feed not available</p>
                  <n-button 
                    type="primary" 
                    size="small"
                    class="mt-2"
                    @click="activateVideoStream"
                  >
                    Connect
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
      title="Assign New Task"
      preset="dialog"
      positive-text="Start"
      negative-text="Cancel"
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
        <n-form-item label="Task Type" path="type" :rule="{ required: true, message: 'Please select a task type' }">
          <n-select
            v-model:value="newTaskForm.type"
            placeholder="Select task type"
            :options="taskTypeOptions"
          />
        </n-form-item>
        <n-form-item label="Task Name" path="name" :rule="{ required: true, message: 'Please enter a task name' }">
          <n-input v-model:value="newTaskForm.name" placeholder="Enter task name" />
        </n-form-item>
        <n-form-item label="Destination" path="destination" :rule="{ required: true, message: 'Please enter a destination' }">
          <n-input v-model:value="newTaskForm.destination" placeholder="Enter coordinates or address" />
        </n-form-item>
      </n-form>
    </n-modal>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
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
import Map3D from '../components/map/Map3D.vue'
import * as droneApi from '@/api/drone'
import * as taskApi from '@/api/task'
import { useWebSocket } from '@/hooks/useWebSocket'

// Setup state
const drones = ref([])
const selectedDrone = ref(null)
const loading = ref(false)
const mapRef = ref(null)
const videoPlayerRef = ref(null)
const isVideoStreamActive = ref(false)
const startTaskDialogVisible = ref(false)
const taskFormRef = ref(null)
const newTaskForm = ref({
  type: '',
  name: '',
  destination: ''
})

const taskTypeOptions = [
  { label: 'Delivery', value: 'delivery' },
  { label: 'Survey', value: 'survey' },
  { label: 'Inspection', value: 'inspection' },
  { label: 'Photography', value: 'photography' },
  { label: 'Security', value: 'security' }
]

// Setup UI components
const notification = useNotification()
const message = useMessage()
const dialog = useDialog()

// Setup WebSocket for real-time updates
const { 
  isConnected: wsConnected, 
  messages: wsMessages,
  connect: connectWs,
  disconnect: disconnectWs
} = useWebSocket('/api/ws/drones')

// Watch for drone updates via WebSocket
const processDroneUpdate = (message) => {
  if (message.type === 'droneUpdate') {
    const index = drones.value.findIndex(d => d.id === message.data.id)
    
    if (index !== -1) {
      drones.value[index] = { ...drones.value[index], ...message.data }
      
      // Update selected drone if it's the one that was updated
      if (selectedDrone.value && selectedDrone.value.id === message.data.id) {
        selectedDrone.value = { ...selectedDrone.value, ...message.data }
      }
    } else {
      drones.value.push(message.data)
    }
  } else if (message.type === 'droneOffline') {
    const index = drones.value.findIndex(d => d.id === message.data.id)
    
    if (index !== -1) {
      drones.value[index] = { ...drones.value[index], status: 'offline' }
      
      if (selectedDrone.value && selectedDrone.value.id === message.data.id) {
        selectedDrone.value = { ...selectedDrone.value, status: 'offline' }
      }
    }
  }
}

// Watch for WebSocket messages
let wsWatcher = null

onMounted(() => {
  wsWatcher = computed(() => {
    if (wsMessages.value.length > 0) {
      const latestMessage = wsMessages.value[wsMessages.value.length - 1]
      processDroneUpdate(latestMessage)
    }
    return wsMessages.value
  })
  
  fetchDrones()
  connectWs()
})

onUnmounted(() => {
  disconnectWs()
  if (isVideoStreamActive.value) {
    stopVideoStream()
  }
})

// Fetch drones data
const fetchDrones = async () => {
  loading.value = true
  try {
    const { data } = await droneApi.getDrones()
    drones.value = data
  } catch (error) {
    console.error('Error fetching drones:', error)
    notification.error({
      title: 'Error',
      content: 'Failed to load drones',
      duration: 3000
    })
  } finally {
    loading.value = false
  }
}

const refreshData = () => {
  fetchDrones()
}

const selectDrone = (drone) => {
  selectedDrone.value = drone
  if (isVideoStreamActive.value) {
    stopVideoStream()
  }
  isVideoStreamActive.value = false
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

const formatCoordinates = (coords) => {
  if (!coords) return 'Unknown'
  return `${coords.lat.toFixed(6)}, ${coords.lng.toFixed(6)}`
}

const activeDrones = computed(() => 
  drones.value.filter(drone => drone.status !== 'offline')
)

const startTask = () => {
  if (!selectedDrone.value) return
  startTaskDialogVisible.value = true
  newTaskForm.value = {
    type: '',
    name: '',
    destination: ''
  }
}

const assignTask = async () => {
  if (!selectedDrone.value) return
  
  try {
    // In a real app, we would validate the form here
    const values = newTaskForm.value
    const taskPayload = {
      ...values,
      droneId: selectedDrone.value.id,
      startLocation: selectedDrone.value.location
    }
    
    await taskApi.createTask(taskPayload)
    notification.success({
      title: 'Success',
      content: `Task assigned to ${selectedDrone.value.name}`,
      duration: 3000
    })
    startTaskDialogVisible.value = false
    
    // Refresh drone data
    fetchDrones()
  } catch (error) {
    console.error('Error assigning task:', error)
    notification.error({
      title: 'Error',
      content: 'Failed to assign task',
      duration: 3000
    })
  }
}

const handleTaskCancel = () => {
  startTaskDialogVisible.value = false
}

const returnHome = () => {
  if (!selectedDrone.value) return
  
  dialog.warning({
    title: 'Confirm Return',
    content: `Command ${selectedDrone.value.name} to return to home base?`,
    positiveText: 'Yes',
    negativeText: 'No',
    onPositiveClick: async () => {
      try {
        await droneApi.controlDrone(selectedDrone.value.id, 'return_home')
        notification.success({
          title: 'Command Sent',
          content: `${selectedDrone.value.name} is returning to home base`,
          duration: 3000
        })
        fetchDrones()
      } catch (error) {
        console.error('Error commanding drone:', error)
        notification.error({
          title: 'Error',
          content: 'Failed to send command',
          duration: 3000
        })
      }
    }
  })
}

const emergencyLand = () => {
  if (!selectedDrone.value) return
  
  dialog.error({
    title: 'Emergency Landing',
    content: `Emergency land ${selectedDrone.value.name} at current location?`,
    positiveText: 'Yes',
    negativeText: 'No',
    onPositiveClick: async () => {
      try {
        await droneApi.controlDrone(selectedDrone.value.id, 'emergency_land')
        notification.warning({
          title: 'Emergency Landing',
          content: `${selectedDrone.value.name} emergency landing initiated`,
          duration: 3000
        })
        fetchDrones()
      } catch (error) {
        console.error('Error commanding drone:', error)
        notification.error({
          title: 'Error',
          content: 'Failed to send emergency command',
          duration: 3000
        })
      }
    }
  })
}

const activateVideoStream = () => {
  if (!selectedDrone.value || !selectedDrone.value.hasCamera) return
  
  // Simulate video streaming connection
  isVideoStreamActive.value = true
  notification.info({
    title: 'Video Feed',
    content: 'Connecting to drone video feed...',
    duration: 3000
  })
  
  // In a real application, this would connect to a video streaming service
  setTimeout(() => {
    // Show a test pattern in a real app
    const canvas = document.createElement('canvas')
    canvas.width = 640
    canvas.height = 360
    const ctx = canvas.getContext('2d')
    
    // Create a test pattern
    ctx.fillStyle = '#000'
    ctx.fillRect(0, 0, canvas.width, canvas.height)
    ctx.font = '20px Arial'
    ctx.fillStyle = '#fff'
    ctx.fillText(`Drone ${selectedDrone.value.name} - Live Feed`, 20, 30)
    ctx.fillText(`Simulated Video Stream`, 20, 60)
    ctx.fillText(`${new Date().toLocaleTimeString()}`, 20, 90)
    
    // Create a video stream from the canvas
    if (canvas.captureStream) {
      const stream = canvas.captureStream(30)
      if (videoPlayerRef.value) {
        videoPlayerRef.value.srcObject = stream
      }
    }
  }, 1000)
}

const stopVideoStream = () => {
  if (videoPlayerRef.value && videoPlayerRef.value.srcObject) {
    const tracks = videoPlayerRef.value.srcObject.getTracks()
    tracks.forEach(track => track.stop())
    videoPlayerRef.value.srcObject = null
  }
}
</script> 