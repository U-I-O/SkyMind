<template>
  <div class="task-list-container">
    <div class="list-header">
      <h3 class="text-lg font-medium">巡逻任务</h3>
      <div class="flex items-center">
        <n-select
          :value="filter"
          :options="filterOptions"
          size="small"
          style="width: 100px"
          @update:value="handleFilterChange"
        />
        <n-button text size="small" type="primary" class="ml-2" @click="refreshTasks">
          刷新
        </n-button>
      </div>
    </div>
    
    <!-- 加载错误提示 -->
    <div v-if="loadError" class="text-center py-4">
      <n-alert type="error">
        加载任务失败，请
        <n-button text type="primary" @click="refreshTasks">重试</n-button>
      </n-alert>
    </div>
    
    <!-- 认证错误提示 -->
    <div v-else-if="authError" class="text-center py-4">
      <n-alert type="error">
        认证失败，请
        <n-button text type="primary" @click="goToLogin">重新登录</n-button>
      </n-alert>
    </div>
    
    <!-- 加载状态 -->
    <div v-else-if="loading" class="text-center py-4">
      <n-spin size="small" />
      <p class="text-xs text-gray-500 mt-2">加载中...</p>
    </div>
    
    <!-- 空状态 -->
    <div v-else-if="patrolTasks.length === 0" class="text-center text-gray-400 py-6">
      暂无巡逻任务
    </div>
    
    <!-- 任务列表 -->
    <div v-else class="task-list">
      <div
        v-for="task in patrolTasks"
        :key="task.task_id || task.id"
        class="task-item mb-3"
        :class="[
          getTaskStatusClass(task.status),
          { 'active-card': activeTaskCard === (task.task_id || task.id) }
        ]"
        @click="handleTaskClick(task)"
      >
        <div class="task-item-header">
          <div class="task-title">{{ task.title || '未命名任务' }}</div>
          <n-tag :type="getTaskStatusType(task.status)" size="small" class="status-tag">
            <template #icon>
              <n-icon :component="getTaskStatusIcon(task.status)" />
            </template>
            {{ getTaskStatusText(task.status) }}
          </n-tag>
        </div>
        
        <div class="task-desc">{{ task.description || '无描述' }}</div>
        
        <div class="task-meta">
          <div class="flex justify-between items-center mb-1">
            <span class="font-medium text-xs flex items-center">
              <n-icon class="mr-1" size="14">
                <calendar-icon />
              </n-icon>
              执行:
            </span> 
            <span class="text-xs">
              {{ isWeeklySchedule(task.schedule?.type) ? '每周重复' : 
                (task.schedule?.type === 'date' ? '指定日期 ' + formatDateShort(task.schedule?.date) : 
                getScheduleTypeText(task.schedule?.type)) }}
            </span>
          </div>
          
          <div v-if="isWeeklySchedule(task.schedule?.type)" class="weekday-container mb-1">
            <div 
              v-for="(day, index) in [0, 1, 2, 3, 4, 5, 6]" 
              :key="day"
              class="weekday-item"
              :class="{ 'active': isWeekdayActive(task.schedule?.weekdays, day) }"
            >
              {{ getWeekdayShortName(day) }}
            </div>
          </div>
          
          <div class="flex justify-between items-center mb-1">
            <span class="font-medium text-xs flex items-center">
              <n-icon class="mr-1" size="14">
                <time-icon />
              </n-icon>
              时间:
            </span>
            <span class="text-xs">{{ task.schedule?.time || '未指定' }}</span>
          </div>

          
          <div class="flex justify-between items-center mb-1">
            <span class="font-medium text-xs flex items-center">
              <n-icon class="mr-1" size="14">
                <drone-icon />
              </n-icon>
              无人机:
            </span>
            <n-tooltip trigger="hover">
              <template #trigger>
                <span class="text-xs truncate max-w-[120px] inline-block">
                  {{ getDroneNames(task.assigned_drones) }}
                </span>
              </template>
              {{ getDroneNames(task.assigned_drones) }}
            </n-tooltip>
          </div>
          <div class="flex justify-between items-center">
            <span class="font-medium text-xs flex items-center">
              <n-icon class="mr-1" size="14">
                <created-icon />
              </n-icon>
              创建于:
            </span>
            <span class="text-xs">{{ formatTimeShort(task.created_at) }}</span>
          </div>
        </div>
        
        <div class="task-actions">
          <n-button size="tiny" quaternary @click.stop="handleTaskClick(task)">
            查看详情
          </n-button>
          
          <template v-if="task.status === 'pending' || task.status === 'cancelled'">
            <n-button 
              size="tiny" 
              type="primary" 
              class="action-btn"
              @click.stop="handleStartTask(task)"
            >
              开始任务
            </n-button>
          </template>
          
          <template v-else-if="task.status === 'in_progress'">
            <n-button 
              size="tiny" 
              type="error" 
              class="action-btn"
              @click.stop="handleStopTask(task)"
            >
              取消任务
            </n-button>
          </template>
          
          <template v-else-if="task.status === 'paused'">
            <n-button 
              size="tiny" 
              type="primary" 
              class="action-btn"
              @click.stop="handleResumeTask(task)"
            >
              恢复任务
            </n-button>
          </template>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { NButton, NTag, NSelect, NSpin, NAlert, NIcon, NTooltip } from 'naive-ui';
import { ref, computed, onMounted, onBeforeUnmount, inject } from 'vue';
import { format } from 'date-fns';
import { getAllSurveillanceTasks } from '@/api/task';
import { useRouter } from 'vue-router';
import { useUserStore } from '@/store/userStore';
import { 
  PlayCircleOutline as PlayIcon, 
  PauseCircleOutline as PauseIcon, 
  CheckmarkCircleOutline as CompleteIcon, 
  CloseCircleOutline as CancelIcon, 
  TimeOutline as PendingIcon,
  AlertCircleOutline as FailedIcon,
  CalendarOutline as CalendarIcon,
  AirplaneOutline as DroneIcon,
  LocationOutline as AreaIcon,
  AlarmOutline as TimeIcon,
  FlagOutline as PriorityIcon,
  CalendarClearOutline as CreatedIcon,
  PlayForwardOutline as NextIcon
} from '@vicons/ionicons5';

// 状态
const loading = ref(false);
const tasks = ref([]);
const filter = ref('all');
const refreshInterval = ref(null);
const authError = ref(false);
const loadError = ref(false);
const activeTaskCard = inject('activeTaskCard', ref(null));

const filterOptions = [
  { label: '全部', value: 'all' },
  { label: '进行中', value: 'in_progress' },
  { label: '待执行', value: 'pending' },
  { label: '已完成', value: 'completed' }
];

const emit = defineEmits(['filter-change', 'open-detail', 'stop-task', 'start-task', 'resume-task']);

const router = useRouter();
const userStore = useUserStore();

// 筛选巡逻任务
const patrolTasks = computed(() => {
  if (!tasks.value || tasks.value.length === 0) {
    console.info('无任务数据或数组为空');
    return [];
  }
  
  // console.info(`筛选前总任务数: ${tasks.value.length}`);
  
  // 不再需要筛选type，后端已经只返回surveillance类型
  let filteredTasks = tasks.value;
  
  if (filter.value !== 'all') {
    filteredTasks = filteredTasks.filter(task => task.status === filter.value);
    console.info(`按状态 ${filter.value} 筛选后: ${filteredTasks.length} 个任务`);
  }
  
  return filteredTasks;
});

// 加载任务列表
const loadTasks = async () => {
  // console.info('开始加载巡逻任务列表...');
  loading.value = true;
  authError.value = false;
  loadError.value = false;
  
  try {
    const taskList = await getAllSurveillanceTasks();
    
    // 检查数据结构
    if (taskList && taskList.length > 0) {
      // console.info('获取到任务总数:', taskList.length);
      // console.info('第一个任务数据示例:', {
      //   id: taskList[0].id,
      //   task_id: taskList[0].task_id,
      //   title: taskList[0].title,
      //   type: taskList[0].type,
      //   status: taskList[0].status
      // });
    } else {
      console.info('返回的任务列表为空');
    }
    
    tasks.value = taskList;
    // console.info(`任务列表已更新，共 ${tasks.value.length} 个任务`);
  } catch (error) {
    console.error('加载巡逻任务失败:', error);
    loadError.value = true;
    tasks.value = [];
  } finally {
    loading.value = false;
  }
};

// 刷新任务
const refreshTasks = () => {
  loadTasks();
};

// 处理筛选变更
const handleFilterChange = (value) => {
  filter.value = value;
  emit('filter-change', value);
};

// 处理任务点击
const handleTaskClick = (task) => {
  emit('open-detail', task);
};

// 处理停止任务
const handleStopTask = (task) => {
  emit('stop-task', task);
};

// 处理开始任务
const handleStartTask = (task) => {
  emit('start-task', task);
};

// 处理恢复任务
const handleResumeTask = (task) => {
  emit('resume-task', task);
};

// 跳转到登录页
const goToLogin = async () => {
  await userStore.logout();
  router.push('/login');
};

// 组件挂载时加载任务
onMounted(() => {
  loadTasks();
  // 设置自动刷新（每60秒）
  refreshInterval.value = setInterval(loadTasks, 60000);
});

// 组件卸载前清除定时器
onBeforeUnmount(() => {
  if (refreshInterval.value) {
    clearInterval(refreshInterval.value);
  }
});

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

const getTaskStatusIcon = (status) => {
  const statusIconMap = {
    'pending': PendingIcon,
    'in_progress': PlayIcon,
    'completed': CompleteIcon,
    'cancelled': CancelIcon,
    'failed': FailedIcon,
    'paused': PauseIcon
  };
  return statusIconMap[status] || PendingIcon;
};

const getTaskStatusClass = (status) => {
  const statusClassMap = {
    'pending': 'status-pending',
    'in_progress': 'status-active',
    'completed': 'status-completed',
    'cancelled': 'status-cancelled',
    'failed': 'status-failed',
    'paused': 'status-paused'
  };
  return statusClassMap[status] || '';
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

const getPriorityText = (priority) => {
  const priorityMap = {
    1: '低',
    2: '中',
    3: '高',
    4: '紧急',
    5: '最高'
  };
  return priorityMap[priority] || priority || '默认';
};

const getPriorityClass = (priority) => {
  const priorityClassMap = {
    1: 'text-gray-500',
    2: 'text-blue-500',
    3: 'text-green-500',
    4: 'text-orange-500',
    5: 'text-red-500'
  };
  return priorityClassMap[priority] || '';
};

const getScheduleTypeText = (type) => {
  const typeMap = {
    'once': '一次性',
    'daily': '每日重复',
    'week': '每周重复',
    'weekly': '每周重复',
    'monthly': '每月重复'
  };
  return typeMap[type] || '一次性';
};

const formatWeekdaysAndTime = (schedule) => {
  if (!schedule) return '无计划';
  
  const type = schedule.type || 'once';
  
  switch (type) {
    case 'once':
      return schedule.time ? schedule.time : '未指定时间';
    case 'daily':
      return schedule.time || '未指定时间';
    case 'weekly':
      const weekdays = schedule.weekdays || [];
      const weekdayNames = {
        0: '周日', 1: '周一', 2: '周二', 3: '周三', 
        4: '周四', 5: '周五', 6: '周六'
      };
      return weekdays.map(day => weekdayNames[day]).join('、') + (schedule.time ? ` ${schedule.time}` : '');
    default:
      return '未指定时间';
  }
};

const formatScheduleTime = (schedule) => {
  if (!schedule) return '无计划';
  
  const type = schedule.type || 'once';
  
  switch (type) {
    case 'once':
      return schedule.date && schedule.time 
        ? `${schedule.date} ${schedule.time}` 
        : '未指定时间';
    case 'daily':
      return schedule.time || '未指定时间';
    case 'weekly':
      const weekdays = schedule.weekdays || [];
      const weekdayNames = {
        0: '周日', 1: '周一', 2: '周二', 3: '周三', 
        4: '周四', 5: '周五', 6: '周六'
      };
      const days = weekdays.map(day => weekdayNames[day]).join(',');
      return days + (schedule.time ? ` ${schedule.time}` : '');
    default:
      return '未指定时间';
  }
};

const getDroneNames = (droneIds) => {
  if (!droneIds || !Array.isArray(droneIds) || droneIds.length === 0) {
    return '未分配';
  }
  
  // 这里应该根据droneIds获取无人机名称
  // 简单处理：直接显示ID
  return droneIds.map(id => `无人机 ${id.substring(0, 4)}`).join(', ');
};

const formatTimeShort = (timestamp) => {
  try {
    return format(new Date(timestamp), 'MM-dd HH:mm');
  } catch (e) {
    return timestamp;
  }
};

const formatTime = (timestamp) => {
  try {
    return format(new Date(timestamp), 'yyyy-MM-dd HH:mm:ss');
  } catch (e) {
    return timestamp;
  }
};

const getWeekdayShortName = (day) => {
  const names = ['日', '一', '二', '三', '四', '五', '六'];
  return names[day];
};

const isWeekdayActive = (weekdays, day) => {
  if (!weekdays || !Array.isArray(weekdays)) return false;
  return weekdays.includes(day);
};

const formatNextExecution = (task) => {
  if (!task || !task.schedule) return '未计划';
  
  if (task.status === 'completed' || task.status === 'cancelled') {
    return '已结束';
  }
  
  // 示例格式化，实际应根据业务逻辑计算下次执行时间
  if (task.next_execution) {
    return formatTimeShort(task.next_execution);
  }
  
  // 模拟计算下次执行时间
  if (task.schedule.type === 'weekly' && Array.isArray(task.schedule.weekdays) && task.schedule.time) {
    const now = new Date();
    const currentDay = now.getDay();
    const nextDays = task.schedule.weekdays.filter(day => day > currentDay);
    
    if (nextDays.length > 0) {
      // 找到当周的下一个执行日
      const nextDay = Math.min(...nextDays);
      const daysToAdd = nextDay - currentDay;
      const nextDate = new Date(now);
      nextDate.setDate(now.getDate() + daysToAdd);
      
      // 格式化日期为 MM-DD
      const month = String(nextDate.getMonth() + 1).padStart(2, '0');
      const day = String(nextDate.getDate()).padStart(2, '0');
      
      return `${month}-${day} ${task.schedule.time}`;
    } else if (task.schedule.weekdays.length > 0) {
      // 找到下周的第一个执行日
      const nextDay = Math.min(...task.schedule.weekdays);
      const daysToAdd = 7 - currentDay + nextDay;
      const nextDate = new Date(now);
      nextDate.setDate(now.getDate() + daysToAdd);
      
      // 格式化日期为 MM-DD
      const month = String(nextDate.getMonth() + 1).padStart(2, '0');
      const day = String(nextDate.getDate()).padStart(2, '0');
      
      return `${month}-${day} ${task.schedule.time}`;
    }
  }
  
  return '未确定';
};

const isWeeklySchedule = (type) => {
  // 处理可能的不同命名：'week'/'weekly'
  return type === 'week' || type === 'weekly';
};

// 添加格式化日期的函数
const formatDateShort = (dateStr) => {
  if (!dateStr) return '';
  try {
    return format(new Date(dateStr), 'MM-dd');
  } catch (e) {
    return dateStr;
  }
};
</script>

<style scoped>
.task-list-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
}

.list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-bottom: 12px;
  margin-bottom: 8px;
  border-bottom: 1px solid var(--border-color);
}

.task-list {
  flex: 1;
  overflow-y: auto;
  padding-right: 4px;
}

/* 自定义滚动条 */
.task-list {
  scrollbar-width: thin;
  scrollbar-color: rgba(51, 65, 85, 0.7) rgba(15, 23, 42, 0.3);
}

.task-list::-webkit-scrollbar {
  width: 4px;
}

.task-list::-webkit-scrollbar-track {
  background: rgba(15, 23, 42, 0.3);
  border-radius: 3px;
}

.task-list::-webkit-scrollbar-thumb {
  background-color: rgba(51, 65, 85, 0.7);
  border-radius: 3px;
}

.task-list::-webkit-scrollbar-thumb:hover {
  background-color: rgba(59, 130, 246, 0.7);
}

.task-item {
  padding: 12px;
  border-radius: 8px;
  background-color: var(--bg-element);
  transition: all 0.2s ease;
  cursor: pointer;
  position: relative;
  overflow: hidden;
  border: 1px solid transparent;
}

.task-item:hover {
  background-color: var(--bg-card-hover);
  transform: translateY(-2px);
  border-color: var(--border-color);
}

.task-item-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.task-title {
  font-weight: 600;
  font-size: 14px;
  line-height: 1.2;
  margin-right: 8px;
}

.task-desc {
  font-size: 12px;
  margin-bottom: 8px;
  color: var(--text-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.task-meta {
  background-color: rgba(0, 0, 0, 0.05);
  padding: 8px;
  border-radius: 6px;
  margin-bottom: 8px;
  font-size: 12px;
}

.task-meta .n-icon {
  color: var(--text-secondary);
}

.task-actions {
  display: flex;
  justify-content: flex-end;
  margin-top: 8px;
  gap: 8px;
}

/* 按钮样式 */
.action-btn {
  background-color: var(--btn-primary-bg) !important;
  border: 1px solid var(--btn-primary-border) !important;
}

.action-btn:hover {
  background-color: var(--btn-primary-hover-bg) !important;
  border: 1px solid white !important;
}

/* 任务状态样式 */
.status-pending {
  border-left: 3px solid #2080f0;
}

.status-in-progress {
  border-left: 3px solid #18a058;
}

.status-completed {
  border-left: 3px solid #63e2b7;
}

.status-cancelled {
  border-left: 3px solid #d03050;
}

.status-failed {
  border-left: 3px solid #d03050;
}

.status-paused {
  border-left: 3px solid #f0a020;
}

.active-card {
  box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.5);
  border-color: var(--highlight-color);
}

/* 周选择器样式 */
.weekday-container {
  display: flex;
  justify-content: space-between;
  margin-top: 2px;
}

.weekday-item {
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 10px;
  border-radius: 50%;
  background-color: rgba(0, 0, 0, 0.1);
  color: var(--text-secondary);
}

.weekday-item.active {
  background-color: rgba(59, 130, 246, 0.2);
  color: var(--highlight-color);
  font-weight: 600;
}
</style> 