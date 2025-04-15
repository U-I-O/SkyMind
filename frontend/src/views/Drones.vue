<template>
  <div class="h-full pointer-events-none">
    <!-- 使用全局地图，不需要在此页面添加地图组件 -->
    <div class="p-4 h-full">
      <div class="h-full grid grid-cols-12 gap-4">
        <!-- 左侧面板 -->
        <div class="col-span-3 flex flex-col gap-4 pointer-events-auto">
          <!-- 标题和操作按钮 -->
          <div class="floating-card bg-white bg-opacity-95">
            <div class="flex justify-between items-center mb-4">
              <h1 class="text-2xl font-bold">无人机管理</h1>
              
              <!-- 操作按钮 -->
              <div class="flex space-x-3">
                <n-button type="primary" @click="showAddDroneModal = true">
                  <template #icon>
                    <n-icon><plus-icon /></n-icon>
                  </template>
                  添加无人机
                </n-button>
                
                <n-button @click="refreshData">
                  <template #icon>
                    <n-icon><reload-icon /></n-icon>
                  </template>
                  刷新
                </n-button>
              </div>
            </div>
          </div>
          
          <!-- 无人机状态统计 (独立面板) -->
          <div class="floating-card bg-white bg-opacity-95">
            <h2 class="font-bold text-lg mb-4">无人机状态</h2>
            <div class="grid grid-cols-5 gap-4">
              <div class="flex flex-col items-center">
                <div class="w-12 h-12 rounded-full flex items-center justify-center bg-blue-100 text-blue-500 mb-2">
                  <n-icon size="24"><drone-icon /></n-icon>
                </div>
                <div class="text-sm text-gray-500">总无人机</div>
                <div class="text-xl font-bold">{{ droneStats.total }}</div>
              </div>
              
              <div class="flex flex-col items-center">
                <div class="w-12 h-12 rounded-full flex items-center justify-center bg-green-100 text-green-500 mb-2">
                  <n-icon size="24"><check-icon /></n-icon>
                </div>
                <div class="text-sm text-gray-500">在线</div>
                <div class="text-xl font-bold">{{ droneStats.online }}</div>
              </div>
              
              <div class="flex flex-col items-center">
                <div class="w-12 h-12 rounded-full flex items-center justify-center bg-yellow-100 text-yellow-500 mb-2">
                  <n-icon size="24"><flight-icon /></n-icon>
                </div>
                <div class="text-sm text-gray-500">飞行中</div>
                <div class="text-xl font-bold">{{ droneStats.flying }}</div>
              </div>
              
              <div class="flex flex-col items-center">
                <div class="w-12 h-12 rounded-full flex items-center justify-center bg-purple-100 text-purple-500 mb-2">
                  <n-icon size="24"><thunderbolt-icon /></n-icon>
                </div>
                <div class="text-sm text-gray-500">充电中</div>
                <div class="text-xl font-bold">{{ droneStats.charging }}</div>
              </div>
              
              <div class="flex flex-col items-center">
                <div class="w-12 h-12 rounded-full flex items-center justify-center bg-red-100 text-red-500 mb-2">
                  <n-icon size="24"><warning-icon /></n-icon>
                </div>
                <div class="text-sm text-gray-500">离线</div>
                <div class="text-xl font-bold">{{ droneStats.offline }}</div>
              </div>
            </div>
          </div>
          
          <!-- 详情信息面板 (移到左侧) -->
          <div v-if="selectedDrone" class="floating-card bg-white bg-opacity-95">
            <div class="flex justify-between items-center mb-2">
              <h3 class="font-bold text-lg">{{ selectedDrone.name }} 详情</h3>
              <n-tag :type="getStatusType(selectedDrone.status)">{{ selectedDrone.status }}</n-tag>
            </div>
            
            <n-divider style="margin: 10px 0;" />
            
            <div class="grid grid-cols-2 gap-2 mb-4">
              <div class="text-gray-500 text-sm">电量</div>
              <div class="text-sm font-medium">{{ selectedDrone.battery_level }}%</div>
              
              <div class="text-gray-500 text-sm">位置</div>
              <div class="text-sm font-medium">
                {{ formatCoordinate(selectedDrone.current_location?.coordinates[0] || 0) }}, 
                {{ formatCoordinate(selectedDrone.current_location?.coordinates[1] || 0) }}
              </div>
              
              <div class="text-gray-500 text-sm">速度</div>
              <div class="text-sm font-medium">{{ selectedDrone.max_speed }} m/s</div>
              
              <div class="text-gray-500 text-sm">飞行时间</div>
              <div class="text-sm font-medium">{{ selectedDrone.max_flight_time }} 分钟</div>
            </div>
            
            <div class="grid grid-cols-2 gap-2">
              <n-button size="small" @click="viewDroneDetails(selectedDrone)">查看完整详情</n-button>
              <n-button size="small" type="primary" @click="openDroneControl(selectedDrone)">控制无人机</n-button>
            </div>
          </div>
          
          <!-- 未选择无人机时的提示 -->
          <div v-if="!selectedDrone" class="floating-card bg-white bg-opacity-95 flex-1 flex items-center justify-center text-gray-400">
            请从右侧列表中选择一个无人机查看详情
          </div>
        </div>
        
        <!-- 右侧面板 -->
        <div class="col-span-3 col-start-10 flex flex-col gap-4 pointer-events-auto">
          <!-- 筛选条件面板 (移到右侧) -->
          <div class="floating-card bg-white bg-opacity-95">
            <div class="flex justify-between items-center mb-4">
              <div class="flex-1">
                <n-input-group>
                  <n-input v-model:value="searchQuery" placeholder="搜索无人机名称或ID"></n-input>
                  <n-button>
                    <template #icon>
                      <n-icon><search-icon /></n-icon>
                    </template>
                  </n-button>
                </n-input-group>
              </div>
              
              <div class="ml-4">
                <n-radio-group v-model:value="viewMode" size="small">
                  <n-radio-button value="list">
                    <n-icon><list-icon /></n-icon>
                  </n-radio-button>
                  <n-radio-button value="grid">
                    <n-icon><grid-icon /></n-icon>
                  </n-radio-button>
                  <n-radio-button value="map">
                    <n-icon><map-icon /></n-icon>
                  </n-radio-button>
                </n-radio-group>
              </div>
            </div>
            
            <div class="flex space-x-2">
              <n-select
                v-model:value="statusFilter"
                :options="statusOptions"
                placeholder="状态筛选"
                clearable
                class="w-full"
              />
              
              <n-select
                v-model:value="modelFilter"
                :options="modelOptions"
                placeholder="型号筛选"
                clearable
                class="w-full"
              />
            </div>
          </div>
          
          <!-- 无人机列表 (移到右侧) -->
          <div class="floating-card bg-white bg-opacity-95 flex-1 flex flex-col">
            <h2 class="font-bold text-lg mb-4">无人机列表</h2>
            
            <!-- 无人机数据表格 -->
            <div v-if="viewMode === 'list'" class="overflow-y-auto" style="max-height: 400px;">
              <n-data-table
                :columns="columns"
                :data="filteredDrones"
                :pagination="pagination"
                :row-key="row => row.drone_id"
                :loading="loading"
                :scroll-x="true"
              />
            </div>
            
            <!-- 无人机卡片网格视图 -->
            <div v-else-if="viewMode === 'grid'" class="overflow-y-auto" style="max-height: 400px;">
              <div class="grid grid-cols-1 gap-4 pb-4">
                <div v-for="drone in filteredDrones" :key="drone.drone_id" 
                     class="border border-gray-200 rounded-lg p-4 hover:bg-gray-50 cursor-pointer"
                     :class="{'bg-blue-50 border-blue-200': selectedDrone?.drone_id === drone.drone_id}"
                     @click="selectDrone(drone)">
                  <div class="flex justify-between items-start">
                    <div>
                      <h3 class="font-bold text-lg">{{ drone.name }}</h3>
                      <div class="text-xs text-gray-500 mt-1">ID: {{ drone.drone_id }}</div>
                    </div>
                    <n-tag :type="getStatusType(drone.status)">{{ drone.status }}</n-tag>
                  </div>
                  
                  <div class="mt-4 grid grid-cols-2 gap-y-2 text-sm">
                    <div class="text-gray-500">型号:</div>
                    <div class="font-medium">{{ drone.model }}</div>
                    
                    <div class="text-gray-500">电量:</div>
                    <div class="font-medium">
                      <n-progress :percentage="drone.battery_level" :show-indicator="false" />
                      {{ drone.battery_level }}%
                    </div>
                    
                    <div class="text-gray-500">最大时间:</div>
                    <div class="font-medium">{{ drone.max_flight_time }} 分钟</div>
                    
                    <div class="text-gray-500">最大速度:</div>
                    <div class="font-medium">{{ drone.max_speed }} m/s</div>
                  </div>
                  
                  <div class="mt-4 flex justify-center space-x-2">
                    <n-button size="small" @click.stop="viewDroneDetails(drone)">详情</n-button>
                    <n-button size="small" type="primary" @click.stop="openDroneControl(drone)">控制</n-button>
                  </div>
                </div>
              </div>
            </div>
            
            <!-- 地图视图 -->
            <div v-else-if="viewMode === 'map'" class="flex-1 flex items-center justify-center">
              <div class="text-center text-gray-500">地图视图已激活，可以直接在地图上查看无人机位置</div>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 添加无人机对话框 -->
    <n-modal v-model:show="showAddDroneModal" preset="card" title="添加无人机" style="width: 500px" @close="resetForm">
      <n-form ref="addFormRef" :model="droneForm" :rules="rules" label-placement="left" label-width="auto">
        <!-- 表单内容保持不变 -->
      </n-form>
      
      <template #footer>
        <div class="flex justify-end space-x-3">
          <n-button @click="showAddDroneModal = false">取消</n-button>
          <n-button type="primary" :loading="submitting" @click="handleAddDrone">添加</n-button>
        </div>
      </template>
    </n-modal>
    
    <!-- 无人机控制对话框 -->
    <n-modal v-model:show="showControlModal" preset="card" :title="`控制 ${selectedDrone?.name || '无人机'}`" style="width: 600px">
      <!-- 控制对话框内容保持不变 -->
    </n-modal>
  </div>
</template>

<script setup>
import { ref, computed, reactive, onMounted, inject } from 'vue'
import { useRouter } from 'vue-router'
import { useMessage } from 'naive-ui'
import { 
  PlusOutlined as PlusIcon,
  SearchOutlined as SearchIcon, 
  ReloadOutlined as ReloadIcon,
  CheckCircleOutlined as CheckIcon, 
  WarningOutlined as WarningIcon,
  RocketOutlined as FlightIcon,
  TableOutlined as ListIcon,
  AppstoreOutlined as GridIcon,
  EnvironmentOutlined as MapIcon,
  RobotOutlined as DroneIcon,
  ThunderboltOutlined as ThunderboltIcon,
  CloseOutlined
} from '@vicons/antd'
import { getDrones, createDrone, controlDrone as apiControlDrone } from '../api/drone'
import { h } from 'vue'

const router = useRouter()
const message = useMessage()
const mapOperations = inject('mapOperations')

// 状态变量
const loading = ref(false)
const submitting = ref(false)
const showAddDroneModal = ref(false)
const showControlModal = ref(false)
const searchQuery = ref('')
const statusFilter = ref(null)
const modelFilter = ref(null)
const viewMode = ref('grid')
const drones = ref([])
const selectedDrone = ref(null)
const targetLongitude = ref(116.3833)
const targetLatitude = ref(39.9)
const targetAltitude = ref(100)

// 表单数据
const addFormRef = ref(null)
const droneForm = reactive({
  name: '',
  model: '',
  max_flight_time: 30,
  max_speed: 15,
  max_altitude: 500,
  camera_equipped: true,
  payload_capacity: 2.0
})

// 状态选项
const statusOptions = ref([
  { label: '空闲', value: 'idle' },
  { label: '飞行中', value: 'flying' },
  { label: '充电中', value: 'charging' },
  { label: '维护中', value: 'maintenance' },
  { label: '离线', value: 'offline' }
])

// 表单验证规则
const rules = {
  name: [
    { required: true, message: '请输入无人机名称', trigger: 'blur' }
  ],
  model: [
    { required: true, message: '请输入无人机型号', trigger: 'blur' }
  ],
  max_flight_time: [
    { required: true, type: 'number', message: '请输入最大飞行时间', trigger: 'blur' }
  ],
  max_speed: [
    { required: true, type: 'number', message: '请输入最大速度', trigger: 'blur' }
  ],
  max_altitude: [
    { required: true, type: 'number', message: '请输入最大高度', trigger: 'blur' }
  ]
}

// 表格列定义
const columns = [
  {
    title: '名称',
    key: 'name',
    sorter: 'default'
  },
  {
    title: '状态',
    key: 'status',
    sorter: 'default',
    filterOptions: statusOptions.value,
    filter: (value, row) => row.status === value
  },
  {
    title: '型号',
    key: 'model',
    sorter: 'default'
  },
  {
    title: '电池电量',
    key: 'battery_level',
    sorter: 'default'
  },
  {
    title: '操作',
    key: 'actions',
    render: (row) => {
      return [
        h('n-button', { size: 'small', onClick: () => viewDroneDetails(row) }, { default: () => '详情' }),
        h('n-button', { size: 'small', type: 'primary', onClick: () => openDroneControl(row) }, { default: () => '控制' })
      ]
    }
  }
]

// 分页配置
const pagination = {
  pageSize: 10
}


// 获取型号选项
const modelOptions = computed(() => {
  const models = [...new Set(drones.value.map(drone => drone.model))]
  return models.map(model => ({ label: model, value: model }))
})

// 过滤无人机列表
const filteredDrones = computed(() => {
  return drones.value.filter(drone => {
    // 搜索过滤
    if (searchQuery.value && !drone.name.toLowerCase().includes(searchQuery.value.toLowerCase()) && 
        !drone.drone_id.toLowerCase().includes(searchQuery.value.toLowerCase())) {
      return false
    }
    
    // 状态过滤
    if (statusFilter.value && drone.status !== statusFilter.value) {
      return false
    }
    
    // 型号过滤
    if (modelFilter.value && drone.model !== modelFilter.value) {
      return false
    }
    
    return true
  })
})

// 无人机统计数据
const droneStats = computed(() => {
  const total = drones.value.length
  const online = drones.value.filter(d => d.status !== 'offline').length
  const flying = drones.value.filter(d => d.status === 'flying').length
  const charging = drones.value.filter(d => d.status === 'charging').length
  const offline = drones.value.filter(d => d.status === 'offline').length
  
  return { total, online, flying, charging, offline }
})

// 根据状态获取标签类型
function getStatusType(status) {
  switch (status) {
    case 'idle': return 'default'
    case 'flying': return 'info'
    case 'charging': return 'warning'
    case 'maintenance': return 'warning'
    case 'offline': return 'error'
    default: return 'default'
  }
}

// 格式化坐标
function formatCoordinate(coord) {
  return coord.toFixed(6)
}

// 查看无人机详情
function viewDroneDetails(drone) {
  router.push(`/drones/${drone.drone_id}`)
}

// 控制无人机
function openDroneControl(drone) {
  selectedDrone.value = drone
  showControlModal.value = true
}

// 选择无人机
function selectDrone(drone) {
  selectedDrone.value = drone
  // 使用地图操作
  if (drone.current_location?.coordinates) {
    mapOperations.flyTo({
      lat: drone.current_location.coordinates[1],
      lng: drone.current_location.coordinates[0],
      zoom: 18
    })
  }
}

// 处理全局点击事件（关闭详情面板）
function handleGlobalClick(event) {
  // 如果点击的是详情面板外部，则关闭详情面板
  selectedDrone.value = null
}

// 重置表单
function resetForm() {
  droneForm.name = ''
  droneForm.model = ''
  droneForm.max_flight_time = 30
  droneForm.max_speed = 15
  droneForm.max_altitude = 500
  droneForm.camera_equipped = true
  droneForm.payload_capacity = 2.0
}

// 添加无人机
function handleAddDrone() {
  addFormRef.value?.validate(async (errors) => {
    if (errors) return
    
    submitting.value = true
    
    try {
      await createDrone(droneForm)
      message.success('无人机添加成功')
      showAddDroneModal.value = false
      resetForm()
      await fetchDrones()
    } catch (error) {
      console.error('添加无人机失败:', error)
      message.error('添加无人机失败: ' + (error.message || '未知错误'))
    } finally {
      submitting.value = false
    }
  })
}

// 刷新数据
function refreshData() {
  fetchDrones()
}

// 获取无人机数据
async function fetchDrones() {
  loading.value = true
  
  try {
    const response = await getDrones()
    drones.value = response
  } catch (error) {
    console.error('获取无人机列表失败:', error)
    message.error('获取无人机列表失败')
  } finally {
    loading.value = false
  }
}

// 无人机控制功能
function handleTakeoff() {
  if (!selectedDrone.value) return
  
  message.info(`正在指令${selectedDrone.value.name}起飞`)
}

function handleLand() {
  if (!selectedDrone.value) return
  
  message.info(`正在指令${selectedDrone.value.name}降落`)
}

function handleReturnHome() {
  if (!selectedDrone.value) return
  
  message.info(`正在指令${selectedDrone.value.name}返航`)
}

function handleMoveTo() {
  if (!selectedDrone.value) return
  
  message.info(`正在指令${selectedDrone.value.name}移动到指定位置`)
  // 实际操作也会让地图飞到对应位置
  mapOperations.flyTo({
    lat: targetLatitude.value,
    lng: targetLongitude.value,
    zoom: 16
  })
}

function handleCreateTask() {
  if (!selectedDrone.value) return
  
  router.push({
    path: '/tasks/new',
    query: { drone_id: selectedDrone.value.drone_id }
  })
}

// 挂载时获取数据
onMounted(() => {
  fetchDrones()
  
  // 监听全局无人机选中事件
  window.addEventListener('drone-selected', (event) => {
    const droneId = event.detail
    const drone = drones.value.find(d => d.drone_id === droneId)
    if (drone) {
      selectDrone(drone)
    }
  })
})
</script>

<style scoped>
.floating-card {
  padding: 1rem;
  border-radius: 0.5rem;
  box-shadow: 0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
  backdrop-filter: blur(4px);
}
</style>