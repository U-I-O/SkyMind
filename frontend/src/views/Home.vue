<template>
  <div class="h-full flex flex-col">
    <!-- 主要内容 -->
    <div class="flex-1 grid grid-cols-12 gap-4 p-4 overflow-auto">
      <!-- 左侧信息面板 -->
      <div class="col-span-3 flex flex-col gap-4">
        <!-- 系统状态卡片 -->
        <div class="card">
          <div class="flex justify-between items-center mb-4">
            <h2 class="font-bold text-lg">系统状态</h2>
            <n-tag type="success" size="small">运行中</n-tag>
          </div>
          
          <div class="space-y-3">
            <div class="flex justify-between items-center">
              <div class="text-gray-600">在线无人机</div>
              <div class="font-medium">{{ summaryData.onlineDrones }}/{{ summaryData.totalDrones }}</div>
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
            <div class="flex justify-between items-center">
              <div class="text-gray-600">系统运行时间</div>
              <div class="font-medium">{{ summaryData.uptime || '加载中...' }}</div>
            </div>
            <div class="flex justify-between items-center">
              <div class="text-gray-600">进程数量</div>
              <div class="font-medium">{{ summaryData.processCount }}</div>
            </div>
          </div>
          
          <n-divider />
          
          <!-- 系统资源使用情况 -->
          <div>
            <div class="flex justify-between items-center mb-2">
              <div class="text-gray-600">CPU使用率 ({{ summaryData.cpuCount }}核)</div>
              <div class="font-medium">{{ summaryData.cpuUsage }}%</div>
            </div>
            <n-progress type="line" :percentage="summaryData.cpuUsage" :indicator-placement="'inside'" :color="cpuUsageColor" />
            
            <div class="flex justify-between items-center mb-2 mt-3">
              <div class="text-gray-600">内存使用率</div>
              <div class="font-medium">{{ summaryData.memoryUsage }}% ({{ formatBytes(summaryData.memoryTotal - summaryData.memoryAvailable) }}/{{ formatBytes(summaryData.memoryTotal) }})</div>
            </div>
            <n-progress type="line" :percentage="summaryData.memoryUsage" :indicator-placement="'inside'" :color="memoryUsageColor" />
            
            <div class="flex justify-between items-center mb-2 mt-3">
              <div class="text-gray-600">存储使用率</div>
              <div class="font-medium">{{ summaryData.storageUsage }}% ({{ formatBytes(summaryData.storageTotal - summaryData.storageFree) }}/{{ formatBytes(summaryData.storageTotal) }})</div>
            </div>
            <n-progress type="line" :percentage="summaryData.storageUsage" :indicator-placement="'inside'" :color="storageUsageColor" />
            
            <div class="flex justify-between items-center mt-3">
              <div class="text-gray-600">网络流量</div>
              <div class="font-medium">↑{{ formatBytes(summaryData.networkSent) }} / ↓{{ formatBytes(summaryData.networkReceived) }}</div>
            </div>
            
          </div>
        </div>
        
        <!-- 智能体状态 -->
        <div class="card">
          <div class="flex justify-between items-center mb-4">
            <h2 class="font-bold text-lg">智能体状态</h2>
            <n-button text size="small" quaternary>查看全部</n-button>
          </div>
          
          <div class="space-y-3">
            <div v-for="agent in agents" :key="agent.id" class="flex items-center justify-between">
              <div class="flex items-center">
                <div class="w-2 h-2 rounded-full mr-2" :class="agent.status === 'active' ? 'bg-green-500' : 'bg-gray-400'"></div>
                <div class="font-medium">{{ agent.name }}</div>
              </div>
              <n-tag :type="agent.status === 'active' ? 'success' : 'default'" size="small">{{ agent.status }}</n-tag>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 中央地图区域 -->
      <div class="col-span-6 card p-0 overflow-hidden">
        <div class="h-full">
          <!-- 3D地图组件 -->
          <Map3D />
        </div>
      </div>
      
      <!-- 右侧控制面板 -->
      <div class="col-span-3 flex flex-col gap-4">
        <!-- 事件和警报 -->
        <div class="card">
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
        <div class="card">
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
        
        <!-- 快速操作 -->
        <div class="card">
          <h2 class="font-bold text-lg mb-4">快速操作</h2>
          
          <div class="grid grid-cols-2 gap-3">
            <n-button @click="initiateEmergencyResponse">应急响应</n-button>
            <n-button @click="createDeliveryTask">创建物流任务</n-button>
            <n-button @click="startSecurityPatrol">安防巡检</n-button>
            <n-button @click="initiateAreaScan">区域扫描</n-button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useMessage } from 'naive-ui'
import { format } from 'date-fns'
import Map3D from '../components/map/Map3D.vue'
import { systemApi } from '../api/system'

const router = useRouter()
const message = useMessage()

// 系统概况数据
const summaryData = ref({
  onlineDrones: 8,
  totalDrones: 12,
  activeAgents: 5,
  totalAgents: 5,
  pendingEvents: 3,
  activeTasks: 4,
  cpuUsage: 42,
  memoryUsage: 68,
  storageUsage: 35,
  // 新增系统资源监控数据
  cpuCount: 4,
  memoryTotal: 0,
  memoryAvailable: 0,
  storageTotal: 0,
  storageFree: 0,
  networkSent: 0,
  networkReceived: 0,
  processCount: 0,
  uptime: '',
  systemInfo: {}
})

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

// 智能体列表
const agents = ref([
  { id: 1, name: '监控智能体', status: 'active', type: 'monitor', cpuUsage: 0, memoryUsage: 0 },
  { id: 2, name: '路径规划智能体', status: 'active', type: 'planner', cpuUsage: 0, memoryUsage: 0 },
  { id: 3, name: '应急响应智能体', status: 'active', type: 'response', cpuUsage: 0, memoryUsage: 0 },
  { id: 4, name: '物流调度智能体', status: 'active', type: 'logistics', cpuUsage: 0, memoryUsage: 0 },
  { id: 5, name: '安防巡检智能体', status: 'active', type: 'security', cpuUsage: 0, memoryUsage: 0 }
])

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

// 格式化字节大小
function formatBytes(bytes, decimals = 2) {
  if (bytes === 0) return '0 Bytes'
  
  const k = 1024
  const dm = decimals < 0 ? 0 : decimals
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB']
  
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  
  return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i]
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

// 快速操作函数
function initiateEmergencyResponse() {
  message.info('正在启动应急响应流程')
  router.push('/emergency')
}

function createDeliveryTask() {
  message.info('正在打开物流任务创建界面')
  router.push('/logistics')
}

function startSecurityPatrol() {
  message.info('正在启动安防巡检任务')
  router.push('/security')
}

function initiateAreaScan() {
  message.info('正在初始化区域扫描')
  router.push('/monitor')
}

// 定时器引用
let statusTimer = null

// 获取系统状态
async function fetchSystemStatus() {
  try {
    const response = await systemApi.getSystemStatus()
    if (response.data) {
      // 更新系统资源数据
      summaryData.value.cpuUsage = response.data.cpu_usage
      summaryData.value.memoryUsage = response.data.memory_usage
      summaryData.value.storageUsage = response.data.storage_usage
      
      // 更新其他系统数据
      summaryData.value.onlineDrones = response.data.online_drones
      summaryData.value.totalDrones = response.data.total_drones
      summaryData.value.activeAgents = response.data.active_agents
      summaryData.value.totalAgents = response.data.total_agents
      summaryData.value.pendingEvents = response.data.pending_events
      summaryData.value.activeTasks = response.data.active_tasks
      
      // 更新新增的系统资源监控数据
      summaryData.value.cpuCount = response.data.cpu_count
      summaryData.value.memoryTotal = response.data.memory_total
      summaryData.value.memoryAvailable = response.data.memory_available
      summaryData.value.storageTotal = response.data.storage_total
      summaryData.value.storageFree = response.data.storage_free
      summaryData.value.networkSent = response.data.network.bytes_sent
      summaryData.value.networkReceived = response.data.network.bytes_recv
      summaryData.value.processCount = response.data.process_count
      summaryData.value.uptime = response.data.uptime_formatted
      summaryData.value.systemInfo = response.data.system_info
    }
  } catch (error) {
    console.error('获取系统状态失败:', error)
  }
}

// 获取智能体状态
async function fetchAgentsStatus() {
  try {
    const response = await systemApi.getAgentsStatus()
    if (response.data && response.data.length > 0) {
      agents.value = response.data
    }
  } catch (error) {
    console.error('获取智能体状态失败:', error)
  }
}

// 数据获取
onMounted(() => {
  // 初始加载数据
  fetchSystemStatus()
  fetchAgentsStatus()
  
  // 设置定时器，每10秒更新一次系统状态
  statusTimer = setInterval(() => {
    fetchSystemStatus()
  }, 10000)
})

// 组件卸载时清除定时器
onUnmounted(() => {
  if (statusTimer) {
    clearInterval(statusTimer)
  }
})
</script>