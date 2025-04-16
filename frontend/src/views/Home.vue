<template>
  <div class="h-full pointer-events-none">
    <!-- 漂浮面板容器 -->
    <div class="p-4 h-full">
      <div class="h-full grid grid-cols-12 gap-4">
          <!-- 左侧信息面板 -->
          <div class="col-span-3 flex flex-col gap-4 pointer-events-auto">
            <!-- 系统状态卡片 -->
            <div class="light-card">
              <div class="card-border">
                <div class="flex justify-between items-center mb-4 title-bar">
                  <div class="light-title">
                    <div class="title-dot"></div>
                    <h2 class="font-bold text-lg text-slate-700 flex items-center">
                      <span class="status-icon mr-2"></span>
                      系统状态
                      <span class="light-badge">01</span>
                    </h2>
                  </div>
                  <n-tag type="success" size="small" class="light-tag">运行中</n-tag>
                </div>
                
                <div class="space-y-3">
                  <div class="flex justify-between items-center hover:bg-blue-50 p-2 rounded-md transition-all">
                    <div class="text-slate-600">在线无人机</div>
                    <div class="font-medium light-number">{{ onlineDrones }}/{{ totalDrones }}</div>
                  </div>
                  <div class="flex justify-between items-center hover:bg-blue-50 p-2 rounded-md transition-all">
                    <div class="text-slate-600">活跃智能体</div>
                    <div class="font-medium light-number">{{ summaryData.activeAgents }}/{{ summaryData.totalAgents }}</div>
                  </div>
                  <div class="flex justify-between items-center hover:bg-blue-50 p-2 rounded-md transition-all">
                    <div class="text-slate-600">未处理事件</div>
                    <div class="font-medium light-number">{{ summaryData.pendingEvents }}</div>
                  </div>
                  <div class="flex justify-between items-center hover:bg-blue-50 p-2 rounded-md transition-all">
                    <div class="text-slate-600">进行中任务</div>
                    <div class="font-medium light-number">{{ summaryData.activeTasks }}</div>
                  </div>
                </div>
                
                <n-divider class="light-divider" />
                
                <!-- 系统资源使用情况 -->
                <div>
                  <div class="flex justify-between items-center mb-2">
                    <div class="text-slate-600">CPU使用率</div>
                    <div class="font-medium text-blue-600">{{ displayedValues.cpuUsage }}%</div>
                  </div>
                  <n-progress type="line" :percentage="displayedValues.cpuUsage" :indicator-placement="'inside'" :color="cpuUsageColor" class="light-progress" />
                  
                  <div class="flex justify-between items-center mb-2 mt-3">
                    <div class="text-slate-600">内存使用率</div>
                    <div class="font-medium text-blue-600">{{ displayedValues.memoryUsage }}%</div>
                  </div>
                  <n-progress type="line" :percentage="displayedValues.memoryUsage" :indicator-placement="'inside'" :color="memoryUsageColor" class="light-progress" />
                  
                  <div class="flex justify-between items-center mb-2 mt-3">
                    <div class="text-slate-600">存储使用率</div>
                    <div class="font-medium text-blue-600">{{ displayedValues.storageUsage }}%</div>
                  </div>
                  <n-progress type="line" :percentage="displayedValues.storageUsage" :indicator-placement="'inside'" :color="storageUsageColor" class="light-progress" />
                </div>
              </div>
            </div>
            
            <!-- 无人机状态面板 -->
            <div class="light-card">
              <div class="card-border">
                <div class="light-title mb-4">
                  <div class="title-dot"></div>
                  <h3 class="text-lg font-medium text-slate-700 flex items-center">
                    <span class="drone-icon mr-2"></span>
                    活跃无人机
                    <span class="light-badge">02</span>
                    <span class="ml-2 text-xs text-slate-500">({{ activeDrones.length }})</span>
                  </h3>
                </div>

                <!-- 选中无人机的实时视频 -->
                <div v-if="selectedDrone && showDroneVideo" class="mb-4">
                  <div class="relative rounded-lg overflow-hidden drone-video-container">
                    <video ref="droneVideoRef" class="w-full h-full object-cover" autoplay></video>
                    <div class="absolute top-2 right-2 flex space-x-2">
                      <button @click="toggleFullscreenVideo" class="video-control-btn">
                        <span class="i-carbon-maximize text-lg"></span>
                      </button>
                      <button @click="closeDroneVideo" class="video-control-btn">
                        <span class="i-carbon-close text-lg"></span>
                      </button>
                    </div>
                    <div class="absolute bottom-0 left-0 right-0 p-2 bg-gradient-to-t from-black/60 to-transparent">
                      <div class="flex justify-between items-center">
                        <div class="flex items-center">
                          <div class="w-3 h-3 bg-red-500 rounded-full animate-pulse mr-2"></div>
                          <span class="text-white text-sm font-medium">实时画面 - {{ selectedDrone.name }}</span>
                        </div>
                        <div class="text-white/80 text-xs">{{ currentTime }}</div>
                      </div>
                    </div>
                  </div>
                </div>

                <div class="overflow-y-auto max-h-60 scrollbar-light grid grid-cols-1 gap-3">
                  <div 
                    v-for="drone in activeDrones" 
                    :key="drone.drone_id"
                    class="rounded-md cursor-pointer transition-all drone-card"
                    :class="selectedDrone?.drone_id === drone.drone_id ? 'selected-drone' : ''"
                    @click="selectDrone(drone)"
                  >
                    <div class="flex items-center p-3">
                      <div class="relative drone-avatar-container mr-3">
                        <div class="drone-avatar-bg">
                          <div v-if="drone.status === 'flying'" class="drone-pulse"></div>
                          <n-icon v-if="drone.status === 'idle'" class="text-blue-500 text-lg"><play-circle-outlined /></n-icon>
                          <n-icon v-else-if="drone.status === 'flying'" class="text-green-500 text-lg"><environment-outlined /></n-icon>
                          <n-icon v-else-if="drone.status === 'charging'" class="text-amber-500 text-lg"><thunderbolt-outlined /></n-icon>
                          <n-icon v-else-if="['maintenance', 'error'].includes(drone.status)" class="text-red-500 text-lg"><warning-outlined /></n-icon>
                        </div>
                        <div v-if="drone.camera_equipped" class="camera-indicator" @click.stop="showDroneVideoStream(drone)">
                          <n-icon><video-camera-outlined /></n-icon>
                        </div>
                      </div>
                      <div class="flex-1">
                        <div class="font-medium text-slate-700 flex items-center justify-between">
                          <span>{{ drone.name }}</span>
                          <n-tag :type="getDroneStatusType(drone.status)" class="light-tag">
                            {{ getStatusText(drone.status) }}
                          </n-tag>
                        </div>
                        <div class="mt-1 flex items-center justify-between">
                          <div class="flex items-center text-xs text-slate-500 mr-2">
                            <n-icon class="mr-1 text-xs"><aim-outlined /></n-icon>
                            {{ formatLocation(drone.current_location) }}
                          </div>
                          <div class="text-xs font-medium" :class="getBatteryTextColor(drone.battery_level)">
                            {{ drone.battery_level }}%
                          </div>
                        </div>
                        <div class="mt-1">
                          <div class="flex justify-between items-center text-xs text-slate-500 mb-1">
                            <span>电量</span>
                          </div>
                          <n-progress 
                            :percentage="drone.battery_level" 
                            :color="getBatteryColor(drone.battery_level)"
                            :show-indicator="false"
                            :height="6"
                            class="light-progress"
                          />
                        </div>
                      </div>
                    </div>
                    <div class="drone-actions flex justify-between px-3 pb-2">
                      <button @click.stop="flyToDrone(drone)" class="drone-action-btn">
                        <n-icon><environment-outlined /></n-icon>
                        <span>定位</span>
                      </button>
                      <button v-if="drone.camera_equipped" @click.stop="showDroneVideoStream(drone)" class="drone-action-btn">
                        <n-icon><video-camera-outlined /></n-icon>
                        <span>监控</span>
                      </button>
                      <button @click.stop="showDroneDetails(drone)" class="drone-action-btn">
                        <n-icon><info-circle-outlined /></n-icon>
                        <span>详情</span>
                      </button>
                    </div>
                  </div>
                  <div v-if="activeDrones.length === 0" class="text-center text-slate-500 py-4">
                    暂无活跃无人机
                  </div>
                </div>
              </div>
            </div>
          </div>
          
          <!-- 中间空白区域 -->
          <div class="col-span-6"></div>
          
          <!-- 右侧控制面板 -->
          <div class="col-span-3 flex flex-col gap-4 pointer-events-auto">
            <!-- 事件和警报 -->
            <div class="light-card">
              <div class="card-border">
                <div class="flex justify-between items-center mb-4 title-bar">
                  <div class="light-title">
                    <div class="title-dot"></div>
                    <h2 class="font-bold text-lg text-slate-700 flex items-center">
                      <span class="event-icon mr-2"></span>
                      最新事件
                      <span class="light-badge">03</span>
                    </h2>
                  </div>
                  <router-link to="/events" class="text-blue-500 text-sm light-link">查看全部</router-link>
                </div>
                
                <div class="space-y-3">
                  <div v-for="event in recentEvents" :key="event.id" class="light-event-card" :class="getLightEventCardClass(event.level)">
                    <div class="flex justify-between items-start">
                      <div>
                        <div class="font-medium text-slate-700">{{ event.title }}</div>
                        <div class="text-xs text-slate-500">{{ formatDate(event.timestamp) }}</div>
                      </div>
                      <n-tag :type="getTagTypeByEventLevel(event.level)" size="small" class="light-tag">{{ event.level }}</n-tag>
                    </div>
                    <div class="text-sm text-slate-600 mt-1">{{ event.description }}</div>
                  </div>
                </div>
              </div>
            </div>
            
            <!-- 任务进度 -->
            <div class="light-card">
              <div class="card-border">
                <div class="flex justify-between items-center mb-4 title-bar">
                  <div class="light-title">
                    <div class="title-dot"></div>
                    <h2 class="font-bold text-lg text-slate-700 flex items-center">
                      <span class="task-icon mr-2"></span>
                      任务进度
                      <span class="light-badge">04</span>
                    </h2>
                  </div>
                  <router-link to="/tasks" class="text-blue-500 text-sm light-link">查看全部</router-link>
                </div>
                
                <div class="space-y-4">
                  <div v-for="task in activeTasks" :key="task.id" class="light-task-card">
                    <div class="flex justify-between items-center">
                      <div class="font-medium text-slate-700">{{ task.title }}</div>
                      <div class="text-xs text-blue-600">{{ task.displayProgress }}%</div>
                    </div>
                    <n-progress type="line" :percentage="task.displayProgress" :processing="task.status === 'in_progress'" :status="getProgressStatus(task.status)" class="light-progress" />
                    <div class="flex justify-between text-xs text-slate-500">
                      <div>{{ formatDate(task.startTime) }}</div>
                      <div>预计完成: {{ formatDate(task.estimatedEndTime) }}</div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, inject, reactive, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useMessage, NIcon } from 'naive-ui'
import { format } from 'date-fns'
import { useDroneStore } from '@/store/drone'
import { 
  PlayCircleOutlined, 
  EnvironmentOutlined,
  ThunderboltOutlined, 
  WarningOutlined,
  VideoCameraOutlined,
  InfoCircleOutlined,
  AimOutlined
} from '@vicons/antd'

const router = useRouter()
const message = useMessage()
const droneStore = useDroneStore()

// 系统概况数据
const summaryData = ref({
  // onlineDrones 将通过 droneStore.activeDroneCount 计算
  // totalDrones 将通过 droneStore.totalDroneCount 计算
  activeAgents: 5, // 示例数据，后续应从 Agent Store 获取
  totalAgents: 5,  // 示例数据
  pendingEvents: 3, // 示例数据，后续应从 Event Store 获取
  activeTasks: 4,   // 示例数据，后续应从 Task Store 获取
  cpuUsage: 42,
  memoryUsage: 68,
  storageUsage: 35
})

// 显示值（用于动画）
const displayedValues = reactive({
  cpuUsage: 0,
  memoryUsage: 0,
  storageUsage: 0
})

// 从 Store 获取的无人机数据
const onlineDrones = computed(() => droneStore.activeDroneCount)
const totalDrones = computed(() => droneStore.totalDroneCount)

// 系统资源使用颜色计算
const cpuUsageColor = computed(() => getUsageColor(summaryData.value.cpuUsage))
const memoryUsageColor = computed(() => getUsageColor(summaryData.value.memoryUsage))
const storageUsageColor = computed(() => getUsageColor(summaryData.value.storageUsage))

// 根据使用率返回颜色
function getUsageColor(usage) {
  if (usage < 50) return '#3b82f6'
  if (usage < 80) return '#f59e0b'
  return '#ef4444'
}

// 无人机相关状态
const selectedDrone = ref(null)

// 获取活跃无人机列表
const activeDrones = computed(() => 
  droneStore.drones.filter(drone => drone.status !== 'offline')
)

// 选择无人机
const selectDrone = (drone) => {
  selectedDrone.value = drone
  
  // 使用全局地图方法定位到无人机
  const flyToLocation = inject('flyToLocation')
  if (flyToLocation && drone.location) {
    flyToLocation(drone.location)
  }
}

// 监听全局无人机选择事件
onMounted(() => {
  window.addEventListener('drone-selected', (event) => {
    const droneId = event.detail.droneId
    const drone = droneStore.getDroneById(droneId)
    if (drone) {
      selectDrone(drone)
    }
  })
  
  // 添加时间更新
  updateCurrentTime()
  timeInterval = setInterval(updateCurrentTime, 1000)
})

onUnmounted(() => {
  if (timeInterval) {
    clearInterval(timeInterval)
  }
})

// 获取无人机状态类型
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

// 获取电池颜色
const getBatteryColor = (level) => {
  if (level <= 20) return '#ef4444'
  if (level <= 50) return '#f59e0b'
  return '#3b82f6'
}

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

// 获取事件卡片样式
const getLightEventCardClass = (level) => {
  if (level === 'high') return 'event-high'
  if (level === 'medium') return 'event-medium'
  return 'event-low'
}

// 最近事件列表
const recentEvents = ref([
  { 
    id: 1, 
    title: '发现可疑人员活动', 
    description: '在北区工业园附近检测到可疑人员活动，已派出无人机进行详细巡查', 
    level: 'medium', 
    timestamp: new Date(Date.now() - 15 * 60 * 1000) 
  },
  { 
    id: 2, 
    title: '交通拥堵预警', 
    description: '东部主干道检测到交通拥堵情况，拥堵指数达到75%', 
    level: 'low', 
    timestamp: new Date(Date.now() - 45 * 60 * 1000) 
  },
  { 
    id: 3, 
    title: '紧急火灾报警', 
    description: '南区仓库区域检测到火灾迹象，温度异常升高，烟雾检测器报警', 
    level: 'high', 
    timestamp: new Date(Date.now() - 5 * 60 * 1000) 
  }
])

// 活跃任务列表
const activeTasks = ref([
  { 
    id: 1, 
    title: '紧急消防支援', 
    progress: 65, 
    displayProgress: 0,
    status: 'in_progress', 
    startTime: new Date(Date.now() - 20 * 60 * 1000),
    estimatedEndTime: new Date(Date.now() + 15 * 60 * 1000)
  },
  { 
    id: 2, 
    title: '日常安防巡逻', 
    progress: 80, 
    displayProgress: 0,
    status: 'in_progress', 
    startTime: new Date(Date.now() - 45 * 60 * 1000),
    estimatedEndTime: new Date(Date.now() + 10 * 60 * 1000)
  },
  { 
    id: 3, 
    title: '物资紧急配送', 
    progress: 30, 
    displayProgress: 0,
    status: 'in_progress', 
    startTime: new Date(Date.now() - 10 * 60 * 1000),
    estimatedEndTime: new Date(Date.now() + 25 * 60 * 1000)
  }
])

// 格式化日期
function formatDate(date) {
  return format(date, 'HH:mm:ss')
}

// 根据事件级别获取边框颜色
function getBorderColorByEventLevel(level) {
  if (level === 'high') return 'border-danger'
  if (level === 'medium') return 'border-warning'
  return 'border-primary'
}

// 根据事件级别获取标签类型
function getTagTypeByEventLevel(level) {
  if (level === 'high') return 'error'
  if (level === 'medium') return 'warning'
  return 'info'
}

// 获取进度条状态
function getProgressStatus(status) {
  if (status === 'completed') return 'success'
  if (status === 'failed') return 'error'
  return 'default'
}

// 在组件挂载时获取无人机数据并启动动画
onMounted(async () => {
  try {
    await droneStore.fetchDrones()
    // 这里可以添加获取其他数据的逻辑，如 agents, events, tasks
    
    // 启动进度条动画
    startProgressAnimation()
  } catch (error) {
    message.error('加载主页数据失败: ' + error.message)
  }
})

// 进度条动画函数
function startProgressAnimation() {
  const duration = 1500 // 动画持续时间（毫秒）
  const steps = 60 // 动画步数
  const interval = duration / steps // 每步间隔时间
  
  let currentStep = 0
  
  const timer = setInterval(() => {
    currentStep++
    const progress = Math.min(currentStep / steps, 1) // 0到1的进度值
    
    // 更新系统资源使用率进度条
    displayedValues.cpuUsage = Math.round(progress * summaryData.value.cpuUsage)
    displayedValues.memoryUsage = Math.round(progress * summaryData.value.memoryUsage)
    displayedValues.storageUsage = Math.round(progress * summaryData.value.storageUsage)
    
    // 更新任务进度条
    activeTasks.value.forEach(task => {
      task.displayProgress = Math.round(progress * task.progress)
    })
    
    // 动画结束后清除定时器
    if (currentStep >= steps) {
      clearInterval(timer)
    }
  }, interval)
}

// 无人机实时视频相关逻辑
const showDroneVideo = ref(false)
const droneVideoRef = ref(null)
const currentTime = ref('')
const videoStreamUrl = ref('')

// 更新当前时间
const updateCurrentTime = () => {
  const now = new Date()
  const hours = String(now.getHours()).padStart(2, '0')
  const minutes = String(now.getMinutes()).padStart(2, '0')
  const seconds = String(now.getSeconds()).padStart(2, '0')
  currentTime.value = `${hours}:${minutes}:${seconds}`
}

// 显示无人机实时视频
const showDroneVideoStream = (drone) => {
  selectedDrone.value = drone
  showDroneVideo.value = true
  
  // 连接到后端的视频流
  // 这里使用API获取视频流URL
  // 以下是示例URL，实际应用中应从后端API获取
  const apiUrl = `/api/drones/${drone.drone_id}/video-stream`
  
  // 模拟API调用
  message.success(`正在连接 ${drone.name} 的视频流...`)
  
  // 在实际应用中，这里应该调用API获取视频流URL
  // 例如： videoStreamUrl.value = await droneApi.getVideoStreamUrl(drone.drone_id)
  // 这里使用模拟数据
  setTimeout(() => {
    // 使用WebSocket或者HLS/DASH流
    videoStreamUrl.value = `https://example.com/drone-streams/${drone.drone_id}/live.m3u8`
    
    // 在实际项目中，你可以使用以下方式之一：
    // 1. WebRTC - 低延迟实时视频
    // 2. HLS/DASH - 稍高延迟但兼容性好
    // 3. RTMP - 传统流媒体协议
    
    // 简单模拟 - 实际中应该使用真实流或Video.js等库
    if (droneVideoRef.value) {
      // 使用模拟视频替代实际流
      droneVideoRef.value.src = 'https://www.w3schools.com/html/mov_bbb.mp4' // 示例视频
      droneVideoRef.value.play().catch(err => {
        console.error('无法播放视频:', err)
        message.error('视频播放失败')
      })
    }
    
    // 通知地图高亮显示选中的无人机
    highlightDroneOnMap(drone.drone_id)
  }, 1000)
}

// 关闭无人机实时视频
const closeDroneVideo = () => {
  if (droneVideoRef.value) {
    droneVideoRef.value.pause()
    droneVideoRef.value.src = ''
  }
  
  videoStreamUrl.value = ''
  showDroneVideo.value = false
  
  // 取消地图上无人机的高亮显示
  resetDroneHighlight()
}

// 切换全屏视频
const toggleFullscreenVideo = () => {
  const videoElement = droneVideoRef.value
  
  if (!videoElement) return
  
  if (!document.fullscreenElement) {
    videoElement.requestFullscreen().catch(err => {
      message.error(`无法进入全屏模式: ${err.message}`)
    })
  } else {
    document.exitFullscreen()
  }
}

// 格式化位置
const formatLocation = (location) => {
  if (!location) return '未知位置'
  
  // 假设location是一个包含经纬度的对象
  if (typeof location === 'object' && location.latitude && location.longitude) {
    // 简化显示，保留两位小数
    return `${location.latitude.toFixed(2)}°, ${location.longitude.toFixed(2)}°`
  } else if (Array.isArray(location) && location.length >= 2) {
    // 如果是数组格式
    return `${location[1].toFixed(2)}°, ${location[0].toFixed(2)}°`
  }
  
  return '未知位置'
}

// 获取电池文本颜色
const getBatteryTextColor = (level) => {
  if (level <= 20) return 'text-red-500'
  if (level <= 50) return 'text-amber-500'
  return 'text-green-500'
}

// 显示无人机详情
const showDroneDetails = (drone) => {
  // 跳转到无人机详情页面
  router.push(`/drones/${drone.drone_id}`)
}

// 定位到无人机
const flyToDrone = (drone) => {
  if (!drone.current_location) {
    message.warning('无法定位，无人机位置信息不可用')
    return
  }
  
  // 使用全局地图方法定位到无人机
  const flyToLocation = inject('flyToLocation')
  if (flyToLocation) {
    flyToLocation(drone.current_location)
    message.success(`已定位到无人机 ${drone.name}`)
  }
  
  // 高亮显示无人机
  highlightDroneOnMap(drone.drone_id)
}

// 在地图上高亮显示无人机
const highlightDroneOnMap = (droneId) => {
  // 这个函数应该与地图组件通信，高亮显示指定的无人机
  // 例如使用事件总线或者Pinia/Vuex状态管理
  window.dispatchEvent(new CustomEvent('highlight-drone', { 
    detail: { droneId } 
  }))
}

// 重置无人机高亮显示
const resetDroneHighlight = () => {
  window.dispatchEvent(new CustomEvent('reset-drone-highlight'))
}
</script>

<style scoped>
.light-card {
  background: white;
  border-radius: 12px;
  box-shadow: 0 5px 20px rgba(0, 0, 0, 0.05);
  padding: 16px;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
}

.light-card:hover {
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.08);
  transform: translateY(-2px);
}

.card-border {
  position: relative;
  border-radius: 8px;
  padding: 4px;
}

.light-title {
  position: relative;
  display: flex;
  align-items: center;
  padding-left: 12px;
}

.title-dot {
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 4px;
  height: 60%;
  background: linear-gradient(to bottom, #93c5fd, #3b82f6);
  border-radius: 2px;
}

.light-badge {
  background-color: #f8fafc;
  color: #3b82f6;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 0.7rem;
  font-weight: 700;
  margin-left: 8px;
  border: 1px solid rgba(59, 130, 246, 0.3);
  font-family: 'Courier New', monospace;
  letter-spacing: 1px;
}

.title-bar {
  border-bottom: 1px solid rgba(59, 130, 246, 0.1);
  padding-bottom: 10px;
  margin-bottom: 16px;
}

.light-divider {
  background-color: rgba(59, 130, 246, 0.1) !important;
  margin: 16px 0;
}

.light-progress :deep(.n-progress-graph) {
  background-color: rgba(59, 130, 246, 0.1) !important;
}

.light-progress :deep(.n-progress-content) {
  background: linear-gradient(to right, #93c5fd, #3b82f6) !important;
}

.light-number {
  font-family: 'Courier New', monospace;
  color: #3b82f6;
  font-weight: bold;
}

.light-tag :deep(.n-tag__content) {
  padding: 1px 8px;
  font-size: 0.75rem;
  letter-spacing: 0.5px;
  font-weight: 500;
}

.light-drone-card {
  background: white;
  border-left: 2px solid transparent;
  transition: all 0.3s ease;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.03);
}

.light-drone-card:hover {
  background: rgba(243, 244, 246, 0.8);
  border-left: 2px solid #3b82f6;
}

.selected-light-drone {
  background: rgba(243, 244, 246, 0.8) !important;
  border-left: 2px solid #3b82f6 !important;
}

.light-icon-bg {
  background: white;
  border: 1px solid rgba(59, 130, 246, 0.3);
  box-shadow: 0 2px 6px rgba(59, 130, 246, 0.1);
}

.light-event-card {
  padding: 12px;
  border-radius: 8px;
  margin-bottom: 10px;
  border-left: 3px solid;
  transition: all 0.3s ease;
  background: white;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.03);
}

.light-event-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.06);
}

.event-high {
  border-left-color: #ef4444;
}

.event-medium {
  border-left-color: #f59e0b;
}

.event-low {
  border-left-color: #3b82f6;
}

.light-task-card {
  padding: 12px;
  border-radius: 8px;
  background: white;
  margin-bottom: 10px;
  transition: all 0.3s ease;
  border: 1px solid rgba(59, 130, 246, 0.1);
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.03);
}

.light-task-card:hover {
  background: rgba(243, 244, 246, 0.8);
  border: 1px solid rgba(59, 130, 246, 0.3);
}

.scrollbar-light::-webkit-scrollbar {
  width: 4px;
}

.scrollbar-light::-webkit-scrollbar-track {
  background: rgba(243, 244, 246, 0.5);
  border-radius: 10px;
}

.scrollbar-light::-webkit-scrollbar-thumb {
  background: rgba(59, 130, 246, 0.3);
  border-radius: 10px;
}

.light-link {
  position: relative;
  transition: all 0.3s ease;
}

.light-link:hover {
  color: #1d4ed8;
}

.light-link::after {
  content: '';
  position: absolute;
  bottom: -2px;
  left: 0;
  width: 0;
  height: 1px;
  background-color: #3b82f6;
  transition: width 0.3s ease;
}

.light-link:hover::after {
  width: 100%;
}

.status-icon, .drone-icon, .event-icon, .task-icon {
  display: inline-block;
  width: 18px;
  height: 18px;
  background: #f1f5f9;
  border-radius: 4px;
  position: relative;
}

.status-icon::before {
  content: '';
  position: absolute;
  inset: 4px;
  background-color: #3b82f6;
  border-radius: 2px;
}

.drone-icon::before {
  content: '';
  position: absolute;
  inset: 4px;
  background-color: #3b82f6;
  border-radius: 2px;
  clip-path: polygon(50% 0%, 100% 50%, 50% 100%, 0% 50%);
}

.event-icon::before {
  content: '';
  position: absolute;
  inset: 4px;
  background-color: #f59e0b;
  border-radius: 2px;
  clip-path: polygon(50% 0%, 100% 38%, 82% 100%, 18% 100%, 0% 38%);
}

.task-icon::before {
  content: '';
  position: absolute;
  inset: 4px;
  background-color: #3b82f6;
  border-radius: 2px;
  clip-path: polygon(0% 0%, 100% 0%, 100% 70%, 50% 100%, 0% 70%);
}

.drone-video-container {
  width: 100%;
  height: 0;
  padding-bottom: 56.25%; /* 16:9 aspect ratio */
  position: relative;
}

.video-control-btn {
  background: none;
  border: none;
  padding: 0;
  cursor: pointer;
  outline: none;
}

.drone-avatar-container {
  width: 40px;
  height: 40px;
  position: relative;
}

.drone-avatar-bg {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  overflow: hidden;
  position: absolute;
  top: 0;
  left: 0;
}

.drone-pulse {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.2);
  animation: pulse 1.5s infinite;
}

@keyframes pulse {
  0% {
    transform: scale(0.5);
    opacity: 0.5;
  }
  50% {
    transform: scale(1);
    opacity: 1;
  }
  100% {
    transform: scale(0.5);
    opacity: 0.5;
  }
}

.camera-indicator {
  position: absolute;
  top: 5px;
  right: 5px;
  width: 20px;
  height: 20px;
  background: rgba(255, 255, 255, 0.8);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
}

.drone-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.drone-action-btn {
  background: none;
  border: none;
  padding: 0;
  cursor: pointer;
  outline: none;
  display: flex;
  align-items: center;
  gap: 4px;
}
</style>