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
                <div class="overflow-y-auto max-h-60 scrollbar-light">
                  <div 
                    v-for="drone in activeDrones" 
                    :key="drone.drone_id"
                    class="p-3 rounded-lg cursor-pointer mb-3 transition-all light-drone-card hover:shadow-md"
                    :class="selectedDrone?.drone_id === drone.drone_id ? 'selected-light-drone border-l-4 border-blue-500' : 'border-l-4 border-transparent'"
                    @click="selectDrone(drone)"
                  >
                    <div class="flex items-start">
                      <div 
                        class="drone-preview-container mr-3 relative"
                        :class="{ 'cursor-pointer': drone.status === 'flying', 'cursor-not-allowed': drone.status !== 'flying' }"
                        @click.stop="openVideoModal(drone)" 
                      >
                        <!-- 无人机视频预览或图标 -->
                        
                        <!-- Case 1: 当前选中且视频激活 (显示动态预览) -->
                        <div v-if="selectedDrone?.drone_id === drone.drone_id && droneVideoActive" 
                             class="drone-video-preview rounded-lg overflow-hidden">
                          <div class="video-active-indicator"></div>
                          <div class="video-preview-play">
                            <n-icon size="18" class="text-white"><video-camera-outlined /></n-icon>
                          </div>
                        </div>
                        
                        <!-- Case 2: 无人机飞行中 (显示图标 + 可点击播放按钮) -->
                        <div v-else-if="drone.status === 'flying'" 
                             class="w-14 h-14 rounded-lg light-icon-bg flex items-center justify-center relative overflow-hidden drone-icon-interactive">
                          <n-icon :class="getDroneIconColor(drone.status)" class="text-2xl">
                            <environment-outlined />
                          </n-icon>
                          <div class="video-preview-button">
                            <n-icon size="12" class="text-white"><video-camera-outlined /></n-icon>
                          </div>
                        </div>
                        
                        <!-- Case 3: 其他状态 (仅显示状态图标，无交互) -->
                        <div v-else 
                             class="w-14 h-14 rounded-lg light-icon-bg flex items-center justify-center drone-icon-static">
                          <n-icon :class="getDroneIconColor(drone.status)" class="text-2xl">
                            <play-circle-outlined v-if="drone.status === 'idle'" />
                            <thunderbolt-outlined v-else-if="drone.status === 'charging'" />
                            <warning-outlined v-else-if="['maintenance', 'error'].includes(drone.status)" />
                            <question-circle-outlined v-else /> <!-- Fallback icon -->
                          </n-icon>
                        </div>
                        
                      </div>
                      
                      <div class="flex-1">
                        <div class="flex justify-between items-start">
                          <div class="font-medium text-slate-700 text-sm">{{ drone.name }}</div>
                          <n-tag :type="getDroneStatusType(drone.status)" class="light-tag text-xs">
                            {{ getStatusText(drone.status) }}
                          </n-tag>
                        </div>
                        
                        <div class="mt-2 flex items-center justify-between">
                          <div class="text-xs text-slate-500">电量</div>
                          <div class="text-xs font-medium" :class="getBatteryTextColor(drone.battery_level)">
                            {{ drone.battery_level }}%
                          </div>
                        </div>
                        <div class="mt-1">
                            <n-progress 
                              :percentage="drone.battery_level" 
                              :color="getBatteryColor(drone.battery_level)"
                              :show-indicator="false"
                            :height="4"
                              class="light-progress"
                            />
                          </div>
                        
                        <div class="mt-2 text-xs text-slate-500 flex items-center justify-between">
                          <span>型号: {{ drone.model || '未知' }}</span>
                          <span class="flex items-center">
                            <n-icon size="tiny" class="mr-1"><environment-outlined /></n-icon>
                            {{ formatCoordinates(drone.current_location) }}
                          </span>
                        </div>
                      </div>
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
  
  <!-- 无人机视频模态框 -->
  <n-modal
    v-model:show="droneVideoModalVisible"
    style="width: 800px; max-width: 90vw;"
    preset="card"
    :title="`${selectedDrone?.name || '未知无人机'} - 实时视频`"
    :bordered="false"
    :segmented="{ content: true }"
    @close="closeVideoModal"
  >
    <div class="drone-video-wrapper" style="height: 450px;">
      <DroneVideoStream
        v-if="selectedDrone"
        ref="videoStreamRef"
        :drone-id="selectedDrone.name"
        :drone-name="selectedDrone.name"
        :status="selectedDrone.status"
        :drone-location="selectedDrone.current_location"
        :auto-connect="true"
        @connected="handleVideoConnected"
        @disconnected="handleVideoDisconnected"
      />
    </div>
    
    <div class="drone-video-info mt-4">
      <div v-if="selectedDrone" class="grid grid-cols-2 gap-y-2 text-sm">
        <div class="text-gray-500">型号:</div>
        <div class="font-medium">{{ selectedDrone.model || '未知' }}</div>
        
        <div class="text-gray-500">电量:</div>
        <div class="font-medium">
          <n-progress :percentage="selectedDrone.battery_level" :color="getBatteryColor(selectedDrone.battery_level)" :show-indicator="false" />
          <span :class="getBatteryTextColor(selectedDrone.battery_level)">{{ selectedDrone.battery_level }}%</span>
        </div>
        
        <div class="text-gray-500">状态:</div>
        <div class="font-medium">
          <n-tag :type="getDroneStatusType(selectedDrone.status)">
            {{ getStatusText(selectedDrone.status) }}
          </n-tag>
        </div>
        
        <div class="text-gray-500">坐标:</div>
        <div class="font-medium">{{ formatCoordinates(selectedDrone.current_location) }}</div>
      </div>
      
      <n-divider />
      
      <div class="flex justify-between">
        <n-button type="primary" @click="droneVideoActive = true" :disabled="droneVideoActive">
          <template #icon><n-icon><play-circle-outlined /></n-icon></template>
          连接视频
        </n-button>
        
        <n-button @click="closeVideoModal">
          关闭
        </n-button>
      </div>
    </div>
  </n-modal>
</template>

<script setup>
import { ref, computed, onMounted, inject, reactive } from 'vue'
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
  QuestionCircleOutlined
} from '@vicons/antd'
import DroneVideoStream from '@/components/drone/DroneVideoStream.vue'

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
const droneVideoActive = ref(false)

// 获取活跃无人机列表
const activeDrones = computed(() => 
  droneStore.drones.filter(drone => drone.status !== 'offline')
)

// 选择无人机
const selectDrone = (drone) => {
  const isCurrentlySelected = selectedDrone.value?.drone_id === drone.drone_id;

  // 只有在点击非当前选中无人机，或者点击当前选中且飞行中的无人机时，才执行后续操作
  if (!isCurrentlySelected || (isCurrentlySelected && drone.status === 'flying')) {
    
    // 如果点击的是已选中的飞行中无人机，尝试打开视频模态框
    if (isCurrentlySelected && drone.status === 'flying') {
      droneVideoModalVisible.value = true;
      return; // 直接返回，不执行下面的地图定位等操作
    }

    // 如果点击的是新的无人机
    if (!isCurrentlySelected) {
      selectedDrone.value = drone;
      droneVideoActive.value = false; // 重置视频激活状态
      
      // 定位地图到新选中的无人机
      const flyToLocation = inject('flyToLocation', null);
      if (flyToLocation && drone.current_location?.coordinates) {
        flyToLocation({
          lng: drone.current_location.coordinates[0],
          lat: drone.current_location.coordinates[1],
          zoom: 16
        });
      }
      
      // 通知地图高亮
      const emitDroneSelected = inject('emitDroneSelected', null);
      if (emitDroneSelected) {
        emitDroneSelected(drone.drone_id);
      }
      
      // 如果新选中的无人机正在飞行，短暂延迟后打开视频模态框
      if (drone.status === 'flying') {
        setTimeout(() => {
          droneVideoModalVisible.value = true;
        }, 300); // 延迟确保地图动画有时间开始
      } else {
          // 如果不是飞行状态，确保模态框是关闭的
          droneVideoModalVisible.value = false;
      }
    }
  } else if (isCurrentlySelected && drone.status !== 'flying') {
      // 如果点击的是当前已选中的非飞行状态无人机，可以给个提示
      message.info(`${drone.name} 当前未在飞行，无法查看实时视频`);
      // 确保模态框关闭
       droneVideoModalVisible.value = false;
  }
}

// 根据状态获取图标颜色
function getDroneIconColor(status) {
  switch (status) {
    case 'idle': return 'text-blue-500'
    case 'flying': return 'text-green-500'
    case 'charging': return 'text-amber-500'
    case 'maintenance': return 'text-orange-500'
    case 'error': return 'text-red-500'
    default: return 'text-gray-500'
  }
}

// 根据状态获取标签类型
function getDroneStatusType(status) {
  switch (status) {
    case 'idle': return 'info'
    case 'flying': return 'success'
    case 'charging': return 'warning'
    case 'maintenance': return 'warning'
    case 'offline': return 'error'
    case 'error': return 'error'
    default: return 'default'
  }
}

// 获取状态文本
function getStatusText(status) {
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

// 根据电池电量获取文本颜色
function getBatteryTextColor(level) {
  if (level <= 20) return 'text-red-500'
  if (level <= 50) return 'text-amber-500'
  return 'text-green-500'
}

// 格式化坐标
function formatCoordinates(geoPoint) {
  if (!geoPoint || !geoPoint.coordinates) return '未知'
  const [lng, lat] = geoPoint.coordinates
  return `${lat.toFixed(4)}, ${lng.toFixed(4)}`
}

// 获取电池颜色
const getBatteryColor = (level) => {
  if (level <= 20) return '#ef4444'
  if (level <= 50) return '#f59e0b'
  return '#3b82f6'
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

// 无人机视频模态框相关逻辑
const droneVideoModalVisible = ref(false)
const videoStreamRef = ref(null)

const handleVideoConnected = () => {
  droneVideoActive.value = true;
  message.success(`已连接到${selectedDrone.value?.name || '无人机'}的视频流`);
}

const handleVideoDisconnected = () => {
  droneVideoActive.value = false;
}

const closeVideoModal = () => {
  droneVideoActive.value = false;
  droneVideoModalVisible.value = false;
  
  // 如果视频组件存在，调用断开连接方法
  if (videoStreamRef.value) {
    videoStreamRef.value.disconnect();
  }
}

// 直接打开视频模态框
const openVideoModal = (drone) => {
  // 只有飞行中的无人机才能打开视频
  if (drone.status !== 'flying') {
    message.info(`${drone.name} 当前未在飞行，无法查看实时视频`);
    return;
  }

  // 如果点击的不是当前选中的无人机，先选中它
  if (!selectedDrone.value || selectedDrone.value.drone_id !== drone.drone_id) {
    selectDrone(drone);
    // 在 selectDrone 中会处理模态框显示，这里不用再显示
    // 但要确保 selectDrone 会在飞行状态下打开模态框
    return; 
  }
  
  // 如果已经是选中的飞行中无人机，直接显示模态框
  droneVideoModalVisible.value = true;
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
  background-color: white;
  border-radius: 0.75rem;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  position: relative;
  overflow: hidden;
}

.light-drone-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
}

.light-drone-card::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: linear-gradient(to right, transparent, rgba(59, 130, 246, 0.5), transparent);
  transform: scaleX(0);
  transition: transform 0.3s ease;
}

.light-drone-card:hover::after {
  transform: scaleX(1);
}

.selected-light-drone {
  background-color: rgba(243, 244, 246, 0.8);
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
}

.drone-preview-container {
  width: 56px;
  height: 56px;
  position: relative;
}

.drone-video-preview {
  width: 100%;
  height: 100%;
  background: linear-gradient(135deg, #1a1a2e, #16213e);
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  animation: pulse 1.5s infinite ease-in-out;
}

.video-active-indicator {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background-color: #e53e3e;
  position: absolute;
  top: 5px;
  right: 5px;
  box-shadow: 0 0 0 2px rgba(255, 255, 255, 0.5);
  animation: blink 1s infinite;
}

.drone-video-preview::after {
  content: '';
  position: absolute;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  border: 2px solid white;
  border-top-color: transparent;
  animation: spin 1s linear infinite;
}

.video-preview-play {
  position: absolute;
  left: 0;
  top: 0;
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.3);
  opacity: 0;
  transition: opacity 0.2s ease;
}

.drone-video-preview:hover .video-preview-play {
  opacity: 1;
}

.video-preview-button {
  position: absolute;
  right: 3px;
  bottom: 3px;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: rgba(59, 130, 246, 0.9);
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transform: scale(0);
  transition: all 0.2s ease;
  z-index: 100; 
}

.light-icon-bg:hover .video-preview-button {
  opacity: 1;
  transform: scale(1);
}

@keyframes pulse {
  0% { opacity: 0.7; }
  50% { opacity: 1; }
  100% { opacity: 0.7; }
}

@keyframes blink {
  0% { opacity: 0.5; }
  50% { opacity: 1; }
  100% { opacity: 0.5; }
}

@keyframes spin {
  100% { transform: rotate(360deg); }
}

.light-event-card {
  border-radius: 0.5rem;
  padding: 0.75rem;
  border-left: 4px solid transparent;
  transition: all 0.3s ease;
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
</style>