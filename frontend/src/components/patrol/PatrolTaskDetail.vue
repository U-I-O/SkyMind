<template>
  <div class="patrol-task-detail">
    <n-tabs type="line" animated>
      <n-tab-pane name="basic" tab="基本信息">
        <n-descriptions :column="1" bordered>
          <n-descriptions-item label="任务名称">
            {{ task.name }}
          </n-descriptions-item>
          <n-descriptions-item label="创建时间">
            {{ formatTime(task.createTime) }}
          </n-descriptions-item>
          <n-descriptions-item label="任务状态">
            <n-tag :type="getTaskStatusType(task.status)">
              {{ getTaskStatusText(task.status) }}
            </n-tag>
          </n-descriptions-item>
          <n-descriptions-item label="巡逻高度">
            {{ task.altitude }} 米
          </n-descriptions-item>
          <n-descriptions-item label="巡逻速度">
            {{ task.speed }} 米/秒
          </n-descriptions-item>
          <n-descriptions-item label="巡逻模式">
            {{ task.mode === 'single' ? '单次巡逻' : '循环巡逻' }}
          </n-descriptions-item>
        </n-descriptions>
      </n-tab-pane>

      <n-tab-pane name="drones" tab="执行无人机">
        <n-list bordered>
          <n-list-item v-for="droneId in task.drones" :key="droneId">
            <n-thing>
              <template #header>
                无人机 {{ droneId }}
              </template>
              <template #description>
                <n-space>
                  <n-button size="small" @click="$emit('focus-on-drone', droneId)">
                    查看位置
                  </n-button>
                  <n-button size="small" type="warning">
                    召回
                  </n-button>
                </n-space>
              </template>
            </n-thing>
          </n-list-item>
        </n-list>
      </n-tab-pane>

      <n-tab-pane name="waypoints" tab="巡逻路径">
        <div class="waypoints-map">
          <n-button 
            size="small" 
            type="primary" 
            @click="$emit('show-on-map', task)"
          >
            在地图上显示
          </n-button>
          <n-table :bordered="false" :single-line="false">
            <thead>
              <tr>
                <th>序号</th>
                <th>经度</th>
                <th>纬度</th>
                <th>高度</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(point, index) in task.waypoints" :key="index">
                <td>{{ index + 1 }}</td>
                <td>{{ point.lng }}</td>
                <td>{{ point.lat }}</td>
                <td>{{ point.altitude }}米</td>
              </tr>
            </tbody>
          </n-table>
        </div>
      </n-tab-pane>
    </n-tabs>

    <div class="detail-actions">
      <n-space justify="end">
        <n-button @click="$emit('close')">关闭</n-button>
        <n-button 
          v-if="task.status === 'stopped'"
          type="primary"
          @click="$emit('resume-task', task)"
        >
          恢复任务
        </n-button>
        <n-button 
          v-if="task.status === 'active'"
          type="error"
          @click="$emit('stop-task', task)"
        >
          停止任务
        </n-button>
      </n-space>
    </div>
  </div>
</template>

<script setup>
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
  NTable
} from 'naive-ui';
import { format } from 'date-fns';

const props = defineProps({
  task: {
    type: Object,
    required: true
  }
});

defineEmits(['close', 'stop-task', 'resume-task', 'focus-on-drone', 'show-on-map']);

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
.patrol-task-detail {
  padding: 16px;
}

.waypoints-map {
  margin-top: 12px;
}

.detail-actions {
  margin-top: 24px;
  padding-top: 16px;
  border-top: 1px solid #eee;
}
</style>