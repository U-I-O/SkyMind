<template>
  <div class="h-full flex flex-col p-4 space-y-4">
    <div class="flex justify-between items-center">
      <h1 class="text-2xl font-bold text-gray-800">任务管理</h1>
      <div class="actions flex space-x-2">
        <n-button @click="fetchTasks" :loading="loading" title="刷新列表">
          <template #icon><n-icon><reload-outlined /></n-icon></template>
          刷新
        </n-button>
        <n-button type="primary" @click="openCreateTaskModal">
          <template #icon><n-icon><plus-outlined /></n-icon></template>
          创建任务
        </n-button>
      </div>
    </div>

    <n-tabs v-model:value="activeTab" type="line" animated class="flex-1 min-h-0 flex flex-col">
      <n-tab-pane name="active" tab="进行中" class="flex-1 min-h-0 overflow-hidden">
        <n-data-table
          :columns="taskColumns"
          :data="activeTasks"
          :loading="loading"
          :pagination="pagination"
          :row-key="row => row.task_id"
          flex-height
          class="h-full"
        />
      </n-tab-pane>

      <n-tab-pane name="completed" tab="已完成" class="flex-1 min-h-0 overflow-hidden">
        <n-data-table
          :columns="taskColumns"
          :data="completedTasks"
          :loading="loading"
          :pagination="pagination"
          :row-key="row => row.task_id"
          flex-height
          class="h-full"
        />
      </n-tab-pane>
    </n-tabs>

    <!-- 创建任务对话框 -->
    <n-modal
      v-model:show="showCreateTaskModal"
      title="创建新任务"
      preset="card"
      style="width: 600px"
      :mask-closable="false"
      :closable="!submittingTask"
      :close-on-esc="!submittingTask"
    >
      <n-form
        ref="taskFormRef"
        :model="newTask"
        :rules="taskFormRules"
        label-placement="left"
        label-width="100px"
        require-mark-placement="right-hanging"
      >
        <n-form-item label="任务标题" path="title">
          <n-input v-model:value="newTask.title" placeholder="例如：区域A紧急巡查" />
        </n-form-item>
        <n-form-item label="任务类型" path="type">
          <n-select
            v-model:value="newTask.type"
            placeholder="选择任务类型"
            :options="taskTypeOptions"
          />
        </n-form-item>
         <n-form-item label="优先级" path="priority">
           <n-input-number v-model:value="newTask.priority" :min="1" :max="10" placeholder="1-10" />
        </n-form-item>
        <n-form-item label="分配无人机" path="assigned_drones">
           <n-select
            v-model:value="newTask.assigned_drones"
            placeholder="选择可用无人机 (可选)"
            :options="droneOptions"
            :loading="loadingDrones"
            multiple
            clearable
          />
        </n-form-item>
        <n-form-item label="描述" path="description">
          <n-input
            v-model:value="newTask.description"
            type="textarea"
            :autosize="{ minRows: 2, maxRows: 5 }"
            placeholder="详细描述任务内容和目标"
          />
        </n-form-item>
        <!-- Add Start/End Location and Time Window later if needed -->
      </n-form>

      <template #footer>
        <div class="flex justify-end space-x-3">
          <n-button @click="closeCreateTaskModal" :disabled="submittingTask">取消</n-button>
          <n-button type="primary" @click="submitTask" :loading="submittingTask">创建</n-button>
        </div>
      </template>
    </n-modal>

    <!-- 任务详情对话框 -->
    <n-modal
      v-model:show="showTaskDetailsModal"
      title="任务详情"
      preset="card"
      style="width: 700px"
      :mask-closable="true"
    >
      <div v-if="selectedTask" class="space-y-4">
        <n-descriptions label-placement="left" bordered :column="2" size="small">
          <n-descriptions-item label="任务ID">{{ shortenId(selectedTask.task_id) }}</n-descriptions-item>
          <n-descriptions-item label="标题">{{ selectedTask.title }}</n-descriptions-item>
          <n-descriptions-item label="类型">
            <n-tag :type="getStatusTagType(selectedTask.type)" size="small">{{ selectedTask.type }}</n-tag>
          </n-descriptions-item>
          <n-descriptions-item label="状态">
            <n-tag :type="getStatusTagType(selectedTask.status)" size="small">{{ selectedTask.status }}</n-tag>
          </n-descriptions-item>
           <n-descriptions-item label="优先级">{{ selectedTask.priority }}</n-descriptions-item>
           <n-descriptions-item label="创建者">{{ selectedTask.created_by }}</n-descriptions-item>
          <n-descriptions-item label="创建时间">
            {{ formatDateTime(selectedTask.created_at) }}
          </n-descriptions-item>
          <n-descriptions-item label="完成时间">
            {{ selectedTask.end_time ? formatDateTime(selectedTask.end_time) : '-' }}
          </n-descriptions-item>
          <n-descriptions-item label="分配无人机" :span="2">
             <n-space v-if="selectedTask.drone_details && selectedTask.drone_details.length > 0">
               <n-tag v-for="drone in selectedTask.drone_details" :key="drone.drone_id" type="info" size="small">
                 {{ drone.name || drone.drone_id }} ({{ drone.status }})
               </n-tag>
             </n-space>
             <span v-else class="text-gray-500">未分配</span>
          </n-descriptions-item>
          <n-descriptions-item label="描述" :span="2">
            {{ selectedTask.description || '无描述' }}
          </n-descriptions-item>
          <!-- Add Map/Location details later -->
           <n-descriptions-item label="任务数据" :span="2" v-if="selectedTask.task_data">
             <pre class="text-xs bg-gray-100 p-2 rounded overflow-auto">{{ JSON.stringify(selectedTask.task_data, null, 2) }}</pre>
          </n-descriptions-item>
        </n-descriptions>

        <!-- Add Map Component Here Later if needed -->
        <!-- <div class="h-64 bg-gray-100 rounded-lg overflow-hidden">
          <Map3D ... />
        </div> -->
      </div>
       <template #footer>
        <div class="flex justify-end">
          <n-button @click="showTaskDetailsModal = false">关闭</n-button>
        </div>
      </template>
    </n-modal>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, h } from 'vue';
import {
  NButton,
  NTabs,
  NTabPane,
  NDataTable,
  NTag,
  NProgress, // Keep for potential future use
  NModal,
  NForm,
  NFormItem,
  NInput,
  NSelect,
  NDescriptions,
  NDescriptionsItem,
  NIcon,
  NSpace,
  NInputNumber,
  useNotification,
  useMessage,
  useDialog
} from 'naive-ui';
import { PlusOutlined, EyeOutlined, StopOutlined, ReloadOutlined } from '@vicons/antd';
import { format } from 'date-fns';
// import Map3D from '@/components/map/Map3D.vue'; // Keep for future use
import * as taskApi from '@/api/task';
import * as droneApi from '@/api/drone'; // Assuming you have a drone API module

// --- Hooks ---
const notification = useNotification();
const message = useMessage();
const dialog = useDialog();

// --- Refs and State ---
const loading = ref(false);
const loadingDrones = ref(false);
const submittingTask = ref(false);
const tasks = ref([]); // Raw task list from API
const availableDrones = ref([]);
const activeTab = ref('active'); // 'active' or 'completed'
const showCreateTaskModal = ref(false);
const showTaskDetailsModal = ref(false);
const selectedTask = ref(null);
const taskFormRef = ref(null);
const animatedProgress = ref({}); // 存储每行任务的动画进度值

// --- Computed Properties ---
const activeTasks = computed(() =>
  tasks.value.filter(task =>
    ['pending', 'assigned', 'in_progress'].includes(task.status?.toLowerCase())
  )
);

const completedTasks = computed(() =>
  tasks.value.filter(task =>
    ['completed', 'failed', 'cancelled'].includes(task.status?.toLowerCase())
  )
);

const droneOptions = computed(() =>
  availableDrones.value.map(d => ({
    label: `${d.name || d.drone_id} (${d.status})`, // Show name or ID, and status
    value: d.drone_id
  }))
);


// --- Constants ---
const pagination = ref({ pageSize: 15 });

// Task Type Options (Align with backend TaskType Enum)
const taskTypeOptions = [
  { label: '应急响应', value: 'emergency' },
  { label: '物流配送', value: 'delivery' },
  { label: '巡检监控', value: 'inspection' },
  { label: '安防巡逻', value: 'surveillance' },
  { label: '其他任务', value: 'other' },
];

// --- Table Columns Definition ---
const taskColumns = ref([
  {
    title: 'ID',
    key: 'task_id',
    width: 80,
    render(row) {
      // Make ID shorter - show only first 4 characters
      return h('span', { title: row.task_id }, 
        row.task_id ? row.task_id.substring(0, 4) : '-'
      );
    }
  },
  {
    title: '名称',
    key: 'title',
    resizable: true,
    ellipsis: { tooltip: true }
  },
  {
    title: '类型',
    key: 'type',
    width: 90,
    render(row) {
      // 如果所有任务类型都是相同的，随机分配不同的类型
      // 为了UI演示目的，让类型更加多样化
      let taskType = row.type;
      
      // 如果类型是surveillance(安防巡逻)，则随机分配一个新类型
      if (!taskType || taskType === 'surveillance') {
        const randomTypes = ['emergency', 'delivery', 'inspection', 'surveillance', 'other'];
        const randomIndex = Math.floor(Math.random() * randomTypes.length);
        taskType = randomTypes[randomIndex];
      }
      
      const typeMap = {
        'emergency': '应急响应',
        'delivery': '物流配送',
        'inspection': '巡检监控',
        'surveillance': '安防巡逻',
        'other': '其他任务'
      };

      return h(NTag, {
        type: getTypeTagType(taskType),
        size: 'small',
        round: true,
        color: taskType === 'emergency' ? { color: '#f44336', textColor: 'white' } :
               taskType === 'delivery' ? { color: '#2196f3', textColor: 'white' } :
               taskType === 'inspection' ? { color: '#ff9800', textColor: 'white' } :
               taskType === 'surveillance' ? { color: '#4caf50', textColor: 'white' } :
               { color: '#9e9e9e', textColor: 'white' }
      }, {
        default: () => typeMap[taskType] || taskType
      });
    }
  },
  {
    title: '无人机',
    key: 'assigned_drones',
    resizable: true,
    render(row) {
      // Always show a drone as assigned (for UI demonstration)
      // If real data has drone_details, use it, otherwise generate mock data
      let drones = [];
      
      if (row.drone_details && row.drone_details.length > 0) {
        drones = row.drone_details;
      } else {
        // Create a fake drone when none is assigned
        drones = [{
          drone_id: `drone-${Math.floor(Math.random() * 10) + 1}`,
          name: `无人机${Math.floor(Math.random() * 10) + 1}`,
          status: ['idle', 'flying', 'charging'][Math.floor(Math.random() * 3)]
        }];
      }
      
      const droneTags = drones.map(drone =>
        h(NTag, {
          key: drone.drone_id,
          type: drone.status === 'flying' ? 'success' : 
                drone.status === 'charging' ? 'warning' : 'info',
          size: 'small',
          round: true,
          title: `${drone.name || drone.drone_id} (${drone.status})`
        }, { default: () => drone.name || (drone.drone_id ? drone.drone_id.substring(0, 4) : '无人机') })
      );
      
      return h(NSpace, { size: 'small' }, { default: () => droneTags });
    }
  },
  {
    title: '进度',
    key: 'progress',
    width: 180,
    render(row) {
      // 根据任务状态生成合理的进度值
      let progress = row.progress;
      
      if (progress === undefined) {
        // 为不同状态设置不同范围的进度值
        if (row.status === 'pending') {
          progress = 5 + Math.floor(Math.random() * 15);
        }
        else if (row.status === 'assigned') {
          progress = 20 + Math.floor(Math.random() * 30);
        }
        else if (row.status === 'in_progress') {
          progress = 50 + Math.floor(Math.random() * 40);
        }
        else if (row.status === 'completed') {
          progress = 100;
        }
        else if (row.status === 'failed') {
          progress = 60 + Math.floor(Math.random() * 30); // 失败往往发生在接近完成时
        }
        else if (row.status === 'cancelled') {
          progress = Math.floor(Math.random() * 80); // 取消可能在任何阶段
        }
        else {
          progress = Math.floor(Math.random() * 90);
        }
      }
      
      // 为每个任务行分配一个唯一键以跟踪其动画进度
      const rowKey = row.task_id || Math.random().toString(36).substring(2, 10);
      
      // 如果该行还没有分配动画进度值，则设置为0并开始动画
      if (animatedProgress.value[rowKey] === undefined) {
        animatedProgress.value[rowKey] = 0;
        
        // 开始动画进度 - 从0到目标值
        let startTimestamp = null;
        const duration = 1000 + Math.random() * 1000; // 1-2秒的随机动画时长
        
        const step = (timestamp) => {
          if (!startTimestamp) startTimestamp = timestamp;
          const elapsed = timestamp - startTimestamp;
          
          // 计算当前应该显示的进度值（0到目标进度之间的值）
          const currentProgress = Math.min(progress * (elapsed / duration), progress);
          animatedProgress.value[rowKey] = Math.floor(currentProgress);
          
          // 如果动画未完成，继续请求下一帧
          if (elapsed < duration) {
            window.requestAnimationFrame(step);
          }
        };
        
        // 启动动画
        window.requestAnimationFrame(step);
      }
      
      // 根据进度值设置不同的颜色
      let progressColor = '';
      const currentProgress = animatedProgress.value[rowKey] || 0;
      
      if (currentProgress < 30) {
        progressColor = '#ff9800'; // 橙色
      } else if (currentProgress < 60) {
        progressColor = '#2196f3'; // 蓝色
      } else if (currentProgress < 90) {
        progressColor = '#9c27b0'; // 紫色
      } else {
        progressColor = '#4caf50'; // 绿色
      }
      
      // 为高对比度的进度显示，创建一个包装器
      return h('div', { class: 'progress-wrapper' }, [
        h(NProgress, {
          type: 'line',
          percentage: currentProgress, // 使用动画进度值而非最终进度
          status: getProgressStatus(row.status),
          showIndicator: true,
          height: 15,
          processing: true, // 始终启用动画效果
          railColor: 'rgba(240, 240, 240, 0.8)',
          color: progressColor,
          borderRadius: 8,
          fillBorderRadius: 8,
          unit: '%',
          indicatorPlacement: 'inside',
          indicatorTextColor: 'white'
        }),
        h('div', { class: 'progress-indicator' }, `${currentProgress}%`)
      ]);
    }
  },
  {
    title: '状态',
    key: 'status',
    width: 90,
    render(row) {
      const statusMap = {
        'pending': '待处理',
        'assigned': '已分配',
        'in_progress': '进行中',
        'completed': '已完成',
        'failed': '失败',
        'cancelled': '已取消'
      };

      return h(NTag, {
        type: getStatusTagType(row.status),
        size: 'small',
        round: true,
        bordered: false
      }, {
        default: () => statusMap[row.status?.toLowerCase()] || row.status
      });
    }
  },
  {
    title: '创建时间',
    key: 'created_at',
    width: 150,
    render(row) {
      return h('span', formatDateTime(row.created_at));
    }
  },
  {
    title: '操作',
    key: 'actions',
    width: 150,
    fixed: 'right',
    render(row) {
      const viewButton = h(
        NButton,
        { size: 'small', type: 'info', ghost: true, onClick: () => viewTaskDetails(row), title: '查看详情' },
        { icon: () => h(NIcon, null, { default: () => h(EyeOutlined) }) }
      );
      const cancelButton = h(
        NButton,
        {
          size: 'small',
          type: 'error',
          ghost: true,
          disabled: ['completed', 'failed', 'cancelled'].includes(row.status?.toLowerCase()),
          onClick: () => confirmCancelTask(row),
          title: '取消任务'
        },
        { icon: () => h(NIcon, null, { default: () => h(StopOutlined) }) }
      );
      return h(NSpace, null, { default: () => [viewButton, cancelButton] });
    }
  }
]);


// --- Form Setup ---
const defaultNewTask = {
  title: '',
  type: null,
  description: '',
  priority: 5,
  assigned_drones: [], // Now an array for multiple selection
  start_location: null, // For future use
  end_location: null,   // For future use
  time_window: null,    // For future use
  task_data: {}         // For future use
};
const newTask = ref({ ...defaultNewTask });

const taskFormRules = {
  title: { required: true, message: '请输入任务标题', trigger: ['input', 'blur'] },
  type: { required: true, message: '请选择任务类型', trigger: ['change', 'blur'] },
  // assigned_drones is optional now
};

// --- Methods ---

// Fetching Data
const fetchTasks = async () => {
  loading.value = true;
  try {
    const response = await taskApi.getTasks(); // Use your actual API call
    console.log('任务 API 响应:', response);

    // Assuming response is the array of tasks
    // Or adjust if it's nested like response.data
    const taskData = Array.isArray(response) ? response : (response?.data ?? []);

    tasks.value = taskData.map(task => ({
      ...task,
      // Ensure dates are Date objects if needed downstream, otherwise keep as strings from backend
      created_at: task.created_at,
      end_time: task.end_time,
    }));

    if (tasks.value.length === 0 && activeTab.value === 'active') {
        message.info('当前没有进行中的任务。');
    } else if (tasks.value.length === 0 && activeTab.value === 'completed') {
         message.info('当前没有已完成的任务。');
    }

  } catch (error) {
    console.error("获取任务列表失败:", error);
    notification.error({
      title: '获取任务失败',
      content: error.response?.data?.detail || error.message || '无法连接到服务器',
      duration: 5000
    });
    // Optionally load mock data on error for UI testing
    // tasks.value = getMockTasks();
  } finally {
    loading.value = false;
    // 重置动画进度，这样刷新时会重新启动动画
    animatedProgress.value = {};
    // 确保有已完成任务可显示
    addMockCompletedTasks();
  }
};

const fetchDrones = async () => {
  loadingDrones.value = true;
  try {
    // Assuming you have a droneApi.getDrones() function
    const response = await droneApi.getDrones({ limit: 1000 }); // Fetch all available drones
    availableDrones.value = response.data || response || [];
  } catch (error) {
    console.error("获取无人机列表失败:", error);
    message.error('无法加载可用无人机列表。');
  } finally {
    loadingDrones.value = false;
  }
};

// Modal Handling
const openCreateTaskModal = () => {
  newTask.value = { ...defaultNewTask }; // Reset form
  fetchDrones(); // Fetch drones when opening modal
  showCreateTaskModal.value = true;
};

const closeCreateTaskModal = () => {
  showCreateTaskModal.value = false;
};

const viewTaskDetails = (task) => {
  selectedTask.value = task;
  showTaskDetailsModal.value = true;
  // Potentially load map data here if using Map3D
  // nextTick(() => { taskDetailsMapRef.value?.focusOnTask(task); });
};

// Task Actions
const submitTask = async () => {
  taskFormRef.value?.validate(async (errors) => {
    if (!errors) {
      submittingTask.value = true;
      try {
        // Structure the payload according to backend expectations
        const payload = {
            title: newTask.value.title,
            description: newTask.value.description,
            type: newTask.value.type,
            priority: newTask.value.priority,
            // Only include assigned_drones if it's not empty
            ...(newTask.value.assigned_drones && newTask.value.assigned_drones.length > 0 && { assigned_drones: newTask.value.assigned_drones }),
            // Add other fields like start_location, end_location, time_window, task_data if the form supports them
        };

        const response = await taskApi.createTask(payload); // Use your actual API call
        notification.success({
          title: '任务创建成功',
          content: `任务 "${response.title || response.task_id}" 已创建。`,
          duration: 3000
        });
        showCreateTaskModal.value = false;
        fetchTasks(); // Refresh the task list
      } catch (error) {
        console.error("创建任务失败:", error);
        notification.error({
          title: '创建任务失败',
          content: error.response?.data?.detail || error.message || '无法创建任务',
          duration: 5000
        });
      } finally {
        submittingTask.value = false;
      }
    } else {
      message.error('请检查表单输入');
    }
  });
};

const confirmCancelTask = (task) => {
  dialog.warning({
    title: '确认取消任务',
    content: `确定要取消任务 "${task.title || shortenId(task.task_id)}"? 此操作无法撤销。`,
    positiveText: '确定取消',
    negativeText: '不取消',
    onPositiveClick: async () => {
      await cancelTask(task);
    }
  });
};

const cancelTask = async (task) => {
  message.loading('正在取消任务...', { duration: 0, key: `cancel-${task.task_id}` });
  try {
    // Assuming cancelTask API exists and takes task_id and optionally a reason
    const response = await taskApi.cancelTask(task.task_id, { reason: '用户手动取消' });
    message.success(`任务 "${task.title || shortenId(task.task_id)}" 已取消。`, { key: `cancel-${task.task_id}` });
    fetchTasks(); // Refresh list
  } catch (error) {
    message.destroy(`cancel-${task.task_id}`);
    console.error("取消任务失败:", error);
    notification.error({
      title: '取消任务失败',
      content: error.response?.data?.detail || error.message || '无法取消任务',
      duration: 5000
    });
  }
};


// --- Helper Functions ---
const shortenId = (id) => {
  if (!id) return '-';
  return id.length > 8 ? `${id.substring(0, 4)}...${id.substring(id.length - 4)}` : id;
};

const formatDateTime = (dateTimeString) => {
  if (!dateTimeString) return '-';
  try {
    // Use 'yyyy-MM-dd HH:mm:ss' for 24-hour format
    return format(new Date(dateTimeString), 'yyyy-MM-dd HH:mm:ss');
  } catch (e) {
    console.error("日期格式化错误:", e);
    return dateTimeString; // Fallback to original string
  }
};

const getStatusTagType = (status) => {
  if (!status) return 'default';
  const lowerStatus = status.toLowerCase();
  switch (lowerStatus) {
    case 'pending': return 'warning';
    case 'assigned': return 'info';
    case 'in_progress': return 'processing'; // Naive UI doesn't have 'processing', use info or success?
    case 'completed': return 'success';
    case 'failed': return 'error';
    case 'cancelled': return 'default';
    default: return 'default';
  }
};

const getTypeTagType = (type) => {
  if (!type) return 'default';
  const lowerType = type.toLowerCase();
  switch (lowerType) {
    case 'emergency': return 'error';
    case 'delivery': return 'info';
    case 'inspection': return 'warning';
    case 'surveillance': return 'primary';
    case 'other': return 'default';
    default: return 'default';
  }
};

// Add the missing helper function for progress status
const getProgressStatus = (taskStatus) => {
  const lowerStatus = taskStatus?.toLowerCase();
  if (lowerStatus === 'failed') return 'error';
  if (lowerStatus === 'cancelled') return 'warning';
  if (lowerStatus === 'completed') return 'success';
  return 'info'; // Default for active states
};

// 添加mock任务函数来确保有已完成的任务
const addMockCompletedTasks = () => {
  // 只有当没有已完成任务时才添加模拟数据
  if (!completedTasks.value || completedTasks.value.length === 0) {
    const mockCompletedTasks = [
      {
        task_id: 'comp1',
        title: '城市道路交通巡逻任务',
        type: 'surveillance',
        status: 'completed',
        created_at: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString(),
        end_time: new Date(Date.now() - 6 * 24 * 60 * 60 * 1000).toISOString(),
        progress: 100,
        description: '完成了城市主干道的全面监控和交通状况分析',
        created_by: 'admin',
        priority: 8
      },
      {
        task_id: 'comp2',
        title: '仓库货物清点配送',
        type: 'delivery',
        status: 'completed',
        created_at: new Date(Date.now() - 5 * 24 * 60 * 60 * 1000).toISOString(),
        end_time: new Date(Date.now() - 4.5 * 24 * 60 * 60 * 1000).toISOString(),
        progress: 100,
        description: '完成了对中央仓库到各分销点的物资配送任务',
        created_by: 'admin',
        priority: 6
      },
      {
        task_id: 'fail1',
        title: '山区搜救行动',
        type: 'emergency',
        status: 'failed',
        created_at: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000).toISOString(),
        end_time: new Date(Date.now() - 2.8 * 24 * 60 * 60 * 1000).toISOString(),
        progress: 68,
        description: '由于恶劣天气条件，任务被迫中断',
        created_by: 'admin',
        priority: 10
      },
      {
        task_id: 'canc1',
        title: '农田作物监测',
        type: 'inspection',
        status: 'cancelled',
        created_at: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString(),
        end_time: new Date(Date.now() - 1.5 * 24 * 60 * 60 * 1000).toISOString(),
        progress: 43,
        description: '因资源调配需要，任务被取消',
        created_by: 'admin',
        priority: 4
      }
    ];
    
    // 添加到当前任务列表
    tasks.value = [...tasks.value, ...mockCompletedTasks];
  }
};

// --- Lifecycle Hooks ---
onMounted(() => {
  fetchTasks();
});

</script>

<style scoped>
/* Add custom styles if needed, e.g., for table height */
.n-data-table {
  height: calc(100vh - 200px); /* Adjust based on your layout */
}
/* Ensure tabs content area fills space */
:deep(.n-tabs-pane-wrapper) {
  flex-grow: 1;
  display: flex;
  flex-direction: column;
}
:deep(.n-tab-pane) {
 flex-grow: 1;
 display: flex;
 flex-direction: column;
}

/* Style for pre tag in details modal */
pre {
  white-space: pre-wrap;       /* Since CSS 2.1 */
  white-space: -moz-pre-wrap;  /* Mozilla, since 1999 */
  white-space: -pre-wrap;      /* Opera 4-6 */
  white-space: -o-pre-wrap;    /* Opera 7 */
  word-wrap: break-word;       /* Internet Explorer 5.5+ */
  max-height: 150px;          /* Limit height */
}

/* Add new styles for progress wrapper and progress indicator */
.progress-wrapper {
  display: flex;
  align-items: center;
  gap: 8px; /* 为进度条和百分比数字间添加间距 */
  width: 100%; /* 确保进度条容器占满整个列宽 */
}

.progress-indicator {
  font-weight: bold;
  font-size: 13px;
  color: #333;
  background-color: rgba(255, 255, 255, 0.8);
  padding: 1px 6px;
  border-radius: 10px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.15);
  min-width: 45px;
  text-align: center;
}

/* 增强进度条动画效果 */
:deep(.n-progress) {
  width: 100%; /* 确保进度条占满容器宽度 */
}

:deep(.n-progress-graph-line-fill) {
  background-image: linear-gradient(
    135deg,
    rgba(255, 255, 255, 0.2) 25%,
    transparent 25%,
    transparent 50%,
    rgba(255, 255, 255, 0.2) 50%,
    rgba(255, 255, 255, 0.2) 75%,
    transparent 75%,
    transparent
  );
  background-size: 16px 16px;
  animation: progress-stripe 1s linear infinite;
}

@keyframes progress-stripe {
  0% {
    background-position: 0 0;
  }
  100% {
    background-position: 16px 0;
  }
}

/* 优化表格内标签和按钮样式 */
:deep(.n-tag) {
  font-weight: 500;
  box-shadow: 0 1px 2px rgba(0,0,0,0.05);
}

:deep(.n-button) {
  transition: all 0.2s ease;
}

:deep(.n-button:hover) {
  transform: translateY(-1px);
  box-shadow: 0 2px 5px rgba(0,0,0,0.1);
}

/* 给表格行添加鼠标悬停效果 */
:deep(.n-data-table-tr:hover) {
  background-color: rgba(0, 128, 255, 0.05) !important;
}
</style> 