<template>
  <div class="info-card">
    <div class="flex justify-between items-center mb-4">
      <h3 class="text-lg font-medium">安全事件</h3>
      <n-button text size="small" type="primary" @click="$emit('view-all')">
        查看全部
      </n-button>
    </div>
    <div v-if="events.length === 0" class="text-center text-gray-400 py-6">
      暂无安全事件
    </div>
    <n-timeline v-else>
      <n-timeline-item
        v-for="event in events"
        :key="event.id"
        :type="getEventType(event.severity)"
        :title="event.description"
        :time="formatTime(event.timestamp)"
        @click="$emit('open-detail', event)"
      >
        <n-button 
          text 
          size="small" 
          type="primary" 
          @click.stop="$emit('focus-event', event)"
        >
          查看位置
        </n-button>
      </n-timeline-item>
    </n-timeline>
  </div>
</template>

<script setup>
import { NButton, NTimeline, NTimelineItem } from 'naive-ui';
import { format } from 'date-fns';

defineProps({
  events: {
    type: Array,
    default: () => []
  }
});

defineEmits(['view-all', 'open-detail', 'focus-event']);

const getEventType = (severity) => {
  const typeMap = {
    'high': 'error',
    'medium': 'warning',
    'low': 'info'
  };
  return typeMap[severity] || 'default';
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

.n-timeline {
  padding: 8px;
}

.n-timeline-item {
  cursor: pointer;
  padding: 8px;
  border-radius: 4px;
  transition: background-color 0.3s;
}

.n-timeline-item:hover {
  background-color: rgba(0, 0, 0, 0.05);
}
</style>