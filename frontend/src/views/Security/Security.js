import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { NButton, NModal, useMessage } from 'naive-ui';
import Map3D from '@/components/map/Map3D.vue';
import PatrolTaskList from '@/components/patrol/PatrolTaskList.vue';
import PatrolTaskCreator from '@/components/patrol/PatrolTaskCreator.vue';
import PatrolTaskDetail from '@/components/patrol/PatrolTaskDetail.vue';
import SecurityEventList from '@/components/security/SecurityEventList.vue';

export default {
  name: 'SecurityView',
  components: {
    Map3D,
    NButton,
    NModal,
    PatrolTaskList,
    PatrolTaskCreator,
    PatrolTaskDetail,
    SecurityEventList
  },

  setup() {
    const router = useRouter();
    const message = useMessage();
    const mapRef = ref(null);
    const showPatrolCreator = ref(false);
    const showTaskDetail = ref(false);
    const patrolCreatorRef = ref(null);
    const currentTask = ref(null);

    // 模拟数据
    const tasks = ref([
      {
        id: 'task-001',
        name: '园区东南角巡逻',
        status: 'active',
        createTime: new Date().toISOString(),
        drones: ['drone-001', 'drone-002'],
        altitude: 100,
        speed: 5,
        mode: 'loop',
        waypoints: [
          { lng: 114.367, lat: 30.54, altitude: 100 },
          { lng: 114.368, lat: 30.542, altitude: 100 },
          { lng: 114.366, lat: 30.538, altitude: 100 }
        ]
      },
      {
        id: 'task-002',
        name: '西区围栏检查',
        status: 'stopped',
        createTime: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
        drones: ['drone-003'],
        altitude: 80,
        speed: 4,
        mode: 'single',
        waypoints: [
          { lng: 114.365, lat: 30.535, altitude: 80 },
          { lng: 114.366, lat: 30.536, altitude: 80 }
        ]
      }
    ]);

    const securityEvents = ref([
      {
        id: 'event-001',
        description: '发现可疑人员聚集',
        severity: 'high',
        timestamp: new Date().toISOString(),
        location: { lng: 114.367, lat: 30.54 },
        status: 'unhandled'
      },
      {
        id: 'event-002',
        description: '检测到异常车辆停放',
        severity: 'medium',
        timestamp: new Date(Date.now() - 30 * 60 * 1000).toISOString(),
        location: { lng: 114.368, lat: 30.542 },
        status: 'handling'
      }
    ]);

    const availableDrones = ref([
      { label: '无人机 A', value: 'drone-001' },
      { label: '无人机 B', value: 'drone-002' },
      { label: '无人机 C', value: 'drone-003' }
    ]);

    const taskFilter = ref('all');
    const filterOptions = [
      { label: '全部', value: 'all' },
      { label: '进行中', value: 'active' },
      { label: '已完成', value: 'completed' },
      { label: '已停止', value: 'stopped' }
    ];

    // 方法
    const handleMapLoaded = () => {
      if (mapRef.value) {
        mapRef.value.setView({
          center: [114.367, 30.54],
          zoom: 15
        });
      }
    };

    const handleMapClick = (event) => {
      if (patrolCreatorRef.value?.isSelectingWaypoints) {
        patrolCreatorRef.value.addWaypoint(event.coordinates);
      }
    };

    const handleWaypointSelectionChange = (isSelecting) => {
      // 处理选点模式变化
    };

    const handlePatrolTaskSubmit = (taskData) => {
      tasks.value.unshift({
        id: `task-${Date.now()}`,
        ...taskData,
        status: 'active',
        createTime: new Date().toISOString()
      });
      showPatrolCreator.value = false;
      message.success('巡逻任务创建成功');
    };

    const openTaskDetail = (task) => {
      currentTask.value = task;
      showTaskDetail.value = true;
    };

    const closeTaskDetail = () => {
      currentTask.value = null;
      showTaskDetail.value = false;
    };

    const stopTask = (task) => {
      const targetTask = tasks.value.find(t => t.id === task.id);
      if (targetTask) {
        targetTask.status = 'stopped';
        message.success('任务已停止');
      }
    };

    const resumeTask = (task) => {
      const targetTask = tasks.value.find(t => t.id === task.id);
      if (targetTask) {
        targetTask.status = 'active';
        message.success('任务已恢复');
      }
    };

    const handleFilterChange = (value) => {
      taskFilter.value = value;
    };

    const viewAllEvents = () => {
      router.push('/security/events');
    };

    const openEventDetail = (event) => {
      // 处理事件详情
    };

    const focusOnEvent = (event) => {
      if (mapRef.value) {
        mapRef.value.setView({
          center: [event.location.lng, event.location.lat],
          zoom: 18
        });
      }
    };

    return {
      mapRef,
      tasks,
      securityEvents,
      showPatrolCreator,
      showTaskDetail,
      patrolCreatorRef,
      currentTask,
      availableDrones,
      taskFilter,
      filterOptions,
      handleMapLoaded,
      handleMapClick,
      handleWaypointSelectionChange,
      handlePatrolTaskSubmit,
      openTaskDetail,
      closeTaskDetail,
      stopTask,
      resumeTask,
      handleFilterChange,
      viewAllEvents,
      openEventDetail,
      focusOnEvent
    };
  }
};