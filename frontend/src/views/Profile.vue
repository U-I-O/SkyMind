<template>
  <div class="h-full flex flex-col p-4">
    <div class="flex justify-between items-center mb-4">
      <h1 class="text-2xl font-bold">个人资料</h1>
      <div>
        <n-button 
          type="primary" 
          :loading="loading" 
          @click="saveProfile"
          :disabled="!hasChanges"
        >
          <template #icon>
            <n-icon><save-outlined /></n-icon>
          </template>
          保存更改
        </n-button>
      </div>
    </div>
    
    <div class="grid grid-cols-12 gap-4 flex-1">
      <!-- 左侧个人信息 -->
      <div class="col-span-8 flex flex-col gap-4">
        <div class="bg-white p-6 rounded-lg shadow">
          <h3 class="text-lg font-medium mb-4">基本信息</h3>
          <n-form 
            ref="formRef"
            :model="formValue"
            label-placement="left" 
            label-width="120px"
            :show-feedback="false"
          >
            <n-form-item label="用户名" path="username">
              <n-input v-model:value="formValue.username" placeholder="请输入用户名" />
            </n-form-item>
            
            <n-form-item label="姓名" path="name">
              <n-input v-model:value="formValue.name" placeholder="请输入姓名" />
            </n-form-item>
            
            <n-form-item label="电子邮箱" path="email">
              <n-input v-model:value="formValue.email" placeholder="请输入电子邮箱" />
            </n-form-item>
            
            <n-form-item label="手机号码" path="phone">
              <n-input v-model:value="formValue.phone" placeholder="请输入手机号码" />
            </n-form-item>
            
            <n-form-item label="部门" path="department">
              <n-select 
                v-model:value="formValue.department"
                :options="departmentOptions"
                placeholder="请选择部门"
              />
            </n-form-item>
            
            <n-form-item label="职位" path="position">
              <n-input v-model:value="formValue.position" placeholder="请输入职位" />
            </n-form-item>
          </n-form>
        </div>
        
        <div class="bg-white p-6 rounded-lg shadow">
          <h3 class="text-lg font-medium mb-4">安全设置</h3>
          <n-form 
            ref="passwordFormRef"
            :model="passwordForm"
            label-placement="left" 
            label-width="120px"
          >
            <n-form-item label="当前密码" path="currentPassword">
              <n-input 
                v-model:value="passwordForm.currentPassword" 
                type="password" 
                placeholder="请输入当前密码"
                show-password-on="click"
              />
            </n-form-item>
            
            <n-form-item label="新密码" path="newPassword">
              <n-input 
                v-model:value="passwordForm.newPassword" 
                type="password" 
                placeholder="请输入新密码"
                show-password-on="click"
              />
            </n-form-item>
            
            <n-form-item label="确认新密码" path="confirmPassword">
              <n-input 
                v-model:value="passwordForm.confirmPassword" 
                type="password" 
                placeholder="请再次输入新密码"
                show-password-on="click"
              />
            </n-form-item>
            
            <div class="flex justify-end">
              <n-button 
                type="primary" 
                @click="changePassword"
                :disabled="!canChangePassword"
              >
                修改密码
              </n-button>
            </div>
          </n-form>
        </div>
      </div>
      
      <!-- 右侧信息 -->
      <div class="col-span-4 flex flex-col gap-4">
        <div class="bg-white p-6 rounded-lg shadow">
          <div class="flex flex-col items-center">
            <div class="w-24 h-24 rounded-full overflow-hidden mb-4">
              <img 
                :src="formValue.avatar || defaultAvatar" 
                alt="用户头像" 
                class="w-full h-full object-cover"
              />
            </div>
            <div class="text-center">
              <h3 class="font-medium text-lg">{{ formValue.name || '未设置姓名' }}</h3>
              <p class="text-gray-500 mt-1">{{ formValue.position || '未设置职位' }}</p>
              <p class="text-sm text-gray-400 mt-1">{{ formValue.department || '未设置部门' }}</p>
            </div>
            <n-button class="mt-4" @click="uploadAvatar">
              更换头像
            </n-button>
          </div>
        </div>
        
        <div class="bg-white p-6 rounded-lg shadow">
          <h3 class="text-lg font-medium mb-4">账号信息</h3>
          <n-descriptions bordered :column="1" size="small">
            <n-descriptions-item label="账号ID">
              {{ userInfo.id }}
            </n-descriptions-item>
            <n-descriptions-item label="账号角色">
              {{ getRoleName(userInfo.role) }}
            </n-descriptions-item>
            <n-descriptions-item label="账号状态">
              <n-tag :type="userInfo.status === 'active' ? 'success' : 'warning'">
                {{ userInfo.status === 'active' ? '正常' : '已禁用' }}
              </n-tag>
            </n-descriptions-item>
            <n-descriptions-item label="创建时间">
              {{ formatDate(userInfo.createdAt) }}
            </n-descriptions-item>
            <n-descriptions-item label="最后登录">
              {{ formatDateTime(userInfo.lastLogin) }}
            </n-descriptions-item>
          </n-descriptions>
        </div>
        
        <div class="bg-white p-6 rounded-lg shadow">
          <h3 class="text-lg font-medium mb-4">偏好设置</h3>
          <div class="space-y-4">
            <div class="flex justify-between items-center">
              <span>接收通知</span>
              <n-switch v-model:value="preferences.notifications" />
            </div>
            <div class="flex justify-between items-center">
              <span>接收邮件提醒</span>
              <n-switch v-model:value="preferences.emailAlerts" />
            </div>
            <div class="flex justify-between items-center">
              <span>自动登录</span>
              <n-switch v-model:value="preferences.autoLogin" />
            </div>
            <div>
              <span>界面主题</span>
              <n-radio-group v-model:value="preferences.theme" class="mt-2">
                <n-space>
                  <n-radio value="light">浅色</n-radio>
                  <n-radio value="dark">深色</n-radio>
                  <n-radio value="system">跟随系统</n-radio>
                </n-space>
              </n-radio-group>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { format } from 'date-fns'
import { 
  NButton, 
  NForm,
  NFormItem,
  NInput,
  NSelect,
  NSwitch,
  NRadioGroup,
  NRadio,
  NSpace,
  NTag,
  NDescriptions,
  NDescriptionsItem,
  NIcon,
  useNotification,
  useMessage,
  useDialog
} from 'naive-ui'
import { 
  SaveOutlined
} from '@vicons/antd'

// UI组件
const message = useMessage()
const notification = useNotification()
const dialog = useDialog()

// 组件状态
const loading = ref(false)
const formRef = ref(null)
const passwordFormRef = ref(null)
const originalFormValue = ref(null)

// 默认头像
const defaultAvatar = 'https://cdn.jsdelivr.net/gh/ruilisi/naiveui-vue-icon@master/svg/person-outline.svg'

// 表单数据
const formValue = ref({
  username: '',
  name: '',
  email: '',
  phone: '',
  department: '',
  position: '',
  avatar: ''
})

const passwordForm = ref({
  currentPassword: '',
  newPassword: '',
  confirmPassword: ''
})

const userInfo = ref({
  id: 'user_12345',
  role: 'admin',
  status: 'active',
  createdAt: '2024-01-15T08:00:00Z',
  lastLogin: '2024-04-15T10:30:45Z'
})

const preferences = ref({
  notifications: true,
  emailAlerts: true,
  autoLogin: false,
  theme: 'light'
})

// 部门选项
const departmentOptions = [
  { label: '运营部', value: '运营部' },
  { label: '技术部', value: '技术部' },
  { label: '管理部', value: '管理部' },
  { label: '安全部', value: '安全部' },
  { label: '无人机管理中心', value: '无人机管理中心' }
]

// 计算属性
const hasChanges = computed(() => {
  if (!originalFormValue.value) return false
  
  return JSON.stringify(formValue.value) !== JSON.stringify(originalFormValue.value)
})

const canChangePassword = computed(() => {
  return passwordForm.value.currentPassword && 
         passwordForm.value.newPassword && 
         passwordForm.value.confirmPassword &&
         passwordForm.value.newPassword === passwordForm.value.confirmPassword
})

// 生命周期钩子
onMounted(() => {
  fetchUserProfile()
})

// 方法
const fetchUserProfile = async () => {
  loading.value = true
  try {
    // 这里应该是API调用
    await mockFetchProfile()
    
    // 保存原始值用于比较是否修改
    originalFormValue.value = JSON.parse(JSON.stringify(formValue.value))
  } catch (error) {
    console.error('获取用户资料出错:', error)
    notification.error({
      title: '错误',
      content: '获取用户资料失败',
      duration: 3000
    })
  } finally {
    loading.value = false
  }
}

const saveProfile = async () => {
  if (!hasChanges.value) return
  
  loading.value = true
  try {
    // 这里应该是API调用
    await mockUpdateProfile(formValue.value)
    
    // 更新原始值
    originalFormValue.value = JSON.parse(JSON.stringify(formValue.value))
    
    notification.success({
      title: '成功',
      content: '个人资料已更新',
      duration: 3000
    })
  } catch (error) {
    console.error('更新用户资料出错:', error)
    notification.error({
      title: '错误',
      content: '更新用户资料失败',
      duration: 3000
    })
  } finally {
    loading.value = false
  }
}

const changePassword = async () => {
  if (!canChangePassword.value) return
  
  if (passwordForm.value.newPassword !== passwordForm.value.confirmPassword) {
    message.error('两次输入的密码不一致')
    return
  }
  
  try {
    // 这里应该是API调用
    await mockChangePassword(passwordForm.value)
    
    notification.success({
      title: '成功',
      content: '密码已更新',
      duration: 3000
    })
    
    // 清空表单
    passwordForm.value = {
      currentPassword: '',
      newPassword: '',
      confirmPassword: ''
    }
  } catch (error) {
    console.error('修改密码出错:', error)
    notification.error({
      title: '错误',
      content: '修改密码失败',
      duration: 3000
    })
  }
}

const uploadAvatar = () => {
  dialog.info({
    title: '上传头像',
    content: '此功能尚未实现，将在后续版本中提供。',
    positiveText: '确定'
  })
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

const getRoleName = (role) => {
  const roles = {
    'admin': '管理员',
    'operator': '操作员',
    'viewer': '查看者',
    'manager': '经理'
  }
  return roles[role] || role
}

// 模拟API调用
const mockFetchProfile = () => {
  return new Promise((resolve) => {
    setTimeout(() => {
      formValue.value = {
        username: 'admin',
        name: '管理员',
        email: 'admin@example.com',
        phone: '13800138000',
        department: '技术部',
        position: '系统管理员',
        avatar: 'https://randomuser.me/api/portraits/men/32.jpg'
      }
      resolve()
    }, 500)
  })
}

const mockUpdateProfile = (profile) => {
  return new Promise((resolve) => {
    setTimeout(() => {
      console.log('更新用户资料:', profile)
      resolve()
    }, 500)
  })
}

const mockChangePassword = (passwordData) => {
  return new Promise((resolve, reject) => {
    setTimeout(() => {
      if (passwordData.currentPassword === 'admin123') {
        console.log('修改密码:', passwordData)
        resolve()
      } else {
        reject(new Error('当前密码不正确'))
      }
    }, 500)
  })
}
</script> 