<template>
  <div class="h-full p-4">
    <div class="floating-card bg-white bg-opacity-95 mb-4">
      <div class="flex justify-between items-center">
        <div class="flex items-center">
          <n-button @click="goBack" class="mr-3">
            <template #icon>
              <n-icon><arrow-left-outlined /></n-icon>
            </template>
            返回
          </n-button>
          <h1 class="text-2xl font-bold">{{ drone?.name || '无人机详情' }}</h1>
        </div>
        <n-tag v-if="drone" :type="getStatusType(drone.status)" size="large">{{ getStatusText(drone.status) }}</n-tag>
      </div>
    </div>

    <div v-if="loading" class="flex justify-center items-center h-64">
      <n-spin size="large" />
    </div>

    <div v-else-if="!drone" class="floating-card bg-white bg-opacity-95 p-8 text-center">
      <n-result status="404" title="无人机未找到" description="无法找到该无人机的信息">
        <template #footer>
          <n-button @click="goBack">返回无人机列表</n-button>
        </template>
      </n-result>
    </div>

    <div v-else class="grid grid-cols-12 gap-4">
      <!-- 左侧详情 -->
      <div class="col-span-4">
        <div class="floating-card bg-white bg-opacity-95 mb-4">
          <h2 class="text-lg font-bold mb-4">基本信息</h2>
          <n-descriptions bordered :column="1" label-placement="left">
            <n-descriptions-item label="ID">{{ drone.drone_id }}</n-descriptions-item>
            <n-descriptions-item label="名称">{{ drone.name }}</n-descriptions-item>
            <n-descriptions-item label="型号">{{ drone.model }}</n-descriptions-item>
            <n-descriptions-item label="状态">
              <n-tag :type="getStatusType(drone.status)">{{ getStatusText(drone.status) }}</n-tag>
            </n-descriptions-item>
            <n-descriptions-item label="电池电量">
              <n-progress type="line" :percentage="drone.battery_level" :indicator-placement="'inside'" :color="getBatteryColor(drone.battery_level)" />
              {{ drone.battery_level }}%
            </n-descriptions-item>
            <n-descriptions-item label="相机">
              {{ drone.camera_equipped ? '已装备' : '未装备' }}
            </n-descriptions-item>
            <n-descriptions-item label="最大载重">
              {{ drone.payload_capacity }} kg
            </n-descriptions-item>
          </n-descriptions>
        </div>

        <div class="floating-card bg-white bg-opacity-95">
          <h2 class="text-lg font-bold mb-4">性能参数</h2>
          <n-descriptions bordered :column="1" label-placement="left">
            <n-descriptions-item label="最大飞行时间">{{ drone.max_flight_time }} 分钟</n-descriptions-item>
            <n-descriptions-item label="最大速度">{{ drone.max_speed }} m/s</n-descriptions-item>
            <n-descriptions-item label="最大高度">{{ drone.max_altitude }} 米</n-descriptions-item>
            <n-descriptions-item label="当前位置">
              经度: {{ getCoordinateLng(drone.current_location, drone) }}°<br/>
              纬度: {{ getCoordinateLat(drone.current_location, drone) }}°
            </n-descriptions-item>
          </n-descriptions>
        </div>
      </div>

      <!-- 中间任务统计 -->
      <div class="col-span-4">
        <div class="floating-card bg-white bg-opacity-95 mb-4">
          <h2 class="text-lg font-bold mb-4">任务统计</h2>
          <div class="grid grid-cols-2 gap-4 mb-4">
            <div class="bg-blue-50 p-3 rounded-lg text-center">
              <div class="text-2xl font-bold text-blue-500">{{ droneStats.totalMissions || 0 }}</div>
              <div class="text-sm text-gray-500">总任务数</div>
            </div>
            <div class="bg-green-50 p-3 rounded-lg text-center">
              <div class="text-2xl font-bold text-green-500">{{ droneStats.completedMissions || 0 }}</div>
              <div class="text-sm text-gray-500">完成任务</div>
            </div>
            <div class="bg-yellow-50 p-3 rounded-lg text-center">
              <div class="text-2xl font-bold text-yellow-500">{{ droneStats.totalFlightHours || 0 }}</div>
              <div class="text-sm text-gray-500">飞行小时</div>
            </div>
            <div class="bg-purple-50 p-3 rounded-lg text-center">
              <div class="text-2xl font-bold text-purple-500">{{ droneStats.totalDistance || 0 }}</div>
              <div class="text-sm text-gray-500">总飞行距离(km)</div>
            </div>
          </div>
        </div>

        <div class="floating-card bg-white bg-opacity-95">
          <h2 class="text-lg font-bold mb-4">当前任务</h2>
          <div v-if="currentTask" class="p-4 border border-blue-200 rounded-lg bg-blue-50">
            <div class="font-bold mb-2">{{ currentTask.title }}</div>
            <div class="text-sm text-gray-600 mb-2">{{ currentTask.description }}</div>
            <n-progress type="line" :percentage="currentTask.progress" :processing="true" />
            <div class="flex justify-between text-xs text-gray-500 mt-2">
              <div>开始: {{ formatDate(currentTask.start_time) }}</div>
              <div>预计完成: {{ formatDate(currentTask.estimated_end_time) }}</div>
            </div>
          </div>
          <div v-else class="p-4 text-center text-gray-400">
            当前无任务
          </div>
        </div>
      </div>

      <!-- 右侧控制面板 -->
      <div class="col-span-4">
        <div class="floating-card bg-white bg-opacity-95 mb-4">
          <h2 class="text-lg font-bold mb-4">控制面板</h2>
          <div class="grid grid-cols-2 gap-3">
            <n-button type="primary" :disabled="drone.status !== 'idle'" @click="handleTakeoff">
              <template #icon><n-icon><rocket-outlined /></n-icon></template>
              起飞
            </n-button>
            <n-button type="warning" :disabled="drone.status !== 'flying'" @click="handleLand">
              <template #icon><n-icon><download-outlined /></n-icon></template>
              降落
            </n-button>
            <n-button :disabled="drone.status !== 'flying'" @click="handleReturnHome">
              <template #icon><n-icon><home-outlined /></n-icon></template>
              返航
            </n-button>
            <n-button type="error" :disabled="drone.status !== 'flying'" @click="handleEmergencyStop">
              <template #icon><n-icon><stop-outlined /></n-icon></template>
              紧急停止
            </n-button>
          </div>

          <div class="mt-4" v-if="drone.status === 'flying'">
            <h3 class="font-bold mb-2">飞行参数</h3>
            <div class="grid grid-cols-2 gap-4 mb-3">
              <div>
                <div class="text-sm text-gray-500 mb-1">目标经度</div>
                <n-input-number v-model:value="targetLongitude" clearable />
              </div>
              <div>
                <div class="text-sm text-gray-500 mb-1">目标纬度</div>
                <n-input-number v-model:value="targetLatitude" clearable />
              </div>
            </div>
            <div class="grid grid-cols-2 gap-4 mb-3">
              <div>
                <div class="text-sm text-gray-500 mb-1">目标高度 (米)</div>
                <n-input-number v-model:value="targetAltitude" clearable :min="0" :max="drone.max_altitude" />
              </div>
              <div>
                <div class="text-sm text-gray-500 mb-1">飞行速度 (m/s)</div>
                <n-input-number v-model:value="flightSpeed" clearable :min="1" :max="drone.max_speed" />
              </div>
            </div>
            <n-button class="w-full" type="primary" @click="handleMoveTo">
              前往目标位置
            </n-button>
          </div>
        </div>

        <div class="floating-card bg-white bg-opacity-95">
          <h2 class="text-lg font-bold mb-4">维护信息</h2>
          <n-descriptions bordered :column="1" label-placement="left">
            <n-descriptions-item label="上次维护">{{ drone.last_maintenance_date || '无记录' }}</n-descriptions-item>
            <n-descriptions-item label="下次维护">{{ drone.next_maintenance_date || '无记录' }}</n-descriptions-item>
            <n-descriptions-item label="总飞行次数">{{ drone.total_flights || 0 }} 次</n-descriptions-item>
            <n-descriptions-item label="累计飞行时间">{{ drone.total_flight_time || 0 }} 小时</n-descriptions-item>
          </n-descriptions>
          <div class="mt-4">
            <n-button class="w-full" :disabled="drone.status === 'maintenance'" @click="scheduleMaintenence">
              <template #icon><n-icon><tool-outlined /></n-icon></template>
              安排维护
            </n-button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, reactive } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useMessage } from 'naive-ui';
import { format } from 'date-fns';
import { 
  ArrowLeftOutlined, 
  RocketOutlined,
  DownloadOutlined,
  HomeOutlined,
  StopOutlined,
  ToolOutlined
} from '@vicons/antd';
import { getDroneById, controlDrone } from '../api/drone';

const route = useRoute();
const router = useRouter();
const message = useMessage();

// 状态变量
const loading = ref(true);
const drone = ref(null);
const currentTask = ref(null);
const droneStats = reactive({
  totalMissions: 0,
  completedMissions: 0,
  totalFlightHours: 0,
  totalDistance: 0
});

// 飞行参数
const targetLongitude = ref(114.367044);
const targetLatitude = ref(30.545212);
const targetAltitude = ref(100);
const flightSpeed = ref(10);

// 获取无人机详情
async function fetchDroneDetail() {
  loading.value = true;
  try {
    const droneId = route.params.id;
    const response = await getDroneById(droneId);
    drone.value = response;
    
    // 模拟统计数据 - 实际应从API获取
    droneStats.totalMissions = Math.floor(Math.random() * 50) + 10;
    droneStats.completedMissions = Math.floor(droneStats.totalMissions * 0.8);
    droneStats.totalFlightHours = Math.floor(Math.random() * 200) + 30;
    droneStats.totalDistance = Math.floor(Math.random() * 500) + 100;
    
    // 如果无人机处于飞行状态，模拟当前任务
    if (drone.value?.status === 'flying') {
      currentTask.value = {
        title: '巡逻任务 #' + Math.floor(Math.random() * 1000),
        description: '对指定区域进行安全巡逻',
        progress: Math.floor(Math.random() * 100),
        start_time: new Date(Date.now() - 60 * 60 * 1000),
        estimated_end_time: new Date(Date.now() + 60 * 60 * 1000)
      };
    }
  } catch (error) {
    console.error('获取无人机详情失败:', error);
    message.error('获取无人机详情失败');
  } finally {
    loading.value = false;
  }
}

// 获取经度
function getCoordinateLng(geoPoint, drone) {
  // 如果有实际坐标，则使用实际坐标
  if (geoPoint && geoPoint.coordinates) {
    return geoPoint.coordinates[0].toFixed(6);
  }
  
  // 如果没有坐标，返回默认值
  return '114.367044';
}

// 获取纬度
function getCoordinateLat(geoPoint, drone) {
  // 如果有实际坐标，则使用实际坐标
  if (geoPoint && geoPoint.coordinates) {
    return geoPoint.coordinates[1].toFixed(6);
  }
  
  // 如果没有坐标，返回默认值
  return '30.545212';
}

// 根据状态获取标签类型
function getStatusType(status) {
  switch (status) {
    case 'idle': return 'default'
    case 'flying': return 'info'
    case 'charging': return 'warning'
    case 'maintenance': return 'warning'
    case 'offline': return 'error'
    default: return 'default'
  }
}

// 获取状态文本
function getStatusText(status) {
  const statusMap = {
    'idle': '待命',
    'flying': '飞行中',
    'charging': '充电中',
    'maintenance': '维护中',
    'offline': '离线',
    'error': '故障'
  };
  return statusMap[status] || status;
}

// 格式化日期
function formatDate(date) {
  return format(new Date(date), 'yyyy-MM-dd HH:mm');
}

// 获取电池颜色
function getBatteryColor(level) {
  if (level <= 20) return '#ef4444';
  if (level <= 50) return '#f59e0b';
  return '#10b981';
}

// 控制操作
function handleTakeoff() {
  message.info(`正在指令${drone.value.name}起飞`);
  controlDrone(drone.value.drone_id, 'takeoff')
    .then(() => {
      message.success('起飞指令已发送');
      drone.value.status = 'flying';
    })
    .catch(error => {
      message.error('发送起飞指令失败');
    });
}

function handleLand() {
  message.info(`正在指令${drone.value.name}降落`);
  controlDrone(drone.value.drone_id, 'land')
    .then(() => {
      message.success('降落指令已发送');
      drone.value.status = 'idle';
      currentTask.value = null;
    })
    .catch(error => {
      message.error('发送降落指令失败');
    });
}

function handleReturnHome() {
  message.info(`正在指令${drone.value.name}返航`);
  controlDrone(drone.value.drone_id, 'return_home')
    .then(() => {
      message.success('返航指令已发送');
    })
    .catch(error => {
      message.error('发送返航指令失败');
    });
}

function handleEmergencyStop() {
  message.info(`正在指令${drone.value.name}紧急停止`);
  controlDrone(drone.value.drone_id, 'emergency_stop')
    .then(() => {
      message.success('紧急停止指令已发送');
      drone.value.status = 'idle';
      currentTask.value = null;
    })
    .catch(error => {
      message.error('发送紧急停止指令失败');
    });
}

function handleMoveTo() {
  message.info(`正在指令${drone.value.name}移动到指定位置`);
  controlDrone(drone.value.drone_id, 'move_to', {
    longitude: targetLongitude.value,
    latitude: targetLatitude.value,
    altitude: targetAltitude.value,
    speed: flightSpeed.value
  })
    .then(() => {
      message.success('移动指令已发送');
    })
    .catch(error => {
      message.error('发送移动指令失败');
    });
}

function scheduleMaintenence() {
  message.info(`正在为${drone.value.name}安排维护`);
  controlDrone(drone.value.drone_id, 'maintenance')
    .then(() => {
      message.success('维护已安排');
      drone.value.status = 'maintenance';
      currentTask.value = null;
    })
    .catch(error => {
      message.error('安排维护失败');
    });
}

// 返回上一页
function goBack() {
  router.push('/drones');
}

// 在组件挂载时获取详情
onMounted(() => {
  fetchDroneDetail();
});
</script>

<style scoped>
.floating-card {
  padding: 1rem;
  border-radius: 0.5rem;
  box-shadow: 0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
  backdrop-filter: blur(4px);
  z-index: 100;
}
</style> 