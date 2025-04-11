<template>
  <div class="h-full flex flex-col p-4">
    <div class="flex justify-between items-center mb-4">
      <h1 class="text-2xl font-bold">安防巡逻</h1>
      <div class="flex space-x-2">
        <n-button type="primary" @click="startPatrol" :loading="startingPatrol">
          <template #icon><n-icon><play-circle-outlined /></n-icon></template>
          开始巡逻
        </n-button>
        <n-button type="error" @click="stopPatrol" :disabled="!patrolActive">
          <template #icon><n-icon><stop-outlined /></n-icon></template>
          停止巡逻
        </n-button>
      </div>
    </div>
    
    <div class="grid grid-cols-12 gap-4 flex-1">
      <!-- 地图区域 -->
      <div class="col-span-8 card p-0 overflow-hidden rounded-lg shadow">
        <Map3D ref="mapRef" />
      </div>
      
      <!-- 信息面板 -->
      <div class="col-span-4 flex flex-col gap-4">
        <!-- 巡逻状态 -->
        <div class="bg-white p-4 rounded-lg shadow">
          <div class="flex justify-between items-center mb-4">
            <h3 class="text-lg font-medium">巡逻状态</h3>
            <n-tag :type="patrolActive ? 'success' : 'default'" size="small">
              {{ patrolActive ? '进行中' : '未开始' }}
            </n-tag>
          </div>
          <n-descriptions label-placement="left" :column="1" size="small">
            <n-descriptions-item label="区域覆盖率">
              <n-progress type="line" :percentage="areaCoverage" :indicator-placement="'inside'" :color="getUsageColor(areaCoverage)" />
            </n-descriptions-item>
            <n-descriptions-item label="巡逻时长">
              {{ patrolDuration }}
            </n-descriptions-item>
            <n-descriptions-item label="分配无人机">
              {{ assignedDrones.length }} 架
            </n-descriptions-item>
          </n-descriptions>
        </div>
        
        <!-- 安全事件 -->
        <div class="bg-white p-4 rounded-lg shadow flex-1 overflow-y-auto">
          <div class="flex justify-between items-center mb-4">
            <h3 class="text-lg font-medium">安全事件</h3>
            <n-button text size="small" type="primary" @click="viewAllEvents">查看全部</n-button>
          </div>
          <div v-if="securityEvents.length === 0" class="text-center text-gray-400 py-6">
            暂无安全事件
          </div>
          <n-timeline v-else>
            <n-timeline-item
              v-for="event in securityEvents"
              :key="event.id"
              :type="getEventType(event.severity)"
              :title="event.description"
              :time="formatTime(event.timestamp)"
            >
              <n-button text size="small" type="primary" @click="focusOnEvent(event)">
                查看位置
              </n-button>
            </n-timeline-item>
          </n-timeline>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue';
import { useRouter } from 'vue-router';
import { 
  NButton, 
  NTag, 
  NDescriptions, 
  NDescriptionsItem, 
  NProgress, 
  NTimeline, 
  NTimelineItem, 
  NIcon, 
  useNotification, 
  useMessage 
} from 'naive-ui';
import { PlayCircleOutlined, StopOutlined } from '@vicons/antd';
import { format, formatDistanceStrict } from 'date-fns';
import Map3D from '@/components/map/Map3D.vue';
import * as droneApi from '@/api/drone';

const notification = useNotification();
const message = useMessage();
const router = useRouter();

const mapRef = ref(null);
const patrolActive = ref(false);
const startingPatrol = ref(false);
const areaCoverage = ref(0);
const patrolDuration = ref('00:00:00');
const patrolTimer = ref(null);
const patrolStartTime = ref(null);
const assignedDrones = ref([]);
const securityEvents = ref([]);

const startPatrol = async () => {
  startingPatrol.value = true;
  try {
    // 获取可用的安防无人机
    const { data } = await droneApi.getDrones({ status: 'available', capability: 'security' });
    const securityDrones = data;
        
    if (securityDrones.length === 0) {
      notification.error({
        title: '错误',
        content: '没有可用的安防无人机进行巡逻',
        duration: 3000
      });
      return;
    }
        
    // 分配无人机 (最多3架)
    assignedDrones.value = securityDrones.slice(0, 3);
        
    // 启动巡逻计时器
    patrolActive.value = true;
    patrolStartTime.value = new Date();
    areaCoverage.value = 0; // 重置覆盖率
        
    patrolTimer.value = setInterval(() => {
      const now = new Date();
      patrolDuration.value = formatDistanceStrict(now, patrolStartTime.value, { unit: 'second' })
        .replace(' seconds', 's').replace(' minutes', 'm').replace(' hours', 'h'); // 简化显示
          
      // 模拟区域覆盖增长
      if (areaCoverage.value < 100) {
        areaCoverage.value = Math.min(100, areaCoverage.value + Math.random() * 1); // 随机增长
      }
    }, 1000);
        
    // 在地图上可视化巡逻路径 (如果Map3D组件支持)
    if (mapRef.value && mapRef.value.startDronePatrol) {
      mapRef.value.startDronePatrol(assignedDrones.value);
    }
        
    notification.success({
      title: '成功',
      content: `安防巡逻已开始，分配了 ${assignedDrones.value.length} 架无人机`,
      duration: 3000
    });
  } catch (error) {
    console.error('启动巡逻失败:', error);
    notification.error({
      title: '错误',
      content: '启动安防巡逻失败',
      duration: 3000
    });
  } finally {
    startingPatrol.value = false;
  }
};

const stopPatrol = () => {
  if (patrolActive.value) {
    clearInterval(patrolTimer.value);
    patrolActive.value = false;
    patrolTimer.value = null;
        
    // 在地图上停止无人机 (如果Map3D组件支持)
    if (mapRef.value && mapRef.value.stopDronePatrol) {
      mapRef.value.stopDronePatrol(assignedDrones.value.map(d => d.id));
    }
        
    notification.info({
      title: '信息',
      content: '安防巡逻已停止',
      duration: 3000
    });
    // 重置状态
    patrolDuration.value = '00:00:00';
    assignedDrones.value = [];
    // areaCoverage 保留最后的值或重置
  }
};
    
const getEventType = (severity) => {
  switch(severity) {
    case 'high': return 'error';
    case 'medium': return 'warning';
    default: return 'info';
  }
};

const formatTime = (timestamp) => {
  try {
    return format(new Date(timestamp), 'yyyy-MM-dd HH:mm:ss');
  } catch (e) {
    return timestamp; // Fallback
  }
};
    
const focusOnEvent = (event) => {
  if (mapRef.value && mapRef.value.flyTo && event.coordinates) {
    mapRef.value.flyTo(event.coordinates);
    message.info(`聚焦事件: ${event.description}`);
  } else {
    message.warning('无法在地图上定位此事件');
  }
};

const viewAllEvents = () => {
  router.push('/events'); // 假设事件列表页路由为/events
};

const getUsageColor = (usage) => {
  if (usage < 70) return '#18A058'; // success
  if (usage < 90) return '#F0A020'; // warning
  return '#D03050'; // error
};
    
// 模拟安全事件数据
const mockSecurityEvents = () => {
  securityEvents.value = [
    {
      id: 'evt-sec-1',
      description: '在禁区检测到未经授权的人员',
      severity: 'high',
      timestamp: new Date(Date.now() - 5 * 60 * 1000).toISOString(),
      coordinates: { lat: 39.905, lng: 116.39, alt: 100 }
    },
    {
      id: 'evt-sec-2',
      description: '围栏附近检测到异常活动',
      severity: 'medium',
      timestamp: new Date(Date.now() - 15 * 60 * 1000).toISOString(),
      coordinates: { lat: 39.91, lng: 116.38, alt: 0 }
    },
    {
      id: 'evt-sec-3',
      description: '完成例行巡逻区域A',
      severity: 'low',
      timestamp: new Date(Date.now() - 30 * 60 * 1000).toISOString(),
      coordinates: null // 有些事件可能没有具体坐标
    }
  ];
};

onMounted(() => {
  mockSecurityEvents();
});

onUnmounted(() => {
  // 组件卸载时停止计时器
  if (patrolTimer.value) {
    clearInterval(patrolTimer.value);
  }
});

</script>

<style scoped>
/* 保持原有样式或根据需要调整 */
.security-container {
  height: 100%;
  display: flex;
  flex-direction: column;
}
.card {
  background-color: #fff;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}
</style> 