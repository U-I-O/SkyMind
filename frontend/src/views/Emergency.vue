<template>
  <div class="h-full pointer-events-none">
    <!-- 使用全局地图，不需要在此页面添加地图组件 -->
    <div class="p-4 h-full">
      <div class="h-full grid grid-cols-12 gap-4">
        <!-- 左侧面板区域 -->
        <div class="col-span-4 flex flex-col gap-4 pointer-events-auto">
          <!-- 标题和操作按钮 -->
          <div class="floating-card bg-white bg-opacity-95">
            <div class="flex justify-between items-center mb-2">
              <h1 class="text-2xl font-bold">应急响应中心</h1>
              
              <!-- 操作按钮 -->
              <div class="flex space-x-3">
                <n-button type="error" @click="activateEmergencyMode">
                  <template #icon>
                    <n-icon><warning-icon /></n-icon>
                  </template>
                  {{ emergencyModeActive ? '取消紧急状态' : '激活紧急状态' }}
                </n-button>
                
                <n-button @click="refreshData">
                  <template #icon>
                    <n-icon><reload-icon /></n-icon>
                  </template>
                  刷新
                </n-button>
              </div>
            </div>
            
            <!-- 状态指示器 -->
            <div v-if="emergencyModeActive" class="bg-red-50 border-l-4 border-red-500 p-4 mb-4 animate-pulse-slow">
              <div class="flex">
                <div class="flex-shrink-0">
                  <n-icon size="24" color="#ef4444"><alert-icon /></n-icon>
                </div>
                <div class="ml-3">
                  <h3 class="text-lg font-bold text-red-700">紧急状态已激活</h3>
                  <div class="text-sm text-red-600">
                    系统处于紧急响应模式，所有应急预案已启动，优先级调整为最高。
                  </div>
                </div>
              </div>
            </div>
            
            <!-- 主要内容 -->
            <div class="grid grid-cols-12 gap-4 flex-1">
              <!-- 左侧应急事件列表 -->
              <div class="col-span-4 flex flex-col">
                <div class="card mb-4">
                  <h2 class="font-bold text-lg mb-3">紧急事件</h2>
                  <n-tabs type="line">
                    <n-tab-pane name="active" tab="活跃事件">
                      <div class="max-h-[300px] overflow-y-auto space-y-3 pb-2">
                        <div v-for="event in activeEvents" :key="event.id" 
                             class="p-3 border-l-4 rounded-md cursor-pointer"
                             :class="[
                               getEventBorderColor(event.level),
                               selectedEvent?.id === event.id ? 'bg-gray-100' : 'hover:bg-gray-50'
                             ]"
                             @click="selectEvent(event)">
                          <div class="flex justify-between items-start">
                            <div>
                              <div class="font-medium">{{ event.title }}</div>
                              <div class="text-xs text-gray-500">{{ formatDateTime(event.detected_at) }}</div>
                            </div>
                            <n-tag :type="getEventTagType(event.level)">{{ event.level }}</n-tag>
                          </div>
                          <div class="mt-1 text-sm text-gray-600">{{ truncateText(event.description, 80) }}</div>
                        </div>
                        
                        <div v-if="activeEvents.length === 0" class="py-12 text-center text-gray-400">
                          暂无活跃紧急事件
                        </div>
                      </div>
                    </n-tab-pane>
                    
                    <n-tab-pane name="resolved" tab="已处理">
                      <div class="max-h-[300px] overflow-y-auto space-y-3 pb-2">
                        <div v-for="event in resolvedEvents" :key="event.id" 
                             class="p-3 border-l-4 border-gray-300 rounded-md hover:bg-gray-50 cursor-pointer"
                             @click="selectEvent(event)">
                          <div class="flex justify-between">
                            <div class="font-medium text-gray-600">{{ event.title }}</div>
                            <div class="text-xs text-gray-500">{{ formatDateTime(event.resolved_at) }}</div>
                          </div>
                          <div class="mt-1 text-sm text-gray-500">{{ truncateText(event.description, 80) }}</div>
                        </div>
                        
                        <div v-if="resolvedEvents.length === 0" class="py-12 text-center text-gray-400">
                          暂无已处理事件
                        </div>
                      </div>
                    </n-tab-pane>
                  </n-tabs>
                </div>
                
                <!-- 应急预案 -->
                <div class="card flex-1">
                  <h2 class="font-bold text-lg mb-3">应急预案</h2>
                  
                  <div v-if="selectedEvent" class="space-y-4">
                    <!-- LLM生成的应急建议 -->
                    <div>
                      <div class="font-medium mb-1">智能建议:</div>
                      <div class="text-sm p-3 bg-gray-50 rounded-md">
                        {{ selectedEvent.emergency_advice || '正在分析事件...' }}
                      </div>
                    </div>
                    
                    <!-- 推荐执行的预案 -->
                    <div>
                      <div class="font-medium mb-1">推荐预案:</div>
                      <n-collapse>
                        <n-collapse-item v-for="plan in selectedEvent.recommended_plans" :key="plan.id" :title="plan.name">
                          <div class="space-y-3">
                            <div class="text-sm">{{ plan.description }}</div>
                            
                            <div>
                              <div class="font-medium text-sm">执行步骤:</div>
                              <div class="space-y-2 mt-1">
                                <div v-for="(step, index) in plan.steps" :key="index" class="flex items-start">
                                  <div class="w-5 h-5 rounded-full bg-primary text-white flex items-center justify-center text-xs mr-2 mt-0.5">
                                    {{ index + 1 }}
                                  </div>
                                  <div class="text-sm">{{ step }}</div>
                                </div>
                              </div>
                            </div>
                            
                            <n-button block type="primary" size="small" @click="executePlan(plan)">
                              执行此预案
                            </n-button>
                          </div>
                        </n-collapse-item>
                      </n-collapse>
                    </div>
                  </div>
                  
                  <div v-else class="py-12 text-center text-gray-400">
                    选择事件查看应急预案
                  </div>
                </div>
              </div>
              
              <!-- 右侧详情区域 -->
              <div class="col-span-8 flex flex-col gap-4">
                <!-- 地图和事件详情 -->
                <div class="card p-0 overflow-hidden flex-1">
                  <div class="relative h-full">
                    <Map3D ref="mapRef" />
                    
                    <!-- 事件详情悬浮窗 -->
                    <div v-if="selectedEvent" class="absolute top-4 right-4 w-80 bg-white/90 backdrop-blur-sm rounded-lg p-4 shadow-lg">
                      <div class="flex justify-between items-start">
                        <div>
                          <h3 class="font-bold text-lg">{{ selectedEvent.title }}</h3>
                          <div class="text-xs text-gray-500">ID: {{ selectedEvent.event_id }}</div>
                        </div>
                        <n-tag :type="getEventTagType(selectedEvent.level)">{{ selectedEvent.level }}</n-tag>
                      </div>
                      
                      <n-divider />
                      
                      <div class="space-y-3 text-sm">
                        <div>
                          <div class="text-gray-500">描述</div>
                          <div>{{ selectedEvent.description }}</div>
                        </div>
                        
                        <div>
                          <div class="text-gray-500">位置</div>
                          <div>{{ selectedEvent.location?.name || '未知位置' }}</div>
                        </div>
                        
                        <div>
                          <div class="text-gray-500">检测时间</div>
                          <div>{{ formatDateTime(selectedEvent.detected_at) }}</div>
                        </div>
                        
                        <div>
                          <div class="text-gray-500">检测来源</div>
                          <div>{{ selectedEvent.detected_by }}</div>
                        </div>
                        
                        <div>
                          <div class="text-gray-500">状态</div>
                          <div>{{ selectedEvent.status }}</div>
                        </div>
                      </div>
                      
                      <div class="flex justify-between mt-4" v-if="selectedEvent.status !== 'resolved'">
                        <n-button @click="assignDrones">分配无人机</n-button>
                        <n-button type="primary" @click="resolveEvent">标记为已处理</n-button>
                      </div>
                    </div>
                  </div>
                </div>
                
                <!-- 应急响应进度 -->
                <div class="card h-64">
                  <h2 class="font-bold text-lg mb-3">响应进度</h2>
                  
                  <div v-if="selectedEvent && selectedEvent.related_tasks.length > 0">
                    <div class="mb-3 grid grid-cols-4 gap-4 text-center">
                      <div class="p-3 bg-gray-50 rounded-lg">
                        <div class="text-lg font-bold">{{ 
                          activeTasks.filter(task => task.status === 'completed').length 
                        }}</div>
                        <div class="text-xs text-gray-500">已完成任务</div>
                      </div>
                      
                      <div class="p-3 bg-gray-50 rounded-lg">
                        <div class="text-lg font-bold">{{ 
                          activeTasks.filter(task => task.status === 'in_progress').length 
                        }}</div>
                        <div class="text-xs text-gray-500">进行中任务</div>
                      </div>
                      
                      <div class="p-3 bg-gray-50 rounded-lg">
                        <div class="text-lg font-bold">{{ 
                          activeTasks.filter(task => task.status === 'pending').length 
                        }}</div>
                        <div class="text-xs text-gray-500">等待中任务</div>
                      </div>
                      
                      <div class="p-3 bg-gray-50 rounded-lg">
                        <div class="text-lg font-bold">{{ assignedDrones.length }}</div>
                        <div class="text-xs text-gray-500">分配的无人机</div>
                      </div>
                    </div>
                    
                    <n-timeline>
                      <n-timeline-item 
                        v-for="task in activeTasks" 
                        :key="task.task_id"
                        :type="getTaskTimelineType(task.status)"
                        :title="task.title"
                      >
                        <template #content>
                          <div class="text-sm">{{ task.description }}</div>
                          <div class="flex justify-between mt-1">
                            <span class="text-xs text-gray-500">{{ formatDateTime(task.created_at) }}</span>
                            <n-tag size="small" :type="getTaskTagType(task.status)">{{ task.status }}</n-tag>
                          </div>
                        </template>
                      </n-timeline-item>
                    </n-timeline>
                  </div>
                  
                  <div v-else class="py-12 text-center text-gray-400">
                    选择事件查看响应进度
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 分配无人机对话框 -->
    <n-modal v-model:show="showDroneModal" preset="card" title="分配无人机" style="width: 500px">
      <div v-if="selectedEvent">
        <div class="text-sm mb-4">为事件 <b>{{ selectedEvent.title }}</b> 分配无人机:</div>
        
        <n-transfer
          v-model:value="selectedDrones"
          :options="availableDrones"
          virtual-scroll
        />
      </div>
      
      <template #footer>
        <div class="flex justify-end space-x-3">
          <n-button @click="showDroneModal = false">取消</n-button>
          <n-button type="primary" @click="confirmAssignDrones">确认分配</n-button>
        </div>
      </template>
    </n-modal>
    
    <!-- 解决事件对话框 -->
    <n-modal v-model:show="showResolveModal" preset="card" title="标记事件为已处理" style="width: 500px">
      <div v-if="selectedEvent">
        <div class="mb-4">确认将事件 <b>{{ selectedEvent.title }}</b> 标记为已处理?</div>
        
        <n-form-item label="处理说明">
          <n-input v-model:value="resolutionNotes" type="textarea" placeholder="输入处理情况说明" />
        </n-form-item>
      </div>
      
      <template #footer>
        <div class="flex justify-end space-x-3">
          <n-button @click="showResolveModal = false">取消</n-button>
          <n-button type="primary" @click="confirmResolve">确认</n-button>
        </div>
      </template>
    </n-modal>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, inject } from 'vue'
import { useMessage } from 'naive-ui'
import { format } from 'date-fns'
import { WarningOutlined as WarningIcon, ReloadOutlined as ReloadIcon, AlertOutlined as AlertIcon } from '@vicons/antd'
// 使用全局地图组件，不需要导入Map3D

const message = useMessage()
// 使用全局地图引用
const mapRef = inject('mapRef')
const flyToLocation = inject('flyToLocation')

// 紧急模式
const emergencyModeActive = ref(false)

// 事件数据
const events = ref([])
const selectedEvent = ref(null)
const activeEvents = computed(() => events.value.filter(e => e.status !== 'resolved').sort((a, b) => {
  // 按级别和时间排序
  if (a.level === 'high' && b.level !== 'high') return -1
  if (a.level !== 'high' && b.level === 'high') return 1
  return new Date(b.detected_at) - new Date(a.detected_at)
}))
const resolvedEvents = computed(() => events.value.filter(e => e.status === 'resolved'))

// 任务数据
const activeTasks = ref([])
const assignedDrones = ref([])

// 分配无人机对话框
const showDroneModal = ref(false)
const selectedDrones = ref([])
const availableDrones = [
  { label: '无人机 #1', value: 'drone-1', disabled: false },
  { label: '无人机 #2', value: 'drone-2', disabled: false },
  { label: '无人机 #3', value: 'drone-3', disabled: false },
  { label: '无人机 #4', value: 'drone-4', disabled: true },
  { label: '无人机 #5', value: 'drone-5', disabled: false }
]

// 解决事件对话框
const showResolveModal = ref(false)
const resolutionNotes = ref('')

// 激活紧急状态
function activateEmergencyMode() {
  emergencyModeActive.value = !emergencyModeActive.value
  
  if (emergencyModeActive.value) {
    message.warning('已激活紧急状态')
  } else {
    message.success('已取消紧急状态')
  }
}

// 刷新数据
function refreshData() {
  message.info('正在刷新数据...')
  fetchEvents()
}

// 选择事件
function selectEvent(event) {
  selectedEvent.value = event
  fetchEventTasks(event.event_id)
  
  // 在地图上定位到事件位置
  if (event.location && flyToLocation) {
    flyToLocation(event.location.position.coordinates)
  }
}

// 分配无人机
function assignDrones() {
  if (!selectedEvent.value) return
  
  selectedDrones.value = selectedEvent.value.assigned_drones || []
  showDroneModal.value = true
}

// 确认分配无人机
function confirmAssignDrones() {
  if (!selectedEvent.value) return
  
  message.success(`成功分配 ${selectedDrones.value.length} 台无人机`)
  showDroneModal.value = false
  
  // 更新本地状态
  selectedEvent.value.assigned_drones = selectedDrones.value
  assignedDrones.value = selectedDrones.value.map(id => {
    const drone = availableDrones.find(d => d.value === id)
    return { id, name: drone.label }
  })
}

// 标记事件为已处理
function resolveEvent() {
  if (!selectedEvent.value) return
  
  resolutionNotes.value = ''
  showResolveModal.value = true
}

// 确认解决事件
function confirmResolve() {
  if (!selectedEvent.value) return
  
  // 更新本地状态
  selectedEvent.value.status = 'resolved'
  selectedEvent.value.resolved_at = new Date()
  selectedEvent.value.resolution_notes = resolutionNotes.value
  
  message.success('事件已标记为已处理')
  showResolveModal.value = false
}

// 执行应急预案
function executePlan(plan) {
  if (!selectedEvent.value) return
  
  message.success(`正在执行预案: ${plan.name}`)
  
  // 通常这里会调用API来执行预案
}

// 获取事件边框颜色
function getEventBorderColor(level) {
  switch (level) {
    case 'high': return 'border-red-500'
    case 'medium': return 'border-yellow-500'
    case 'low': return 'border-blue-500'
    default: return 'border-gray-500'
  }
}

// 获取事件标签类型
function getEventTagType(level) {
  switch (level) {
    case 'high': return 'error'
    case 'medium': return 'warning'
    case 'low': return 'info'
    default: return 'default'
  }
}

// 获取任务时间线类型
function getTaskTimelineType(status) {
  switch (status) {
    case 'completed': return 'success'
    case 'in_progress': return 'info'
    case 'failed': return 'error'
    default: return 'default'
  }
}

// 获取任务标签类型
function getTaskTagType(status) {
  switch (status) {
    case 'completed': return 'success'
    case 'in_progress': return 'info'
    case 'failed': return 'error'
    case 'pending': return 'default'
    default: return 'default'
  }
}

// 格式化日期时间
function formatDateTime(dateStr) {
  if (!dateStr) return '未知'
  return format(new Date(dateStr), 'yyyy-MM-dd HH:mm:ss')
}

// 截断文本
function truncateText(text, length) {
  if (!text) return ''
  return text.length > length ? text.substring(0, length) + '...' : text
}

// 获取事件数据
async function fetchEvents() {
  // 这里应该是API调用，这里模拟数据
  events.value = [
    {
      event_id: 'event-1',
      type: 'emergency',
      level: 'high',
      title: '南区仓库火灾',
      description: '南区仓库发生火灾，烟雾浓度高，需要立即处理。附近有多个易燃物品仓库，存在蔓延风险。',
      location: {
        name: '南区仓库',
        position: {
          type: 'Point',
          coordinates: [116.375, 39.895]
        }
      },
      detected_at: '2025-04-11T09:15:00Z',
      detected_by: '监控智能体',
      status: 'processing',
      video_source: 'south-cam-3',
      image_evidence: ['/images/fire-evidence1.jpg', '/images/fire-evidence2.jpg'],
      assigned_drones: ['drone-1', 'drone-3'],
      related_tasks: ['task-1', 'task-2'],
      emergency_advice: '建议立即派遣消防无人机进行灭火，同时通知附近人员疏散，并对周边区域进行警戒隔离。启动预案E-101处理火灾事件。',
      recommended_plans: [
        {
          id: 'plan-1',
          name: '火灾应急预案E-101',
          description: '适用于中小型火灾的标准处理流程',
          steps: [
            '派遣消防无人机到达现场进行初步灭火',
            '通知人工消防队赶赴现场',
            '启动周边疏散程序',
            '监测空气质量和火势蔓延情况',
            '协调周边交通以确保消防车辆通行'
          ]
        },
        {
          id: 'plan-2',
          name: '危险品处理预案E-202',
          description: '处理火灾中可能涉及的危险化学品',
          steps: [
            '识别火灾区域内的危险品类型',
            '派遣特种无人机采集空气样本',
            '根据危险品类型选择合适的灭火材料',
            '建立隔离区防止有害物质扩散',
            '准备医疗救援设备和人员'
          ]
        }
      ]
    },
    {
      event_id: 'event-2',
      type: 'security',
      level: 'medium',
      title: '北区入口可疑人员',
      description: '北区入口监测到多名可疑人员活动，行为异常，可能存在安全隐患。',
      location: {
        name: '北区入口',
        position: {
          type: 'Point',
          coordinates: [116.383, 39.91]
        }
      },
      detected_at: '2025-04-11T10:30:00Z',
      detected_by: 'YOLO检测',
      status: 'new',
      video_source: 'north-cam-1',
      image_evidence: ['/images/suspect1.jpg'],
      assigned_drones: [],
      related_tasks: [],
      emergency_advice: '建议派遣安防无人机进行近距离监控，同时通知保安人员前往现场核查。保持对区域的持续监控。',
      recommended_plans: [
        {
          id: 'plan-3',
          name: '可疑人员处理预案S-301',
          description: '处理可疑人员的标准流程',
          steps: [
            '派遣高清摄像无人机进行人脸识别',
            '通知保安人员进行现场核查',
            '保持对可疑人员的持续跟踪',
            '如有必要，联系警方支援',
            '记录全程监控证据'
          ]
        }
      ]
    },
    {
      event_id: 'event-3',
      type: 'emergency',
      level: 'low',
      title: '东区积水',
      description: '东区停车场因降雨出现积水情况，可能影响车辆通行。',
      location: {
        name: '东区停车场',
        position: {
          type: 'Point',
          coordinates: [116.39, 39.9]
        }
      },
      detected_at: '2025-04-11T08:45:00Z',
      detected_by: '监控智能体',
      status: 'resolved',
      resolved_at: '2025-04-11T11:20:00Z',
      resolution_notes: '已派遣工作人员处理积水，并疏通排水系统。现场已恢复正常。',
      video_source: 'east-cam-2',
      image_evidence: ['/images/water1.jpg'],
      assigned_drones: ['drone-2'],
      related_tasks: ['task-3']
    }
  ]
  
  // 如果有选中的事件，更新它
  if (selectedEvent.value) {
    const updatedEvent = events.value.find(e => e.event_id === selectedEvent.value.event_id)
    if (updatedEvent) {
      selectedEvent.value = updatedEvent
    }
  }
}

// 获取事件相关任务
async function fetchEventTasks(eventId) {
  // 这里应该是API调用，这里模拟数据
  if (eventId === 'event-1') {
    activeTasks.value = [
      {
        task_id: 'task-1',
        title: '火灾现场勘查',
        description: '派遣无人机进行火灾现场勘查，评估火势范围和严重程度。',
        type: 'emergency',
        priority: 10,
        status: 'completed',
        created_at: '2025-04-11T09:17:00Z',
        created_by: '应急响应智能体'
      },
      {
        task_id: 'task-2',
        title: '火灾扑救',
        description: '使用消防无人机进行初步灭火，控制火势蔓延。',
        type: 'emergency',
        priority: 10,
        status: 'in_progress',
        created_at: '2025-04-11T09:20:00Z',
        created_by: '应急响应智能体'
      }
    ]
    assignedDrones.value = [
      { id: 'drone-1', name: '无人机 #1' },
      { id: 'drone-3', name: '无人机 #3' }
    ]
  } else if (eventId === 'event-3') {
    activeTasks.value = [
      {
        task_id: 'task-3',
        title: '积水情况勘查',
        description: '派遣无人机勘查积水范围和深度，评估影响程度。',
        type: 'inspection',
        priority: 5,
        status: 'completed',
        created_at: '2025-04-11T08:50:00Z',
        created_by: '监控智能体'
      }
    ]
    assignedDrones.value = [
      { id: 'drone-2', name: '无人机 #2' }
    ]
  } else {
    activeTasks.value = []
    assignedDrones.value = []
  }
}

// 组件挂载时获取数据
onMounted(() => {
  fetchEvents()
})
</script>