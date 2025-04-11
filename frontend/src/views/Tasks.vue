<template>
  <div class="h-full flex flex-col p-4">
    <div class="flex justify-between items-center mb-4">
      <h1 class="text-2xl font-bold">任务管理</h1>
      <div class="actions">
        <n-button type="primary" @click="showCreateTaskModal = true">
          <template #icon><n-icon><plus-outlined /></n-icon></template>
          创建任务
        </n-button>
      </div>
    </div>
    
    <div class="flex-1 overflow-auto">
      <n-tabs v-model:value="activeTab" type="line">
        <n-tab-pane name="active" tab="进行中">
          <n-data-table
            :columns="activeTaskColumns"
            :data="activeTasks"
            :loading="loading"
            :pagination="pagination"
            :row-key="row => row.id"
          />
        </n-tab-pane>
        
        <n-tab-pane name="completed" tab="已完成">
          <n-data-table
            :columns="completedTaskColumns"
            :data="completedTasks"
            :loading="loading"
            :pagination="pagination"
            :row-key="row => row.id"
          />
        </n-tab-pane>
      </n-tabs>
    </div>
    
    <!-- 创建任务对话框 -->
    <n-modal
      v-model:show="showCreateTaskModal"
      title="创建新任务"
      preset="card"
      style="width: 600px"
    >
      <n-form
        ref="taskFormRef"
        :model="newTask"
        label-placement="left"
        label-width="100px"
      >
        <n-form-item label="任务名称" path="name" :rule="{ required: true, message: '请输入任务名称' }">
          <n-input v-model:value="newTask.name" placeholder="输入任务名称" />
        </n-form-item>
        <n-form-item label="任务类型" path="type" :rule="{ required: true, message: '请选择任务类型' }">
          <n-select 
            v-model:value="newTask.type" 
            placeholder="选择任务类型"
            :options="taskTypeOptions"
          />
        </n-form-item>
        <n-form-item label="分配无人机" path="droneId" :rule="{ required: true, message: '请选择无人机' }">
          <n-select 
            v-model:value="newTask.droneId" 
            placeholder="选择可用无人机"
            :options="droneOptions"
            :loading="loadingDrones"
          />
        </n-form-item>
        <n-form-item label="描述" path="description">
          <n-input 
            v-model:value="newTask.description" 
            type="textarea" 
            placeholder="输入任务描述"
          />
        </n-form-item>
        <n-form-item label="起始位置" path="startLocation">
          <n-input v-model:value="newTask.startLocation" placeholder="输入坐标或地址">
            <template #suffix>
              <n-button text type="primary" @click="selectOnMap('start')">地图选择</n-button>
            </template>
          </n-input>
        </n-form-item>
        <n-form-item label="目标位置" path="destination">
          <n-input v-model:value="newTask.destination" placeholder="输入坐标或地址">
            <template #suffix>
              <n-button text type="primary" @click="selectOnMap('destination')">地图选择</n-button>
            </template>
          </n-input>
        </n-form-item>
      </n-form>
      
      <template #footer>
        <div class="flex justify-end space-x-3">
          <n-button @click="showCreateTaskModal = false">取消</n-button>
          <n-button type="primary" @click="submitTask" :loading="submittingTask">创建</n-button>
        </div>
      </template>
    </n-modal>
    
    <!-- 任务详情对话框 -->
    <n-modal
      v-model:show="showTaskDetailsModal"
      title="任务详情"
      preset="card"
      style="width: 700px"
    >
      <div v-if="selectedTask" class="space-y-4">
        <n-descriptions label-placement="left" bordered :column="2">
          <n-descriptions-item label="任务ID">{{ selectedTask.id }}</n-descriptions-item>
          <n-descriptions-item label="名称">{{ selectedTask.name }}</n-descriptions-item>
          <n-descriptions-item label="类型">
            <n-tag :type="getTagType(selectedTask.type)">{{ selectedTask.type }}</n-tag>
          </n-descriptions-item>
          <n-descriptions-item label="状态">
            <n-tag :type="getTagType(selectedTask.status)">{{ selectedTask.status }}</n-tag>
          </n-descriptions-item>
          <n-descriptions-item label="创建时间">
            {{ formatDateTime(selectedTask.createdAt) }}
          </n-descriptions-item>
          <n-descriptions-item label="完成时间">
            {{ selectedTask.completedAt ? formatDateTime(selectedTask.completedAt) : '未完成' }}
          </n-descriptions-item>
          <n-descriptions-item label="分配无人机">
            {{ selectedTask.drone?.name || selectedTask.droneId || '未分配' }}
          </n-descriptions-item>
          <n-descriptions-item label="进度">
            <n-progress 
              type="line" 
              :percentage="selectedTask.progress || 0"
              :status="selectedTask.status === 'failed' ? 'error' : selectedTask.status === 'completed' ? 'success' : 'processing'"
            />
          </n-descriptions-item>
          <n-descriptions-item label="描述" :span="2">
            {{ selectedTask.description || '无描述' }}
          </n-descriptions-item>
        </n-descriptions>
        
        <div class="h-64 bg-gray-100 rounded-lg overflow-hidden">
          <Map3D 
            ref="taskDetailsMapRef" 
            :initial-coordinates="selectedTask.startLocation"
            :show-task-route="true"
            :task-data="selectedTask"
          />
        </div>
      </div>
    </n-modal>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, h } from 'vue';
import { 
  NButton, 
  NTabs, 
  NTabPane, 
  NDataTable, 
  NTag, 
  NProgress, 
  NModal, 
  NForm, 
  NFormItem, 
  NInput, 
  NSelect, 
  NDescriptions, 
  NDescriptionsItem, 
  NIcon, 
  useNotification, 
  useMessage, 
  useDialog 
} from 'naive-ui';
import { PlusOutlined, EyeOutlined, StopOutlined } from '@vicons/antd';
import { format } from 'date-fns';
import Map3D from '@/components/map/Map3D.vue';
import * as taskApi from '@/api/task';
import * as droneApi from '@/api/drone';

const notification = useNotification();
const message = useMessage();
const dialog = useDialog();

// 状态
const loading = ref(false);
const loadingDrones = ref(false);
const submittingTask = ref(false);
const tasks = ref([]);
const availableDrones = ref([]);
const activeTab = ref('active');
const showCreateTaskModal = ref(false);
const showTaskDetailsModal = ref(false);
const selectedTask = ref(null);
const taskFormRef = ref(null);
const taskDetailsMapRef = ref(null);

// 分页
const pagination = ref({ pageSize: 10 });

// 新任务表单
const newTask = ref({
  name: '',
  type: '',
  description: '',
  droneId: null,
  startLocation: '',
  destination: '',
  waypoints: []
});

// 任务类型选项
const taskTypeOptions = [
  { label: '配送', value: 'delivery' },
  { label: '测绘', value: 'survey' },
  { label: '巡检', value: 'inspection' },
  { label: '摄影', value: 'photography' },
  { label: '安防', value: 'security' }
];

// 无人机选项
const droneOptions = computed(() => 
  availableDrones.value.map(d => ({ label: `${d.name} (${d.id})`, value: d.id }))
);

// 获取数据
const fetchTasks = async () => {
  loading.value = true;
  try {
    const { data } = await taskApi.getTasks();
    // 假设API返回的数据直接是任务列表
    tasks.value = data.map(task => ({ ...task, createdAt: new Date(task.createdAt) })); // 示例：转换日期
  } catch (error) {
    console.error('获取任务列表失败:', error);
    notification.error({
      title: '错误',
      content: '无法加载任务列表',
      duration: 3000
    });
  } finally {
    loading.value = false;
  }
};
    
const fetchAvailableDrones = async () => {
  loadingDrones.value = true;
  try {
    const { data } = await droneApi.getDrones({ status: 'available' }); // 或 'idle'
    availableDrones.value = data;
  } catch (error) {
    console.error('获取可用无人机失败:', error);
    notification.error({
      title: '错误',
      content: '无法加载可用无人机列表',
      duration: 3000
    });
  } finally {
    loadingDrones.value = false;
  }
};
    
// 计算属性：筛选任务
const activeTasks = computed(() => {
  return tasks.value.filter(task => 
    !['completed', 'cancelled', 'failed'].includes(task.status)
  );
});
    
const completedTasks = computed(() => {
  return tasks.value.filter(task => 
    ['completed', 'cancelled', 'failed'].includes(task.status)
  );
});

// 表格列定义 (使用渲染函数来创建按钮和标签)
const createColumns = (isActiveList) => [
  {
    title: 'ID',
    key: 'id',
    width: 80
  },
  {
    title: '名称',
    key: 'name',
    ellipsis: { tooltip: true }
  },
  {
    title: '类型',
    key: 'type',
    width: 100,
    render(row) {
      return h(NTag, { type: getTagType(row.type) }, { default: () => row.type });
    }
  },
  {
    title: '无人机',
    key: 'droneId',
    width: 120,
    ellipsis: { tooltip: true }
  },
  {
    title: '进度',
    key: 'progress',
    width: 150,
    render(row) {
      return h(NProgress, { 
        type: 'line', 
        percentage: row.progress || 0,
        status: row.status === 'failed' ? 'error' : row.status === 'completed' ? 'success' : 'processing'
      });
    }
  },
  {
    title: '状态',
    key: 'status',
    width: 100,
    render(row) {
      return h(NTag, { type: getTagType(row.status) }, { default: () => row.status });
    }
  },
  {
    title: '创建时间',
    key: 'createdAt',
    width: 180,
    render(row) {
      return formatDateTime(row.createdAt);
    }
  },
  ...(isActiveList ? [
    {
      title: '操作',
      key: 'actions',
      width: 150,
      fixed: 'right',
      render(row) {
        return h(NSpace, null, {
          default: () => [
            h(NButton, 
              { size: 'small', onClick: () => viewTask(row) }, 
              { default: () => '查看', icon: () => h(NIcon, null, { default: () => h(EyeOutlined) }) }
            ),
            h(NButton, 
              { size: 'small', type: 'error', onClick: () => confirmCancelTask(row), disabled: !['pending', 'in-progress'].includes(row.status) }, 
              { default: () => '取消', icon: () => h(NIcon, null, { default: () => h(StopOutlined) }) }
            )
          ]
        });
      }
    }
  ] : [
    {
      title: '完成时间',
      key: 'completedAt',
      width: 180,
      render(row) {
        return row.completedAt ? formatDateTime(row.completedAt) : 'N/A';
      }
    },
    {
      title: '操作',
      key: 'actions',
      width: 100,
      fixed: 'right',
      render(row) {
        return h(NButton, 
          { size: 'small', onClick: () => viewTask(row) }, 
          { default: () => '详情' }
        );
      }
    }
  ])
];

const activeTaskColumns = computed(() => createColumns(true));
const completedTaskColumns = computed(() => createColumns(false));

// 获取标签类型
const getTagType = (typeOrStatus) => {
  const typeMap = {
    'delivery': 'success',
    'survey': 'info',
    'inspection': 'warning',
    'photography': 'primary',
    'security': 'error',
    'pending': 'default',
    'in-progress': 'info',
    'completed': 'success',
    'failed': 'error',
    'cancelled': 'warning'
  };
  return typeMap[typeOrStatus] || 'default';
};

// 格式化时间
const formatDateTime = (date) => {
  try {
    return date ? format(new Date(date), 'yyyy-MM-dd HH:mm:ss') : 'N/A';
  } catch (e) {
    return 'Invalid Date';
  }
};

// 查看任务详情
const viewTask = (task) => {
  selectedTask.value = task;
  showTaskDetailsModal.value = true;
};

// 确认取消任务
const confirmCancelTask = (task) => {
  dialog.warning({
    title: '确认取消',
    content: `确定要取消任务 "${task.name}" 吗？`,
    positiveText: '确定取消',
    negativeText: '不了',
    onPositiveClick: async () => {
      try {
        await taskApi.cancelTask(task.id);
        notification.success({
          title: '成功',
          content: '任务已取消',
          duration: 3000
        });
        fetchTasks(); // 刷新列表
      } catch (error) {
        console.error('取消任务失败:', error);
        notification.error({
          title: '错误',
          content: '无法取消任务',
          duration: 3000
        });
      }
    }
  });
};
    
// 地图选择（模拟）
const selectOnMap = (locationType) => {
  message.info(`请在地图上选择${locationType === 'start' ? '起始' : '目标'}位置 (功能待实现)`);
  // 实际应用中会打开地图交互让用户选择坐标
};
    
// 提交新任务
const submitTask = async () => {
  taskFormRef.value?.validate(async (errors) => {
    if (errors) {
      message.error('请检查表单输入');
      return;
    }
        
    submittingTask.value = true;
    try {
      const taskData = { ...newTask.value };
      // TODO: 处理坐标字符串到实际坐标对象
      
      await taskApi.createTask(taskData);
      
      notification.success({
        title: '成功',
        content: '新任务已创建',
        duration: 3000
      });
      
      showCreateTaskModal.value = false;
      fetchTasks(); // 刷新列表
      
      // 重置表单
      newTask.value = {
        name: '', type: '', description: '', droneId: null, 
        startLocation: '', destination: '', waypoints: []
      };
    } catch (error) {
      console.error('创建任务失败:', error);
      notification.error({
        title: '错误',
        content: '创建任务失败',
        duration: 3000
      });
    } finally {
      submittingTask.value = false;
    }
  });
};
    
onMounted(() => {
  fetchTasks();
  fetchAvailableDrones();
});
</script>

<style scoped>
.tasks-container {
  height: 100%;
  display: flex;
  flex-direction: column;
}
</style> 