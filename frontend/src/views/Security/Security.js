import { ref, onMounted, watch } from 'vue';
import { useRouter } from 'vue-router';
import { NButton, NModal, NDrawer, NDrawerContent, useMessage } from 'naive-ui';
import Map3D from '@/components/map/Map3D.vue';
import PatrolTaskList from '@/components/patrol/PatrolTaskList.vue';
import PatrolTaskCreator from '@/components/patrol/PatrolTaskCreator.vue';
import PatrolTaskDetail from '@/components/patrol/PatrolTaskDetail.vue';
import SecurityEventList from '@/components/security/SecurityEventList.vue';
import { CloseOutline as CloseIcon, ReloadOutline as ReloadIcon } from '@vicons/ionicons5';

export default {
  name: 'SecurityView',
  components: {
    Map3D,
    NButton,
    NModal,
    NDrawer,
    NDrawerContent,
    PatrolTaskList,
    PatrolTaskCreator,
    PatrolTaskDetail,
    SecurityEventList,
    CloseIcon,
    ReloadIcon
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
        speed: 5,
        patrolArea: [
          [114.367, 30.54], 
          [114.368, 30.542], 
          [114.366, 30.538],
          [114.367, 30.54]
        ]
      },
      {
        id: 'task-002',
        name: '西区围栏检查',
        status: 'stopped',
        createTime: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
        drones: ['drone-003'],
        speed: 4,
        patrolArea: [
          [114.365, 30.535], 
          [114.366, 30.536],
          [114.364, 30.5365], 
          [114.365, 30.535]
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

    const handlePatrolTaskSubmit = (taskData) => {
      const selectedDroneIds = ['drone-001'];
      
      tasks.value.unshift({
        id: `task-${Date.now()}`,
        ...taskData,
        drones: selectedDroneIds,
        status: 'pending',
        createTime: new Date().toISOString()
      });
      showPatrolCreator.value = false;
      message.success('巡逻任务创建成功');
      
      console.log("New task created:", tasks.value[0]);
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

    const closePatrolCreator = () => {
      showPatrolCreator.value = false;
      if (patrolCreatorRef.value && patrolCreatorRef.value.isDrawingArea) {
        patrolCreatorRef.value.cancelDrawing();
      }
    };
    
    // 监听创建任务表单的显示状态变化
    watch(showPatrolCreator, (newValue) => {
      if (!newValue && patrolCreatorRef.value && patrolCreatorRef.value.isDrawingArea) {
        patrolCreatorRef.value.cancelDrawing();
      }
    });
    
    // 刷新数据
    const refreshData = () => {
      message.success('数据已刷新');
      // 这里可以添加实际的数据刷新逻辑
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
      handlePatrolTaskSubmit,
      openTaskDetail,
      closeTaskDetail,
      stopTask,
      resumeTask,
      handleFilterChange,
      viewAllEvents,
      openEventDetail,
      focusOnEvent,
      closePatrolCreator,
      refreshData
    };
  }
};