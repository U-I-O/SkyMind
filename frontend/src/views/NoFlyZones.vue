<template>
  <div class="h-full flex flex-col p-4">
    <div class="flex justify-between items-center mb-4">
      <h1 class="text-2xl font-bold">禁飞区管理</h1>
      <div class="flex gap-2">
        <n-button 
          type="primary" 
          @click="showAddZoneModal = true"
        >
          <template #icon>
            <n-icon><plus-outlined /></n-icon>
          </template>
          新增禁飞区
        </n-button>
        <n-button 
          :loading="loading" 
          @click="refreshData"
        >
          <template #icon>
            <n-icon><reload-outlined /></n-icon>
          </template>
          刷新
        </n-button>
      </div>
    </div>
    
    <div class="grid grid-cols-12 gap-4 flex-1">
      <!-- 地图显示区域 -->
      <div class="col-span-8 card p-0 overflow-hidden rounded-lg shadow">
        <div class="h-full">
          <Map3D 
            ref="mapRef"
            :show-no-fly-zones="true"
            :selected-zone="selectedZone"
            @map-click="handleMapClick"
          />
          
          <!-- 创建区域模式指示 -->
          <div v-if="drawingMode" class="absolute top-4 left-4 bg-white/90 p-3 rounded-lg shadow-md z-10">
            <div class="text-sm font-bold mb-2">绘制模式</div>
            <div class="text-xs text-gray-600 mb-2">点击地图添加点，双击结束</div>
            <div class="flex space-x-2">
              <n-button size="tiny" @click="cancelDrawing">取消</n-button>
              <n-button size="tiny" type="primary" @click="finishDrawing">完成</n-button>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 禁飞区列表 -->
      <div class="col-span-4 flex flex-col gap-4">
        <div class="bg-white p-4 rounded-lg shadow">
          <h3 class="text-lg font-medium mb-4">禁飞区列表</h3>
          <div class="overflow-y-auto max-h-[400px]">
            <div 
              v-for="zone in noFlyZones" 
              :key="zone.id"
              class="p-3 rounded-md cursor-pointer mb-2 transition-colors"
              :class="selectedZone?.id === zone.id ? 'bg-blue-50' : 'hover:bg-gray-50'"
              @click="selectZone(zone)"
            >
              <div class="flex justify-between">
                <div class="font-medium">{{ zone.name }}</div>
                <n-tag :type="zone.active ? 'success' : 'default'">
                  {{ zone.active ? '激活' : '未激活' }}
                </n-tag>
              </div>
              <div class="text-sm text-gray-500 mt-1">
                {{ zone.description || '无描述' }}
              </div>
              <div class="text-xs text-gray-400 mt-1">
                {{ formatDate(zone.createdAt) }} 创建
              </div>
            </div>
            <div v-if="noFlyZones.length === 0" class="text-center text-gray-500 py-4">
              暂无禁飞区数据
            </div>
          </div>
        </div>
        
        <!-- 禁飞区详细信息 -->
        <div v-if="selectedZone" class="bg-white p-4 rounded-lg shadow flex-1">
          <div class="flex justify-between items-center mb-4">
            <h3 class="text-lg font-medium">禁飞区详情</h3>
            <div class="flex space-x-2">
              <n-button size="small" @click="editSelectedZone">
                编辑
              </n-button>
              <n-button size="small" type="error" @click="confirmDeleteZone">
                删除
              </n-button>
            </div>
          </div>
          
          <n-descriptions bordered size="small" :column="1">
            <n-descriptions-item label="ID">{{ selectedZone.id }}</n-descriptions-item>
            <n-descriptions-item label="名称">{{ selectedZone.name }}</n-descriptions-item>
            <n-descriptions-item label="状态">
              <n-tag :type="selectedZone.active ? 'success' : 'default'">
                {{ selectedZone.active ? '激活' : '未激活' }}
              </n-tag>
            </n-descriptions-item>
            <n-descriptions-item label="类型">
              {{ getZoneTypeName(selectedZone.type) }}
            </n-descriptions-item>
            <n-descriptions-item label="半径" v-if="selectedZone.type === 'circle'">
              {{ selectedZone.radius }} 米
            </n-descriptions-item>
            <n-descriptions-item label="顶点数" v-if="selectedZone.type === 'polygon'">
              {{ selectedZone.coordinates.length }} 个
            </n-descriptions-item>
            <n-descriptions-item label="高度限制">
              {{ selectedZone.maxAltitude || '无限制' }} 米
            </n-descriptions-item>
            <n-descriptions-item label="生效时间">
              {{ selectedZone.startTime ? formatDateTime(selectedZone.startTime) : '永久' }}
            </n-descriptions-item>
            <n-descriptions-item label="结束时间">
              {{ selectedZone.endTime ? formatDateTime(selectedZone.endTime) : '永久' }}
            </n-descriptions-item>
            <n-descriptions-item label="创建时间">
              {{ formatDateTime(selectedZone.createdAt) }}
            </n-descriptions-item>
          </n-descriptions>
          
          <div class="mt-4">
            <div class="font-medium mb-2">描述:</div>
            <div class="text-sm p-3 bg-gray-50 rounded-md">
              {{ selectedZone.description || '无描述' }}
            </div>
          </div>
          
          <div class="mt-4 flex justify-between">
            <n-button 
              :type="selectedZone.active ? 'warning' : 'success'"
              @click="toggleZoneStatus"
            >
              {{ selectedZone.active ? '停用' : '激活' }}
            </n-button>
            <n-button 
              type="primary"
              @click="centerOnZone"
            >
              <template #icon>
                <n-icon><environment-outlined /></n-icon>
              </template>
              在地图上查看
            </n-button>
          </div>
        </div>
        
        <div v-else class="bg-white p-4 rounded-lg shadow flex-1 flex items-center justify-center text-gray-400">
          请选择一个禁飞区查看详情
        </div>
      </div>
    </div>
    
    <!-- 添加禁飞区对话框 -->
    <n-modal
      v-model:show="showAddZoneModal"
      :title="isEditing ? '编辑禁飞区' : '添加禁飞区'"
      preset="card"
      style="width: 500px"
    >
      <n-form
        ref="zoneFormRef"
        :model="zoneForm"
        label-placement="left"
        label-width="auto"
      >
        <n-form-item label="名称" path="name" :rule="{ required: true, message: '请输入名称' }">
          <n-input v-model:value="zoneForm.name" placeholder="输入禁飞区名称" />
        </n-form-item>
        
        <n-form-item label="类型" path="type">
          <n-radio-group v-model:value="zoneForm.type" name="zoneType">
            <n-space>
              <n-radio value="polygon">多边形区域</n-radio>
              <n-radio value="circle">圆形区域</n-radio>
            </n-space>
          </n-radio-group>
        </n-form-item>
        
        <n-form-item v-if="zoneForm.type === 'circle'" label="圆心坐标">
          <div class="flex space-x-2">
            <n-input-number v-model:value="zoneForm.center.lat" placeholder="纬度" />
            <n-input-number v-model:value="zoneForm.center.lng" placeholder="经度" />
            <n-button size="small" @click="drawingMode = true; showAddZoneModal = false">
              在地图上选择
            </n-button>
          </div>
        </n-form-item>
        
        <n-form-item v-if="zoneForm.type === 'circle'" label="半径(米)" path="radius">
          <n-input-number v-model:value="zoneForm.radius" :min="10" :max="10000" />
        </n-form-item>
        
        <n-form-item v-if="zoneForm.type === 'polygon'" label="区域坐标">
          <n-button block @click="drawingMode = true; showAddZoneModal = false">
            在地图上绘制区域
          </n-button>
          <div v-if="zoneForm.coordinates.length > 0" class="mt-2 text-xs text-gray-500">
            已添加 {{ zoneForm.coordinates.length }} 个坐标点
          </div>
        </n-form-item>
        
        <n-form-item label="最大高度(米)" path="maxAltitude">
          <n-input-number v-model:value="zoneForm.maxAltitude" :min="0" :max="500" placeholder="不填则无限制" />
        </n-form-item>
        
        <n-form-item label="时间限制">
          <n-switch v-model:value="hasTimeLimit" />
        </n-form-item>
        
        <template v-if="hasTimeLimit">
          <n-form-item label="开始时间" path="startTime">
            <n-date-picker 
              v-model:value="zoneForm.startTime"
              type="datetime"
              clearable
            />
          </n-form-item>
          
          <n-form-item label="结束时间" path="endTime">
            <n-date-picker 
              v-model:value="zoneForm.endTime"
              type="datetime"
              clearable
            />
          </n-form-item>
        </template>
        
        <n-form-item label="描述" path="description">
          <n-input 
            v-model:value="zoneForm.description" 
            type="textarea" 
            placeholder="输入禁飞区描述信息" 
          />
        </n-form-item>
        
        <n-form-item label="立即激活">
          <n-switch v-model:value="zoneForm.active" />
        </n-form-item>
      </n-form>
      
      <template #footer>
        <div class="flex justify-end space-x-3">
          <n-button @click="showAddZoneModal = false">取消</n-button>
          <n-button type="primary" @click="submitZoneForm">确定</n-button>
        </div>
      </template>
    </n-modal>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { format } from 'date-fns'
import { 
  NButton, 
  NTag, 
  NDescriptions, 
  NDescriptionsItem,
  NModal, 
  NForm,
  NFormItem,
  NInput,
  NInputNumber,
  NSwitch,
  NRadioGroup,
  NRadio,
  NSpace,
  NDatePicker,
  NIcon,
  useNotification,
  useMessage,
  useDialog
} from 'naive-ui'
import { 
  ReloadOutlined,
  PlusOutlined,
  EnvironmentOutlined
} from '@vicons/antd'
import Map3D from '../components/map/Map3D_WG.vue'

// UI组件
const message = useMessage()
const notification = useNotification()
const dialog = useDialog()

// 组件状态
const loading = ref(false)
const noFlyZones = ref([])
const selectedZone = ref(null)
const mapRef = ref(null)

// 表单状态
const zoneFormRef = ref(null)
const showAddZoneModal = ref(false)
const isEditing = ref(false)
const drawingMode = ref(false)
const hasTimeLimit = ref(false)

// 表单数据
const defaultZoneForm = {
  name: '',
  type: 'polygon',
  coordinates: [],
  center: { lat: 0, lng: 0 },
  radius: 500,
  maxAltitude: null,
  startTime: null,
  endTime: null,
  description: '',
  active: true
}
const zoneForm = reactive({...defaultZoneForm})

// 生命周期钩子
onMounted(() => {
  refreshData()
})

// 方法
const refreshData = async () => {
  loading.value = true
  try {
    // 这里应该是API调用
    await mockFetchNoFlyZones()
    message.success('数据已刷新')
  } catch (error) {
    console.error('刷新数据出错:', error)
    notification.error({
      title: '错误',
      content: '刷新数据失败',
      duration: 3000
    })
  } finally {
    loading.value = false
  }
}

const selectZone = (zone) => {
  selectedZone.value = zone
}

const centerOnZone = () => {
  if (!selectedZone.value || !mapRef.value) return
  
  if (selectedZone.value.type === 'circle') {
    // mapRef.value.flyTo(selectedZone.value.center)
  } else {
    // 计算多边形中心点
    const coords = selectedZone.value.coordinates
    if (coords && coords.length > 0) {
      const center = coords.reduce(
        (acc, coord) => ({ lat: acc.lat + coord.lat, lng: acc.lng + coord.lng }),
        { lat: 0, lng: 0 }
      )
      center.lat /= coords.length
      center.lng /= coords.length
      
      // mapRef.value.flyTo(center)
    }
  }
}

const editSelectedZone = () => {
  if (!selectedZone.value) return
  
  isEditing.value = true
  
  // 填充表单
  Object.assign(zoneForm, selectedZone.value)
  
  // 设置时间限制
  hasTimeLimit.value = !!(zoneForm.startTime || zoneForm.endTime)
  
  showAddZoneModal.value = true
}

const confirmDeleteZone = () => {
  if (!selectedZone.value) return
  
  dialog.warning({
    title: '确认删除',
    content: `确定要删除禁飞区 "${selectedZone.value.name}" 吗？此操作不可撤销。`,
    positiveText: '确定',
    negativeText: '取消',
    onPositiveClick: () => deleteZone(selectedZone.value.id)
  })
}

const deleteZone = async (zoneId) => {
  try {
    // 这里应该是API调用
    await mockDeleteZone(zoneId)
    
    // 更新本地数据
    noFlyZones.value = noFlyZones.value.filter(zone => zone.id !== zoneId)
    
    if (selectedZone.value && selectedZone.value.id === zoneId) {
      selectedZone.value = null
    }
    
    notification.success({
      title: '成功',
      content: '禁飞区已删除',
      duration: 3000
    })
  } catch (error) {
    console.error('删除禁飞区出错:', error)
    notification.error({
      title: '错误',
      content: '删除禁飞区失败',
      duration: 3000
    })
  }
}

const toggleZoneStatus = async () => {
  if (!selectedZone.value) return
  
  try {
    // 这里应该是API调用
    const newStatus = !selectedZone.value.active
    await mockUpdateZoneStatus(selectedZone.value.id, newStatus)
    
    // 更新本地数据
    const index = noFlyZones.value.findIndex(zone => zone.id === selectedZone.value.id)
    if (index !== -1) {
      noFlyZones.value[index].active = newStatus
      selectedZone.value.active = newStatus
    }
    
    notification.success({
      title: '成功',
      content: newStatus ? '禁飞区已激活' : '禁飞区已停用',
      duration: 3000
    })
  } catch (error) {
    console.error('更新禁飞区状态出错:', error)
    notification.error({
      title: '错误',
      content: '更新禁飞区状态失败',
      duration: 3000
    })
  }
}

const handleMapClick = (coords) => {
  if (!drawingMode.value) return
  
  if (zoneForm.type === 'circle') {
    // 设置圆心
    zoneForm.center = coords
    drawingMode.value = false
    showAddZoneModal.value = true
  } else if (zoneForm.type === 'polygon') {
    // 添加多边形顶点
    zoneForm.coordinates.push(coords)
  }
}

const finishDrawing = () => {
  if (!drawingMode.value) return
  
  if (zoneForm.type === 'polygon' && zoneForm.coordinates.length < 3) {
    message.warning('多边形需要至少3个顶点')
    return
  }
  
  drawingMode.value = false
  showAddZoneModal.value = true
}

const cancelDrawing = () => {
  drawingMode.value = false
  if (zoneForm.type === 'polygon') {
    zoneForm.coordinates = []
  }
  showAddZoneModal.value = true
}

const submitZoneForm = async () => {
  if (zoneForm.type === 'polygon' && zoneForm.coordinates.length < 3) {
    message.warning('多边形需要至少3个顶点')
    return
  }
  
  if (zoneForm.type === 'circle' && (!zoneForm.center.lat || !zoneForm.center.lng)) {
    message.warning('请设置圆心坐标')
    return
  }
  
  // 处理时间限制
  if (!hasTimeLimit.value) {
    zoneForm.startTime = null
    zoneForm.endTime = null
  }
  
  try {
    if (isEditing.value) {
      // 更新现有禁飞区
      await mockUpdateZone(zoneForm)
      
      // 更新本地数据
      const index = noFlyZones.value.findIndex(zone => zone.id === zoneForm.id)
      if (index !== -1) {
        noFlyZones.value[index] = {...zoneForm}
        
        if (selectedZone.value && selectedZone.value.id === zoneForm.id) {
          selectedZone.value = noFlyZones.value[index]
        }
      }
      
      notification.success({
        title: '成功',
        content: '禁飞区已更新',
        duration: 3000
      })
    } else {
      // 创建新禁飞区
      const newZone = await mockCreateZone(zoneForm)
      
      // 添加到本地数据
      noFlyZones.value.push(newZone)
      
      notification.success({
        title: '成功',
        content: '禁飞区已创建',
        duration: 3000
      })
    }
    
    // 重置表单
    resetForm()
  } catch (error) {
    console.error('提交禁飞区数据出错:', error)
    notification.error({
      title: '错误',
      content: isEditing.value ? '更新禁飞区失败' : '创建禁飞区失败',
      duration: 3000
    })
  }
}

const resetForm = () => {
  Object.assign(zoneForm, defaultZoneForm)
  hasTimeLimit.value = false
  isEditing.value = false
  showAddZoneModal.value = false
}

// 工具函数
const formatDate = (dateStr) => {
  try {
    return format(new Date(dateStr), 'yyyy-MM-dd')
  } catch (e) {
    return dateStr || '未知'
  }
}

const formatDateTime = (dateStr) => {
  try {
    return format(new Date(dateStr), 'yyyy-MM-dd HH:mm:ss')
  } catch (e) {
    return dateStr || '未知'
  }
}

const getZoneTypeName = (type) => {
  const types = {
    'polygon': '多边形区域',
    'circle': '圆形区域'
  }
  return types[type] || type
}

// 模拟API调用
const mockFetchNoFlyZones = () => {
  return new Promise((resolve) => {
    setTimeout(() => {
      noFlyZones.value = [
        {
          id: 'nfz-001',
          name: '机场禁飞区',
          type: 'circle',
          center: { lat: 39.9, lng: 116.4 },
          radius: 5000,
          maxAltitude: 300,
          startTime: null,
          endTime: null,
          description: '首都机场周边禁飞区域，半径5公里',
          active: true,
          createdAt: '2025-03-10T08:00:00Z'
        },
        {
          id: 'nfz-002',
          name: '校园禁飞区',
          type: 'polygon',
          coordinates: [
            { lat: 39.91, lng: 116.38 },
            { lat: 39.92, lng: 116.38 },
            { lat: 39.92, lng: 116.39 },
            { lat: 39.91, lng: 116.39 }
          ],
          maxAltitude: 150,
          startTime: null,
          endTime: null,
          description: '大学校园区域，禁止无人机飞行',
          active: true,
          createdAt: '2025-03-15T10:30:00Z'
        },
        {
          id: 'nfz-003',
          name: '临时管制区',
          type: 'polygon',
          coordinates: [
            { lat: 39.89, lng: 116.41 },
            { lat: 39.9, lng: 116.42 },
            { lat: 39.89, lng: 116.43 },
            { lat: 39.88, lng: 116.42 }
          ],
          maxAltitude: 100,
          startTime: '2025-04-10T08:00:00Z',
          endTime: '2025-04-20T18:00:00Z',
          description: '重要活动期间临时禁飞区域',
          active: false,
          createdAt: '2025-04-05T14:20:00Z'
        }
      ]
      resolve()
    }, 500)
  })
}

const mockCreateZone = (zoneData) => {
  return new Promise((resolve) => {
    setTimeout(() => {
      const newZone = {
        ...zoneData,
        id: 'nfz-' + Math.floor(Math.random() * 10000).toString().padStart(3, '0'),
        createdAt: new Date().toISOString()
      }
      console.log('创建禁飞区:', newZone)
      resolve(newZone)
    }, 500)
  })
}

const mockUpdateZone = (zoneData) => {
  return new Promise((resolve) => {
    setTimeout(() => {
      console.log('更新禁飞区:', zoneData)
      resolve()
    }, 500)
  })
}

const mockUpdateZoneStatus = (zoneId, newStatus) => {
  return new Promise((resolve) => {
    setTimeout(() => {
      console.log('更新禁飞区状态:', zoneId, newStatus)
      resolve()
    }, 500)
  })
}

const mockDeleteZone = (zoneId) => {
  return new Promise((resolve) => {
    setTimeout(() => {
      console.log('删除禁飞区:', zoneId)
      resolve()
    }, 500)
  })
}
</script> 