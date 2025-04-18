import { ref, onMounted, watch, provide, nextTick, computed, onUnmounted, inject } from 'vue';
import { useRouter } from 'vue-router';
import { NButton, NModal, NDrawer, NDrawerContent, useMessage, useDialog } from 'naive-ui';
import Map3D from '@/components/map/Map3D_uio.vue';
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
        
        // 向地图添加巡逻区域
        await addPatrolAreasToMap();
        
        message.success('任务列表已更新');
      } catch (error) {
        console.error('加载任务列表失败:', error);
        message.error('加载任务列表失败');
      } finally {
        loading.value = false;
      }
    };

    /**
     * 将任务列表中的巡逻区域添加到地图
     */
    const addPatrolAreasToMap = () => {
      console.log('尝试添加巡逻区域到地图，所有任务:', tasks.value?.length);
      
      if (!tasks.value || tasks.value.length === 0) {
        console.warn('没有任务数据，无法添加巡逻区域');
        return;
      }
      
      if (!mapRef.value) {
        console.warn('地图实例未初始化，无法添加巡逻区域');
        return;
      }
      
      try {
        // 确保地图组件已完全加载
        const ensureMapReady = () => {
          return new Promise((resolve) => {
            // 检查地图组件是否已准备就绪
            if (mapRef.value && typeof mapRef.value.addPatrolAreaToMap === 'function') {
              console.log('地图组件已准备就绪');
              resolve(true);
            } else {
              console.log('地图组件尚未就绪，等待500ms后重试');
              setTimeout(() => {
                if (mapRef.value && typeof mapRef.value.addPatrolAreaToMap === 'function') {
                  console.log('地图组件现在已就绪');
                  resolve(true);
                } else {
                  console.warn('地图组件仍未就绪，将继续尝试添加巡逻区域');
                  resolve(false);
                }
              }, 500);
            }
          });
        };
        
        ensureMapReady().then((isReady) => {
          if (!isReady) {
            console.warn('地图组件可能未完全就绪，但仍将尝试添加巡逻区域');
          }
          
          console.log('任务数据结构示例:', tasks.value[0]);
          
          // 过滤有效的巡逻区域任务
          const validTasks = tasks.value.filter(task => {
            if (!task || !task.patrol_area) {
              console.warn(`任务 ${task?.task_id || '未知ID'} 没有patrol_area字段`);
              return false;
            }
            
            // GeoJSON格式应该是 [[[lng1,lat1], [lng2,lat2], ...]] 形式（多边形）
            let isValid = true;
            
            // 检查patrol_area对象结构
            if (!task.patrol_area.coordinates) {
              console.warn(`任务 ${task.task_id || '未知ID'} 的patrol_area缺少coordinates字段`);
              return false;
            }
            
            // 确认数据格式 - 可能是直接坐标数组或嵌套数组
            let coordinates = task.patrol_area.coordinates;
            if (!Array.isArray(coordinates)) {
              console.warn(`任务 ${task.task_id || '未知ID'} 的coordinates不是数组`);
              isValid = false;
            } else if (coordinates.length === 0) {
              console.warn(`任务 ${task.task_id || '未知ID'} 的coordinates数组为空`);
              isValid = false;
            } else if (!Array.isArray(coordinates[0])) {
              console.warn(`任务 ${task.task_id || '未知ID'} 的坐标格式可能不正确`);
              isValid = false;
            } else if (Array.isArray(coordinates[0]) && coordinates[0].length < 3) {
              console.warn(`任务 ${task.task_id || '未知ID'} 的坐标点不足3个，无法形成多边形`);
              isValid = false;
            }
            
            console.log(`任务 ${task.task_id || '未知ID'} patrol_area 校验: ${isValid ? '通过' : '不通过'}`);
            return isValid;
          });
          
          if (validTasks.length === 0) {
            console.log('没有包含有效巡逻区域的任务');
            return;
          }
          
          console.log(`找到${validTasks.length}个有效巡逻区域任务`);
          
          // 添加每个任务的巡逻区域
          if (typeof mapRef.value.addPatrolAreaToMap === 'function') {
            validTasks.forEach((task, index) => {
              console.log(`添加第${index+1}个巡逻区域: ${task.title || '未命名任务'} (ID: ${task.task_id})`);
              
              // 不同状态的任务使用不同颜色
              let fillColor = [59, 130, 246, 100]; // 默认蓝色
              
              // 根据任务状态设置不同的颜色
              switch(task.status) {
                case 'in_progress':
                  fillColor = [76, 175, 80, 120]; // 绿色，进行中
                  break;
                case 'completed':
                  fillColor = [33, 150, 243, 100]; // 蓝色，已完成
                  break;
                case 'pending':
                  fillColor = [255, 152, 0, 100]; // 橙色，待执行
                  break;
                case 'cancelled':
                case 'failed':
                  fillColor = [244, 67, 54, 80]; // 红色，取消或失败
                  break;
              }
              
              // 处理坐标格式 - 确保符合GeoJSON多边形格式
              let coordinates = task.patrol_area.coordinates;
              let geojson = {...task.patrol_area};
              
              // 如果是简单数组 [[lng1,lat1], [lng2,lat2], ...] 包装为多边形格式
              if (Array.isArray(coordinates[0]) && !Array.isArray(coordinates[0][0])) {
                geojson = {
                  type: 'Polygon',
                  coordinates: [coordinates]
                };
                console.log(`转换任务 ${task.task_id} 的坐标格式为标准多边形格式`);
              }
              
              console.log(`任务 ${task.task_id} 最终geojson:`, geojson);
              
              try {
                mapRef.value.addPatrolAreaToMap({
                  geojson: geojson,
                  taskId: task.task_id,
                  taskName: task.title || '巡逻任务',
                  color: fillColor,
                  status: task.status
                }, true);
              } catch (e) {
                console.error(`添加巡逻区域 ${task.task_id} 时出错:`, e);
              }
            });
            
            console.log('所有巡逻区域已添加到地图');
          } else {
            console.warn('地图实例不支持添加巡逻区域方法');
          }
        });
      } catch (error) {
        console.error('向地图添加巡逻区域时出错:', error);
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
      
      // 在地图上高亮显示任务区域，但不缩放地图
      if (mapRef.value && task.patrol_area) {
        // 添加区域到地图并高亮显示，不移动视角
        showAreaOnMap(task.patrol_area, false);
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
      router.push('/events');
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
    
    // 在地图上显示并聚焦巡逻区域
    const showAreaOnMap = (area, shouldZoom = true) => {
      if (!area || !area.coordinates || area.coordinates.length === 0) {
        message.warning('巡逻区域没有有效的坐标信息');
        return;
      }

      // 使用组件内已有的mapRef引用
      if (!mapRef.value) {
        console.error('地图实例未找到');
        message.error('无法在地图上显示，地图组件未加载');
        return;
      }

      try {
        // 清除其他区域的高亮状态
        if (typeof mapRef.value.clearHighlightedAreas === 'function') {
          mapRef.value.clearHighlightedAreas();
        }
        
        // 添加区域到地图并高亮显示
        if (typeof mapRef.value.addPatrolAreaToMap === 'function') {
          mapRef.value.addPatrolAreaToMap({
            geojson: area,
            taskId: currentTask.value?.task_id || 'temp-task',
            taskName: currentTask.value?.title || '巡逻任务区域',
            color: [59, 130, 246, 150], // 高亮颜色，蓝色半透明
            isHighlighted: true
          }, true);
          
          // 如果需要缩放，才执行缩放逻辑
          if (shouldZoom) {
            // 计算边界并缩放地图到合适的视野
            const coords = area.coordinates[0];
            if (coords && coords.length > 0) {
              // 找出区域边界
              let minLng = Infinity, maxLng = -Infinity;
              let minLat = Infinity, maxLat = -Infinity;
              
              for (const [lng, lat] of coords) {
                if (lng && lat) { // 添加非空检查
                  minLng = Math.min(minLng, lng);
                  maxLng = Math.max(maxLng, lng);
                  minLat = Math.min(minLat, lat);
                  maxLat = Math.max(maxLat, lat);
                }
              }
              
              // 如果找到了有效的边界
              if (isFinite(minLng) && isFinite(maxLng) && isFinite(minLat) && isFinite(maxLat)) {
                // 使用flyTo方法飞行到区域，确保视野合适
                if (typeof mapRef.value.flyTo === 'function') {
                  // 计算中心点
                  const centerLng = (minLng + maxLng) / 2;
                  const centerLat = (minLat + maxLat) / 2;
                  
                  // 计算对角线距离，用于估算合适的缩放级别
                  const diagonalDistance = Math.sqrt(
                    Math.pow(maxLng - minLng, 2) + 
                    Math.pow(maxLat - minLat, 2)
                  );
                  
                  // 根据区域大小估算缩放级别
                  // 区域越大，缩放级别越小；区域越小，缩放级别越大
                  // 使用对数关系计算缩放级别
                  const zoom = Math.max(13, Math.min(18, 16 - Math.log10(diagonalDistance * 1000)));
                  
                  mapRef.value.flyTo({
                    center: [centerLng, centerLat],
                    zoom: zoom,
                    duration: 1000,
                    pitch: 45 // 添加一点倾斜角度以便更好地查看
                  });
                  
                  message.success('已定位到巡逻区域');
                } else {
                  message.warning('地图无法自动缩放到区域位置');
                }
              } else {
                message.warning('无法计算巡逻区域边界');
              }
            }
          } else {
            // 不缩放，只显示成功消息
            message.success('已在地图上高亮显示巡逻区域');
          }
        } else {
          message.error('地图组件不支持显示巡逻区域');
        }
      } catch (error) {
        console.error('显示巡区域时出错:', error);
        message.error('无法在地图上显示区域');
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

    // 取消编辑任务
    const cancelEditTask = () => {
      // 关闭创建表单
      showPatrolCreator.value = false;
      
      // 清空编辑中的任务
      editingTask.value = null;
      
      // 重新打开详情面板
      if (currentTask.value) {
        showDetailPanel.value = true;
        
        // 更新地图高亮
        activeTaskCard.value = currentTask.value.id || currentTask.value.task_id;
        
        // 提示用户
        message.info('已取消编辑任务');
      }
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
    onMounted(async () => {
      console.log('Security组件已挂载');
      
      // 确保地图实例已就绪
      await ensureMapReady();
      
      // 加载任务数据
      await loadTasks();
      
    });

    // 确保地图实例已就绪
    const ensureMapReady = () => {
      return new Promise((resolve) => {
        // 如果已有mapRef，直接返回
        if (mapRef.value) {
          console.log('已获取地图实例');
          resolve(mapRef.value);
          return;
        }
        
        // 尝试从全局获取地图实例
        const getGlobalMap = () => {
          try {
            // 从inject获取
            const globalMapRef = inject('mapRef', null);
            if (globalMapRef?.value) {
              console.log('从inject获取地图实例成功');
              mapRef.value = globalMapRef.value;
              resolve(mapRef.value);
              return true;
            }
            
            // 从window调试对象获取
            if (window.skymindDebug?.mapRef?.value) {
              console.log('从window.skymindDebug获取地图实例成功');
              mapRef.value = window.skymindDebug.mapRef.value;
              resolve(mapRef.value);
              return true;
            }
            
            return false;
          } catch (err) {
            console.error('获取地图实例出错:', err);
            return false;
          }
        };
        
        // 立即尝试获取一次
        if (getGlobalMap()) return;
        
        // 如果获取失败，等待地图实例加载完成
        console.log('地图实例未就绪，等待地图加载...');
        let attempts = 0;
        const maxAttempts = 10;
        const checkInterval = setInterval(() => {
          attempts++;
          if (getGlobalMap() || attempts >= maxAttempts) {
            clearInterval(checkInterval);
            if (!mapRef.value) {
              console.warn(`无法获取地图实例，已尝试${attempts}次`);
            }
            resolve(mapRef.value);
          }
        }, 500); // 每500ms检查一次，最多尝试10次（5秒）
      });
    };


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
      cancelEditTask,
      deleteTask,
      isEditMode
    };
  }
};