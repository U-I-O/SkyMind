<template>
    <div class="h-full flex flex-col p-4">
      <div class="flex justify-between items-center mb-4">
        <h1 class="text-2xl font-bold">物流调度中心</h1>
        
        <!-- 操作按钮 -->
        <div class="flex space-x-3">
          <n-button type="primary" @click="showDeliveryModal = true">
            <template #icon>
              <n-icon><plus-icon /></n-icon>
            </template>
            创建配送任务
          </n-button>
          
          <n-button @click="refreshData">
            <template #icon>
              <n-icon><reload-icon /></n-icon>
            </template>
            刷新
          </n-button>
        </div>
      </div>
      
      <!-- 统计卡片 -->
      <div class="grid grid-cols-4 gap-4 mb-4">
        <div class="card flex items-center">
          <div class="w-12 h-12 rounded-full flex items-center justify-center bg-primary-light text-white mr-4">
            <n-icon size="24"><box-icon /></n-icon>
          </div>
          <div>
            <div class="text-xs text-gray-500">今日配送</div>
            <div class="text-2xl font-bold">{{ stats.deliveriesToday }}</div>
          </div>
        </div>
        
        <div class="card flex items-center">
          <div class="w-12 h-12 rounded-full flex items-center justify-center bg-green-500 text-white mr-4">
            <n-icon size="24"><check-icon /></n-icon>
          </div>
          <div>
            <div class="text-xs text-gray-500">完成率</div>
            <div class="text-2xl font-bold">{{ stats.completionRate }}%</div>
          </div>
        </div>
        
        <div class="card flex items-center">
          <div class="w-12 h-12 rounded-full flex items-center justify-center bg-blue-500 text-white mr-4">
            <n-icon size="24"><clock-icon /></n-icon>
          </div>
          <div>
            <div class="text-xs text-gray-500">平均配送时间</div>
            <div class="text-2xl font-bold">{{ stats.avgDeliveryTime }}分钟</div>
          </div>
        </div>
        
        <div class="card flex items-center">
          <div class="w-12 h-12 rounded-full flex items-center justify-center bg-purple-500 text-white mr-4">
            <n-icon size="24"><drone-icon /></n-icon>
          </div>
          <div>
            <div class="text-xs text-gray-500">可用无人机</div>
            <div class="text-2xl font-bold">{{ stats.availableDrones }}/{{ stats.totalDrones }}</div>
          </div>
        </div>
      </div>
      
      <!-- 主要内容区域 -->
      <div class="flex-1 grid grid-cols-12 gap-4">
        <!-- 左侧配送任务列表 -->
        <div class="col-span-4 card overflow-y-auto">
          <h2 class="font-bold text-lg mb-3">配送任务</h2>
          
          <n-tabs type="line">
            <n-tab-pane name="active" tab="进行中">
              <div class="space-y-3">
                <div v-for="task in activeTasks" :key="task.id" 
                     class="p-3 border border-gray-200 rounded-md hover:bg-gray-50 cursor-pointer"
                     :class="selectedTask?.id === task.id ? 'bg-blue-50 border-blue-200' : ''"
                     @click="selectTask(task)">
                  <div class="flex justify-between">
                    <div class="font-medium">{{ task.title }}</div>
                    <n-tag :type="getStatusType(task.status)">{{ task.status }}</n-tag>
                  </div>
                  <div class="mt-1 text-xs text-gray-500">
                    <div>从: {{ task.from }}</div>
                    <div>到: {{ task.to }}</div>
                  </div>
                  <div class="flex justify-between mt-2 text-xs">
                    <div class="text-gray-500">预计: {{ formatTime(task.eta) }}</div>
                    <div>优先级: {{ task.priority }}</div>
                  </div>
                </div>
                
                <div v-if="activeTasks.length === 0" class="py-10 text-center text-gray-400">
                  没有进行中的配送任务
                </div>
              </div>
            </n-tab-pane>
            
            <n-tab-pane name="completed" tab="已完成">
              <div class="space-y-3">
                <div v-for="task in completedTasks" :key="task.id" 
                     class="p-3 border border-gray-200 rounded-md hover:bg-gray-50 cursor-pointer"
                     @click="selectTask(task)">
                  <div class="flex justify-between">
                    <div class="font-medium">{{ task.title }}</div>
                    <n-tag type="success">已完成</n-tag>
                  </div>
                  <div class="mt-1 text-xs text-gray-500">
                    <div>从: {{ task.from }}</div>
                    <div>到: {{ task.to }}</div>
                  </div>
                  <div class="flex justify-between mt-2 text-xs">
                    <div class="text-gray-500">完成时间: {{ formatDateTime(task.completedAt) }}</div>
                  </div>
                </div>
                
                <div v-if="completedTasks.length === 0" class="py-10 text-center text-gray-400">
                  没有已完成的配送任务
                </div>
              </div>
            </n-tab-pane>
          </n-tabs>
        </div>
        
        <!-- 右侧地图和详情 -->
        <div class="col-span-8 flex flex-col gap-4">
          <!-- 地图区域 -->
          <div class="card p-0 flex-1 overflow-hidden">
            <div class="h-full relative">
              <Map3D ref="mapRef" />
              
              <!-- 任务详情卡片 -->
              <div v-if="selectedTask" class="absolute top-4 right-4 w-80 bg-white/90 backdrop-blur-sm p-4 rounded-lg shadow-lg">
                <div class="flex justify-between items-start">
                  <h3 class="font-bold text-lg">{{ selectedTask.title }}</h3>
                  <n-tag :type="getStatusType(selectedTask.status)">{{ selectedTask.status }}</n-tag>
                </div>
                
                <n-divider />
                
                <div class="space-y-3 text-sm">
                  <div>
                    <div class="text-gray-500">物品类型</div>
                    <div>{{ selectedTask.packageType }}</div>
                  </div>
                  
                  <div>
                    <div class="text-gray-500">重量</div>
                    <div>{{ selectedTask.weight }} kg</div>
                  </div>
                  
                  <div>
                    <div class="text-gray-500">起点</div>
                    <div>{{ selectedTask.from }}</div>
                  </div>
                  
                  <div>
                    <div class="text-gray-500">终点</div>
                    <div>{{ selectedTask.to }}</div>
                  </div>
                  
                  <div>
                    <div class="text-gray-500">状态</div>
                    <div class="flex items-center">
                      <n-progress 
                        :percentage="getProgressPercentage(selectedTask)" 
                        :processing="selectedTask.status === 'in_progress'"
                        :show-indicator="false"
                        class="flex-1"
                      />
                      <span class="ml-2">{{ getProgressPercentage(selectedTask) }}%</span>
                    </div>
                  </div>
                  
                  <div>
                    <div class="text-gray-500">分配无人机</div>
                    <div>{{ selectedTask.drone ? selectedTask.drone : '未分配' }}</div>
                  </div>
                </div>
                
                <div class="mt-4 flex justify-between">
                  <n-button size="small" @click="trackDelivery" :disabled="selectedTask.status !== 'in_progress'">
                    追踪配送
                  </n-button>
                  <n-button type="primary" size="small" @click="controlDelivery" :disabled="selectedTask.status === 'completed'">
                    {{ selectedTask.status === 'pending' ? '开始配送' : '控制' }}
                  </n-button>
                </div>
              </div>
            </div>
          </div>
          
          <!-- 物流状态 -->
          <div class="card h-56">
            <h2 class="font-bold text-lg mb-3">物流状态</h2>
            
            <div v-if="selectedTask">
              <n-steps :current="getCurrentStep(selectedTask)" :status="getStepStatus(selectedTask)">
                <n-step title="订单创建" description="已创建配送任务" />
                <n-step title="无人机分配" description="已分配无人机" />
                <n-step title="取件中" description="无人机前往取件点" />
                <n-step title="配送中" description="无人机正在配送" />
                <n-step title="已送达" description="物品已送达目的地" />
              </n-steps>
              
              <div class="mt-4 text-xs text-gray-500">
                <div>创建时间: {{ formatDateTime(selectedTask.createdAt) }}</div>
                <div>预计送达: {{ formatDateTime(selectedTask.eta) }}</div>
                <div v-if="selectedTask.status === 'completed'">实际送达: {{ formatDateTime(selectedTask.completedAt) }}</div>
              </div>
            </div>
            
            <div v-else class="py-10 text-center text-gray-400">
              选择任务查看物流状态
            </div>
          </div>
        </div>
      </div>
      
      <!-- 创建配送任务对话框 -->
      <n-modal v-model:show="showDeliveryModal" preset="card" title="创建配送任务" style="width: 500px">
        <n-form :model="deliveryForm" label-placement="left" label-width="auto">
          <n-form-item label="任务名称">
            <n-input v-model:value="deliveryForm.title" placeholder="输入任务名称" />
          </n-form-item>
          
          <n-form-item label="物品类型">
            <n-select v-model:value="deliveryForm.packageType" :options="packageTypeOptions" />
          </n-form-item>
          
          <n-form-item label="重量 (kg)">
            <n-input-number v-model:value="deliveryForm.weight" :min="0.1" :max="5" :precision="2" />
          </n-form-item>
          
          <n-form-item label="起点">
            <n-select v-model:value="deliveryForm.from" :options="locationOptions" />
          </n-form-item>
          
          <n-form-item label="终点">
            <n-select v-model:value="deliveryForm.to" :options="locationOptions" />
          </n-form-item>
          
          <n-form-item label="优先级">
            <n-slider v-model:value="deliveryForm.priority" :step="1" :marks="{1:'低', 5:'中', 10:'高'}" :min="1" :max="10" />
          </n-form-item>
          
          <n-form-item label="指定无人机">
            <n-select v-model:value="deliveryForm.drone" :options="droneOptions" placeholder="自动分配" clearable />
          </n-form-item>
        </n-form>
        
        <template #footer>
          <div class="flex justify-end space-x-3">
            <n-button @click="showDeliveryModal = false">取消</n-button>
            <n-button type="primary" @click="createDelivery" :loading="submitting">创建</n-button>
          </div>
        </template>
      </n-modal>
    </div>
  </template>
  
  <script setup>
  import { ref, computed, reactive, onMounted } from 'vue'
  import { useMessage } from 'naive-ui'
  import { format } from 'date-fns'
  import { 
    PlusOutlined as PlusIcon, 
    ReloadOutlined as ReloadIcon,
    CheckCircleOutlined as CheckIcon,
    ClockCircleOutlined as ClockIcon,
    RobotOutlined as DroneIcon,
    GiftOutlined as BoxIcon
  } from '@vicons/antd'
  import Map3D from '../components/map/Map3D_WG.vue'
  
  const message = useMessage()
  const mapRef = ref(null)
  
  // 统计数据
  const stats = reactive({
    deliveriesToday: 12,
    completionRate: 92,
    avgDeliveryTime: 18,
    availableDrones: 5,
    totalDrones: 8
  })
  
  // 任务列表
  const tasks = ref([])
  const selectedTask = ref(null)
  const activeTasks = computed(() => tasks.value.filter(t => t.status !== 'completed'))
  const completedTasks = computed(() => tasks.value.filter(t => t.status === 'completed'))
  
  // 创建配送表单
  const showDeliveryModal = ref(false)
  const submitting = ref(false)
  const deliveryForm = reactive({
    title: '',
    packageType: 'regular',
    weight: 1.0,
    from: '',
    to: '',
    priority: 5,
    drone: null
  })
  
  // 选项
  const packageTypeOptions = [
    { label: '普通包裹', value: 'regular' },
    { label: '紧急物资', value: 'urgent' },
    { label: '医疗物品', value: 'medical' },
    { label: '易碎物品', value: 'fragile' }
  ]
  
  const locationOptions = [
    { label: '北区仓库', value: 'north-warehouse' },
    { label: '南区配送中心', value: 'south-center' },
    { label: '东区医院', value: 'east-hospital' },
    { label: '西区园区', value: 'west-campus' },
    { label: '中心商业区', value: 'central-market' }
  ]
  
  const droneOptions = [
    { label: '无人机 #1', value: 'Drone-001' },
    { label: '无人机 #2', value: 'Drone-002' },
    { label: '无人机 #3', value: 'Drone-003' },
    { label: '无人机 #4', value: 'Drone-004', disabled: true },
    { label: '无人机 #5', value: 'Drone-005' }
  ]
  
  // 刷新数据
  function refreshData() {
    message.info('正在刷新数据...')
    fetchTasks()
  }
  
  // 选择任务
  function selectTask(task) {
    selectedTask.value = task
    
    // 在地图上显示任务路径
    if (mapRef.value) {
      // 如果地图组件有这个方法
      // mapRef.value.showPath(task.path)
    }
  }
  
  // 追踪配送
  function trackDelivery() {
    if (!selectedTask.value) return
    message.info(`正在追踪配送: ${selectedTask.value.title}`)
  }
  
  // 控制配送
  function controlDelivery() {
    if (!selectedTask.value) return
    
    if (selectedTask.value.status === 'pending') {
      message.success(`已开始配送: ${selectedTask.value.title}`)
      selectedTask.value.status = 'in_progress'
    } else {
      message.info(`正在控制配送: ${selectedTask.value.title}`)
    }
  }
  
  // 创建配送任务
  function createDelivery() {
    if (deliveryForm.from === deliveryForm.to) {
      message.error('起点和终点不能相同')
      return
    }
    
    submitting.value = true
    
    setTimeout(() => {
      // 模拟API调用
      const newTask = {
        id: `task-${Date.now()}`,
        title: deliveryForm.title || `${deliveryForm.packageType} 配送任务`,
        packageType: deliveryForm.packageType,
        weight: deliveryForm.weight,
        from: locationOptions.find(l => l.value === deliveryForm.from)?.label || deliveryForm.from,
        to: locationOptions.find(l => l.value === deliveryForm.to)?.label || deliveryForm.to,
        priority: deliveryForm.priority,
        status: 'pending',
        createdAt: new Date(),
        eta: new Date(Date.now() + 30 * 60 * 1000), // 30分钟后
        drone: deliveryForm.drone ? droneOptions.find(d => d.value === deliveryForm.drone)?.label : null,
        path: [] // 实际应用中应该有路径数据
      }
      
      tasks.value.unshift(newTask)
      selectedTask.value = newTask
      
      message.success('配送任务创建成功')
      showDeliveryModal.value = false
      submitting.value = false
      
      // 重置表单
      deliveryForm.title = ''
      deliveryForm.packageType = 'regular'
      deliveryForm.weight = 1.0
      deliveryForm.from = ''
      deliveryForm.to = ''
      deliveryForm.priority = 5
      deliveryForm.drone = null
    }, 1000)
  }
  
  // 获取状态类型
  function getStatusType(status) {
    switch (status) {
      case 'completed': return 'success'
      case 'in_progress': return 'info'
      case 'pending': return 'warning'
      default: return 'default'
    }
  }
  
  // 获取进度百分比
  function getProgressPercentage(task) {
    if (task.status === 'completed') return 100
    if (task.status === 'pending') return 0
    
    // 根据创建时间和预计到达时间计算进度
    const now = Date.now()
    const createdTime = new Date(task.createdAt).getTime()
    const etaTime = new Date(task.eta).getTime()
    
    if (now >= etaTime) return 99
    
    const totalDuration = etaTime - createdTime
    const elapsedDuration = now - createdTime
    return Math.round((elapsedDuration / totalDuration) * 100)
  }
  
  // 获取当前步骤
  function getCurrentStep(task) {
    if (task.status === 'completed') return 4
    if (task.status === 'in_progress') {
      // 根据进度确定步骤
      const progress = getProgressPercentage(task)
      if (progress < 30) return 2
      if (progress < 70) return 3
      return 3
    }
    if (task.drone) return 1
    return 0
  }
  
  // 获取步骤状态
  function getStepStatus(task) {
    if (task.status === 'completed') return 'finish'
    return 'process'
  }
  
  // 格式化时间
  function formatTime(date) {
    return format(new Date(date), 'HH:mm:ss')
  }
  
  // 格式化日期时间
  function formatDateTime(date) {
    return format(new Date(date), 'MM-dd HH:mm')
  }
  
  // 获取任务数据
  function fetchTasks() {
    // 模拟API调用
    tasks.value = [
      {
        id: 'task-1',
        title: '医疗物资紧急配送',
        packageType: 'medical',
        weight: 2.5,
        from: '南区配送中心',
        to: '东区医院',
        priority: 10,
        status: 'in_progress',
        createdAt: new Date(Date.now() - 15 * 60 * 1000), // 15分钟前
        eta: new Date(Date.now() + 10 * 60 * 1000), // 10分钟后
        drone: '无人机 #1',
        path: [] // 实际应用中应该有路径数据
      },
      {
        id: 'task-2',
        title: '办公物资配送',
        packageType: 'regular',
        weight: 1.8,
        from: '北区仓库',
        to: '西区园区',
        priority: 4,
        status: 'pending',
        createdAt: new Date(Date.now() - 30 * 60 * 1000), // 30分钟前
        eta: new Date(Date.now() + 45 * 60 * 1000), // 45分钟后
        drone: null,
        path: []
      },
      {
        id: 'task-3',
        title: '易碎设备运输',
        packageType: 'fragile',
        weight: 0.9,
        from: '北区仓库',
        to: '中心商业区',
        priority: 6,
        status: 'completed',
        createdAt: new Date(Date.now() - 120 * 60 * 1000), // 2小时前
        eta: new Date(Date.now() - 90 * 60 * 1000), // 1.5小时前
        completedAt: new Date(Date.now() - 85 * 60 * 1000), // 1小时25分钟前
        drone: '无人机 #3',
        path: []
      }
    ]
  }
  
  // 组件挂载时获取数据
  onMounted(() => {
    fetchTasks()
  })
  </script>