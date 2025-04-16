<template>
  <div class="h-full pointer-events-none">
    <!-- 漂浮面板容器 -->
    <div class="p-4 h-full">
      <div class="h-full grid grid-cols-12 gap-4">
          <!-- 左侧信息面板 -->
          <div class="col-span-3 flex flex-col gap-4 pointer-events-auto">
            <!-- 系统状态卡片 -->
            <div class="floating-card bg-white bg-opacity-95">
              <div class="flex justify-between items-center mb-4">
                <h2 class="font-bold text-lg">系统状态</h2>
                <n-tag type="success" size="small">运行中</n-tag>
              </div>
              
              <div class="space-y-3">
                <div class="flex justify-between items-center">
                  <div class="text-gray-600">在线无人机</div>
                  <div class="font-medium">{{ onlineDrones }}/{{ totalDrones }}</div>
                </div>
                <div class="flex justify-between items-center">
                  <div class="text-gray-600">活跃智能体</div>
                  <div class="font-medium">{{ summaryData.activeAgents }}/{{ summaryData.totalAgents }}</div>
                </div>
                <div class="flex justify-between items-center">
                  <div class="text-gray-600">未处理事件</div>
                  <div class="font-medium">{{ summaryData.pendingEvents }}</div>
                </div>
                <div class="flex justify-between items-center">
                  <div class="text-gray-600">进行中任务</div>
                  <div class="font-medium">{{ summaryData.activeTasks }}</div>
                </div>
              </div>
              
              <n-divider />
              
              <!-- 系统资源使用情况 -->
              <div>
                <div class="flex justify-between items-center mb-2">
                  <div class="text-gray-600">CPU使用率</div>
                  <div class="font-medium">{{ summaryData.cpuUsage }}%</div>
                </div>
                <n-progress type="line" :percentage="summaryData.cpuUsage" :indicator-placement="'inside'" :color="cpuUsageColor" />
                
                <div class="flex justify-between items-center mb-2 mt-3">
                  <div class="text-gray-600">内存使用率</div>
                  <div class="font-medium">{{ summaryData.memoryUsage }}%</div>
                </div>
                <n-progress type="line" :percentage="summaryData.memoryUsage" :indicator-placement="'inside'" :color="memoryUsageColor" />
                
                <div class="flex justify-between items-center mb-2 mt-3">
                  <div class="text-gray-600">存储使用率</div>
                  <div class="font-medium">{{ summaryData.storageUsage }}%</div>
                </div>
                <n-progress type="line" :percentage="summaryData.storageUsage" :indicator-placement="'inside'" :color="storageUsageColor" />
              </div>
            </div>
            
            <!-- 无人机状态面板 -->
            <div class="floating-card bg-white bg-opacity-95">
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
          </div>
          
          <!-- 中间空白区域 -->
          <div class="col-span-6"></div>
          
          <!-- 右侧控制面板 -->
          <div class="col-span-3 flex flex-col gap-4 pointer-events-auto">
            <!-- 事件和警报 -->
            <div class="floating-card bg-white bg-opacity-95">
          <div class="flex justify-between items-center mb-4">
            <h2 class="font-bold text-lg">最新事件</h2>
            <router-link to="/events" class="text-primary text-sm">查看全部</router-link>
          </div>
          
          <div class="space-y-3">
            <div v-for="event in recentEvents" :key="event.id" class="border-l-4 pl-3 py-1" :class="getBorderColorByEventLevel(event.level)">
              <div class="flex justify-between items-start">
                <div>
                  <div class="font-medium">{{ event.title }}</div>
                  <div class="text-xs text-gray-500">{{ formatDate(event.timestamp) }}</div>
                </div>
                <n-tag :type="getTagTypeByEventLevel(event.level)" size="small">{{ event.level }}</n-tag>
              </div>
              <div class="text-sm text-gray-600 mt-1">{{ event.description }}</div>
            </div>
          </div>
            </div>
            
            <!-- 任务进度 -->
            <div class="floating-card bg-white bg-opacity-95">
          <div class="flex justify-between items-center mb-4">
            <h2 class="font-bold text-lg">任务进度</h2>
            <router-link to="/tasks" class="text-primary text-sm">查看全部</router-link>
          </div>
          
          <div class="space-y-4">
            <div v-for="task in activeTasks" :key="task.id" class="space-y-2">
              <div class="flex justify-between items-center">
                <div class="font-medium">{{ task.title }}</div>
                <div class="text-xs text-gray-500">{{ task.progress }}%</div>
              </div>
              <n-progress type="line" :percentage="task.progress" :processing="task.status === 'in_progress'" :status="getProgressStatus(task.status)" />
              <div class="flex justify-between text-xs text-gray-500">
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
</template>

<script setup>
import { ref, computed, onMounted, inject } from 'vue'
import { useRouter } from 'vue-router'
import { useMessage, NIcon } from 'naive-ui'
import { format } from 'date-fns'
import { useDroneStore } from '@/store/drone'
import { 
  PlayCircleOutlined, 
  EnvironmentOutlined,
  ThunderboltOutlined, 
  WarningOutlined
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

// 从 Store 获取的无人机数据
const onlineDrones = computed(() => droneStore.activeDroneCount)
const totalDrones = computed(() => droneStore.totalDroneCount)

// 系统资源使用颜色计算
const cpuUsageColor = computed(() => getUsageColor(summaryData.value.cpuUsage))
const memoryUsageColor = computed(() => getUsageColor(summaryData.value.memoryUsage))
const storageUsageColor = computed(() => getUsageColor(summaryData.value.storageUsage))

// 根据使用率返回颜色
function getUsageColor(usage) {
  if (usage < 50) return '#18A058'
  if (usage < 80) return '#F0A020'
  return '#D03050'
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
  if (level <= 20) return '#ff4d4f'
  if (level <= 50) return '#faad14'
  return '#52c41a'
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
    status: 'in_progress', 
    startTime: new Date(Date.now() - 20 * 60 * 1000),
    estimatedEndTime: new Date(Date.now() + 15 * 60 * 1000)
  },
  { 
    id: 2, 
    title: '日常安防巡逻', 
    progress: 80, 
    status: 'in_progress', 
    startTime: new Date(Date.now() - 45 * 60 * 1000),
    estimatedEndTime: new Date(Date.now() + 10 * 60 * 1000)
  },
  { 
    id: 3, 
    title: '物资紧急配送', 
    progress: 30, 
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



// 在组件挂载时获取无人机数据
onMounted(async () => {
  try {
    await droneStore.fetchDrones()
    // 这里可以添加获取其他数据的逻辑，如 agents, events, tasks
  } catch (error) {
    message.error('加载主页数据失败: ' + error.message)
  }
})
</script>

<style scoped lang="postcss">
.card {
  @apply bg-white p-4 rounded-lg shadow;
}

.floating-card {
  @apply p-4 rounded-lg shadow-lg;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
  backdrop-filter: blur(4px);
  z-index: 100; 
}

.border-danger {
  border-color: #D03050;
}

.border-warning {
  border-color: #F0A020;
}

.border-primary {
  border-color: #2080F0;
}
</style>