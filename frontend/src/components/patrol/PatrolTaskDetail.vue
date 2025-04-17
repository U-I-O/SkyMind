<template>
  <div class="patrol-task-detail">
    <!-- 加载状态 -->
    <div v-if="loading" class="text-center py-8 animate-pulse">
      <n-spin size="medium" />
      <p class="text-sm text-gray-500 mt-4">加载任务详情中...</p>
    </div>
    
    <!-- 详情内容 -->
    <div v-else class="fade-in">
      <n-tabs type="line" animated>
        <n-tab-pane name="basic" tab="基本信息">
          <div class="grid grid-cols-1 gap-2">
            <div class="detail-row">
              <div class="detail-label">任务标题</div>
              <div class="detail-value">{{ task.title }}</div>
            </div>
            <div class="detail-row">
              <div class="detail-label">任务描述</div>
              <div class="detail-value">{{ task.description }}</div>
            </div>
            <div class="detail-row">
              <div class="detail-label">任务ID</div>
              <div class="detail-value">{{ task.task_id }}</div>
            </div>
            <div class="detail-row">
              <div class="detail-label">任务类型</div>
              <div class="detail-value">{{ getTaskTypeText(task.type) }}</div>
            </div>
            <div class="detail-row">
              <div class="detail-label">创建时间</div>
              <div class="detail-value">{{ formatTime(task.created_at) }}</div>
            </div>
            <div class="detail-row">
              <div class="detail-label">创建者</div>
              <div class="detail-value">{{ task.created_by }}</div>
            </div>
            <div class="detail-row">
              <div class="detail-label">任务状态</div>
              <div class="detail-value">
                <n-tag :type="getTaskStatusType(task.status)">
                  {{ getTaskStatusText(task.status) }}
                </n-tag>
              </div>
            </div>
            <div class="detail-row">
              <div class="detail-label">巡逻高度</div>
              <div class="detail-value">{{ task.altitude }} 米</div>
            </div>
            <div class="detail-row">
              <div class="detail-label">巡逻速度</div>
              <div class="detail-value">{{ task.speed }} 米/秒</div>
            </div>
            <div class="detail-row">
              <div class="detail-label">巡逻轮次</div>
              <div class="detail-value">{{ task.rounds }} 次</div>
            </div>
            <div class="detail-row">
              <div class="detail-label">优先级</div>
              <div class="detail-value">{{ task.priority }}</div>
            </div>
          </div>
        </n-tab-pane>
        
        <n-tab-pane name="schedule" tab="计划调度">
          <div v-if="task.schedule" class="grid grid-cols-1 gap-2">
            <div class="detail-row">
              <div class="detail-label">执行模式</div>
              <div class="detail-value">
                <n-tag :type="getScheduleTypeStyle(task.schedule.type)">
                  {{ getScheduleTypeText(task.schedule.type) }}
                </n-tag>
              </div>
            </div>
            
            <!-- 指定日期模式 (date) -->
            <div v-if="task.schedule.type === 'date'" class="detail-row">
              <div class="detail-label">执行日期</div>
              <div class="detail-value">{{ task.schedule.date ? formatDate(task.schedule.date) : '未指定' }}</div>
            </div>
            
            <!-- 每周重复模式 (week/weekly) -->
            <div v-if="isWeeklySchedule(task.schedule.type)" class="detail-row">
              <div class="detail-label">执行日</div>
              <div class="detail-value">
                <n-space>
                  <n-tag 
                    v-for="day in task.schedule.weekdays" 
                    :key="day" 
                    size="small"
                    type="success"
                  >
                    {{ getWeekdayText(day) }}
                  </n-tag>
                </n-space>
                <span v-if="!task.schedule.weekdays || task.schedule.weekdays.length === 0" class="text-gray-400">
                  未指定
                </span>
              </div>
            </div>
            
            <!-- 所有模式都需要时间（除了单次执行） -->
            <div v-if="task.schedule.type !== 'once'" class="detail-row">
              <div class="detail-label">执行时间</div>
              <div class="detail-value">{{ task.schedule.time || '未指定' }}</div>
            </div>
            
            <!-- 单次执行模式 (once) -->
            <div v-if="task.schedule.type === 'once'" class="detail-row">
              <div class="detail-label">执行方式</div>
              <div class="detail-value">
                <n-tag type="warning">需要在任务列表中手动触发执行</n-tag>
              </div>
            </div>
            
            <!-- 下次执行时间预估 -->
            <div v-if="task.schedule.type !== 'once'" class="detail-row">
              <div class="detail-label">下次执行</div>
              <div class="detail-value">{{ getNextExecutionTime() }}</div>
            </div>
          </div>
          <div v-else class="text-center text-gray-400 py-4">
            无计划调度信息
          </div>
        </n-tab-pane>
        
        <n-tab-pane name="drones" tab="执行无人机">
          <div v-if="task.assigned_drones && task.assigned_drones.length > 0">
            <n-list>
              <n-list-item v-for="drone in task.assigned_drones" :key="drone">
                <n-thing>
                  <template #header>
                    {{ drone }}
                  </template>
                  <template #description>
                    <n-button 
                      size="small" 
                      text 
                      type="primary"
                      @click="$emit('focus-on-drone', drone)"
                    >
                      在地图上显示
                    </n-button>
                  </template>
                </n-thing>
              </n-list-item>
            </n-list>
          </div>
          <div v-else class="text-center text-gray-400 py-4">
            暂无指派的无人机
          </div>
        </n-tab-pane>
        
        <n-tab-pane name="events" tab="相关事件">
          <div v-if="task.related_events && task.related_events.length > 0">
            <n-list>
              <n-list-item v-for="event in task.related_events" :key="event.id">
                <n-thing :title="event.title || '未命名事件'">
                  <template #description>
                    {{ event.description || '无描述' }}
                  </template>
                </n-thing>
              </n-list-item>
            </n-list>
          </div>
          <div v-else class="text-center text-gray-400 py-4">
            暂无相关事件
          </div>
        </n-tab-pane>
        
        <n-tab-pane name="patrol_area" tab="巡逻区域">
          <div v-if="task.patrol_area && task.patrol_area.coordinates" class="patrol-area-map">
            <n-table :bordered="false">
              <thead>
                <tr>
                  <th>顶点序号</th>
                  <th>经度</th>
                  <th>纬度</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(point, index) in getPatrolAreaCoordinates" :key="index">
                  <td>{{ index + 1 }}</td>
                  <td>{{ point?.[0] !== undefined ? point[0].toFixed(4) : '0.0000' }}</td>
                  <td>{{ point?.[1] !== undefined ? point[1].toFixed(4) : '0.0000' }}</td>
                </tr>
              </tbody>
            </n-table>
          </div>
          <div v-else class="text-center text-gray-400 py-4">
            无巡逻区域数据
          </div>
        </n-tab-pane>
      </n-tabs>

      <div class="detail-actions">
        <n-space justify="end">
          <!-- 编辑模式下显示取消按钮 -->
          <template v-if="props.isEditMode">
            <n-button 
              secondary
              @click="$emit('cancel-edit')"
            >
              <template #icon>
                <n-icon><close-icon /></n-icon>
              </template>
              取消修改
            </n-button>
          </template>
          
          <!-- 非编辑模式下的按钮 -->
          <template v-else>
            <!-- 通用操作按钮 -->
            <n-button 
              secondary
              @click="$emit('show-on-map', task.patrol_area)"
              v-if="task.patrol_area && task.patrol_area.coordinates"
            >
              <template #icon>
                <n-icon><environment-icon /></n-icon>
              </template>
              高亮显示区域
            </n-button>

            <n-button 
              secondary
              @click="$emit('edit-task', task)"
              v-if="task.status === 'pending' || task.status === 'cancelled'"
            >
              <template #icon>
                <n-icon><edit-icon /></n-icon>
              </template>
              修改任务
            </n-button>

            <n-button 
              secondary
              type="error"
              @click="confirmDelete"
            >
              <template #icon>
                <n-icon><delete-icon /></n-icon>
              </template>
              删除任务
            </n-button>

            <n-divider vertical style="height: 24px" />

            <!-- 状态相关操作按钮 -->
            <n-button 
              v-if="task.status === 'pending' || task.status === 'cancelled'"
              type="primary"
              @click="$emit('start-task', task)"
            >
              开始任务
            </n-button>
            <n-button 
              v-if="task.status === 'in_progress'"
              type="error"
              @click="$emit('stop-task', task)"
            >
              停止任务
            </n-button>
            <n-button
              v-if="task.status === 'paused'"
              type="success"
              @click="$emit('resume-task', task)"
            >
              恢复任务
            </n-button>
          </template>
        </n-space>
      </div>
    </div>

    <!-- 添加删除确认对话框 -->
    <n-modal
      v-model:show="showDeleteConfirm"
      preset="dialog"
      title="确认删除"
      positive-text="确认"
      negative-text="取消"
      @positive-click="handleDelete"
      @negative-click="cancelDelete"
    >
      <template #default>
        <div>确定要删除任务"{{ task.title }}"吗？此操作不可撤销。</div>
      </template>
    </n-modal>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue';
import { getPatrolTaskById } from '@/api/task';
import { 
  NTabs,
  NTabPane,
  NDescriptions,
  NDescriptionsItem,
  NTag,
  NList,
  NListItem,
  NThing,
  NSpace,
  NButton,
  NTable,
  NSpin,
  NModal,
  NIcon,
  NDivider,
  useMessage
} from 'naive-ui';
import { format } from 'date-fns';
import { 
  EnvironmentOutlined as EnvironmentIcon,
  EditOutlined as EditIcon,
  DeleteOutlined as DeleteIcon,
  CloseOutlined as CloseIcon
} from '@vicons/antd';

const props = defineProps({
  taskId: {
    type: String,
    default: ''
  },
  task: {
    type: Object,
    default: () => ({})
  },
  isEditMode: {
    type: Boolean,
    default: false
  }
});

const loading = ref(false);
const taskData = ref(props.task || {});

const message = useMessage();
const showDeleteConfirm = ref(false);

// 加载任务详情
const loadTaskDetail = async (id) => {
  if (!id) return;
  
  loading.value = true;
  try {
    const response = await getPatrolTaskById(id);
    console.info('加载任务详情成功:', response);
    taskData.value = response;
  } catch (error) {
    console.error('加载巡逻任务详情失败:', error);
  } finally {
    loading.value = false;
  }
};

// 监听 taskId 变化
watch(() => props.taskId, (newId) => {
  if (newId) {
    loadTaskDetail(newId);
  }
}, { immediate: true });

// 监听 task 变化，更新内部数据
watch(() => props.task, (newTask) => {
  if (newTask && Object.keys(newTask).length > 0) {
    // 添加短暂的加载动画
    loading.value = true;
    setTimeout(() => {
      taskData.value = newTask;
      loading.value = false;
    }, 300); // 300毫秒的加载动画，足够让用户感知到切换
  }
}, { immediate: true });

// 计算属性获取任务数据
const task = computed(() => {
  return Object.keys(taskData.value).length > 0 ? taskData.value : props.task;
});

// 获取巡逻区域坐标
const getPatrolAreaCoordinates = computed(() => {
  if (task.value?.patrol_area?.coordinates) {
    // 如果是多边形，coordinates[0]是外环
    if (Array.isArray(task.value.patrol_area.coordinates[0])) {
      return task.value.patrol_area.coordinates[0];
    }
    // 单点的情况
    return [task.value.patrol_area.coordinates];
  }
  return [];
});

const emit = defineEmits(['close', 'stop-task', 'start-task', 'resume-task', 'focus-on-drone', 'show-on-map', 'edit-task', 'delete-task', 'cancel-edit']);

const getTaskStatusType = (status) => {
  const statusMap = {
    'pending': 'default',
    'in_progress': 'success',
    'completed': 'info',
    'cancelled': 'warning',
    'failed': 'error',
    'paused': 'warning'
  };
  return statusMap[status] || 'default';
};

const getTaskStatusText = (status) => {
  const statusMap = {
    'pending': '待执行',
    'in_progress': '进行中',
    'completed': '已完成',
    'cancelled': '已取消',
    'failed': '执行失败',
    'paused': '已暂停'
  };
  return statusMap[status] || '未知状态';
};

const getTaskTypeText = (type) => {
  const typeMap = {
    'surveillance': '监控巡逻',
    'transport': '物资运输',
    'inspection': '设备巡检',
    'emergency': '应急处置'
  };
  return typeMap[type] || type || '未知类型';
};

const formatTime = (timestamp) => {
  try {
    return format(new Date(timestamp), 'yyyy-MM-dd HH:mm:ss');
  } catch (e) {
    return timestamp || '未设置';
  }
};

const formatDate = (dateStr) => {
  try {
    return format(new Date(dateStr), 'yyyy-MM-dd');
  } catch (e) {
    return dateStr || '未设置';
  }
};

const getScheduleTypeText = (type) => {
  const typeMap = {
    'once': '单次执行',
    'date': '指定日期',
    'week': '每周重复',
    'weekly': '每周重复'
  };
  return typeMap[type] || type || '未知类型';
};

const getScheduleTypeStyle = (type) => {
  const styleMap = {
    'once': 'default',
    'date': 'info',
    'week': 'success',
    'weekly': 'success'
  };
  return styleMap[type] || 'default';
};

const getWeekdayText = (day) => {
  const weekdayMap = {
    0: '周日',
    1: '周一',
    2: '周二',
    3: '周三',
    4: '周四',
    5: '周五',
    6: '周六'
  };
  return weekdayMap[day] || `未知(${day})`;
};

const getNextExecutionTime = () => {
  try {
    // 如果是date类型，直接返回日期+时间
    if (task.value.schedule.type === 'date' && task.value.schedule.date) {
      const date = new Date(task.value.schedule.date);
      if (task.value.schedule.time) {
        const [hours, minutes] = task.value.schedule.time.split(':').map(Number);
        date.setHours(hours, minutes);
      }
      return format(date, 'yyyy-MM-dd HH:mm');
    }
    
    // 如果是week类型，计算下一个执行日
    if (isWeeklySchedule(task.value.schedule.type) && task.value.schedule.weekdays && task.value.schedule.weekdays.length > 0) {
      const today = new Date();
      const todayWeekday = today.getDay(); // 0-6, 0是周日
      const weekdays = task.value.schedule.weekdays.map(Number).sort((a, b) => a - b);
      
      // 找出下一个执行日
      let nextWeekday = weekdays.find(day => day > todayWeekday);
      if (!nextWeekday) nextWeekday = weekdays[0]; // 如果这周没有了，就取下周的第一天
      
      // 计算日期差
      const daysToAdd = nextWeekday > todayWeekday 
        ? nextWeekday - todayWeekday 
        : 7 - todayWeekday + nextWeekday;
      
      const nextDate = new Date(today);
      nextDate.setDate(today.getDate() + daysToAdd);
      
      // 设置时间
      if (task.value.schedule.time) {
        const [hours, minutes] = task.value.schedule.time.split(':').map(Number);
        nextDate.setHours(hours, minutes);
      }
      
      return format(nextDate, 'yyyy-MM-dd HH:mm');
    }
    
    return '无法计算';
  } catch (e) {
    console.error('计算下次执行时间出错:', e);
    return '计算错误';
  }
};

// 判断是否为周重复模式
const isWeeklySchedule = (type) => {
  return type === 'week' || type === 'weekly';
};

// 显示删除确认对话框
const confirmDelete = () => {
  showDeleteConfirm.value = true;
};

// 处理删除操作
const handleDelete = () => {
  // 由父组件处理实际删除操作
  console.log('删除任务:', task.value);
  message.info('正在删除任务...');
  emit('delete-task', task.value);
  showDeleteConfirm.value = false;
};

// 取消删除
const cancelDelete = () => {
  showDeleteConfirm.value = false;
};
</script>

<style scoped>
.patrol-task-detail {
  width: 100%;
  height: 100%;
  overflow-y: auto;
  color: var(--text-primary);
}

.fade-in {
  animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.detail-row {
  display: flex;
  padding: 8px 0;
  border-bottom: 1px solid var(--border-color);
}

.detail-label {
  flex: 0 0 90px;
  font-weight: 500;
  color: var(--text-secondary);
}

.detail-value {
  flex: 1;
}

.patrol-area-map {
  height: 300px;
  margin-top: 1rem;
  border-radius: 4px;
  overflow: hidden;
  border: 1px solid var(--border-color);
}

.detail-actions {
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid var(--border-color);
}

.patrol-task-detail {
  scrollbar-width: thin;
  scrollbar-color: rgba(51, 65, 85, 0.7) rgba(15, 23, 42, 0.3);
}

.patrol-task-detail::-webkit-scrollbar {
  width: 4px;
}

.patrol-task-detail::-webkit-scrollbar-track {
  background: rgba(15, 23, 42, 0.3);
  border-radius: 3px;
}

.patrol-task-detail::-webkit-scrollbar-thumb {
  background-color: rgba(51, 65, 85, 0.7);
  border-radius: 3px;
}

.patrol-task-detail::-webkit-scrollbar-thumb:hover {
  background-color: rgba(59, 130, 246, 0.7);
}
</style> 