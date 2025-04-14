<template>
  <div class="patrol-task-creator">
    <div class="form-container">
    <n-form
      ref="formRef"
      :model="formModel"
      :rules="rules"
      label-placement="left"
      label-width="100"
      require-mark-placement="right-hanging"
    >
      <n-form-item label="任务名称" path="name">
        <n-input v-model:value="formModel.name" placeholder="请输入任务名称" />
      </n-form-item>

      <n-form-item label="巡逻速度" path="speed">
        <n-input-number
          v-model:value="formModel.speed"
          :min="1"
          :max="20"
          placeholder="巡逻速度(米/秒)"
        >
         <template #suffix>
            米/秒
          </template>
        </n-input-number>
      </n-form-item>

      <n-form-item label="任务时段" path="scheduleType">
        <n-radio-group v-model:value="formModel.scheduleType">
          <n-space>
            <n-radio value="date">指定日期</n-radio>
            <n-radio value="week">每周</n-radio>
          </n-space>
        </n-radio-group>
        <n-space vertical>
          <n-date-picker
            v-if="formModel.scheduleType === 'date'"
            v-model:value="formModel.date"
            type="date"
            placeholder="选择日期"
            clearable
          />
          <n-select
            v-if="formModel.scheduleType === 'week'"
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
          />
          <n-time-picker
            v-model:value="formModel.time"
            format="HH:mm"
            placeholder="选择时间"
            clearable
          />
        </n-space>
      </n-form-item>

      <n-form-item label="执行趟数" path="rounds">
        <n-input-number
          v-model:value="formModel.rounds"
          :min="1"
          placeholder="执行趟数"
        />
      </n-form-item>

      <n-form-item label="巡逻区域" path="patrolArea">
        <div class="area-container">
          <div class="area-info">
            <span v-if="formModel.patrolArea.length === 0">尚未绘制巡逻区域</span>
            <span v-else>已绘制区域，包含 {{ formModel.patrolArea.length - 1 }} 个顶点</span>
            <n-button 
              size="small" 
              :type="isDrawingArea ? 'warning' : 'primary'" 
              @click="toggleAreaDrawing"
              class="ml-2"
            >
              {{ isDrawingArea ? '取消绘制' : '绘制巡逻区域' }}
            </n-button>
            <n-button 
              v-if="formModel.patrolArea.length > 0 && !isDrawingArea"
              size="small" 
              type="error" 
              @click="clearPatrolArea"
              class="ml-2"
            >
              清除区域
            </n-button>
          </div>
          <div v-if="formModel.patrolArea.length > 0 && !isDrawingArea" class="area-preview text-xs text-gray-500 mt-1">
            区域顶点: {{ formModel.patrolArea.map(p => `(${p[0].toFixed(4)}, ${p[1].toFixed(4)})`).join(', ') }}
          </div>
        </div>
      </n-form-item>

      <div class="form-actions">
        <n-space justify="end">
          <n-button @click="resetForm">重置</n-button>
          <n-button type="primary" @click="handleSubmit">创建任务</n-button>
        </n-space>
      </div>
    </n-form>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, inject, onMounted, onUnmounted } from 'vue';
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
  useMessage
} from 'naive-ui';

const props = defineProps({
  // 移除 map3dRef prop，我们将注入全局 mapRef
});

const emit = defineEmits(['submit']); // 移除 'waypoint-selection-change'
const message = useMessage();
const formRef = ref(null);
const isDrawingArea = ref(false); // 新状态：是否正在绘制区域

// 注入全局地图引用
const mapRef = inject('mapRef', ref(null)); // 提供默认值以防万一

const formModel = ref({
  name: '',
  speed: 5,
  patrolArea: [], // 替换 waypoints
  scheduleType: 'date',
  date: null,
  weekdays: [],
  time: null,
  rounds: 1
});

const rules = {
  name: {
    required: true,
    message: '请输入任务名称',
    trigger: 'blur'
  },
  speed: {
    required: true,
    type: 'number',
    min: 1,
    max: 20,
    message: '请输入有效的巡逻速度 (1-20米/秒)',
    trigger: ['input', 'blur']
  },
  patrolArea: { // 更新验证规则
    required: true,
    type: 'array',
    validator: (rule, value) => value && value.length >= 4, // 至少3个顶点+闭合点
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
  }
};

const toggleAreaDrawing = () => {
  if (!mapRef.value) {
    message.error("地图实例尚未准备好");
    return;
  }
  isDrawingArea.value = !isDrawingArea.value;
  if (isDrawingArea.value) {
    // 进入绘制模式前清除可能存在的旧区域
    formModel.value.patrolArea = []; 
    mapRef.value.startDrawingPatrolArea(); // 调用地图组件的方法开始绘制
    message.info("请在地图上点击绘制巡逻区域顶点，至少3个点。")
  } else {
    mapRef.value.cancelDrawingPatrolArea(); // 调用地图组件的方法取消绘制
  }
};

const clearPatrolArea = () => {
  formModel.value.patrolArea = [];
  // 如果需要，也可以通知地图清除可能显示的旧区域（如果地图组件支持的话）
};

const handleAreaDrawn = (event) => {
  // event.detail 应该包含坐标数组
  const areaCoordinates = event.detail;
  if (areaCoordinates && areaCoordinates.length >= 4) { // 至少3个顶点 + 闭合点
    formModel.value.patrolArea = areaCoordinates;
    isDrawingArea.value = false; // 绘制完成，退出绘制模式
    message.success(`巡逻区域绘制完成，包含 ${areaCoordinates.length - 1} 个顶点。`);
    formRef.value?.validateField('patrolArea'); // 手动触发验证
  } else {
    message.error("绘制的区域无效，请重新绘制。");
    // 可能需要调用 mapRef.value.cancelDrawingPatrolArea() 再次确保清除状态
    if (mapRef.value && mapRef.value.cancelDrawingPatrolArea) {
      mapRef.value.cancelDrawingPatrolArea();
    }
    isDrawingArea.value = false; 
  }
};

const resetForm = () => {
  formRef.value?.restoreValidation();
  // 如果正在绘制，取消绘制
  if (isDrawingArea.value && mapRef.value && mapRef.value.cancelDrawingPatrolArea) {
      mapRef.value.cancelDrawingPatrolArea();
      isDrawingArea.value = false;
  }
  formModel.value = {
    name: '',
    speed: 5,
    patrolArea: [],
    scheduleType: 'date',
    date: null,
    weekdays: [],
    time: null,
    rounds: 1
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
      // 可以在这里对 patrolArea 做进一步处理，例如发送到后端
      console.log('Form Data:', formModel.value);
      emit('submit', { ...formModel.value });
      message.success("巡逻任务创建请求已提交");
      // 可以在提交后重置表单
      // resetForm(); 
    } else {
      console.log('Validation Errors:', errors)
      message.error('请检查表单信息是否完整且有效');
    }
  });
};

// 在组件挂载时监听地图事件
onMounted(() => {
  // 监听 Map3D 发出的 patrol-area-drawn 事件
  // 注意：这里假设事件是全局派发的，或者通过某种方式传递
  // 如果 Map3D 是通过 provide/inject 或 props 传递的，需要相应调整监听方式
  // 假设使用 window 全局事件 (如果 Map3D 是这样派发的)
  window.addEventListener('patrol-area-drawn', handleAreaDrawn);
});

// 在组件卸载时移除监听器
onUnmounted(() => {
  window.removeEventListener('patrol-area-drawn', handleAreaDrawn);
  // 如果正在绘制，确保取消
  if (isDrawingArea.value && mapRef.value && mapRef.value.cancelDrawingPatrolArea) {
      mapRef.value.cancelDrawingPatrolArea();
  }
});
</script>

<style scoped>
.patrol-task-creator {
  display: flex;
  flex-direction: column;
  height: 100%;
  width: 100%;
  background-color: #f8f9fa; /* Optional: Add a background color */
}

.form-container {
  width: 100%;
  padding: 20px; /* Increased padding */
  overflow-y: auto;
  max-height: calc(100vh - 100px); /* Adjust based on header height */
  background-color: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.area-container { /* 替换 waypoints-container */
  border: 1px solid #e0e0e6;
  border-radius: 3px;
  padding: 12px;
  width: 100%; /* Ensure it takes full width */
  background-color: #fdfdfd;
}

.area-info {
  display: flex;
  align-items: center;
  justify-content: space-between; /* Adjust alignment */
  margin-bottom: 8px;
  font-size: 14px;
  color: #333;
}

.area-preview {
  margin-top: 8px;
  padding: 8px;
  background-color: #f8f8f8;
  border-radius: 3px;
  word-break: break-all; /* Prevent long coordinate strings from overflowing */
}

.form-actions {
  margin-top: 24px;
  padding-top: 16px;
  border-top: 1px solid #e0e0e6;
}

/* Helper class for margin */
.ml-2 {
  margin-left: 8px;
}
</style>