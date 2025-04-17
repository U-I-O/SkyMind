<template>
  <div class="info-card custom-scrollbar">
    <div class="flex justify-between items-center mb-4">
      <h3 class="text-lg font-medium event-header">安全事件</h3>
      <n-button text size="small" type="primary" class="view-all-btn" @click="$emit('view-all')">
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
        :color="getSeverityColor(event.severity)"
        class="timeline-item"
        @click="$emit('open-detail', event)"
      >
        <template #icon>
          <div class="severity-icon" :class="getSeverityClass(event.severity)">
            <n-icon size="18">
              <component :is="getSeverityIcon(event.severity)" />
            </n-icon>
          </div>
        </template>
        
        <div class="event-content">
          <div class="event-header-row">
            <div class="event-title">{{ event.title }}</div>
            <n-tag size="small" :type="getEventType(event.severity)" class="severity-tag">
              {{ getSeverityText(event.severity) }}
            </n-tag>
          </div>
          
          <div class="event-description">{{ event.description }}</div>
          
          <div class="event-meta">
            <div class="event-time">
              <n-icon size="14" class="mr-1">
                <clock-icon />
              </n-icon>
              {{ formatTime(event.timestamp) }}
            </div>
            
            <div class="event-location" v-if="event.location">
              <n-icon size="14" class="mr-1">
                <location-icon />
              </n-icon>
              {{ event.location }}
            </div>
          </div>
          
          <div class="event-actions">
            <n-button 
              text 
              size="small" 
              type="primary" 
              class="action-btn"
              @click.stop="$emit('focus-event', event)"
            >
              <n-icon size="14" class="mr-1">
                <location-icon />
              </n-icon>
              查看位置
            </n-button>
            
            <n-button 
              text 
              size="small" 
              type="info" 
              class="action-btn"
              @click.stop="$emit('open-detail', event)"
            >
              <n-icon size="14" class="mr-1">
                <detail-icon />
              </n-icon>
              详情
            </n-button>
          </div>
        </div>
      </n-timeline-item>
    </n-timeline>
  </div>
</template>



<script setup>
import { h, ref } from 'vue';
import { NButton, NTimeline, NTimelineItem, NTag, NIcon } from 'naive-ui';
import { format } from 'date-fns';
import { 
  AlarmOutline as AlarmIcon,
  WarningOutline as WarningIcon,
  InformationCircleOutline as InfoIcon,
  TimeOutline as ClockIcon,
  LocationOutline as LocationIcon,
  DocumentTextOutline as DetailIcon
} from '@vicons/ionicons5';
import { defaultEvents } from '../security/security-events';
const props = defineProps({
  events: {
    type: Array,
    default: () => defaultEvents
  }
});

defineEmits(['view-all', 'open-detail', 'focus-event']);

// 获取事件类型
const getEventType = (severity) => {
  const typeMap = {
    'high': 'error',
    'medium': 'warning',
    'low': 'info'
  };
  return typeMap[severity] || 'default';
};

// 获取事件严重程度对应的显示文字
const getSeverityText = (severity) => {
  const textMap = {
    'high': '紧急',
    'medium': '警告',
    'low': '提示'
  };
  return textMap[severity] || '未知';
};

// 获取事件严重程度对应的图标
const getSeverityIcon = (severity) => {
  const iconMap = {
    'high': AlarmIcon,
    'medium': WarningIcon,
    'low': InfoIcon
  };
  return iconMap[severity] || InfoIcon;
};

// 获取事件严重程度对应的颜色
const getSeverityColor = (severity) => {
  const colorMap = {
    'high': '#e11d48',
    'medium': '#fb923c',
    'low': '#38bdf8'
  };
  return colorMap[severity] || '#38bdf8';
};

// 获取事件严重程度对应的类名
const getSeverityClass = (severity) => {
  return `severity-${severity}`;
};

// 格式化时间
const formatTime = (timestamp) => {
  try {
    if (typeof timestamp === 'string' && !timestamp.includes('T')) {
      // 如果是已格式化的字符串，直接返回
      return timestamp;
    }
    return format(new Date(timestamp), 'yyyy-MM-dd HH:mm:ss');
  } catch (e) {
    return timestamp;
  }
};
</script>

<style scoped>
.info-card {
  background-color: var(--bg-card);
  backdrop-filter: blur(8px);
  border-radius: 0.5rem;
  padding: 1rem;
  box-shadow: var(--card-shadow);
  max-height: calc(50vh - 2rem);
  overflow-y: auto;
  color: var(--text-primary);
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.event-header {
  font-weight: 600;
  letter-spacing: 0.5px;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.5);
}

.view-all-btn {
  opacity: 0.8;
  transition: opacity 0.2s;
  font-weight: 500;
}

.view-all-btn:hover {
  opacity: 1;
}

.n-timeline {
  padding: 8px 4px;
}

.timeline-item {
  position: relative;
  margin-bottom: 16px;
  transition: all 0.3s;
}

.event-content {
  background-color: rgba(30, 41, 59, 0.5);
  border-radius: 8px;
  padding: 12px;
  margin-left: 8px;
  border: 1px solid rgba(255, 255, 255, 0.05);
  transition: all 0.3s;
}

.timeline-item:hover .event-content {
  background-color: rgba(40, 51, 69, 0.8);
  border-color: rgba(255, 255, 255, 0.15);
  transform: translateX(2px);
}

.severity-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background-color: rgba(0, 0, 0, 0.3);
  box-shadow: 0 0 10px rgba(0, 0, 0, 0.2), 0 0 0 2px rgba(255, 255, 255, 0.1);
}

.severity-high {
  background-color: rgba(225, 29, 72, 0.8);
  box-shadow: 0 0 10px rgba(225, 29, 72, 0.6), 0 0 0 2px rgba(225, 29, 72, 0.4);
  animation: pulsate 2s infinite;
}

.severity-medium {
  background-color: rgba(251, 146, 60, 0.8);
  box-shadow: 0 0 10px rgba(251, 146, 60, 0.5), 0 0 0 2px rgba(251, 146, 60, 0.3);
}

.severity-low {
  background-color: rgba(56, 189, 248, 0.8);
  box-shadow: 0 0 5px rgba(56, 189, 248, 0.4), 0 0 0 2px rgba(56, 189, 248, 0.2);
}

@keyframes pulsate {
  0% {
    box-shadow: 0 0 10px rgba(225, 29, 72, 0.6), 0 0 0 2px rgba(225, 29, 72, 0.4);
  }
  50% {
    box-shadow: 0 0 15px rgba(225, 29, 72, 0.8), 0 0 0 3px rgba(225, 29, 72, 0.6);
  }
  100% {
    box-shadow: 0 0 10px rgba(225, 29, 72, 0.6), 0 0 0 2px rgba(225, 29, 72, 0.4);
  }
}

.event-header-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.event-title {
  font-weight: 600;
  font-size: 14px;
  color: var(--text-primary);
  text-shadow: 0 1px 1px rgba(0, 0, 0, 0.5);
}

.severity-tag {
  font-size: 10px;
  font-weight: 600;
  padding: 0 6px;
  border-radius: 10px;
  letter-spacing: 0.5px;
}

.event-description {
  font-size: 12px;
  color: var(--text-secondary);
  margin-bottom: 8px;
  line-height: 1.4;
}

.event-meta {
  display: flex;
  font-size: 11px;
  color: var(--text-muted);
  margin-bottom: 10px;
  gap: 12px;
}

.event-time, .event-location {
  display: flex;
  align-items: center;
}

.mr-1 {
  margin-right: 4px;
}

.event-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

.action-btn {
  font-size: 12px;
  font-weight: 500;
  display: flex;
  align-items: center;
  background-color: rgba(30, 41, 59, 0.7) !important;
  border: 1px solid rgba(255, 255, 255, 0.1) !important;
  border-radius: 4px;
  padding: 2px 8px !important;
  transition: all 0.2s;
}

.action-btn:hover {
  background-color: rgba(51, 65, 85, 0.9) !important;
  border: 1px solid rgba(255, 255, 255, 0.2) !important;
}
</style>