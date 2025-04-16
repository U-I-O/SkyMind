import { ref, onMounted, watch, provide, nextTick, computed } from 'vue';
import { useRouter } from 'vue-router';
import { NButton, NModal, NDrawer, NDrawerContent, useMessage, useDialog } from 'naive-ui';
import Map3D from '@/components/map/Map3D.vue';
import PatrolTaskList from '@/components/patrol/PatrolTaskList.vue';
import PatrolTaskCreator from '@/components/patrol/PatrolTaskCreator.vue';
import PatrolTaskDetail from '@/components/patrol/PatrolTaskDetail.vue';
import SecurityEventList from '@/components/security/SecurityEventList.vue';
import { CloseOutline as CloseIcon, ReloadOutline as ReloadIcon } from '@vicons/ionicons5';
import { getAllSurveillanceTasks, getPatrolTaskById, updatePatrolTask, deletePatrolTask } from '@/api/task';

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
    const dialog = useDialog();
    const mapRef = ref(null);
    const showPatrolCreator = ref(false);
    const showTaskDetail = ref(false);
    const showDetailPanel = ref(false);
    const patrolCreatorRef = ref(null);
    const currentTask = ref(null);
    const activeTaskCard = ref(null);
    const tasks = ref([]);
    const loading = ref(false);
    const editingTask = ref(null);

    // 添加计算属性：判断是否是编辑模式
    const isEditMode = computed(() => {
      return !!editingTask.value;
    });

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
      { label: '进行中', value: 'in_progress' },
      { label: '待执行', value: 'pending' },
      { label: '已完成', value: 'completed' },
      { label: '已取消', value: 'cancelled' }
    ];

    // 加载任务列表
    const loadTasks = async () => {
      loading.value = true;
      try {
        const response = await getAllSurveillanceTasks();
        tasks.value = response || [];
        message.success('任务列表已更新');
      } catch (error) {
        console.error('加载任务列表失败:', error);
        message.error('加载任务列表失败');
      } finally {
        loading.value = false;
      }
    };

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
      
    };

    const openTaskDetail = (task) => {
      currentTask.value = task;
      
      // 在左侧面板显示详情而不是弹窗
      showDetailPanel.value = true;
      showTaskDetail.value = false; // 不再显示弹窗
      
      // 如果正在显示创建任务表单，则关闭它
      if (showPatrolCreator.value) {
        showPatrolCreator.value = false;
      }
      
      // 在地图上高亮显示任务区域
      if (mapRef.value && task.patrol_area) {
        // 假设地图组件有显示区域的方法
        // mapRef.value.highlightArea(task.patrol_area);
        
        // 将地图中心移动到任务区域
        if (task.patrol_area.coordinates && task.patrol_area.coordinates.length > 0) {
          const coords = task.patrol_area.coordinates[0];
          if (coords && coords.length > 0) {
            mapRef.value.setView({
              center: coords[0],
              zoom: 16
            });
          }
        }
      }
      
      // 设置活动卡片
      activeTaskCard.value = task.id || task.task_id;
    };

    const closeTaskDetail = () => {
      if (showTaskDetail.value) {
        // 关闭弹窗
        showTaskDetail.value = false;
      }
      // 左侧面板保持当前状态不变
    };

    const closeDetailPanel = () => {
      showDetailPanel.value = false;
      activeTaskCard.value = null;
      
      // 清除地图上的高亮显示
      if (mapRef.value) {
        // mapRef.value.clearHighlights();
      }
    };

    const startTask = async (task) => {
      try {
        message.loading('启动任务中...');
        
        // 更新任务状态
        const updatedTask = await updatePatrolTask(task.task_id, {
          ...task,
          status: 'in_progress'
        });
        
        // 更新本地任务列表
        const index = tasks.value.findIndex(t => t.task_id === task.task_id);
        if (index !== -1) {
          tasks.value[index] = {
            ...tasks.value[index],
            status: 'in_progress'
          };
        }
        
        // 更新当前任务
        if (currentTask.value && currentTask.value.task_id === task.task_id) {
          currentTask.value = {
            ...currentTask.value,
            status: 'in_progress'
          };
        }
        
        message.success('任务已启动');
        
        // 刷新任务列表
        await loadTasks();
      } catch (error) {
        console.error('启动任务失败:', error);
        message.error('启动任务失败，请重试');
      }
    };

    const stopTask = async (task) => {
      try {
        message.loading('停止任务中...');
        
        // 更新任务状态
        const updatedTask = await updatePatrolTask(task.task_id, {
          ...task,
          status: 'cancelled'
        });
        
        // 更新本地任务列表
        const index = tasks.value.findIndex(t => t.task_id === task.task_id);
        if (index !== -1) {
          tasks.value[index] = {
            ...tasks.value[index],
            status: 'cancelled'
          };
        }
        
        // 更新当前任务
        if (currentTask.value && currentTask.value.task_id === task.task_id) {
          currentTask.value = {
            ...currentTask.value,
            status: 'cancelled'
          };
        }
        
        message.success('任务已停止');
        
        // 刷新任务列表
        await loadTasks();
      } catch (error) {
        console.error('停止任务失败:', error);
        message.error('停止任务失败，请重试');
      }
    };

    const resumeTask = async (task) => {
      try {
        message.loading('恢复任务中...');
        
        // 更新任务状态
        const updatedTask = await updatePatrolTask(task.task_id, {
          ...task,
          status: 'in_progress'
        });
        
        // 更新本地任务列表
        const index = tasks.value.findIndex(t => t.task_id === task.task_id);
        if (index !== -1) {
          tasks.value[index] = {
            ...tasks.value[index],
            status: 'in_progress'
          };
        }
        
        // 更新当前任务
        if (currentTask.value && currentTask.value.task_id === task.task_id) {
          currentTask.value = {
            ...currentTask.value,
            status: 'in_progress'
          };
        }
        
        message.success('任务已恢复');
        
        // 刷新任务列表
        await loadTasks();
      } catch (error) {
        console.error('恢复任务失败:', error);
        message.error('恢复任务失败，请重试');
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
    
    const focusOnDrone = (droneId) => {
      // 假设存在获取无人机位置的方法
      if (mapRef.value) {
        // 获取无人机位置并将地图中心设置到那里
        const dronePosition = [114.367, 30.54]; // 示例位置
        mapRef.value.setView({
          center: dronePosition,
          zoom: 18
        });
        
        // 高亮显示无人机
        // mapRef.value.highlightDrone(droneId);
      }
    };
    
    const showAreaOnMap = (area) => {
      if (mapRef.value && area && area.coordinates) {
        // 高亮显示该区域
        if (typeof mapRef.value.addPatrolAreaToMap === 'function') {
          mapRef.value.addPatrolAreaToMap({
            geojson: area,
            taskId: currentTask.value?.task_id || 'temp-task',
            taskName: currentTask.value?.title || '任务详情'
          });
        }
        
        // 将地图视野调整到包含整个区域
        if (area.coordinates.length > 0) {
          const coords = area.coordinates[0];
          if (coords && coords.length > 0) {
            // 找出边界
            let minLng = Infinity, maxLng = -Infinity, minLat = Infinity, maxLat = -Infinity;
            for (const [lng, lat] of coords) {
              minLng = Math.min(minLng, lng);
              maxLng = Math.max(maxLng, lng);
              minLat = Math.min(minLat, lat);
              maxLat = Math.max(maxLat, lat);
            }
            
            // 设置地图视野
            if (mapRef.value.fitBounds) {
              mapRef.value.fitBounds([
                [minLng, minLat],
                [maxLng, maxLat]
              ]);
              
              // 显示消息提示
              message.success('已在地图上显示巡逻区域');
            }
          }
        }
      }
    };

    const closePatrolCreator = () => {
      showPatrolCreator.value = false;
      if (patrolCreatorRef.value && patrolCreatorRef.value.isDrawingArea) {
        patrolCreatorRef.value.cancelDrawing();
      }
    };
    
    // 双击或特定按钮打开弹窗详情
    const openTaskDetailModal = (task) => {
      currentTask.value = task;
      showTaskDetail.value = true;
      activeTaskCard.value = task.id || task.task_id;
    };
    
    // 在任务列表项上点击查看详情
    const handleTaskClick = (task) => {
      openTaskDetail(task);
    };
    
    // 监听创建任务表单的显示状态变化
    watch(showPatrolCreator, (newValue) => {
      if (!newValue && patrolCreatorRef.value && patrolCreatorRef.value.isDrawingArea) {
        patrolCreatorRef.value.cancelDrawing();
      }
    });
    
    // 刷新数据
    const refreshData = async () => {
      await loadTasks();
    };
    
    // 提供activeTaskCard给子组件
    provide('activeTaskCard', activeTaskCard);
    
    // 编辑任务
    const editTask = (task) => {
      // 保存当前任务到临时变量，以便创建表单使用
      editingTask.value = { ...task };
      
      // 关闭详情面板
      closeDetailPanel();
      
      // 打开创建表单并设置为编辑模式
      showPatrolCreator.value = true;
      
      // 在下一个渲染周期设置表单数据
      nextTick(() => {
        if (patrolCreatorRef.value) {
          patrolCreatorRef.value.setEditMode(task);
          message.info(`正在编辑任务"${task.title}"`);
        } else {
          message.error('无法加载编辑表单，请重试');
        }
      });
    };

    // 删除任务
    const deleteTask = async (task) => {
      try {
        message.loading('正在删除任务...');
        
        // 调用API删除任务
        await deletePatrolTask(task.task_id);
        
        // 更新本地任务列表
        tasks.value = tasks.value.filter(t => t.task_id !== task.task_id);
        
        // 关闭详情面板
        closeDetailPanel();
        
        message.success('任务已成功删除');
      } catch (error) {
        console.error('删除任务失败:', error);
        message.error('删除任务失败，请重试');
      }
    };
    
    // 初始化时加载任务列表
    onMounted(() => {
      loadTasks();
    });

    return {
      mapRef,
      tasks,
      securityEvents,
      showPatrolCreator,
      showTaskDetail,
      showDetailPanel,
      patrolCreatorRef,
      currentTask,
      activeTaskCard,
      availableDrones,
      taskFilter,
      filterOptions,
      loading,
      handleMapLoaded,
      handlePatrolTaskSubmit,
      openTaskDetail,
      closeTaskDetail,
      closeDetailPanel,
      startTask,
      stopTask,
      resumeTask,
      handleFilterChange,
      viewAllEvents,
      openEventDetail,
      focusOnEvent,
      focusOnDrone,
      showAreaOnMap,
      closePatrolCreator,
      refreshData,
      openTaskDetailModal,
      handleTaskClick,
      editTask,
      deleteTask,
      isEditMode
    };
  }
};