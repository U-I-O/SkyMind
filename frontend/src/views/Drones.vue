<template>
  <div class="h-full flex flex-col p-4">
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
    
    <!-- 无人机状态统计 -->
    <div class="grid grid-cols-5 gap-4 mb-6">
      <div class="card flex items-center px-6">
        <div class="w-12 h-12 rounded-full flex items-center justify-center bg-blue-100 text-blue-500 mr-4">
          <n-icon size="24"><drone-icon /></n-icon>
        </div>
        <div>
          <div class="text-sm text-gray-500">总无人机</div>
          <div class="text-2xl font-bold">{{ droneStats.total }}</div>
        </div>
      </div>
      
      <div class="card flex items-center px-6">
        <div class="w-12 h-12 rounded-full flex items-center justify-center bg-green-100 text-green-500 mr-4">
          <n-icon size="24"><check-icon /></n-icon>
        </div>
        <div>
          <div class="text-sm text-gray-500">在线</div>
          <div class="text-2xl font-bold">{{ droneStats.online }}</div>
        </div>
      </div>
      
      <div class="card flex items-center px-6">
        <div class="w-12 h-12 rounded-full flex items-center justify-center bg-yellow-100 text-yellow-500 mr-4">
          <n-icon size="24"><flight-icon /></n-icon>
        </div>
        <div>
          <div class="text-sm text-gray-500">飞行中</div>
          <div class="text-2xl font-bold">{{ droneStats.flying }}</div>
        </div>
      </div>
      
      <div class="card flex items-center px-6">
        <div class="w-12 h-12 rounded-full flex items-center justify-center bg-purple-100 text-purple-500 mr-4">
          <n-icon size="24"><thunderbolt-icon /></n-icon>
        </div>
        <div>
          <div class="text-sm text-gray-500">充电中</div>
          <div class="text-2xl font-bold">{{ droneStats.charging }}</div>
        </div>
      </div>
      
      <div class="card flex items-center px-6">
        <div class="w-12 h-12 rounded-full flex items-center justify-center bg-red-100 text-red-500 mr-4">
          <n-icon size="24"><warning-icon /></n-icon>
        </div>
        <div>
          <div class="text-sm text-gray-500">离线</div>
          <div class="text-2xl font-bold">{{ droneStats.offline }}</div>
        </div>
      </div>
    </div>
    
    <!-- 筛选条件 -->
    <div class="flex justify-between items-center mb-4 card p-4">
      <div class="flex space-x-4">
        <n-input-group>
          <n-input v-model:value="searchQuery" placeholder="搜索无人机名称或ID"></n-input>
          <n-button>
            <template #icon>
              <n-icon><search-icon /></n-icon>
            </template>
          </n-button>
        </n-input-group>
        
        <n-select
          v-model:value="statusFilter"
          :options="statusOptions"
          placeholder="状态筛选"
          clearable
          style="width: 150px"
        />
        
        <n-select
          v-model:value="modelFilter"
          :options="modelOptions"
          placeholder="型号筛选"
          clearable
          style="width: 150px"
        />
      </div>
      
      <div>
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
    
    <!-- 无人机数据表格 -->
    <div v-if="viewMode === 'list'" class="flex-1 overflow-auto">
      <n-data-table
        :columns="columns"
        :data="filteredDrones"
        :pagination="pagination"
        :row-key="row => row.drone_id"
        :loading="loading"
      />
    </div>
    
    <!-- 无人机卡片网格视图 -->
    <div v-else-if="viewMode === 'grid'" class="flex-1 overflow-auto">
      <div class="grid grid-cols-4 gap-4">
        <div v-for="drone in filteredDrones" :key="drone.drone_id" class="card">
          <div class="flex justify-between items-start">
            <div>
              <h3 class="font-bold text-lg">{{ drone.name }}</h3>
              <div class="text-xs text-gray-500 mt-1">ID: {{ drone.drone_id }}</div>
            </div>
            <n-tag :type="getStatusType(drone.status)">{{ drone.status }}</n-tag>
          </div>
          
          <div class="mt-4 text-center">
            <img :src="getDroneImage(drone)" alt="Drone" class="h-32 mx-auto mb-3 filter drop-shadow-md">
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
            <n-button size="small" @click="viewDroneDetails(drone)">详情</n-button>
            <n-button size="small" type="primary" @click="controlDrone(drone)">控制</n-button>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 地图视图 -->
    <div v-else-if="viewMode === 'map'" class="flex-1">
      <Map3D />
    </div>
    
    <!-- 添加无人机对话框 -->
    <n-modal v-model:show="showAddDroneModal" preset="card" title="添加无人机" style="width: 500px" @close="resetForm">
      <n-form ref="addFormRef" :model="droneForm" :rules="rules" label-placement="left" label-width="auto">
        <n-form-item label="名称" path="name">
          <n-input v-model:value="droneForm.name" placeholder="输入无人机名称" />
        </n-form-item>
        
        <n-form-item label="型号" path="model">
          <n-input v-model:value="droneForm.model" placeholder="输入无人机型号" />
        </n-form-item>
        
        <n-form-item label="最大飞行时间(分钟)" path="max_flight_time">
          <n-input-number v-model:value="droneForm.max_flight_time" :min="1" :max="500" />
        </n-form-item>
        
        <n-form-item label="最大速度(m/s)" path="max_speed">
          <n-input-number v-model:value="droneForm.max_speed" :min="1" :max="100" />
        </n-form-item>
        
        <n-form-item label="最大高度(米)" path="max_altitude">
          <n-input-number v-model:value="droneForm.max_altitude" :min="1" :max="5000" />
        </n-form-item>
        
        <n-form-item label="搭载相机" path="camera_equipped">
          <n-switch v-model:value="droneForm.camera_equipped" />
        </n-form-item>
        
        <n-form-item label="载荷能力(千克)" path="payload_capacity">
          <n-input-number v-model:value="droneForm.payload_capacity" :min="0" :precision="2" />
        </n-form-item>
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
      <div v-if="selectedDrone">
        <div class="grid grid-cols-2 gap-4 mb-6">
          <div class="text-center p-3 bg-gray-50 rounded-lg">
            <div class="text-xl font-bold">{{ selectedDrone.battery_level }}%</div>
            <div class="text-sm text-gray-500">电量</div>
          </div>
          
          <div class="text-center p-3 bg-gray-50 rounded-lg">
            <div class="text-xl font-bold">{{ selectedDrone.status }}</div>
            <div class="text-sm text-gray-500">状态</div>
          </div>
          
          <div class="text-center p-3 bg-gray-50 rounded-lg">
            <div class="text-xl font-bold">{{ formatCoordinate(selectedDrone.current_location?.coordinates[0] || 0) }}</div>
            <div class="text-sm text-gray-500">经度</div>
          </div>
          
          <div class="text-center p-3 bg-gray-50 rounded-lg">
            <div class="text-xl font-bold">{{ formatCoordinate(selectedDrone.current_location?.coordinates[1] || 0) }}</div>
            <div class="text-sm text-gray-500">纬度</div>
          </div>
        </div>
        
        <n-divider />
        
        <div class="grid grid-cols-2 gap-4">
          <n-button :disabled="selectedDrone.status !== 'idle'" @click="handleTakeoff">起飞</n-button>
          <n-button :disabled="selectedDrone.status !== 'flying'" @click="handleLand">降落</n-button>
          <n-button :disabled="selectedDrone.status !== 'flying'" @click="handleReturnHome">返航</n-button>
          <n-button @click="handleCreateTask">创建任务</n-button>
        </div>
        
        <n-divider />
        
        <div>
          <div class="mb-2 font-medium">移动到指定位置</div>
          <div class="flex space-x-3 mb-3">
            <n-input-number v-model:value="targetLongitude" placeholder="经度" :precision="6" />
            <n-input-number v-model:value="targetLatitude" placeholder="纬度" :precision="6" />
            <n-input-number v-model:value="targetAltitude" placeholder="高度(米)" />
          </div>
          <n-button block :disabled="selectedDrone.status !== 'flying'" @click="handleMoveTo">移动到位置</n-button>
        </div>
      </div>
    </n-modal>
  </div>
</template>

<script setup>
import { ref, computed, reactive, onMounted } from 'vue'
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
  ThunderboltOutlined as ThunderboltIcon
} from '@vicons/antd'
import { getDrones, createDrone, controlDrone } from '../api/drone'
import Map3D from '../components/map/Map3D.vue'
import { h } from 'vue'

const router = useRouter()
const message = useMessage()

// 状态变量
const loading = ref(false)
const submitting = ref(false)
const showAddDroneModal = ref(false)
const showControlModal = ref(false)
const searchQuery = ref('')
const statusFilter = ref(null)
const modelFilter = ref(null)
const viewMode = ref('list')
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

// 获取无人机图片
function getDroneImage(drone) {
  // 根据无人机型号返回图片
  return '/images/drone-default.png'
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
})
</script> 