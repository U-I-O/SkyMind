<template>
  <div class="patrol-task-creator">
    <div class="form-container">
      <n-form
        ref="formRef"
        :model="formModel"
        :rules="rules"
        label-placement="left"
        label-width="80"
        require-mark-placement="right-hanging"
        size="small"
      >
        <!-- 任务基本信息 -->
        <div class="form-section">
          <div class="section-title">基本信息</div>
          <div class="section-content">
            <div class="form-row">
              <n-form-item label="任务名称" path="name">
                <n-input v-model:value="formModel.name" placeholder="请输入任务名称" />
              </n-form-item>
            </div>
            <div class="form-row">
              <n-form-item label="执行趟数" path="rounds" style="flex: 1">
                <n-input-number v-model:value="formModel.rounds" :min="1" placeholder="执行趟数" />
              </n-form-item>
            </div>
          </div>
        </div>

        <!-- 飞行参数 -->
        <div class="form-section">
          <div class="section-title">飞行参数</div>
          <div class="section-content">
            <div class="form-row">
              <n-form-item label="飞行高度(米)" path="altitude" style="flex: 1">
                <n-input-number 
                  v-model:value="formModel.altitude" 
                  :min="10" 
                  :max="500"
                  placeholder="飞行高度"
                />
              </n-form-item>
            </div>
            <div class="form-row">
              <n-form-item label="飞行速度(m/s)" path="speed" style="flex: 1">
                <n-input-number 
                  v-model:value="formModel.speed" 
                  :min="1" 
                  :max="20"
                  placeholder="飞行速度"
                />
              </n-form-item>
            </div>
            <div class="form-row">
              <n-form-item label="关联无人机" path="droneIds">
                <n-select
                  v-model:value="formModel.droneIds"
                  multiple
                  filterable
                  :options="droneOptions"
                  placeholder="选择执行任务的无人机"
                  style="width:16vw"
                />
              </n-form-item>
            </div>
          </div>
        </div>

        <!-- 时间安排 -->
        <div class="form-section">
          <div class="section-title">时间安排</div>
          <div class="section-content">
            <div class="form-row">
              <n-form-item label="执行模式" path="scheduleType">
                <n-radio-group v-model:value="formModel.scheduleType" class="schedule-type-selector">
                  <n-space>
                    <n-radio value="date">指定日期</n-radio>
                    <n-radio value="week">每周重复</n-radio>
                  </n-space>
                </n-radio-group>
              </n-form-item>
            </div>
            
            <div class="schedule-details">
              <div class="form-row">
                <!-- 指定日期选择器 -->
                <n-form-item v-if="formModel.scheduleType === 'date'" label="执行日期" path="date" style="flex: 1">
                  <n-date-picker
                    v-model:value="formModel.date"
                    type="date"
                    placeholder="选择日期"
                    clearable
                    style="width: 100%"
                  />
                </n-form-item>
                
                <!-- 每周重复选择器 -->
                <n-form-item v-if="formModel.scheduleType === 'week'" label="执行日" path="weekdays" style="flex: 1">
                  <n-select
                    v-model:value="formModel.weekdays"
                    multiple
                    :options="[
                      { label: '周一', value: 1 },
                      { label: '周二', value: 2 },
                      { label: '周三', value: 3 },
                      { label: '周四', value: 4 },
                      { label: '周五', value: 5 },
                      { label: '周六', value: 6 },
                      { label: '周日', value: 0 }
                    ]"
                    placeholder="选择周几"
                    style="width: 100%"
                  />
                </n-form-item>
                
                <!-- 时间选择器 -->
                <n-form-item label="执行时间" path="time" style="flex: 1">
                  <n-time-picker
                    v-model:value="formModel.time"
                    format="HH:mm"
                    placeholder="选择时间"
                    clearable
                    style="width: 100%"
                  />
                </n-form-item>
              </div>
            </div>
          </div>
        </div>

        <!-- 巡逻区域 -->
        <div class="form-section">
          <div class="section-title">巡逻区域</div>
          <div class="section-content">
            <n-form-item path="patrolArea">
              <div class="area-container">
                <div class="area-status">
                  <div class="status-icon" :class="{ 'status-completed': formModel.patrolArea.length >= 3 }">
                    <n-icon v-if="formModel.patrolArea.length >= 3" size="16">
                      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M21,7L9,19L3.5,13.5L4.91,12.09L9,16.17L19.59,5.59L21,7Z" /></svg>
                    </n-icon>
                    <n-icon v-else size="16">
                      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M19,6.41L17.59,5L12,10.59L6.41,5L5,6.41L10.59,12L5,17.59L6.41,19L12,13.41L17.59,19L19,17.59L13.41,12L19,6.41Z" /></svg>
                    </n-icon>
                  </div>
                  <div class="status-text">
                    <div class="status-title">{{ formModel.patrolArea.length === 0 ? '尚未绘制巡逻区域' : '已绘制巡逻区域' }}</div>
                    <div v-if="formModel.patrolArea.length > 0" class="status-subtitle">包含 {{ formModel.patrolArea.length }} 个顶点</div>
                  </div>
                  <div class="area-actions">
                    <n-button 
                      size="tiny" 
                      :type="isDrawingArea ? 'warning' : 'primary'" 
                      @click="toggleAreaDrawing"
                    >
                      {{ isDrawingArea ? '完成绘制' : '绘制区域' }}
                    </n-button>
                    <n-button 
                      v-if="formModel.patrolArea.length > 0 && !isDrawingArea"
                      size="tiny" 
                      type="error" 
                      @click="clearPatrolArea"
                      class="ml-2"
                    >
                      清除
                    </n-button>
                  </div>
                </div>
                
                <div v-if="formModel.patrolArea.length > 0 && !isDrawingArea" class="area-preview">
                  <div class="coordinates-list">
                    <div v-for="(point, index) in formModel.patrolArea" :key="index" class="coordinate-item">
                      点{{ index + 1 }}: ({{ point[0].toFixed(4) }}, {{ point[1].toFixed(4) }})
                    </div>
                  </div>
                </div>
              </div>
            </n-form-item>
          </div>
        </div>

        <div class="form-actions">
          <n-space justify="end">
            <n-button size="small" @click="resetForm">重置</n-button>
            <n-button size="small" type="primary" @click="handleSubmit">创建任务</n-button>
          </n-space>
        </div>
      </n-form>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, inject, onMounted, onUnmounted, watch } from 'vue';
import { 
  NForm, 
  NFormItem, 
  NInput, 
  NInputNumber, 
  NRadioGroup, 
  NRadio, 
  NSpace, 
  NButton,
  NDatePicker,
  NTimePicker,
  NSelect,
  useMessage
} from 'naive-ui';
import { useTaskStore } from '@/store/task';
import { useDroneStore } from '@/store/drone';

const props = defineProps({
  // 移除 map3dRef prop，我们将注入全局 mapRef
});

const emit = defineEmits(['submit']); // 移除 'waypoint-selection-change'
const droneStore = useDroneStore();
const message = useMessage();
const formRef = ref(null);
const taskStore = useTaskStore(); // 导入任务store

// 无人机选项
const droneOptions = computed(() => {
  return droneStore.drones.map(drone => ({
    label: `${drone.name} (${drone.drone_id}) - 电量: ${drone.battery}%`,
    value: drone.drone_id
  }));
});

const formModel = ref({
  name: '',
  patrolArea: [],
  scheduleType: 'date',
  date: null,
  weekdays: [],
  time: null,
  rounds: 1,
  isManual: false,
  altitude: 50, // 默认飞行高度50米
  speed: 5,    // 默认飞行速度5m/s
  droneIds: [] // 关联的无人机ID数组
});

// 使用watch监听taskStore中patrolAreaCoordinates的变化
watch(() => taskStore.patrolAreaCoordinates, (newCoords) => {
  // 更新表单中的巡逻区域
  formModel.value.patrolArea = [...newCoords];
}, { deep: true });

// 使用watch监听taskStore中patrolAreaGeoJSON的变化
watch(() => taskStore.patrolAreaGeoJSON, (newGeoJSON) => {
  if (newGeoJSON) {
    console.log('巡逻区域GeoJSON已更新:', newGeoJSON);
    // 这里可以进一步处理GeoJSON数据，例如显示详细信息或保存到其他地方
  }
}, { deep: true });

const rules = {
  name: {
    required: true,
    message: '请输入任务名称',
    trigger: 'blur'
  },
  patrolArea: { // 更新验证规则
    required: true,
    type: 'array',
    validator: (rule, value) => value && value.length >= 3, // 至少3个顶点
    message: '请绘制巡逻区域 (至少3个顶点)',
    trigger: 'change'
  },
  date: {
    required: true,
    validator: (rule, value) => {
      if (formModel.value.scheduleType === 'date' && !value) {
        return false;
      }
      return true;
    },
    message: '请选择任务日期',
    trigger: 'change'
  },
  weekdays: {
    required: true,
    validator: (rule, value) => {
      if (formModel.value.scheduleType === 'week' && value.length === 0) {
        return false;
      }
      return true;
    },
    message: '请选择周几执行',
    trigger: 'change'
  },
  time: {
    required: true,
    type: 'number', // Naive UI time-picker v-model:value 绑定的是时间戳
    message: '请选择任务时间',
    trigger: 'change'
  },
  rounds: {
    required: true,
    type: 'number',
    min: 1,
    message: '请输入执行趟数 (至少1趟)',
    trigger: ['input', 'blur']
  },
  altitude: {
    required: true,
    type: 'number',
    min: 10,
    max: 500,
    message: '请输入有效的飞行高度(10-500米)',
    trigger: ['input', 'blur']
  },
  speed: {
    required: true,
    type: 'number',
    min: 1,
    max: 20,
    message: '请输入有效的飞行速度(1-20m/s)',
    trigger: ['input', 'blur']
  },
  droneIds: {
    required: true,
    type: 'array',
    validator: (rule, value) => value && value.length > 0,
    message: '请至少选择一架无人机',
    trigger: 'change'
  }
};

// 在组件挂载时加载无人机列表
onMounted(async () => {
  await droneStore.fetchDrones();
  
  // 监听地图组件的patrol-area-drawn事件
  if (mapRef.value) {
    mapRef.value.$el.addEventListener('patrol-area-drawn', (event) => {
      handleAreaDrawn(event.detail);
    });
  }
});

// 在组件卸载时取消监听和清理状态
onUnmounted(() => {
  // 移除事件监听
  if (mapRef.value) {
    mapRef.value.$el.removeEventListener('patrol-area-drawn', handleAreaDrawn);
  }
  
  // 如果正在绘制，确保取消
  if (isDrawingArea.value) {
    taskStore.cancelDrawingPatrolArea();
    if (mapRef.value && mapRef.value.cancelDrawingPatrolArea) {
      mapRef.value.cancelDrawingPatrolArea();
    }
  }
  
  // 清除临时巡逻区域
  if (mapRef.value && typeof mapRef.value.clearTempPatrolArea === 'function') {
    mapRef.value.clearTempPatrolArea();
  }
});

// 使用计算属性将 isDrawingArea 连接到store
const isDrawingArea = computed({
  get: () => taskStore.isDrawingPatrolArea,
  set: (value) => {
    // 我们通过调用方法来设置值
    if (!value && taskStore.isDrawingPatrolArea) {
      taskStore.cancelDrawingPatrolArea();
    }
    // 开始绘制会在 toggleAreaDrawing 方法中处理
  }
});

// 注入全局地图引用
const mapRef = inject('mapRef', ref(null)); // 提供默认值以防万一

// 使用watch监听taskStore中patrolAreaCoordinates的变化
watch(() => taskStore.patrolAreaCoordinates, (newCoords) => {
  // 更新表单中的巡逻区域
  formModel.value.patrolArea = [...newCoords];
}, { deep: true });

// 使用watch监听taskStore中patrolAreaGeoJSON的变化
watch(() => taskStore.patrolAreaGeoJSON, (newGeoJSON) => {
  if (newGeoJSON) {
    console.log('巡逻区域GeoJSON已更新:', newGeoJSON);
    // 这里可以进一步处理GeoJSON数据，例如显示详细信息或保存到其他地方
  }
}, { deep: true });

const toggleAreaDrawing = () => {
  if (!mapRef.value) {
    message.error("地图实例尚未准备好");
    return;
  }
  
  if (isDrawingArea.value) {
    // 如果当前正在绘制，则取消绘制
    taskStore.cancelDrawingPatrolArea();
    mapRef.value.cancelDrawingPatrolArea(); // 调用地图组件的方法取消绘制
  } else {
    // 进入绘制模式前清除可能存在的旧区域
    formModel.value.patrolArea = []; 
    
    // 生成任务表单ID - 使用时间戳作为临时ID
    const taskFormId = `task_form_${Date.now()}`;
    
    // 通过store开始绘制
    taskStore.startDrawingPatrolArea(taskFormId);
    
    // 调用地图组件的开始绘制方法 - 传入taskFormId
    mapRef.value.startDrawingPatrolArea(taskFormId);
    
    message.info("请在地图上点击绘制巡逻区域顶点，至少3个点。");
  }
};

const clearPatrolArea = () => {
  // 清空表单中的巡逻区域
  formModel.value.patrolArea = [];
  
  // 如果正在绘制，取消绘制
  if (isDrawingArea.value) {
    taskStore.cancelDrawingPatrolArea();
    if (mapRef.value && mapRef.value.cancelDrawingPatrolArea) {
      mapRef.value.cancelDrawingPatrolArea();
    }
  }
};

const handleAreaDrawn = (result) => {
  // 结果直接来自store和地图组件
  if (result && result.points && result.points.length >= 3) {
    // 更新表单数据
    formModel.value.patrolArea = [...result.points];
    
    // 地图和store中的绘制状态已经被更新，这里只需显示成功信息
    message.success(`巡逻区域绘制完成，包含 ${result.points.length} 个顶点。`);
    
    // 手动触发验证
    formRef.value?.validateField('patrolArea');
  } else {
    message.error("绘制的区域无效，请重新绘制。");
  }
};

const resetForm = () => {
  formRef.value?.restoreValidation();
  
  // 如果正在绘制，取消绘制
  if (isDrawingArea.value) {
    taskStore.cancelDrawingPatrolArea();
    if (mapRef.value && mapRef.value.cancelDrawingPatrolArea) {
      mapRef.value.cancelDrawingPatrolArea();
    }
  }
  
  // 清除临时巡逻区域
  if (mapRef.value && typeof mapRef.value.clearTempPatrolArea === 'function') {
    mapRef.value.clearTempPatrolArea();
  }
  
  formModel.value = {
    name: '',
    patrolArea: [],
    scheduleType: 'date',
    date: null,
    weekdays: [],
    time: null,
    rounds: 1,
    isManual: false,
    altitude: 50,
    speed: 5,
    droneIds: []
  };
};

const handleSubmit = () => {
  formRef.value?.validate((errors) => {
    if (!errors) {
       // 确保不在绘制模式
      if (isDrawingArea.value) {
        message.warning("请先完成或取消绘制巡逻区域");
        return;
      }
      
      // 准备提交数据
      
      const taskData = { 
        ...formModel.value,
        // 添加无人机详情
        assignedDrones: formModel.value.droneIds.map(id => ({
          drone_id: id,
          // 从store中获取无人机详情
          ...droneStore.getDroneById(id)
        }))
      };
      
      // 如果有GeoJSON，添加到提交数据中
      if (taskStore.patrolAreaGeoJSON) {
        taskData.patrolAreaGeoJSON = taskStore.patrolAreaGeoJSON;
      }
      
      console.log('Form Data:', taskData);
      
      // 提交任务
      emit('submit', taskData);
      
      // 任务提交成功
      message.success("巡逻任务创建请求已提交");
      
      // 将临时巡逻区域添加到地图上永久显示
      if (mapRef.value && typeof mapRef.value.addPatrolAreaToMap === 'function' && 
          taskStore.patrolAreaGeoJSON && formModel.value.patrolArea.length >= 3) {
        // 创建包含任务信息的巡逻区域对象
        const patrolAreaWithTaskInfo = {
          taskId: `task_${Date.now()}`, // 使用时间戳创建临时ID，实际应使用后端返回的ID
          taskName: formModel.value.name,
          points: [...formModel.value.patrolArea],
          geojson: taskStore.patrolAreaGeoJSON,
          createdAt: new Date()
        };
        
        // 添加到地图 - 传入 true 表示这是已确认的任务
        mapRef.value.addPatrolAreaToMap(patrolAreaWithTaskInfo, true);
        
        console.log('巡逻区域已添加到地图显示');
      }
      
      // 可以在提交后重置表单
      // resetForm(); 
    } else {
      console.log('Validation Errors:', errors)
      message.error('请检查表单信息是否完整且有效');
    }
  });
};

const cancelTaskCreation = () => {
  // 取消任务创建并清除临时区域
  message.info("已取消任务创建");
  resetForm();
};
</script>

<style scoped>

.patrol-task-creator {
  display: flex;
  flex-direction: column;
  height: 100%;
  width: 100%;
  position: relative; /* 添加相对定位 */
}

.form-container {
  width: 25vw;
  padding: 12px 16px 60px; /* 底部增加内边距给按钮留空间 */
  overflow-y: auto;
  max-height: 90vh;
  background-color: #fff;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  position: relative;
}

.form-actions {
  position: sticky; /* 或者使用 fixed */
  bottom: 5vh; /* 固定在底部 */
  left: 0;
  right: 0;
  margin-top: 16px;
  padding: 12px 16px;
  border-top: 1px solid #e0e0e6;
  background-color: #fff; /* 确保背景色 */
  display: flex;
  justify-content: flex-end;
  z-index: 1; /* 确保按钮在内容之上 */
  box-shadow: 0 -2px 8px rgba(0, 0, 0, 0.05); /* 添加轻微阴影增强层次感 */
}

.form-section {
  margin-bottom: 12px;
}

.section-title {
  font-size: 14px;
  font-weight: 600;
  color: #333;
  position: relative;
  padding-left: 10px;
  margin-bottom: 8px;
}

.section-title::before {
  content: '';
  position: absolute;
  left: 0;
  top: 4px;
  height: calc(100% - 8px);
  width: 3px;
  background-color: #18a058;
  border-radius: 2px;
}

.section-content {
  padding: 10px;
  background-color: #f9f9f9;
  border-radius: 6px;
  border: 1px solid #eaeaea;
}

.form-row {
  display: flex;
  gap: 12px;
  margin-bottom: 8px;
}

.form-row:last-child {
  margin-bottom: 0;
}

.schedule-type-selector {
  margin-bottom: 8px;
}

.schedule-details {
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px dashed #eaeaea;
}

.area-container {
  border: 1px solid #e0e0e6;
  border-radius: 6px;
  padding: 10px;
  width: 100%;
  background-color: #fdfdfd;
}

.area-status {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
}

.status-icon {
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background-color: #f3f3f3;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 8px;
  color: #999;
  flex-shrink: 0;
}

.status-completed {
  background-color: #edf7ed;
  color: #18a058;
}

.status-text {
  flex: 1;
}

.status-title {
  font-size: 13px;
  font-weight: 600;
  margin-bottom: 2px;
}

.status-subtitle {
  font-size: 12px;
  color: #666;
}

.area-actions {
  display: flex;
  align-items: center;
  margin-left: auto;
}

.area-preview {
  margin-top: 8px;
  padding: 6px;
  background-color: #f8f8f8;
  border-radius: 4px;
  border: 1px dashed #e0e0e6;
  max-height: 100px;
  overflow-y: auto;
}

.coordinates-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  gap: 6px;
}

.coordinate-item {
  padding: 4px 6px;
  background-color: #fff;
  border-radius: 3px;
  border: 1px solid #f0f0f0;
  font-size: 11px;
  font-family: monospace;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}


.ml-2 {
  margin-left: 8px;
}

/* 滚动条样式优化 */
.form-container::-webkit-scrollbar {
  width: 4px;
}

.form-container::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 4px;
}

.form-container::-webkit-scrollbar-thumb {
  background: #ddd;
  border-radius: 4px;
}

.form-container::-webkit-scrollbar-thumb:hover {
  background: #ccc;
}

.area-preview::-webkit-scrollbar {
  width: 3px;
}

.area-preview::-webkit-scrollbar-track {
  background: #f1f1f1;
}

.area-preview::-webkit-scrollbar-thumb {
  background: #ddd;
}
</style>