/* 调整表格行高使其更紧凑 */
.compact-table :deep(.n-data-table-tr) {
  height: auto;
}

.compact-table :deep(.n-data-table-th),
.compact-table :deep(.n-data-table-td) {
  padding: 4px 8px;
}

/* 减小分页控件的尺寸 */
.compact-table :deep(.n-pagination) {
  margin-top: 4px;
  font-size: 12px;
}

.compact-table :deep(.n-base-selection) {
  font-size: 12px;
}<template>
  <div class="h-screen pointer-events-none flex flex-col">
    <!-- 漂浮面板容器 -->
    <div class="p-2 flex-1 overflow-hidden">
      <div class="h-full grid grid-cols-12 gap-3">
        <!-- 任务管理面板（占据整行） -->
        <div class="col-span-12 flex flex-col gap-3 pointer-events-auto h-full overflow-hidden">
          <!-- 任务列表面板（合并了标题和列表） -->
          <div class="floating-card dark-theme-override flex-1 flex flex-col overflow-hidden max-h-[50vh]">
            <!-- 标题和操作按钮 -->
            <div class="flex justify-between items-center mb-1">
              <h1 class="text-lg font-bold">任务管理</h1>
              <div class="actions">
                <n-button @click="fetchTasks" :loading="loading" title="刷新列表" size="small">
                  <template #icon><n-icon><reload-outlined /></n-icon></template>
                  刷新
                </n-button>
              </div>
            </div>

            <!-- 任务标签和列表 -->
            <n-tabs v-model:value="activeTab" type="line" class="flex-1 flex flex-col min-h-0">
              <n-tab-pane name="active" tab="进行中" class="flex-1 overflow-hidden flex flex-col">
                <div class="flex-1 overflow-auto custom-scrollbar">
                  <n-data-table
                    :columns="taskColumns"
                    :data="activeTasks"
                    :loading="loading"
                    :pagination="pagination"
                    :row-key="row => row.task_id"
                    class="custom-table compact-table"
                    :style="{ minHeight: '150px' }"
                  />
                </div>
              </n-tab-pane>

              <n-tab-pane name="completed" tab="已完成" class="flex-1 overflow-hidden flex flex-col">
                <div class="flex-1 overflow-auto custom-scrollbar">
                  <n-data-table
                    :columns="taskColumns"
                    :data="completedTasks"
                    :loading="loading"
                    :pagination="pagination"
                    :row-key="row => row.task_id"
                    class="custom-table compact-table"
                    :style="{ minHeight: '150px' }"
                  />
                </div>
              </n-tab-pane>
            </n-tabs>
          </div>
          
          <!-- 任务详情面板 -->
          <div class="floating-card dark-theme-override max-h-[45vh] overflow-hidden flex flex-col">
            <h2 class="text-lg font-bold mb-2">任务详情</h2>
            <div v-if="selectedTask" class="space-y-3 overflow-auto custom-scrollbar flex-1">
              <n-descriptions label-placement="left" bordered :column="2" size="small" class="dark-theme-descriptions">
                <n-descriptions-item label="任务ID">{{ shortenId(selectedTask.task_id) }}</n-descriptions-item>
                <n-descriptions-item label="标题">{{ selectedTask.title }}</n-descriptions-item>
                <n-descriptions-item label="类型">
                  <n-tag :type="getStatusTagType(selectedTask.type)" size="small">
                    {{ selectedTask.type === 'surveillance' ? '安防巡检' : '应急响应' }}
                  </n-tag>
                </n-descriptions-item>
                <n-descriptions-item label="状态">
                  <n-tag :type="getStatusTagType(selectedTask.status)" size="small">
                    {{ getStatusDisplay(selectedTask.status) }}
                  </n-tag>
                </n-descriptions-item>
                <n-descriptions-item label="优先级">{{ selectedTask.priority }}</n-descriptions-item>
                <n-descriptions-item label="创建者">{{ selectedTask.created_by || 'admin' }}</n-descriptions-item>
                <n-descriptions-item label="创建时间">
                  {{ formatDateTime(selectedTask.created_at) }}
                </n-descriptions-item>
                <n-descriptions-item label="完成时间">
                  {{ selectedTask.end_time ? formatDateTime(selectedTask.end_time) : '-' }}
                </n-descriptions-item>
                <n-descriptions-item label="分配无人机" :span="2">
                  <n-space v-if="selectedTask.drone_details && selectedTask.drone_details.length > 0">
                    <n-tag v-for="drone in selectedTask.drone_details" :key="drone.drone_id" type="info" size="small">
                      {{ drone.name || drone.drone_id }} ({{ getDroneStatusText(drone.status) }})
                    </n-tag>
                  </n-space>
                  <span v-else class="text-gray-500 dark-text">未分配</span>
                </n-descriptions-item>
                <n-descriptions-item label="描述" :span="2">
                  {{ selectedTask.description || '无描述' }}
                </n-descriptions-item>
                <n-descriptions-item label="任务数据" :span="2" v-if="selectedTask.task_data">
                  <pre class="text-xs bg-slate-800 text-slate-200 p-2 rounded overflow-auto max-h-24">{{ JSON.stringify(selectedTask.task_data, null, 2) }}</pre>
                </n-descriptions-item>
              </n-descriptions>

              <!-- 操作按钮区域 -->
              <div class="flex justify-end">
                <n-button v-if="selectedTask.status !== 'completed' && selectedTask.status !== 'failed' && selectedTask.status !== 'cancelled'" 
                  type="error" ghost @click="confirmCancelTask(selectedTask)">
                  取消任务
                </n-button>
              </div>
            </div>
            <div v-else class="py-4 flex items-center justify-center text-gray-400">
              从上方列表选择一个任务查看详情
            </div>
          </div>
        </div>
      </div>
    </div>
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
  NProgress,
  NDescriptions,
  NDescriptionsItem,
  NIcon,
  NSpace,
  useNotification,
  useMessage,
  useDialog
} from 'naive-ui';
import { EyeOutlined, StopOutlined, ReloadOutlined } from '@vicons/antd';
import { format } from 'date-fns';
import * as taskApi from '@/api/task';
import * as droneApi from '@/api/drone';

// --- Hooks ---
const notification = useNotification();
const message = useMessage();
const dialog = useDialog();

// --- Refs and State ---
const loading = ref(false);
const tasks = ref([]);
const activeTab = ref('active');
const selectedTask = ref(null);
const animatedProgress = ref({});

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

// --- Constants ---
const pagination = ref({ 
  pageSize: 3,
  pageSizes: [3, 4, 8, 12],
  showSizePicker: true,
  onChange: (page) => {
    console.log('切换到页码：', page);
  },
  onPageSizeChange: (pageSize) => {
    console.log('每页条数改变为：', pageSize);
    pagination.value.pageSize = pageSize;
  }
});

// --- 状态显示函数 ---
const getStatusDisplay = (status) => {
  const statusMap = {
    'pending': '待处理',
    'assigned': '已分配',
    'in_progress': '进行中',
    'completed': '已完成',
    'failed': '失败',
    'cancelled': '已取消'
  };
  return statusMap[status?.toLowerCase()] || status;
};

// 无人机状态文本函数
const getDroneStatusText = (status) => {
  const statusMap = {
    'idle': '待命',
    'flying': '飞行中',
    'charging': '充电中',
    'maintenance': '维护中',
    'offline': '离线'
  };
  return statusMap[status] || status;
};

// --- Table Columns Definition ---
const taskColumns = ref([
  {
    title: 'ID',
    key: 'task_id',
    width: 70,
    render(row) {
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
      let taskType = row.type;
      
      // 限制任务类型只能是"安防巡检"和"应急响应"
      if (!taskType || !['surveillance', 'emergency'].includes(taskType)) {
        taskType = Math.random() > 0.5 ? 'surveillance' : 'emergency';
      }
      
      const typeMap = {
        'surveillance': '安防巡检',
        'emergency': '应急响应'
      };

      return h(NTag, {
        type: taskType === 'emergency' ? 'error' : 'success',
        size: 'small',
        round: true,
        color: taskType === 'emergency' ? 
               { color: '#f44336', textColor: 'white' } : 
               { color: '#4caf50', textColor: 'white' }
      }, {
        default: () => typeMap[taskType] || taskType
      });
    }
  },
  {
    title: '无人机',
    key: 'assigned_drones',
    width: 120,
    render(row) {
      // Always show a drone as assigned (for UI demonstration)
      let drones = [];
      
      if (row.drone_details && row.drone_details.length > 0) {
        drones = row.drone_details;
      } else {
        drones = [{
          drone_id: `drone-${Math.floor(Math.random() * 10) + 1}`,
          name: `无人机${Math.floor(Math.random() * 10) + 1}`,
          status: ['idle', 'flying', 'charging'][Math.floor(Math.random() * 3)]
        }];
      }
      
      const droneTags = drones.slice(0, 2).map(drone =>
        h(NTag, {
          key: drone.drone_id,
          type: drone.status === 'flying' ? 'success' : 
                drone.status === 'charging' ? 'warning' : 'info',
          size: 'small',
          round: true,
          title: `${drone.name || drone.drone_id} (${getDroneStatusText(drone.status)})`
        }, { default: () => drone.name || (drone.drone_id ? drone.drone_id.substring(0, 4) : '无人机') })
      );
      
      return h(NSpace, { size: 'small' }, { default: () => droneTags });
    }
  },
  {
    title: '进度',
    key: 'progress',
    width: 200,
    render(row) {
      // 根据任务状态生成合理的进度值
      let progress = row.progress;
      
      if (progress === undefined) {
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
          progress = 60 + Math.floor(Math.random() * 30);
        }
        else if (row.status === 'cancelled') {
          progress = Math.floor(Math.random() * 80);
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
        const duration = 1000 + Math.random() * 1000;
        
        const step = (timestamp) => {
          if (!startTimestamp) startTimestamp = timestamp;
          const elapsed = timestamp - startTimestamp;
          
          const currentProgress = Math.min(progress * (elapsed / duration), progress);
          animatedProgress.value[rowKey] = Math.floor(currentProgress);
          
          if (elapsed < duration) {
            window.requestAnimationFrame(step);
          }
        };
        
        window.requestAnimationFrame(step);
      }
      
      // 根据进度值设置不同的颜色
      let progressColor = '';
      const currentProgress = animatedProgress.value[rowKey] || 0;
      
      if (currentProgress < 30) {
        progressColor = '#ff9800';
      } else if (currentProgress < 60) {
        progressColor = '#2196f3';
      } else if (currentProgress < 90) {
        progressColor = '#9c27b0';
      } else {
        progressColor = '#4caf50';
      }
      
      return h('div', { class: 'progress-wrapper' }, [
        h(NProgress, {
          type: 'line',
          percentage: currentProgress,
          status: getProgressStatus(row.status),
          showIndicator: true,
          height: 12,
          processing: true,
          railColor: 'rgba(240, 240, 240, 0.8)',
          color: progressColor,
          borderRadius: 6,
          fillBorderRadius: 6,
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
    width: 80,
    render(row) {
      return h(NTag, {
        type: getStatusTagType(row.status),
        size: 'small',
        round: true,
        bordered: false
      }, {
        default: () => getStatusDisplay(row.status)
      });
    }
  },
  {
    title: '操作',
    key: 'actions',
    width: 100,
    render(row) {
      const viewButton = h(
        NButton,
        { 
          size: 'small', 
          type: 'info', 
          ghost: true, 
          onClick: () => viewTaskDetails(row), 
          title: '查看详情',
          class: 'action-btn'
        },
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
          title: '取消任务',
          class: 'action-btn'
        },
        { icon: () => h(NIcon, null, { default: () => h(StopOutlined) }) }
      );
      return h(NSpace, null, { default: () => [viewButton, cancelButton] });
    }
  }
]);

// --- Methods ---

// Fetching Data
const fetchTasks = async () => {
  loading.value = true;
  try {
    const response = await taskApi.getTasks();
    console.log('任务 API 响应:', response);

    const taskData = Array.isArray(response) ? response : (response?.data ?? []);

    tasks.value = taskData.map(task => ({
      ...task,
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
  } finally {
    loading.value = false;
    animatedProgress.value = {};
    addMockCompletedTasks();
    addMockActiveTasks(); // 添加模拟的活跃任务
  }
};

// 查看任务详情（现在直接更新详情面板而不是打开模态框）
const viewTaskDetails = (task) => {
  selectedTask.value = task;
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
    return format(new Date(dateTimeString), 'yyyy-MM-dd HH:mm:ss');
  } catch (e) {
    console.error("日期格式化错误:", e);
    return dateTimeString;
  }
};

const getStatusTagType = (status) => {
  if (!status) return 'default';
  const lowerStatus = status.toLowerCase();
  switch (lowerStatus) {
    case 'pending': return 'warning';
    case 'assigned': return 'info';
    case 'in_progress': return 'processing';
    case 'completed': return 'success';
    case 'failed': return 'error';
    case 'cancelled': return 'default';
    case 'surveillance': return 'success';
    case 'emergency': return 'error';
    default: return 'default';
  }
};

const getProgressStatus = (taskStatus) => {
  const lowerStatus = taskStatus?.toLowerCase();
  if (lowerStatus === 'failed') return 'error';
  if (lowerStatus === 'cancelled') return 'warning';
  if (lowerStatus === 'completed') return 'success';
  return 'info';
};

// 添加模拟活跃任务
const addMockActiveTasks = () => {
  // 只有当活跃任务数量少于一定数量时才添加模拟数据
  if (activeTasks.value.length < 5) {
    const currentDateTime = new Date();
    
    const mockActiveTasks = [
      {
        task_id: 'act-001',
        title: '商业区周边安全巡检',
        type: 'surveillance',
        status: 'in_progress',
        created_at: new Date(currentDateTime.getTime() - 45 * 60000).toISOString(),
        progress: 67,
        description: '对商业区周边进行安全巡检，确保区域安全，监控可疑活动',
        created_by: 'system',
        priority: 5,
        drone_details: [
          {
            drone_id: 'drone-3',
            name: '安防无人机03',
            status: 'flying'
          },
          {
            drone_id: 'drone-7',
            name: '高清摄像无人机02',
            status: 'flying'
          }
        ]
      },
      {
        task_id: 'act-002',
        title: '西区火情应急监控',
        type: 'emergency',
        status: 'in_progress',
        created_at: new Date(currentDateTime.getTime() - 30 * 60000).toISOString(),
        progress: 85,
        description: '西区工厂附近发生火情，无人机紧急出动监控火势发展，协助消防人员灭火',
        created_by: 'admin',
        priority: 9,
        drone_details: [
          {
            drone_id: 'drone-1',
            name: '消防无人机01',
            status: 'flying'
          }
        ]
      },
      {
        task_id: 'act-003',
        title: '北区学校周边安全巡检',
        type: 'surveillance',
        status: 'assigned',
        created_at: new Date(currentDateTime.getTime() - 20 * 60000).toISOString(),
        progress: 32,
        description: '对北区学校周边进行安全巡检，保障学生安全',
        created_by: 'system',
        priority: 6,
        drone_details: [
          {
            drone_id: 'drone-4',
            name: '安防无人机04',
            status: 'flying'
          }
        ]
      },
      {
        task_id: 'act-004',
        title: '商业中心停车场监控',
        type: 'surveillance',
        status: 'pending',
        created_at: new Date(currentDateTime.getTime() - 10 * 60000).toISOString(),
        progress: 12,
        description: '对商业中心停车场进行定期监控，防止车辆盗窃和破坏事件',
        created_by: 'admin',
        priority: 4,
        drone_details: [
          {
            drone_id: 'drone-8',
            name: '常规巡检无人机02',
            status: 'idle'
          }
        ]
      },
      {
        task_id: 'act-005',
        title: '东区交通事故现场勘查',
        type: 'emergency',
        status: 'in_progress',
        created_at: new Date(currentDateTime.getTime() - 55 * 60000).toISOString(),
        progress: 78,
        description: '东区主干道发生交通事故，无人机紧急出动协助交警勘查现场，疏导交通',
        created_by: 'system',
        priority: 8,
        drone_details: [
          {
            drone_id: 'drone-5',
            name: '交通无人机01',
            status: 'flying'
          },
          {
            drone_id: 'drone-6',
            name: '高清摄像无人机01',
            status: 'flying'
          }
        ]
      },
      {
        task_id: 'act-006',
        title: '城市公园巡检',
        type: 'surveillance',
        status: 'assigned',
        created_at: new Date(currentDateTime.getTime() - 15 * 60000).toISOString(),
        progress: 24,
        description: '对城市中央公园进行例行巡检，确保公共安全',
        created_by: 'admin',
        priority: 3,
        drone_details: [
          {
            drone_id: 'drone-9',
            name: '常规巡检无人机03',
            status: 'charging'
          }
        ]
      },
      {
        task_id: 'act-007',
        title: '南区医院周边防疫检查',
        type: 'surveillance',
        status: 'pending',
        created_at: new Date(currentDateTime.getTime() - 5 * 60000).toISOString(),
        progress: 5,
        description: '对南区医院周边进行防疫检查，监测人员聚集情况',
        created_by: 'system',
        priority: 5,
        drone_details: []
      },
      {
        task_id: 'act-008',
        title: '化工厂有毒气体泄漏响应',
        type: 'emergency',
        status: 'in_progress',
        created_at: new Date(currentDateTime.getTime() - 40 * 60000).toISOString(),
        progress: 62,
        description: '工业区化工厂报告可能存在有毒气体泄漏，无人机紧急出动进行空气采样和监测',
        created_by: 'admin',
        priority: 10,
        drone_details: [
          {
            drone_id: 'drone-10',
            name: '特种检测无人机01',
            status: 'flying'
          }
        ]
      },
      {
        task_id: 'act-009',
        title: '高速公路交通流量监测',
        type: 'surveillance',
        status: 'pending',
        created_at: new Date(currentDateTime.getTime() - 25 * 60000).toISOString(),
        progress: 8,
        description: '对城市周边高速公路进行交通流量监测，预防交通拥堵',
        created_by: 'system',
        priority: 4,
        drone_details: []
      }
    ];
    
    // 添加到当前任务列表
    tasks.value = [...tasks.value, ...mockActiveTasks];
    
    // 如果有任务，自动选择第一个任务显示详情
    if (tasks.value.length > 0 && !selectedTask.value) {
      selectedTask.value = tasks.value[0];
    }
  }
};

// 添加mock已完成任务
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
        priority: 8,
        drone_details: [
          {
            drone_id: 'drone-4',
            name: '交通监控无人机04',
            status: 'idle'
          }
        ]
      },
      {
        task_id: 'comp2',
        title: '仓库安全巡检',
        type: 'surveillance',
        status: 'completed',
        created_at: new Date(Date.now() - 5 * 24 * 60 * 60 * 1000).toISOString(),
        end_time: new Date(Date.now() - 4.5 * 24 * 60 * 60 * 1000).toISOString(),
        progress: 100,
        description: '完成了对中央仓储区的安全巡检，确认无安全隐患',
        created_by: 'admin',
        priority: 6,
        drone_details: [
          {
            drone_id: 'drone-7',
            name: '安防无人机07',
            status: 'idle'
          }
        ]
      },
      {
        task_id: 'fail1',
        title: '山区森林火灾救援',
        type: 'emergency',
        status: 'failed',
        created_at: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000).toISOString(),
        end_time: new Date(Date.now() - 2.8 * 24 * 60 * 60 * 1000).toISOString(),
        progress: 68,
        description: '由于恶劣天气条件，森林火灾救援任务被迫中断',
        created_by: 'admin',
        priority: 10,
        drone_details: [
          {
            drone_id: 'drone-1',
            name: '消防无人机01',
            status: 'maintenance'
          },
          {
            drone_id: 'drone-2',
            name: '消防无人机02',
            status: 'maintenance'
          }
        ]
      },
      {
        task_id: 'canc1',
        title: '城市绿化监测',
        type: 'surveillance',
        status: 'cancelled',
        created_at: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString(),
        end_time: new Date(Date.now() - 1.5 * 24 * 60 * 60 * 1000).toISOString(),
        progress: 43,
        description: '因资源调配需要，城市绿化监测任务被取消',
        created_by: 'admin',
        priority: 4,
        drone_details: [
          {
            drone_id: 'drone-9',
            name: '常规巡检无人机03',
            status: 'idle'
          }
        ]
      },
      {
        task_id: 'comp3',
        title: '工业园区安全检查',
        type: 'surveillance',
        status: 'completed',
        created_at: new Date(Date.now() - 4 * 24 * 60 * 60 * 1000).toISOString(),
        end_time: new Date(Date.now() - 3.7 * 24 * 60 * 60 * 1000).toISOString(),
        progress: 100,
        description: '完成了对工业园区的安全检查，记录并上报了潜在安全隐患',
        created_by: 'system',
        priority: 7,
        drone_details: [
          {
            drone_id: 'drone-5',
            name: '安防无人机05',
            status: 'idle'
          }
        ]
      },
      {
        task_id: 'comp4',
        title: '医院防疫巡检',
        type: 'surveillance',
        status: 'completed',
        created_at: new Date(Date.now() - 6 * 24 * 60 * 60 * 1000).toISOString(),
        end_time: new Date(Date.now() - 5.8 * 24 * 60 * 60 * 1000).toISOString(),
        progress: 100,
        description: '完成了市中心医院区域的防疫巡检，监测到的人员密度符合规定',
        created_by: 'admin',
        priority: 8,
        drone_details: [
          {
            drone_id: 'drone-6',
            name: '常规巡检无人机01',
            status: 'idle'
          }
        ]
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

<style scoped lang="postcss">
/* 只保留Tasks.vue特有的样式 */
.custom-table .n-data-table-tr {
  transition: all 0.2s ease;
}

.custom-table .n-data-table-tr:hover {
  transform: translateY(-1px);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.progress-wrapper {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
}

.progress-indicator {
  font-weight: bold;
  font-size: 12px;
  color: #e2e8f0;
  background-color: rgba(30, 41, 59, 0.8);
  padding: 1px 6px;
  border-radius: 10px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.3);
  min-width: 40px;
  text-align: center;
}

.action-btn {
  transition: all 0.2s ease;
  margin: 0 3px;
}

.action-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 2px 5px rgba(0,0,0,0.1);
}

pre {
  white-space: pre-wrap;
  word-wrap: break-word;
  max-height: 150px;
}

/* 自定义样式调整任务详情面板 */
.dark-theme-descriptions :deep(.n-descriptions-table-wrapper) {
  background-color: var(--bg-element) !important;
}

.dark-theme-descriptions :deep(.n-descriptions-table-header) {
  background-color: rgba(30, 41, 59, 0.8) !important;
}

.dark-theme-descriptions :deep(.n-descriptions-table-tbody) {
  background-color: rgba(30, 41, 59, 0.5) !important;
}

.dark-theme-descriptions :deep(.n-descriptions-table) {
  border-collapse: collapse;
  border-color: var(--border-color) !important;
}

.dark-theme-descriptions :deep(.n-descriptions-table-td) {
  background-color: rgba(30, 41, 59, 0.5) !important;
  border-color: var(--border-color) !important;
  color: var(--text-primary) !important;
}

.dark-theme-descriptions :deep(.n-descriptions-table-th) {
  background-color: rgba(30, 41, 59, 0.8) !important;
  border-color: var(--border-color) !important;
  color: var(--text-primary) !important;
}

/* 调整任务数据JSON预览区域样式 */
pre.dark-theme-override {
  background-color: rgba(15, 23, 42, 0.8);
  color: var(--text-primary);
  border: 1px solid var(--border-color);
}

/* 确保所有文本颜色在暗色主题下可见 */
.dark-text {
  color: var(--text-secondary) !important;
}

/* 强制覆盖任务详情表格的所有元素 */
.dark-theme-descriptions :deep(td),
.dark-theme-descriptions :deep(th),
.dark-theme-descriptions :deep(tr),
.dark-theme-descriptions :deep(table) {
  background-color: rgba(30, 41, 59, 0.5) !important;
  color: var(--text-primary) !important;
  border-color: var(--border-color) !important;
}
</style>