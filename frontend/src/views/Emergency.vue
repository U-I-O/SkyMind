<template>
  <div class="h-full pointer-events-none">
    <!-- 使用全局地图，不需要在此页面添加地图组件 -->
    <div class="p-4 h-full">
      <div class="h-full grid grid-cols-12 gap-4">
        <!-- 左侧面板区域 -->
        <div class="col-span-3 flex flex-col gap-4 pointer-events-auto">
          <!-- 标题和操作按钮 -->
          <div class="floating-card dark-theme-override">
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
            <div v-if="emergencyModeActive" class="bg-red-900 bg-opacity-30 border-l-4 border-red-500 p-4 mb-4 animate-pulse-slow">
              <div class="flex">
                <div class="flex-shrink-0">
                  <n-icon size="24" color="#ef4444"><alert-icon /></n-icon>
                </div>
                <div class="ml-3">
                  <h3 class="text-lg font-bold text-red-400">紧急状态已激活</h3>
                  <div class="text-sm text-red-300">
                    系统处于紧急响应模式，所有应急预案已启动，优先级调整为最高。
                  </div>
                </div>
              </div>
            </div>
          </div>
          
          <!-- 应急事件列表 -->
          <div class="floating-card dark-theme-override flex-1 overflow-hidden flex flex-col">
            <h2 class="font-bold text-lg mb-3">应急事件列表</h2>
            
            <n-tabs type="line" class="flex-1 flex flex-col">
              <n-tab-pane name="drone" tab="无人机巡逻发现" class="flex-1 flex flex-col">
                <div class="space-y-3 overflow-y-auto custom-scrollbar flex-1">
                  <div v-for="event in droneEvents" :key="event.id" 
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
                    <div class="mt-1 text-xs">
                      <n-tag size="small" :type="getStatusTagType(event.status)">{{ getStatusText(event.status) }}</n-tag>
                    </div>
                  </div>
                  
                  <div v-if="droneEvents.length === 0" class="py-12 text-center text-gray-400">
                    暂无无人机巡逻发现的事件
                  </div>
                </div>
              </n-tab-pane>
              
              <n-tab-pane name="external" tab="其他平台同步" class="flex-1 flex flex-col">
                <div class="space-y-3 overflow-y-auto custom-scrollbar flex-1">
                  <div v-for="event in externalEvents" :key="event.id" 
                       class="p-3 border-l-4 rounded-md cursor-pointer"
                       :class="[
                         getEventBorderColor(event.level),
                         selectedEvent?.id === event.id ? 'bg-gray-100' : 'hover:bg-gray-50'
                       ]"
                       @click="selectEvent(event)">
                    <div class="flex justify-between items-start">
                      <div>
                        <div class="font-medium">{{ event.title }}</div>
                        <div class="text-xs text-gray-500">{{ formatDateTime(event.received_at) }}</div>
                      </div>
                      <n-tag :type="getEventTagType(event.level)">{{ event.level }}</n-tag>
                    </div>
                    <div class="mt-1 text-sm text-gray-600">{{ truncateText(event.description, 80) }}</div>
                    <div class="flex justify-between mt-1">
                      <div class="text-xs text-gray-500">来源: {{ event.source }}</div>
                      <n-tag size="small" :type="getStatusTagType(event.status)">{{ getStatusText(event.status) }}</n-tag>
                    </div>
                  </div>
                  
                  <div v-if="externalEvents.length === 0" class="py-12 text-center text-gray-400">
                    暂无外部平台同步的事件
                  </div>
                </div>
              </n-tab-pane>
              
              <n-tab-pane name="resolved" tab="已处理事件" class="flex-1 flex flex-col">
                <div class="space-y-3 overflow-y-auto custom-scrollbar flex-1">
                  <div v-for="event in resolvedEvents" :key="event.id" 
                       class="p-3 border-l-4 border-gray-300 rounded-md hover:bg-gray-50 cursor-pointer"
                       @click="selectEvent(event)">
                    <div class="flex justify-between">
                      <div class="font-medium text-gray-600">{{ event.title }}</div>
                      <div class="text-xs text-gray-500">{{ formatDateTime(event.resolved_at) }}</div>
                    </div>
                    <div class="mt-1 text-sm text-gray-500">{{ truncateText(event.description, 80) }}</div>
                    <div class="flex justify-between mt-1">
                      <div class="text-xs text-gray-500">{{ event.source ? '来源: ' + event.source : '无人机发现' }}</div>
                      <n-tag size="small" type="success">已处理</n-tag>
                    </div>
                  </div>
                  
                  <div v-if="resolvedEvents.length === 0" class="py-12 text-center text-gray-400">
                    暂无已处理事件
                  </div>
                </div>
              </n-tab-pane>
            </n-tabs>
          </div>
        </div>
        
        <!-- 中间区域（地图区域） -->
        <div class="col-span-6">
          <!-- 地图由全局组件提供，这里不需要额外添加 -->
        </div>
        
        <!-- 右侧面板区域 -->
        <div class="col-span-3 flex flex-col gap-4 pointer-events-auto">
          <!-- 事件详情和处理流程 -->
          <div class="floating-card dark-theme-override flex-1 flex flex-col" v-if="selectedEvent">
            <div class="flex justify-between items-start mb-3">
              <h2 class="font-bold text-lg">事件详情</h2>
              <n-tag :type="getEventTagType(selectedEvent.level)">{{ selectedEvent.level }}</n-tag>
            </div>
            
            <div class="space-y-3 overflow-y-auto mb-4">
              <div>
                <div class="text-gray-500 text-sm">事件标题</div>
                <div class="font-medium">{{ selectedEvent.title }}</div>
              </div>
              
              <div>
                <div class="text-gray-500 text-sm">事件描述</div>
                <div>{{ selectedEvent.description }}</div>
              </div>
              
              <div>
                <div class="text-gray-500 text-sm">位置</div>
                <div>{{ selectedEvent.location?.name || '未知位置' }}</div>
              </div>
              
              <div>
                <div class="text-gray-500 text-sm">{{ selectedEvent.source ? '接收时间' : '检测时间' }}</div>
                <div>{{ formatDateTime(selectedEvent.source ? selectedEvent.received_at : selectedEvent.detected_at) }}</div>
              </div>
              
              <div v-if="selectedEvent.source">
                <div class="text-gray-500 text-sm">事件来源</div>
                <div>{{ selectedEvent.source }}</div>
              </div>
              
              <div v-else>
                <div class="text-gray-500 text-sm">检测来源</div>
                <div>{{ selectedEvent.detected_by }}</div>
              </div>
            </div>
            
            <n-divider />
            
            <!-- 无人机主动上报事件的处理流程 -->
            <div v-if="!selectedEvent.source && selectedEvent.status !== 'resolved'" class="flex-1 flex flex-col">
              <h3 class="font-medium">事件处理流程</h3>
              
              <n-steps :current="droneEventCurrentStep" vertical class="mt-3 flex-1">
                <n-step title="事件分析" description="自动生成相关部门通知表单">
                  <template #icon>
                    <n-icon><file-search-outlined /></n-icon>
                  </template>
                </n-step>
                
                <n-step title="人工审查" description="确认或修改通知表单">
                  <template #icon>
                    <n-icon><audit-outlined /></n-icon>
                  </template>
                </n-step>
                
                <n-step title="事件发送" description="同步事件到相关部门">
                  <template #icon>
                    <n-icon><send-outlined /></n-icon>
                  </template>
                </n-step>
              </n-steps>
              
              <!-- 表单区域 -->
              <div class="mt-3">
                <!-- 事件分析阶段 -->
                <template v-if="droneEventCurrentStep === 0">
                  <div class="bg-gray-50 p-3 rounded-md mb-3">
                    <div class="text-sm font-medium mb-2">自动生成通知表单</div>
                    <n-spin :show="isGeneratingForm">
                      <div v-if="notificationForm" class="space-y-2">
                        <div class="text-sm">
                          <div class="text-gray-500">通知部门</div>
                          <div>{{ notificationForm.departments.join(', ') }}</div>
                        </div>
                        <div class="text-sm">
                          <div class="text-gray-500">紧急程度</div>
                          <div>{{ notificationForm.urgency }}</div>
                        </div>
                        <div class="text-sm">
                          <div class="text-gray-500">事件概述</div>
                          <div>{{ notificationForm.summary }}</div>
                        </div>
                        <div class="text-sm">
                          <div class="text-gray-500">建议措施</div>
                          <div>{{ notificationForm.recommendations }}</div>
                        </div>
                      </div>
                    </n-spin>
                  </div>
                  
                  <div class="flex justify-end">
                    <n-button type="primary" @click="moveToNextStep">下一步: 人工审查</n-button>
                  </div>
                </template>
                
                <!-- 人工审查阶段 -->
                <template v-if="droneEventCurrentStep === 1">
                  <n-form ref="formRef" :model="notificationForm" label-placement="left" label-width="80" class="mb-3">
                    <n-form-item label="通知部门" path="departments">
                      <n-select v-model:value="notificationForm.departments" multiple :options="departmentOptions" />
                    </n-form-item>
                    
                    <n-form-item label="紧急程度" path="urgency">
                      <n-select v-model:value="notificationForm.urgency" :options="urgencyOptions" />
                    </n-form-item>
                    
                    <n-form-item label="事件概述" path="summary">
                      <n-input v-model:value="notificationForm.summary" type="textarea" />
                    </n-form-item>
                    
                    <n-form-item label="建议措施" path="recommendations">
                      <n-input v-model:value="notificationForm.recommendations" type="textarea" />
                    </n-form-item>
                  </n-form>
                  
                  <div class="flex justify-between">
                    <n-button @click="droneEventCurrentStep = 0">上一步</n-button>
                    <n-button type="primary" @click="moveToNextStep">确认并发送通知</n-button>
                  </div>
                </template>
                
                <!-- 事件发送阶段 -->
                <template v-if="droneEventCurrentStep === 2">
                  <div class="bg-blue-50 p-3 rounded-md mb-3">
                    <div class="flex items-start">
                      <n-icon size="24" color="#2080f0" class="mr-2"><info-circle-outlined /></n-icon>
                      <div>
                        <div class="font-medium">事件已发送</div>
                        <div class="text-sm mt-1">已成功将通知发送至以下部门:</div>
                        <div class="text-sm mt-1">{{ notificationForm.departments.join(', ') }}</div>
                      </div>
                    </div>
                  </div>
                  
                  <div class="flex justify-end">
                    <n-button type="primary" @click="resolveEvent">标记为已处理</n-button>
                  </div>
                </template>
              </div>
            </div>
            
            <!-- 外部同步事件的处理流程 -->
            <div v-else-if="selectedEvent.source && selectedEvent.status !== 'resolved'" class="flex-1 flex flex-col">
              <h3 class="font-medium">无人机处理方案</h3>
              
              <n-steps :current="externalEventCurrentStep" vertical class="mt-3 flex-1">
                <n-step title="智能方案生成" description="自动生成无人机处理方案">
                  <template #icon>
                    <n-icon><robot-outlined /></n-icon>
                  </template>
                </n-step>
                
                <n-step title="人工审查" description="确认或修改处理方案">
                  <template #icon>
                    <n-icon><audit-outlined /></n-icon>
                  </template>
                </n-step>
                
                <n-step title="执行任务" description="派遣无人机执行任务">
                  <template #icon>
                    <n-icon><rocket-outlined /></n-icon>
                  </template>
                </n-step>
              </n-steps>
              
              <!-- 方案处理区域 -->
              <div class="mt-3">
                <!-- 智能方案生成阶段 -->
                <template v-if="externalEventCurrentStep === 0">
                  <div class="bg-gray-50 p-3 rounded-md mb-3">
                    <div class="text-sm font-medium mb-2">自动生成无人机方案</div>
                    <n-spin :show="isGeneratingPlan">
                      <div v-if="dronePlan" class="space-y-2">
                        <div class="text-sm">
                          <div class="text-gray-500">方案名称</div>
                          <div>{{ dronePlan.name }}</div>
                        </div>
                        <div class="text-sm">
                          <div class="text-gray-500">所需无人机</div>
                          <div>{{ dronePlan.requiredDrones.join(', ') }}</div>
                        </div>
                        <div class="text-sm">
                          <div class="text-gray-500">任务描述</div>
                          <div>{{ dronePlan.description }}</div>
                        </div>
                        <div class="text-sm">
                          <div class="text-gray-500">预计完成时间</div>
                          <div>{{ formatDateTime(dronePlan.estimatedCompletionTime) }}</div>
                        </div>
                      </div>
                    </n-spin>
                  </div>
                  
                  <div class="flex justify-end">
                    <n-button type="primary" @click="moveToNextStep">下一步: 人工审查</n-button>
                  </div>
                </template>
                
                <!-- 人工审查阶段 -->
                <template v-if="externalEventCurrentStep === 1">
                  <n-form ref="planFormRef" :model="dronePlan" label-placement="left" label-width="80" class="mb-3">
                    <n-form-item label="方案名称" path="name">
                      <n-input v-model:value="dronePlan.name" />
                    </n-form-item>
                    
                    <n-form-item label="所需无人机" path="requiredDrones">
                      <n-select v-model:value="dronePlan.requiredDrones" multiple :options="droneOptions" />
                    </n-form-item>
                    
                    <n-form-item label="任务描述" path="description">
                      <n-input v-model:value="dronePlan.description" type="textarea" />
                    </n-form-item>
                    
                    <n-form-item label="预计完成" path="estimatedCompletionTime">
                      <n-date-picker v-model:value="dronePlan.estimatedCompletionTime" type="datetime" clearable />
                    </n-form-item>
                  </n-form>
                  
                  <div class="flex justify-between">
                    <n-button @click="externalEventCurrentStep = 0">上一步</n-button>
                    <n-button type="primary" @click="moveToNextStep">确认方案</n-button>
                  </div>
                </template>
                
                <!-- 执行任务阶段 -->
                <template v-if="externalEventCurrentStep === 2">
                  <div class="bg-green-50 p-3 rounded-md mb-3">
                    <div class="flex">
                      <n-icon size="24" color="#18a058" class="mr-2"><check-circle-outlined /></n-icon>
                      <div>
                        <div class="font-medium">任务已派遣</div>
                        <div class="text-sm mt-1">无人机任务已派遣，当前执行进度:</div>
                        <n-progress type="line" :percentage="taskProgress" :indicator-placement="'inside'" class="mt-2" />
                        <div class="text-xs text-gray-500 mt-1">预计完成时间: {{ formatDateTime(dronePlan.estimatedCompletionTime) }}</div>
                      </div>
                    </div>
                  </div>
                  
                  <div v-if="selectedEvent.droneTaskDetails" class="mt-3">
                    <div class="font-medium mb-2">无人机任务详情</div>
                    <n-collapse>
                      <n-collapse-item v-for="(drone, index) in selectedEvent.droneTaskDetails" :key="index" :title="drone.name">
                        <div class="space-y-2">
                          <div class="flex justify-between text-sm">
                            <div>状态:</div>
                            <n-tag :type="getTaskStatusTagType(drone.status)">{{ getTaskStatusText(drone.status) }}</n-tag>
                          </div>
                          <div class="text-sm">
                            <div>当前动作: {{ drone.currentAction }}</div>
                          </div>
                          <div class="text-sm">
                            <div>位置: {{ drone.location }}</div>
                          </div>
                          <div class="text-sm">
                            <div>电量: {{ drone.batteryLevel }}%</div>
                            <n-progress type="line" :percentage="drone.batteryLevel" :color="getBatteryColor(drone.batteryLevel)" :show-indicator="false" />
                          </div>
                        </div>
                      </n-collapse-item>
                    </n-collapse>
                  </div>
                  
                  <div class="flex justify-end mt-3">
                    <n-button type="primary" @click="resolveEvent">标记为已处理</n-button>
                  </div>
                </template>
              </div>
            </div>
            
            <!-- 已处理事件 -->
            <div v-else-if="selectedEvent.status === 'resolved'" class="flex-1">
              <div class="bg-green-50 p-3 rounded-md">
                <div class="flex">
                  <n-icon size="24" color="#18a058" class="mr-2"><check-circle-outlined /></n-icon>
                  <div>
                    <div class="font-medium">事件已处理</div>
                    <div class="text-sm mt-1">处理完成时间: {{ formatDateTime(selectedEvent.resolved_at) }}</div>
                    <div class="text-sm mt-1" v-if="selectedEvent.resolution_notes">处理说明: {{ selectedEvent.resolution_notes }}</div>
                  </div>
                </div>
              </div>
              
              <div v-if="selectedEvent.resolutionDetails" class="mt-4">
                <div class="font-medium mb-2">处理详情</div>
                <div class="text-sm space-y-2">
                  <div v-for="(detail, index) in selectedEvent.resolutionDetails" :key="index" class="bg-gray-50 p-2 rounded">
                    {{ detail }}
                  </div>
                </div>
              </div>
            </div>
            
            <div v-else class="flex-1 flex items-center justify-center text-gray-400">
              选择事件查看详细信息
            </div>
          </div>
          
          <!-- 未选择事件时的提示 -->
          <div v-else class="floating-card dark-theme-override flex-1 flex items-center justify-center text-gray-400">
            请从左侧列表选择一个事件
          </div>
        </div>
      </div>
    </div>
    
    <!-- 解决事件对话框 -->
    <n-modal v-model:show="showResolveModal" preset="card" title="标记事件为已处理" style="width: 500px" class="dark-theme-override">
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
import { 
  WarningOutlined as WarningIcon, 
  ReloadOutlined as ReloadIcon, 
  AlertOutlined as AlertIcon,
  FileSearchOutlined,
  AuditOutlined,
  SendOutlined,
  RobotOutlined,
  RocketOutlined,
  InfoCircleOutlined,
  CheckCircleOutlined
} from '@vicons/antd'

const message = useMessage()
// 使用全局地图引用
const mapRef = inject('mapRef')
const flyToLocation = inject('flyToLocation')

// 紧急模式
const emergencyModeActive = ref(false)

// 事件数据
const droneEvents = ref([])
const externalEvents = ref([])
const resolvedEvents = ref([])
const selectedEvent = ref(null)

// 无人机上报事件处理步骤
const droneEventCurrentStep = ref(0)
const notificationForm = ref(null)
const isGeneratingForm = ref(false)

// 外部事件处理步骤
const externalEventCurrentStep = ref(0)
const dronePlan = ref(null)
const isGeneratingPlan = ref(false)
const taskProgress = ref(0)

// 解决事件对话框
const showResolveModal = ref(false)
const resolutionNotes = ref('')

// 部门选项
const departmentOptions = [
  { label: '消防部门', value: '消防部门' },
  { label: '安防部门', value: '安防部门' },
  { label: '医疗救援', value: '医疗救援' },
  { label: '交通管理', value: '交通管理' },
  { label: '环境监测', value: '环境监测' }
]

// 紧急程度选项
const urgencyOptions = [
  { label: '特急 - 需立即处理', value: '特急' },
  { label: '紧急 - 1小时内处理', value: '紧急' },
  { label: '一般 - 24小时内处理', value: '一般' },
  { label: '低 - 可延后处理', value: '低' }
]

// 无人机选项
const droneOptions = [
  { label: '消防无人机 #1', value: '消防无人机 #1' },
  { label: '消防无人机 #2', value: '消防无人机 #2' },
  { label: '高清摄像无人机 #1', value: '高清摄像无人机 #1' },
  { label: '巡逻无人机 #1', value: '巡逻无人机 #1' },
  { label: '巡逻无人机 #2', value: '巡逻无人机 #2' },
  { label: '运输无人机 #1', value: '运输无人机 #1' }
]

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
  
  // 根据事件类型设置初始步骤
  if (event.source) {
    // 外部事件
    if (event.status === 'new') {
      externalEventCurrentStep.value = 0
      generateDronePlan()
    } else if (event.status === 'processing') {
      externalEventCurrentStep.value = 2
    } else {
      externalEventCurrentStep.value = 2
    }
  } else {
    // 无人机上报事件
    if (event.status === 'new') {
      droneEventCurrentStep.value = 0
      generateNotificationForm()
    } else if (event.status === 'processing') {
      droneEventCurrentStep.value = 1
    } else {
      droneEventCurrentStep.value = 2
    }
  }
  
  // 在地图上定位到事件位置
  if (event.location && event.location.position && flyToLocation) {
    flyToLocation(event.location.position.coordinates)
  }
}

// 移动到下一步
function moveToNextStep() {
  if (selectedEvent.value.source) {
    // 外部事件流程
    if (externalEventCurrentStep.value < 2) {
      externalEventCurrentStep.value++
      
      // 如果进入了执行任务阶段，更新事件状态
      if (externalEventCurrentStep.value === 2) {
        selectedEvent.value.status = 'processing'
        
        // 启动任务进度模拟
        simulateTaskProgress()
      }
    }
  } else {
    // 无人机上报事件流程
    if (droneEventCurrentStep.value < 2) {
      droneEventCurrentStep.value++
      
      // 如果进入了事件发送阶段，更新事件状态
      if (droneEventCurrentStep.value === 2) {
        selectedEvent.value.status = 'processing'
      }
    }
  }
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
  
  // 更新事件列表
  if (selectedEvent.value.source) {
    externalEvents.value = externalEvents.value.filter(e => e.id !== selectedEvent.value.id)
  } else {
    droneEvents.value = droneEvents.value.filter(e => e.id !== selectedEvent.value.id)
  }
  resolvedEvents.value.push(selectedEvent.value)
  
  message.success('事件已标记为已处理')
  showResolveModal.value = false
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

// 获取状态标签类型
function getStatusTagType(status) {
  switch (status) {
    case 'new': return 'default'
    case 'processing': return 'info'
    case 'resolved': return 'success'
    default: return 'default'
  }
}

// 获取任务状态标签类型
function getTaskStatusTagType(status) {
  switch (status) {
    case 'waiting': return 'default'
    case 'flying': return 'info'
    case 'working': return 'warning'
    case 'returning': return 'success'
    case 'completed': return 'success'
    case 'error': return 'error'
    default: return 'default'
  }
}

// 获取状态文本
function getStatusText(status) {
  switch (status) {
    case 'new': return '新建'
    case 'processing': return '处理中'
    case 'resolved': return '已处理'
    default: return status
  }
}

// 获取任务状态文本
function getTaskStatusText(status) {
  switch (status) {
    case 'waiting': return '等待中'
    case 'flying': return '飞行中'
    case 'working': return '工作中'
    case 'returning': return '返航中'
    case 'completed': return '已完成'
    case 'error': return '故障'
    default: return status
  }
}

// 获取电池颜色
function getBatteryColor(level) {
  if (level <= 20) return '#ff4d4f'
  if (level <= 50) return '#faad14'
  return '#52c41a'
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

// 生成通知表单
function generateNotificationForm() {
  if (!selectedEvent.value) return
  
  isGeneratingForm.value = true
  
  // 模拟生成通知表单的过程
  setTimeout(() => {
    // 根据事件类型和级别生成建议的通知部门
    let departments = []
    if (selectedEvent.value.type === 'fire') {
      departments.push('消防部门')
    }
    if (['security', 'suspicious'].includes(selectedEvent.value.type)) {
      departments.push('安防部门')
    }
    if (['accident', 'medical'].includes(selectedEvent.value.type)) {
      departments.push('医疗救援')
    }
    if (['traffic', 'roadblock'].includes(selectedEvent.value.type)) {
      departments.push('交通管理')
    }
    if (['pollution', 'weather'].includes(selectedEvent.value.type)) {
      departments.push('环境监测')
    }
    
    // 根据事件级别设置紧急程度
    let urgency = '一般'
    if (selectedEvent.value.level === 'high') {
      urgency = '特急'
    } else if (selectedEvent.value.level === 'medium') {
      urgency = '紧急'
    } else if (selectedEvent.value.level === 'low') {
      urgency = '一般'
    }
    
    // 生成表单
    notificationForm.value = {
      departments: departments,
      urgency: urgency,
      summary: selectedEvent.value.description,
      recommendations: selectedEvent.value.emergency_advice || '建议立即安排相关部门对事件进行处理，无人机将继续监测事件进展。'
    }
    
    isGeneratingForm.value = false
  }, 1500)
}

// 生成无人机处理方案
function generateDronePlan() {
  if (!selectedEvent.value) return
  
  isGeneratingPlan.value = true
  
  // 模拟生成无人机方案的过程
  setTimeout(() => {
    // 根据事件类型选择合适的无人机
    let requiredDrones = []
    if (['fire', 'explosion'].includes(selectedEvent.value.type)) {
      requiredDrones.push('消防无人机 #1', '高清摄像无人机 #1')
    } else if (['security', 'suspicious'].includes(selectedEvent.value.type)) {
      requiredDrones.push('高清摄像无人机 #1', '巡逻无人机 #1')
    } else if (['accident', 'medical'].includes(selectedEvent.value.type)) {
      requiredDrones.push('运输无人机 #1', '高清摄像无人机 #1')
    } else if (['traffic', 'roadblock'].includes(selectedEvent.value.type)) {
      requiredDrones.push('巡逻无人机 #1', '巡逻无人机 #2')
    } else {
      requiredDrones.push('高清摄像无人机 #1')
    }
    
    // 生成预计完成时间（当前时间 + 1-2小时）
    const now = new Date()
    const estimatedTime = new Date(now.getTime() + (60 + Math.random() * 60) * 60 * 1000)
    
    // 生成方案
    dronePlan.value = {
      name: `${selectedEvent.value.title} 无人机应急处理`,
      requiredDrones: requiredDrones,
      description: `针对${selectedEvent.value.title}事件，使用${requiredDrones.join('、')}进行现场勘查和监控，收集事件相关信息并实时传回处理中心。`,
      estimatedCompletionTime: estimatedTime
    }
    
    isGeneratingPlan.value = false
  }, 1500)
}

// 模拟任务进度
function simulateTaskProgress() {
  taskProgress.value = 0
  const interval = setInterval(() => {
    taskProgress.value += Math.random() * 5
    if (taskProgress.value >= 100) {
      taskProgress.value = 100
      clearInterval(interval)
      
      // 更新无人机任务详情
      if (selectedEvent.value) {
        selectedEvent.value.droneTaskDetails = dronePlan.value.requiredDrones.map(drone => {
          return {
            name: drone,
            status: 'completed',
            currentAction: '任务完成，已返回基地',
            location: '基地',
            batteryLevel: 70 + Math.floor(Math.random() * 30)
          }
        })
      }
    }
    
    // 更新无人机任务详情
    if (selectedEvent.value && !selectedEvent.value.droneTaskDetails) {
      selectedEvent.value.droneTaskDetails = dronePlan.value.requiredDrones.map(drone => {
        let status = 'flying'
        let currentAction = '前往事件现场'
        
        if (taskProgress.value > 30) {
          status = 'working'
          currentAction = '在现场进行任务处理'
        }
        
        if (taskProgress.value > 80) {
          status = 'returning'
          currentAction = '任务完成，正在返回基地'
        }
        
        return {
          name: drone,
          status: status,
          currentAction: currentAction,
          location: selectedEvent.value.location?.name || '事件现场',
          batteryLevel: 100 - Math.floor(taskProgress.value / 3)
        }
      })
    }
  }, 1000)
}

// 获取事件数据
async function fetchEvents() {
  // 模拟无人机发现的事件数据
  droneEvents.value = [
    {
      id: 'drone-event-1',
      type: 'fire',
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
      detected_by: '无人机巡逻系统',
      status: 'new',
      evidence: ['/images/fire-evidence1.jpg', '/images/fire-evidence2.jpg'],
      emergency_advice: '建议立即派遣消防车和救援人员进行灭火，同时通知附近人员疏散，并对周边区域进行警戒隔离。'
    },
    {
      id: 'drone-event-2',
      type: 'traffic',
      level: 'medium',
      title: '主干道交通拥堵',
      description: '东部主干道检测到交通拥堵情况，拥堵指数达到75%，可能影响应急车辆通行。',
      location: {
        name: '东部主干道',
        position: {
          type: 'Point',
          coordinates: [116.39, 39.9]
        }
      },
      detected_at: '2025-04-11T10:30:00Z',
      detected_by: '交通监控无人机',
      status: 'processing',
      evidence: ['/images/traffic1.jpg'],
      emergency_advice: '建议通知交通管理部门调整信号灯配时，并派出交警疏导交通。'
    }
  ]
  
  // 模拟外部平台同步的事件数据
  externalEvents.value = [
    {
      id: 'external-event-1',
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
      received_at: '2025-04-11T10:30:00Z',
      source: '安防监控中心',
      status: 'new',
      emergency_advice: '建议派遣安防人员进行现场核查。'
    },
    {
      id: 'external-event-2',
      type: 'medical',
      level: 'high',
      title: '工业园区安全事故',
      description: '工业园区报告发生安全事故，有人员受伤，需要紧急医疗支援。',
      location: {
        name: '工业园区A3厂房',
        position: {
          type: 'Point',
          coordinates: [116.38, 39.905]
        }
      },
      received_at: '2025-04-11T11:15:00Z',
      source: '安全生产监督部门',
      status: 'processing',
      emergency_advice: '建议紧急派遣医疗救援无人机运送医疗用品，并协助定位受伤人员。',
      droneTaskDetails: [
        {
          name: '运输无人机 #1',
          status: 'working',
          currentAction: '运送医疗物资',
          location: '工业园区A3厂房',
          batteryLevel: 75
        },
        {
          name: '高清摄像无人机 #1',
          status: 'working',
          currentAction: '现场勘查并协助定位受伤人员',
          location: '工业园区A3厂房',
          batteryLevel: 82
        }
      ]
    }
  ]
  
  // 模拟已处理的事件数据
  resolvedEvents.value = [
    {
      id: 'resolved-event-1',
      type: 'weather',
      level: 'low',
      title: '东区暴雨积水',
      description: '东区停车场因暴雨出现积水情况，影响车辆通行。',
      location: {
        name: '东区停车场',
        position: {
          type: 'Point',
          coordinates: [116.39, 39.9]
        }
      },
      detected_at: '2025-04-11T08:45:00Z',
      detected_by: '无人机巡逻系统',
      status: 'resolved',
      resolved_at: '2025-04-11T11:20:00Z',
      resolution_notes: '已派遣工作人员处理积水，并疏通排水系统。现场已恢复正常。',
      evidence: ['/images/water1.jpg'],
      resolutionDetails: [
        '09:00 - 无人机巡逻发现积水情况',
        '09:15 - 通知设施管理部门',
        '10:30 - 工作人员到达现场疏通排水系统',
        '11:20 - 积水已清理完毕，恢复正常通行'
      ]
    },
    {
      id: 'resolved-event-2',
      type: 'suspicious',
      level: 'medium',
      title: '西区围墙异常活动',
      description: '西区围墙附近检测到异常活动，可能存在翻越围墙行为。',
      location: {
        name: '西区围墙',
        position: {
          type: 'Point',
          coordinates: [116.37, 39.89]
        }
      },
      received_at: '2025-04-11T09:30:00Z',
      source: '安防监控中心',
      status: 'resolved',
      resolved_at: '2025-04-11T10:45:00Z',
      resolution_notes: '安保人员确认是维修工作人员在进行围墙检修，属正常活动。',
      resolutionDetails: [
        '09:30 - 接收安防监控中心异常活动报告',
        '09:35 - 派遣高清摄像无人机进行现场勘查',
        '09:50 - 安保人员到达现场核实情况',
        '10:45 - 确认是维修人员正常作业，解除警报'
      ]
    }
  ]
  
  // 如果有选中的事件，更新它
  if (selectedEvent.value) {
    // 查找更新后的事件
    let updatedEvent = [
      ...droneEvents.value,
      ...externalEvents.value,
      ...resolvedEvents.value
    ].find(e => e.id === selectedEvent.value.id)
    
    if (updatedEvent) {
      selectedEvent.value = updatedEvent
    }
  }
}

// 组件挂载时获取数据
onMounted(() => {
  fetchEvents()
})
</script>

<style scoped>
/* 只保留Emergency.vue特有的样式 */
.animate-pulse-slow {
  animation: pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.7;
  }
}
</style>