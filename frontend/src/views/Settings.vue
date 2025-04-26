<template>
  <div class="h-full flex flex-col p-4">
    <div class="flex justify-between items-center mb-4">
      <h1 class="text-2xl font-bold">系统设置</h1>
      <div>
        <n-button 
          type="primary" 
          :loading="loading" 
          @click="saveSettings"
          :disabled="!hasChanges"
        >
          <template #icon>
            <n-icon><save-outlined /></n-icon>
          </template>
          保存设置
        </n-button>
      </div>
    </div>
    
    <div class="grid grid-cols-12 gap-4 flex-1">
      <!-- 左侧设置项 -->
      <div class="col-span-8 flex flex-col gap-4">
        <!-- 系统设置 -->
        <div class="bg-white p-6 rounded-lg shadow">
          <h3 class="text-lg font-medium mb-4">系统设置</h3>
          <n-form 
            ref="systemFormRef"
            :model="systemSettings"
            label-placement="left" 
            label-width="160px"
          >
            <n-form-item label="系统名称" path="systemName">
              <n-input v-model:value="systemSettings.systemName" placeholder="请输入系统名称" />
            </n-form-item>
            
            <n-form-item label="公司名称" path="companyName">
              <n-input v-model:value="systemSettings.companyName" placeholder="请输入公司名称" />
            </n-form-item>
            
            <n-form-item label="系统Logo" path="logo">
              <div class="flex items-center">
                <div class="w-12 h-12 mr-4 border rounded flex items-center justify-center overflow-hidden">
                  <img v-if="systemSettings.logo" :src="systemSettings.logo" class="w-full h-full object-cover" />
                  <n-icon v-else size="24"><picture-outlined /></n-icon>
                </div>
                <n-button @click="uploadLogo">上传Logo</n-button>
              </div>
            </n-form-item>
            
            <n-form-item label="系统时区" path="timezone">
              <n-select 
                v-model:value="systemSettings.timezone" 
                :options="timezoneOptions"
                placeholder="请选择系统时区"
              />
            </n-form-item>
            
            <n-form-item label="默认语言" path="language">
              <n-select 
                v-model:value="systemSettings.language" 
                :options="languageOptions"
                placeholder="请选择默认语言"
              />
            </n-form-item>
            
            <n-form-item label="系统首页" path="homePage">
              <n-select 
                v-model:value="systemSettings.homePage" 
                :options="pageOptions"
                placeholder="请选择首页"
              />
            </n-form-item>
            
            <n-form-item label="启用数据备份" path="enableBackup">
              <n-switch v-model:value="systemSettings.enableBackup" />
            </n-form-item>
            
            <n-form-item v-if="systemSettings.enableBackup" label="备份频率" path="backupFrequency">
              <n-select 
                v-model:value="systemSettings.backupFrequency" 
                :options="backupOptions"
                placeholder="请选择备份频率"
              />
            </n-form-item>
          </n-form>
        </div>
        
        <!-- 安全设置 -->
        <div class="bg-white p-6 rounded-lg shadow">
          <h3 class="text-lg font-medium mb-4">安全设置</h3>
          <n-form 
            ref="securityFormRef"
            :model="securitySettings"
            label-placement="left" 
            label-width="160px"
          >
            <n-form-item label="登录有效期(小时)" path="sessionTimeout">
              <n-input-number 
                v-model:value="securitySettings.sessionTimeout" 
                :min="1" 
                :max="720"
              />
            </n-form-item>
            
            <n-form-item label="允许自动登录" path="allowAutoLogin">
              <n-switch v-model:value="securitySettings.allowAutoLogin" />
            </n-form-item>
            
            <n-form-item label="登录尝试限制" path="loginAttempts">
              <n-input-number 
                v-model:value="securitySettings.loginAttempts" 
                :min="3" 
                :max="10"
              />
            </n-form-item>
            
            <n-form-item label="密码复杂度要求" path="passwordComplexity">
              <n-select 
                v-model:value="securitySettings.passwordComplexity" 
                :options="passwordOptions"
                placeholder="请选择密码复杂度"
              />
            </n-form-item>
            
            <n-form-item label="密码过期时间(天)" path="passwordExpiry">
              <n-input-number 
                v-model:value="securitySettings.passwordExpiry" 
                :min="30" 
                :max="180"
              />
            </n-form-item>
            
            <n-form-item label="启用双因素认证" path="enableTwoFactor">
              <n-switch v-model:value="securitySettings.enableTwoFactor" />
            </n-form-item>
            
            <n-form-item label="启用IP限制" path="enableIpRestriction">
              <n-switch v-model:value="securitySettings.enableIpRestriction" />
            </n-form-item>
            
            <n-form-item v-if="securitySettings.enableIpRestriction" label="IP白名单" path="ipWhitelist">
              <n-input 
                v-model:value="securitySettings.ipWhitelist" 
                type="textarea" 
                placeholder="请输入IP白名单，每行一个IP地址"
              />
            </n-form-item>
          </n-form>
        </div>
      </div>
      
      <!-- 右侧设置项 -->
      <div class="col-span-4 flex flex-col gap-4">
        <!-- 无人机设置 -->
        <div class="bg-white p-6 rounded-lg shadow">
          <h3 class="text-lg font-medium mb-4">无人机设置</h3>
          <n-form 
            ref="droneFormRef"
            :model="droneSettings"
            label-placement="left" 
            label-width="160px"
          >
            <n-form-item label="默认超时时间(分钟)" path="defaultTimeout">
              <n-input-number 
                v-model:value="droneSettings.defaultTimeout" 
                :min="5" 
                :max="120"
              />
            </n-form-item>
            
            <n-form-item label="低电量警告阈值(%)" path="lowBatteryThreshold">
              <n-input-number 
                v-model:value="droneSettings.lowBatteryThreshold" 
                :min="10" 
                :max="30"
              />
            </n-form-item>
            
            <n-form-item label="自动返航电量阈值(%)" path="returnHomeThreshold">
              <n-input-number 
                v-model:value="droneSettings.returnHomeThreshold" 
                :min="15" 
                :max="40"
              />
            </n-form-item>
            
            <n-form-item label="默认最大高度(米)" path="maxAltitude">
              <n-input-number 
                v-model:value="droneSettings.maxAltitude" 
                :min="50" 
                :max="500"
              />
            </n-form-item>
            
            <n-form-item label="默认操作范围(米)" path="operationRadius">
              <n-input-number 
                v-model:value="droneSettings.operationRadius" 
                :min="500" 
                :max="10000"
              />
            </n-form-item>
            
            <n-form-item label="启用自动任务分配" path="enableAutoAssignment">
              <n-switch v-model:value="droneSettings.enableAutoAssignment" />
            </n-form-item>
          </n-form>
        </div>
        
        <!-- 通知设置 -->
        <div class="bg-white p-6 rounded-lg shadow">
          <h3 class="text-lg font-medium mb-4">通知设置</h3>
          <n-form 
            ref="notificationFormRef"
            :model="notificationSettings"
            label-placement="left" 
            label-width="160px"
          >
            <n-form-item label="启用电子邮件通知" path="enableEmailNotifications">
              <n-switch v-model:value="notificationSettings.enableEmailNotifications" />
            </n-form-item>
            
            <n-form-item v-if="notificationSettings.enableEmailNotifications" label="SMTP服务器" path="smtpServer">
              <n-input v-model:value="notificationSettings.smtpServer" placeholder="请输入SMTP服务器地址" />
            </n-form-item>
            
            <n-form-item v-if="notificationSettings.enableEmailNotifications" label="SMTP端口" path="smtpPort">
              <n-input-number v-model:value="notificationSettings.smtpPort" :min="1" :max="65535" />
            </n-form-item>
            
            <n-form-item v-if="notificationSettings.enableEmailNotifications" label="发送者邮箱" path="senderEmail">
              <n-input v-model:value="notificationSettings.senderEmail" placeholder="请输入发送者邮箱" />
            </n-form-item>
            
            <n-form-item label="启用系统通知" path="enableSystemNotifications">
              <n-switch v-model:value="notificationSettings.enableSystemNotifications" />
            </n-form-item>
            
            <n-form-item label="启用短信通知" path="enableSmsNotifications">
              <n-switch v-model:value="notificationSettings.enableSmsNotifications" />
            </n-form-item>
            
            <n-form-item label="事件通知级别" path="notificationLevel">
              <n-select 
                v-model:value="notificationSettings.notificationLevel" 
                :options="notificationLevelOptions"
                placeholder="请选择通知级别"
              />
            </n-form-item>
          </n-form>
        </div>
        
        <!-- 地图设置 -->
        <div class="bg-white p-6 rounded-lg shadow">
          <h3 class="text-lg font-medium mb-4">地图设置</h3>
          <n-form 
            ref="mapFormRef"
            :model="mapSettings"
            label-placement="left" 
            label-width="160px"
          >
            <n-form-item label="默认地图中心" path="defaultCenter">
              <div class="grid grid-cols-2 gap-2">
                <n-input-number v-model:value="mapSettings.defaultCenter.lat" placeholder="纬度" />
                <n-input-number v-model:value="mapSettings.defaultCenter.lng" placeholder="经度" />
              </div>
            </n-form-item>
            
            <n-form-item label="默认缩放级别" path="defaultZoom">
              <n-input-number v-model:value="mapSettings.defaultZoom" :min="1" :max="20" />
            </n-form-item>
            
            <n-form-item label="地图提供商" path="mapProvider">
              <n-select 
                v-model:value="mapSettings.mapProvider" 
                :options="mapProviderOptions"
                placeholder="请选择地图提供商"
              />
            </n-form-item>
          </n-form>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { 
  NButton, 
  NForm,
  NFormItem,
  NInput,
  NInputNumber,
  NSelect,
  NSwitch,
  NIcon,
  useNotification,
  useMessage,
  useDialog
} from 'naive-ui'
import { 
  SaveOutlined,
  PictureOutlined
} from '@vicons/antd'

// UI组件
const message = useMessage()
const notification = useNotification()
const dialog = useDialog()

// 组件状态
const loading = ref(false)
const systemFormRef = ref(null)
const securityFormRef = ref(null)
const droneFormRef = ref(null)
const notificationFormRef = ref(null)
const mapFormRef = ref(null)

// 原始设置数据，用于比较是否有更改
const originalSettings = ref(null)

// 系统设置
const systemSettings = ref({
  systemName: '智能无人机管理系统',
  companyName: '未来科技',
  logo: null,
  timezone: 'Asia/Shanghai',
  language: 'zh-CN',
  homePage: 'dashboard',
  enableBackup: true,
  backupFrequency: 'daily'
})

// 安全设置
const securitySettings = ref({
  sessionTimeout: 24,
  allowAutoLogin: true,
  loginAttempts: 5,
  passwordComplexity: 'medium',
  passwordExpiry: 90,
  enableTwoFactor: false,
  enableIpRestriction: false,
  ipWhitelist: ''
})

// 无人机设置
const droneSettings = ref({
  defaultTimeout: 30,
  lowBatteryThreshold: 20,
  returnHomeThreshold: 25,
  maxAltitude: 120,
  operationRadius: 2000,
  enableAutoAssignment: true
})

// 通知设置
const notificationSettings = ref({
  enableEmailNotifications: true,
  smtpServer: 'smtp.example.com',
  smtpPort: 587,
  senderEmail: 'noreply@example.com',
  enableSystemNotifications: true,
  enableSmsNotifications: false,
  notificationLevel: 'warning'
})

// 地图设置
const mapSettings = ref({
  defaultCenter: {
    lat: 39.9042,
    lng: 116.4074
  },
  defaultZoom: 12,
  mapProvider: 'amap'
})

// 选项数据
const timezoneOptions = [
  { label: '北京时间 (UTC+8)', value: 'Asia/Shanghai' },
  { label: '东京时间 (UTC+9)', value: 'Asia/Tokyo' },
  { label: '伦敦时间 (UTC+0)', value: 'Europe/London' },
  { label: '纽约时间 (UTC-5)', value: 'America/New_York' }
]

const languageOptions = [
  { label: '简体中文', value: 'zh-CN' },
  { label: '繁體中文', value: 'zh-TW' },
  { label: 'English', value: 'en-US' },
  { label: '日本語', value: 'ja-JP' }
]

const pageOptions = [
  { label: '仪表盘', value: 'dashboard' },
  { label: '监控中心', value: 'monitor' },
  { label: '任务管理', value: 'tasks' },
  { label: '无人机列表', value: 'drones' }
]

const backupOptions = [
  { label: '每天', value: 'daily' },
  { label: '每周', value: 'weekly' },
  { label: '每月', value: 'monthly' }
]

const passwordOptions = [
  { label: '低 (仅字母数字)', value: 'low' },
  { label: '中 (字母+数字)', value: 'medium' },
  { label: '高 (字母+数字+特殊字符)', value: 'high' }
]

const notificationLevelOptions = [
  { label: '全部', value: 'all' },
  { label: '错误和警告', value: 'warning' },
  { label: '仅错误', value: 'error' }
]

const mapProviderOptions = [
  { label: '高德地图', value: 'amap' },
  { label: '百度地图', value: 'baidu' },
  { label: 'Google地图', value: 'google' },
  { label: 'Mapbox', value: 'mapbox' }
]

// 计算属性
const hasChanges = computed(() => {
  if (!originalSettings.value) return false
  
  const currentSettings = getCombinedSettings()
  return JSON.stringify(currentSettings) !== JSON.stringify(originalSettings.value)
})

// 生命周期钩子
onMounted(() => {
  fetchSettings()
})

// 方法
const fetchSettings = async () => {
  loading.value = true
  try {
    // 这里应该是API调用
    await mockFetchSettings()
    
    // 保存原始设置用于比较
    originalSettings.value = getCombinedSettings()
  } catch (error) {
    console.error('获取设置信息出错:', error)
    notification.error({
      title: '错误',
      content: '获取设置信息失败',
      duration: 3000
    })
  } finally {
    loading.value = false
  }
}

const saveSettings = async () => {
  if (!hasChanges.value) return
  
  loading.value = true
  try {
    // 这里应该是API调用
    const settings = getCombinedSettings()
    await mockSaveSettings(settings)
    
    // 更新原始设置
    originalSettings.value = JSON.parse(JSON.stringify(settings))
    
    notification.success({
      title: '成功',
      content: '系统设置已更新',
      duration: 3000
    })
  } catch (error) {
    console.error('保存设置信息出错:', error)
    notification.error({
      title: '错误',
      content: '保存设置信息失败',
      duration: 3000
    })
  } finally {
    loading.value = false
  }
}

const uploadLogo = () => {
  dialog.info({
    title: '上传Logo',
    content: '此功能尚未实现，将在后续版本中提供。',
    positiveText: '确定'
  })
}

// 合并所有设置
const getCombinedSettings = () => {
  return {
    system: JSON.parse(JSON.stringify(systemSettings.value)),
    security: JSON.parse(JSON.stringify(securitySettings.value)),
    drone: JSON.parse(JSON.stringify(droneSettings.value)),
    notification: JSON.parse(JSON.stringify(notificationSettings.value)),
    map: JSON.parse(JSON.stringify(mapSettings.value))
  }
}

// 模拟API调用
const mockFetchSettings = () => {
  return new Promise((resolve) => {
    setTimeout(() => {
      // 这里可以使用模拟数据初始化设置
      // 这里我们使用已有的默认值
      resolve()
    }, 500)
  })
}

const mockSaveSettings = (settings) => {
  return new Promise((resolve) => {
    setTimeout(() => {
      console.log('保存设置:', settings)
      resolve()
    }, 500)
  })
}
</script> 