<template>
  <div class="h-full pointer-events-none">
    <!-- 漂浮面板容器 -->
    <div class="p-4 h-full">
      <div class="h-full">
        <!-- 事件列表面板 - 占据左半部分 -->
        <div class="w-1/2 pointer-events-auto">
          <!-- 标题、筛选和统计面板 -->
          <div class="floating-card bg-white bg-opacity-95 mb-4">
            <div class="flex justify-between items-center mb-4">
              <h1 class="text-2xl font-bold">事件中心</h1>
              <div>
                <n-button 
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
            
            <!-- 事件类型筛选 -->
            <div class="mb-4">
              <n-select 
                v-model:value="eventTypeFilter" 
                :options="eventTypeOptions"
                placeholder="筛选事件类型"
                style="width: 100%"
              />
            </div>
            
            <!-- 事件统计 -->
            <div class="grid grid-cols-4 gap-3">
              <div class="p-2 bg-gray-50 rounded-lg text-center">
                <div class="text-xl font-bold">{{ events.length }}</div>
                <div class="text-xs text-gray-500">总事件数</div>
              </div>
              <div class="p-2 bg-gray-50 rounded-lg text-center">
                <div class="text-xl font-bold">{{ unhandledEvents.length }}</div>
                <div class="text-xs text-gray-500">未处理事件</div>
              </div>
              <div class="p-2 bg-gray-50 rounded-lg text-center">
                <div class="text-xl font-bold">{{ highPriorityEvents.length }}</div>
                <div class="text-xs text-gray-500">高优先级事件</div>
              </div>
              <div class="p-2 bg-gray-50 rounded-lg text-center">
                <div class="text-xl font-bold">{{ todayEvents.length }}</div>
                <div class="text-xs text-gray-500">今日事件</div>
              </div>
            </div>
          </div>
          
          <!-- 事件列表面板 -->
          <div class="floating-card bg-white bg-opacity-95 flex-1 flex flex-col h-96">
            <h3 class="text-lg font-medium mb-3">事件列表</h3>
            
            <n-data-table
              :columns="columns"
              :data="filteredEvents"
              :loading="loading"
              :pagination="pagination"
              :row-key="row => row.id"
              @update:page="handlePageChange"
              class="flex-1 overflow-auto"
              :row-props="(row) => ({ class: 'compact-row' })"
              max-height="calc(100vh - 350px)"
            />
          </div>
        </div>
      </div>
    </div>
    
    <!-- 分配任务对话框 -->
    <n-modal
      v-model:show="showTaskModal"
      title="分配任务"
      preset="card"
      style="width: 500px"
    >
      <n-form
        v-if="selectedEvent"
        ref="taskFormRef"
        :model="taskForm"
        label-placement="left"
        label-width="auto"
      >
        <n-form-item label="事件">
          <n-input disabled :value="selectedEvent.title" />
        </n-form-item>
        <n-form-item label="任务名称" path="name">
          <n-input v-model:value="taskForm.name" placeholder="输入任务名称" />
        </n-form-item>
        <n-form-item label="任务类型" path="type">
          <n-select
            v-model:value="taskForm.type"
            :options="[
              { label: '安防巡检', value: 'surveillance' },
              { label: '应急响应', value: 'emergency' }
            ]"
            placeholder="选择任务类型"
          />
        </n-form-item>
        <n-form-item label="分配无人机" path="droneId">
          <n-select
            v-model:value="taskForm.droneId"
            :options="droneOptions"
            placeholder="选择无人机"
          />
        </n-form-item>
        <n-form-item label="任务优先级" path="priority">
          <n-slider
            v-model:value="taskForm.priority"
            :step="1"
            :marks="{1:'低', 5:'中', 10:'高'}"
            :min="1"
            :max="10"
          />
        </n-form-item>
        <n-form-item label="描述" path="description">
          <n-input v-model:value="taskForm.description" type="textarea" />
        </n-form-item>
      </n-form>
      
      <template #footer>
        <div class="flex justify-end space-x-3">
          <n-button @click="showTaskModal = false">取消</n-button>
          <n-button type="primary" @click="submitTask">创建任务</n-button>
        </div>
      </template>
    </n-modal>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, inject } from 'vue'
import { format } from 'date-fns'
import { 
  NButton, 
  NTag, 
  NDataTable,
  NSelect,
  NModal,
  NForm,
  NFormItem,
  NInput,
  NSlider,
  NIcon,
  useNotification,
  useMessage
} from 'naive-ui'
import { 
  ReloadOutlined,
} from '@vicons/antd'

// 组件状态
const loading = ref(false)
const events = ref([])
const selectedEvent = ref(null)
const pagination = ref({
  page: 1,
  pageSize: 10,
  showSizePicker: true,
  pageSizes: [10, 20, 30, 50],
  onChange: (page) => {
    pagination.value.page = page
  },
  onUpdatePageSize: (pageSize) => {
    pagination.value.pageSize = pageSize
    pagination.value.page = 1
  }
})

// 任务表单
const taskFormRef = ref(null)
const showTaskModal = ref(false)
const taskForm = ref({
  name: '',
  type: '',
  droneId: '',
  priority: 5,
  description: ''
})

// 筛选状态
const eventTypeFilter = ref(null)

// UI组件
const message = useMessage()
const notification = useNotification()

// 注入全局地图引用
const mapRef = inject('mapRef')
const flyToLocation = inject('flyToLocation')
const setMapEvents = inject('setMapEvents')

// 表格列定义
const columns = [
  {
    title: 'ID',
    key: 'id',
    width: 60
  },
  {
    title: '标题',
    key: 'title',
    width: 140
  },
  {
    title: '类型',
    key: 'type',
    width: 80,
    render(row) {
      return h(
        NTag,
        {
          type: getEventTypeTag(row.type),
          size: 'small'
        },
        { default: () => row.type }
      )
    }
  },
  {
    title: '优先级',
    key: 'priority',
    width: 70,
    render(row) {
      return h(
        NTag,
        {
          type: getPriorityTag(row.priority),
          size: 'small'
        },
        { default: () => row.priority }
      )
    }
  },
  {
    title: '状态',
    key: 'status',
    width: 70,
    render(row) {
      return h(
        NTag,
        {
          type: getStatusTag(row.status),
          size: 'small'
        },
        { default: () => row.status }
      )
    }
  },
  {
    title: '操作',
    key: 'actions',
    width: 120,
    render(row) {
      return h('div', [
        h(
          NButton,
          {
            size: 'small',
            onClick: () => showEventOnMap(row)
          },
          { default: () => '查看' }
        ),
        ' ',
        h(
          NButton,
          {
            size: 'small',
            type: 'primary',
            disabled: row.status === 'resolved',
            onClick: () => assignTask(row)
          },
          { default: () => '分配任务' }
        )
      ])
    }
  }
]

// 选项数据
const eventTypeOptions = [
  { label: '全部类型', value: null },
  { label: '故障', value: 'fault' },
  { label: '安全', value: 'security' },
  { label: '告警', value: 'alert' },
  { label: '任务', value: 'task' }
]

const droneOptions = [
  { label: '无人机 #1', value: 'drone-1' },
  { label: '无人机 #2', value: 'drone-2' },
  { label: '无人机 #3', value: 'drone-3' }
]

// 计算属性
const filteredEvents = computed(() => {
  if (!eventTypeFilter.value) return events.value
  return events.value.filter(event => event.type === eventTypeFilter.value)
})

const unhandledEvents = computed(() => 
  events.value.filter(event => event.status !== 'resolved')
)

const highPriorityEvents = computed(() => 
  events.value.filter(event => event.priority === 'high')
)

const todayEvents = computed(() => {
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  return events.value.filter(event => new Date(event.reportTime) >= today)
})

// 方法
const refreshData = async () => {
  loading.value = true
  try {
    // 这里应该是API调用，现在用模拟数据
    await mockFetchEvents()
    
    // 更新地图事件
    if (setMapEvents) {
      setMapEvents(events.value)
    }
    
    message.success('数据已刷新')
  } catch (error) {
    console.error('刷新数据出错:', error)
    notification.error({
      title: '错误',
      content: '刷新数据失败',
      duration: 3000
    })
  } finally {
    loading.value = false
  }
}

// 在地图上显示事件并弹出信息窗口
const showEventOnMap = (event) => {
  selectedEvent.value = event
  
  // 先飞行到事件位置
  if (flyToLocation && event.location && event.location.coordinates) {
    flyToLocation({
      lng: event.location.coordinates[0],
      lat: event.location.coordinates[1],
      zoom: 16,
      pitch: 45
    })
    
    // 然后显示事件信息
    setTimeout(() => {
      if (mapRef.value) {
        mapRef.value.showEventInfo(event)
      }
    }, 500)
  }
}

const assignTask = (event) => {
  selectedEvent.value = event
  showTaskModal.value = true
  
  // 预填任务表单
  taskForm.value = {
    name: `处理-${event.title}`,
    type: '',
    droneId: '',
    priority: event.priority === 'high' ? 8 : event.priority === 'medium' ? 5 : 2,
    description: `处理事件: ${event.description}`
  }
}

const submitTask = async () => {
  if (!selectedEvent.value) return
  
  try {
    // 这里应该是API调用
    await mockCreateTask(taskForm.value)
    
    notification.success({
      title: '成功',
      content: '任务已创建',
      duration: 3000
    })
    
    showTaskModal.value = false
    refreshData()
  } catch (error) {
    console.error('创建任务出错:', error)
    notification.error({
      title: '错误',
      content: '创建任务失败',
      duration: 3000
    })
  }
}

const resolveEvent = async (event) => {
  try {
    // 这里应该是API调用
    await mockResolveEvent(event.id)
    
    // 更新本地状态
    const index = events.value.findIndex(e => e.id === event.id)
    if (index !== -1) {
      events.value[index].status = 'resolved'
      selectedEvent.value = events.value[index]
    }
    
    notification.success({
      title: '成功',
      content: '事件已标记为已解决',
      duration: 3000
    })
  } catch (error) {
    console.error('解决事件出错:', error)
    notification.error({
      title: '错误',
      content: '解决事件失败',
      duration: 3000
    })
  }
}

const handlePageChange = (page) => {
  pagination.value.page = page
}

// 工具函数
const getEventTypeTag = (type) => {
  const types = {
    'fault': 'error',
    'security': 'warning',
    'alert': 'info',
    'task': 'success'
  }
  return types[type] || 'default'
}

const getPriorityTag = (priority) => {
  if (priority === 'high') return 'error'
  if (priority === 'medium') return 'warning'
  return 'info'
}

const getStatusTag = (status) => {
  if (status === 'new') return 'info'
  if (status === 'processing') return 'warning'
  if (status === 'resolved') return 'success'
  return 'default'
}

const formatTime = (timeStr) => {
  try {
    return format(new Date(timeStr), 'yyyy-MM-dd HH:mm:ss')
  } catch (e) {
    return timeStr || '未知'
  }
}

// 模拟API调用
const mockFetchEvents = () => {
  return new Promise((resolve) => {
    setTimeout(() => {
      events.value = [
        {
          id: 'evt-001',
          title: '南区摄像头检测到可疑人员',
          type: 'security',
          priority: 'high',
          status: 'new',
          reportTime: '2025-04-15T13:45:30Z',
          location: {
            name: '南区门口',
            coordinates: [114.367, 30.531, 0]
          },
          description: '南区门口摄像头检测到多名可疑人员徘徊，行为异常，请派无人机前往查看。'
        },
        {
          id: 'evt-002',
          title: '北区无人机故障',
          type: 'fault',
          priority: 'medium',
          status: 'processing',
          reportTime: '2025-04-15T12:30:00Z',
          location: {
            name: '北区巡逻点',
            coordinates: [114.373, 30.543, 0]
          },
          description: '北区巡逻无人机报告电池故障，需要更换电池或维修。'
        },
        {
          id: 'evt-003',
          title: '东区温度过高告警',
          type: 'alert',
          priority: 'medium',
          status: 'new',
          reportTime: '2025-04-15T14:10:15Z',
          location: {
            name: '东区电力设施',
            coordinates: [114.382, 30.538, 0]
          },
          description: '东区电力设施温度传感器报告温度异常，请派遣无人机前往检查是否有火灾隐患。'
        },
        {
          id: 'evt-004',
          title: '仓库巡检任务完成',
          type: 'task',
          priority: 'low',
          status: 'resolved',
          reportTime: '2025-04-15T11:20:00Z',
          location: {
            name: '主仓库',
            coordinates: [114.365, 30.535, 0]
          },
          description: '主仓库巡检任务已完成，所有设施正常，无异常情况。'
        },
        {
          id: 'evt-005',
          title: '西区围栏破损',
          type: 'security',
          priority: 'high',
          status: 'processing',
          reportTime: '2025-04-15T10:15:00Z',
          location: {
            name: '西区围栏',
            coordinates: [114.358, 30.541, 0]
          },
          description: '西区围栏发现破损，可能有入侵风险，已派遣安保人员前往。'
        }
      ]
      resolve()
    }, 500)
  })
}

const mockCreateTask = (task) => {
  return new Promise((resolve) => {
    console.log('创建任务:', task)
    setTimeout(resolve, 500)
  })
}

const mockResolveEvent = (eventId) => {
  return new Promise((resolve) => {
    console.log('解决事件:', eventId)
    setTimeout(resolve, 500)
  })
}

// 生命周期钩子
onMounted(() => {
  refreshData()
})

// 导入h函数用于渲染函数
import { h } from 'vue'
</script> 

<style scoped>
.floating-card {
  padding: 1rem;
  border-radius: 0.5rem;
  box-shadow: 0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
  backdrop-filter: blur(4px);
  z-index: 100; 
}

/* 更紧凑的表格行 */
:deep(.compact-row) td {
  padding: 6px 8px !important;
}

:deep(.n-tag) {
  padding: 0 6px !important;
}
</style>