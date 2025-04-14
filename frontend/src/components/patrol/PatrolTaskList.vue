<template>
  <div class="info-card">
    <div class="flex justify-between items-center mb-4">
      <h3 class="text-lg font-medium">巡逻任务</h3>
      <n-select
        :value="filter"
        :options="filterOptions"
        size="small"
        style="width: 100px"
        @update:value="$emit('filter-change', $event)"
      />
    </div>
    
    <div v-if="tasks.length === 0" class="text-center text-gray-400 py-6">
      暂无巡逻任务
    </div>
    <div v-else class="task-list">
      <n-card
        v-for="task in tasks"
        :key="task.id"
        class="mb-4 task-card"
        :class="{ 'active-task': task.status === 'active' }"
        size="small"
        @click="$emit('open-detail', task)"
      >
        <div class="flex justify-between items-start">
          <div>
            <div class="font-medium">{{ task.name }}</div>
            <div class="text-xs text-gray-500 mt-1">
              创建时间：{{ formatTime(task.createTime) }}
            </div>
          </div>
          <n-tag :type="getTaskStatusType(task.status)" size="small">
            {{ getTaskStatusText(task.status) }}
          </n-tag>
        </div>
        <div class="text-xs text-gray-500 mt-2">
          执行无人机：{{ task.drones.length }} 架
        </div>
        <div class="flex justify-end mt-2 space-x-2">
          <n-button size="tiny" @click.stop="$emit('open-detail', task)">
            查看详情
          </n-button>
          <n-button 
            size="tiny" 
            type="error" 
            v-if="task.status === 'active'"
            @click.stop="$emit('stop-task', task)"
          >
            停止任务
          </n-button>
        </div>
      </n-card>
    </div>
  </div>
</template>

<script setup>
import { NCard, NButton, NTag, NSelect } from 'naive-ui';
import { format } from 'date-fns';

const props = defineProps({
  tasks: {
    type: Array,
    default: () => []
  },
  filter: {
    type: String,
    required: true
  },
  filterOptions: {
    type: Array,
    required: true
  }
});

defineEmits(['filter-change', 'open-detail', 'stop-task']);

const getTaskStatusType = (status) => {
  const statusMap = {
    'active': 'success',
    'completed': 'info',
    'stopped': 'warning',
    'failed': 'error'
  };
  return statusMap[status] || 'default';
};

const getTaskStatusText = (status) => {
  const statusMap = {
    'active': '进行中',
    'completed': '已完成',
    'stopped': '已停止',
    'failed': '执行失败'
  };
  return statusMap[status] || '未知状态';
};

const formatTime = (timestamp) => {
  try {
    return format(new Date(timestamp), 'yyyy-MM-dd HH:mm:ss');
  } catch (e) {
    return timestamp;
  }
};
</script>

<style scoped>
.info-card {
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(8px);
  border-radius: 0.5rem;
  padding: 1rem;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  max-height: calc(50vh - 2rem);
  overflow-y: auto;
}

.task-list {
  max-height: 400px;
  overflow-y: auto;
}

.task-card {
  cursor: pointer;
  transition: all 0.3s ease;
}

.task-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.active-task {
  border-left: 4px solid var(--success-color);
}

.space-x-2 > * + * {
  margin-left: 0.5rem;
}
</style>