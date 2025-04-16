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
              <div class="flex justify-between items-center mb-4">
                <h2 class="font-bold text-lg">活跃无人机</h2>
                <span class="text-xs text-gray-500">({{ activeDrones.length }})</span>
              </div>
              
              <div class="overflow-y-auto max-h-60">
                  <div 
                    v-for="drone in activeDrones" 
                    :key="drone.drone_id"
                    class="p-3 rounded-lg cursor-pointer mb-3 transition-all hover:shadow-md border-l-4"
                    :class="selectedDrone?.drone_id === drone.drone_id ? 'border-blue-500 bg-blue-50 bg-opacity-50' : 'border-transparent'"
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
                             class="w-14 h-14 rounded-lg overflow-hidden relative bg-blue-500">
                          <div class="absolute top-0 right-0 w-2 h-2 rounded-full bg-green-500 animate-pulse m-1"></div>
                          <div class="absolute inset-0 flex items-center justify-center bg-black bg-opacity-30">
                            <n-icon size="18" class="text-white"><video-camera-outlined /></n-icon>
                          </div>
                        </div>
                        
                        <!-- Case 2: 无人机飞行中 (显示图标 + 可点击播放按钮) -->
                        <div v-else-if="drone.status === 'flying'" 
                             class="w-14 h-14 rounded-lg bg-gray-100 flex items-center justify-center relative overflow-hidden drone-icon-interactive">
                          <n-icon :class="getDroneIconColor(drone.status)" class="text-2xl">
                            <environment-outlined />
                          </n-icon>
                          <div class="absolute inset-0 bg-black bg-opacity-0 hover:bg-opacity-30 flex items-center justify-center transition-all">
                            <div class="w-6 h-6 rounded-full bg-primary flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
                              <n-icon size="12" class="text-white"><video-camera-outlined /></n-icon>
                            </div>
                          </div>
                        </div>
                        
                        <!-- Case 3: 其他状态 (仅显示状态图标，无交互) -->
                        <div v-else 
                             class="w-14 h-14 rounded-lg bg-gray-100 flex items-center justify-center drone-icon-static">
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
                          <n-tag :type="getDroneStatusType(drone.status)" size="small" class="text-xs">
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
                              class=""
                            />
                          </div>
                        
                        <div class="mt-2 text-xs text-gray-500 flex items-center justify-between">
                          <span>型号: {{ drone.model || '未知' }}</span>
                          <span class="flex items-center">
                            <n-icon size="tiny" class="mr-1"><environment-outlined /></n-icon>
                            {{ formatCoordinates(drone.current_location) }}
                          </span>
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
    
    <!-- 无人机视频模态框 - 移到父容器外部，使其不受pointer-events-none的影响 -->
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
  if (usage < 50) return '#18A058'
  if (usage < 80) return '#F0A020'
  return '#D03050'
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