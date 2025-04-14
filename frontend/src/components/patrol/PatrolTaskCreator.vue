<template>
  <div class="patrol-task-creator drawer-container">
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
                  <td>{{ point.lng.toFixed(4) }}</td>
                  <td>{{ point.lat.toFixed(4) }}</td>
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
    <div class="map-container">
      <SecurityMap3D 
        ref="map3dRef"
        @waypoint-added="addWaypoint"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';
import { 
  NForm, 
  NFormItem, 
  NInput, 
  NInputNumber, 
  NRadioGroup, 
  NRadio, 
  NSpace, 
  NButton,
  NTable,
  NDatePicker,
  NTimePicker,
  useMessage
} from 'naive-ui';
import SecurityMap3D from './SecurityMap3D.vue';

const props = defineProps({
  map3dRef: {
    type: Object,
    required: false
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
  waypoints: [],
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
    message: '请选择任务时间',
    trigger: 'change'
  },
  rounds: {
    required: true,
    type: 'number',
    min: 1,
    message: '请输入执行趟数',
    trigger: 'change'
  }
};

const toggleWaypointSelection = () => {
  isSelectingWaypoints.value = !isSelectingWaypoints.value;
  emit('waypoint-selection-change', isSelectingWaypoints.value);
  if (isSelectingWaypoints.value) {
    props.map3dRef.startWaypointSelection(addWaypoint);
  } else {
    props.map3dRef.stopWaypointSelection();
  }
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
    waypoints: [],
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
.patrol-task-creator.drawer-container {
  display: flex;
  height: 100%;
  width: 100%;
  
  .form-container {
    width: 40%;
    min-width: 500px;
    padding: 2vh 2vw;
    overflow-y: auto;
  }
  
  .map-container {
    flex: 1;
    border-left: 1px solid #eee;
    min-width: 60%
  }
}

.waypoints-container {
  border: 1px solid #eee;
  border-radius: 4px;
  padding: 12px;
}

.waypoints-header {
  margin-bottom: 12px;
  
  .waypoints-info {
    margin-bottom: 8px;
    font-size: 14px;
    color: #666;
  }
  
  .waypoints-actions {
    display: flex;
    gap: 8px;
  }
}

.waypoints-list {
  max-height: 300px;
  overflow-y: auto;
  
  :deep(table) {
    width: 100%;
    
    th, td {
      padding: 12px;
      text-align: center;
    }
    
    td:nth-child(2),
    td:nth-child(3) {
      font-family: monospace;
    }
  }
}

.form-actions {
  margin-top: 24px;
  padding-top: 16px;
  border-top: 1px solid #eee;
}
</style>