<template>
  <div class="patrol-task-creator">
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
      
      <n-form-item label="选择无人机" path="droneIds">
        <n-select
          v-model:value="formModel.droneIds"
          multiple
          :options="drones"
          placeholder="请选择执行任务的无人机"
        />
      </n-form-item>

      <n-form-item label="巡逻高度" path="altitude">
        <n-input-number
          v-model:value="formModel.altitude"
          :min="0"
          :max="500"
          placeholder="巡逻高度(米)"
        />
      </n-form-item>

      <n-form-item label="巡逻速度" path="speed">
        <n-input-number
          v-model:value="formModel.speed"
          :min="0"
          :max="20"
          placeholder="巡逻速度(米/秒)"
        />
      </n-form-item>

      <n-form-item label="巡逻模式" path="mode">
        <n-radio-group v-model:value="formModel.mode">
          <n-space>
            <n-radio value="single">单次巡逻</n-radio>
            <n-radio value="loop">循环巡逻</n-radio>
          </n-space>
        </n-radio-group>
      </n-form-item>

      <n-form-item label="巡逻路径" path="waypoints">
        <div class="waypoints-container">
          <div class="waypoints-header">
            <span>已选择 {{ formModel.waypoints.length }} 个路径点</span>
            <n-button 
              size="small" 
              type="primary" 
              @click="toggleWaypointSelection"
            >
              {{ isSelectingWaypoints ? '完成选点' : '在地图上选点' }}
            </n-button>
            <n-button 
              size="small" 
              type="error" 
              @click="clearWaypoints"
              :disabled="formModel.waypoints.length === 0"
            >
              清空路径点
            </n-button>
          </div>
          <div class="waypoints-list" v-if="formModel.waypoints.length > 0">
            <n-table :bordered="false" :single-line="false">
              <thead>
                <tr>
                  <th>序号</th>
                  <th>经度</th>
                  <th>纬度</th>
                  <th>操作</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(point, index) in formModel.waypoints" :key="index">
                  <td>{{ index + 1 }}</td>
                  <td>{{ point.lng }}</td>
                  <td>{{ point.lat }}</td>
                  <td>
                    <n-button 
                      size="tiny" 
                      type="error" 
                      @click="removeWaypoint(index)"
                    >
                      删除
                    </n-button>
                  </td>
                </tr>
              </tbody>
            </n-table>
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
</template>

<script setup>
import { ref, computed } from 'vue';
import { 
  NForm, 
  NFormItem, 
  NInput, 
  NInputNumber, 
  NSelect, 
  NRadioGroup, 
  NRadio, 
  NSpace, 
  NButton,
  NTable,
  useMessage
} from 'naive-ui';

const props = defineProps({
  drones: {
    type: Array,
    default: () => []
  }
});

const emit = defineEmits(['submit', 'waypoint-selection-change']);
const message = useMessage();
const formRef = ref(null);
const isSelectingWaypoints = ref(false);

const formModel = ref({
  name: '',
  droneIds: [],
  altitude: 100,
  speed: 5,
  mode: 'single',
  waypoints: []
});

const rules = {
  name: {
    required: true,
    message: '请输入任务名称',
    trigger: 'blur'
  },
  droneIds: {
    required: true,
    type: 'array',
    min: 1,
    message: '请至少选择一台无人机',
    trigger: 'change'
  },
  altitude: {
    required: true,
    type: 'number',
    message: '请输入巡逻高度',
    trigger: 'change'
  },
  speed: {
    required: true,
    type: 'number',
    message: '请输入巡逻速度',
    trigger: 'change'
  },
  waypoints: {
    required: true,
    type: 'array',
    min: 2,
    message: '请至少选择两个路径点',
    trigger: 'change'
  }
};

const toggleWaypointSelection = () => {
  isSelectingWaypoints.value = !isSelectingWaypoints.value;
  emit('waypoint-selection-change', isSelectingWaypoints.value);
};

const addWaypoint = (coordinates) => {
  formModel.value.waypoints.push(coordinates);
};

const removeWaypoint = (index) => {
  formModel.value.waypoints.splice(index, 1);
};

const clearWaypoints = () => {
  formModel.value.waypoints = [];
};

const resetForm = () => {
  formRef.value?.restoreValidation();
  formModel.value = {
    name: '',
    droneIds: [],
    altitude: 100,
    speed: 5,
    mode: 'single',
    waypoints: []
  };
};

const handleSubmit = () => {
  formRef.value?.validate((errors) => {
    if (!errors) {
      emit('submit', { ...formModel.value });
    } else {
      message.error('请完善表单信息');
    }
  });
};

defineExpose({
  addWaypoint,
  isSelectingWaypoints
});
</script>

<style scoped>
.patrol-task-creator {
  padding: 16px;
}

.waypoints-container {
  border: 1px solid #eee;
  border-radius: 4px;
  padding: 12px;
}

.waypoints-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.waypoints-list {
  max-height: 200px;
  overflow-y: auto;
}

.form-actions {
  margin-top: 24px;
  padding-top: 16px;
  border-top: 1px solid #eee;
}
</style>