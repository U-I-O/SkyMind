<template>
  <header class="bg-slate-800 bg-opacity-85 backdrop-filter backdrop-blur-md border-b border-slate-700 z-10 text-white shadow-lg">
    <div class="container mx-auto px-6 py-2 flex justify-between items-center">
      <!-- 左侧Logo -->
      <div class="flex-shrink-0 ml-2">
        <router-link to="/" class="flex items-center space-x-2">
          <div class="w-10 h-10 rounded-lg bg-gradient-to-r from-primary to-secondary flex items-center justify-center text-white text-lg font-bold">
            SG
          </div>
          <h1 class="text-xl font-bold text-white">SkyGuard</h1>
        </router-link>
      </div>
      
      <!-- 居中的主导航菜单 -->
      <nav class="hidden md:flex flex-1 justify-center">
        <div class="flex space-x-8">
          <router-link 
            v-for="item in mainNavItems" 
            :key="item.path" 
            :to="item.path" 
            class="py-2 px-1 relative transition-all duration-300 ease-in-out group"
            :class="[
              isActiveRoute(item.path) 
                ? 'text-blue-400 font-bold text-lg' 
                : 'text-gray-300 hover:text-blue-400 font-medium text-base'
            ]"
          >
            {{ item.title }}
            <div 
              class="absolute bottom-0 left-0 w-full h-0.5 bg-primary transform transition-all duration-300 ease-in-out"
              :class="[
                isActiveRoute(item.path) 
                  ? 'scale-x-100' 
                  : 'scale-x-0 group-hover:scale-x-100'
              ]"
            ></div>
          </router-link>
        </div>
      </nav>
      
      <!-- 右侧功能区 -->
      <div class="flex items-center space-x-4 flex-shrink-0 mr-2">
        <!-- 搜索按钮 -->
        <n-button circle secondary @click="showSearch = true">
          <template #icon>
            <n-icon><search-outlined class="text-white" /></n-icon>
          </template>
        </n-button>
        
        <!-- 消息通知 -->
        <n-badge :value="unreadCount" :max="99" :show="unreadCount > 0" @click="showNotifications = true">
          <n-button circle secondary @click="showNotifications = true">
            <template #icon>
              <n-icon><bell-outlined class="text-white" /></n-icon>
            </template>
          </n-button>
        </n-badge>
        
        <!-- 用户菜单 -->
        <n-dropdown :options="userMenuOptions" placement="bottom-end" trigger="click" @select="handleUserMenuSelect">
          <div class="flex items-center cursor-pointer">
            <div class="w-8 h-8 rounded-full overflow-hidden bg-primary flex items-center justify-center text-white text-sm font-bold">
              {{ userInitials }}
            </div>
          </div>
        </n-dropdown>
        
        <!-- 设置按钮 -->
        <n-button circle secondary @click="showSettings = true">
          <template #icon>
            <n-icon>
              <setting-outlined class="text-white" />
            </n-icon>
          </template>
        </n-button>
      </div>
    </div>
  </header>
  
  <!-- 搜索对话框 -->
  <n-modal v-model:show="showSearch" preset="card" title="全局搜索" style="width: 600px">
    <n-input 
      v-model:value="searchQuery" 
      placeholder="搜索事件、任务、无人机..." 
      size="large"
      @keyup.enter="handleSearch"
    >
      <template #prefix>
        <n-icon><search-outlined /></n-icon>
      </template>
    </n-input>
    
    <div v-if="searchResults.length > 0" class="mt-4">
      <div class="text-sm font-medium text-gray-700 mb-2">搜索结果</div>
      <n-list hoverable clickable>
        <n-list-item v-for="result in searchResults" :key="result.id" @click="handleResultClick(result)">
          <div class="flex items-center">
            <div class="p-2 rounded-full mr-3" :class="getResultTypeClass(result.type)">
              <n-icon size="18" :component="getResultTypeIcon(result.type)" />
            </div>
            <div>
              <div class="font-medium">{{ result.title }}</div>
              <div class="text-xs text-gray-500">{{ result.description }}</div>
            </div>
          </div>
        </n-list-item>
      </n-list>
    </div>
    
    <div v-else-if="searchQuery && hasSearched" class="mt-4 p-4 text-center text-gray-500">
      未找到匹配的结果
    </div>
    
    <div v-else-if="!searchQuery" class="mt-4">
      <div class="text-sm font-medium text-gray-700 mb-2">最近搜索</div>
      <div class="flex flex-wrap gap-2">
        <n-tag 
          v-for="(term, index) in recentSearches" 
          :key="index"
          size="small"
          round
          clickable
          @click="quickSearch(term)"
        >
          {{ term }}
        </n-tag>
      </div>
    </div>
    
    <template #footer>
      <div class="flex justify-between items-center">
        <div class="text-xs text-gray-500">按 ESC 键关闭</div>
        <n-button type="primary" @click="handleSearch" :disabled="!searchQuery">搜索</n-button>
      </div>
    </template>
  </n-modal>
  
  <!-- 消息通知对话框 -->
  <n-drawer v-model:show="showNotifications" width="380" placement="right">
    <n-drawer-content title="通知消息" closable>
      <div class="flex justify-between items-center mb-4">
        <div class="text-sm text-gray-500">您有 {{ unreadCount }} 条未读消息</div>
        <n-button text @click="markAllAsRead">全部标为已读</n-button>
      </div>
      
      <n-tabs type="line">
        <n-tab-pane name="all" tab="全部">
          <n-list hoverable clickable>
            <n-list-item v-for="notification in notifications" :key="notification.id" @click="viewNotification(notification)">
              <div class="flex py-1">
                <div class="mr-3 mt-1">
                  <div class="w-2 h-2 rounded-full" :class="notification.read ? 'bg-gray-300' : 'bg-primary'"></div>
                </div>
                <div class="flex-1">
                  <div class="flex justify-between">
                    <span class="font-medium" :class="notification.read ? 'text-gray-600' : 'text-gray-800'">
                      {{ notification.title }}
                    </span>
                    <span class="text-xs text-gray-500">{{ notification.time }}</span>
                  </div>
                  <div class="text-sm text-gray-500 mt-1">{{ notification.message }}</div>
                </div>
              </div>
            </n-list-item>
          </n-list>
        </n-tab-pane>
        <n-tab-pane name="unread" tab="未读">
          <n-list hoverable clickable>
            <n-list-item v-for="notification in unreadNotifications" :key="notification.id" @click="viewNotification(notification)">
              <div class="flex py-1">
                <div class="mr-3 mt-1">
                  <div class="w-2 h-2 rounded-full bg-primary"></div>
                </div>
                <div class="flex-1">
                  <div class="flex justify-between">
                    <span class="font-medium text-gray-800">{{ notification.title }}</span>
                    <span class="text-xs text-gray-500">{{ notification.time }}</span>
                  </div>
                  <div class="text-sm text-gray-500 mt-1">{{ notification.message }}</div>
                </div>
              </div>
            </n-list-item>
          </n-list>
        </n-tab-pane>
      </n-tabs>
    </n-drawer-content>
  </n-drawer>
  
  <!-- 设置对话框 -->
  <n-drawer v-model:show="showSettings" width="380" placement="right">
    <n-drawer-content title="系统设置" closable>
      <n-list>
        <n-list-item>
          <div class="flex justify-between items-center w-full">
            <span>深色模式</span>
            <n-switch v-model:value="isDarkMode" @update:value="toggleDarkMode" />
          </div>
        </n-list-item>
        
        <n-list-item>
          <div class="flex justify-between items-center w-full">
            <span>消息通知</span>
            <n-switch v-model:value="notificationsEnabled" />
          </div>
        </n-list-item>
        
        <n-list-item>
          <div class="flex justify-between items-center w-full">
            <span>声音提示</span>
            <n-switch v-model:value="soundEnabled" />
          </div>
        </n-list-item>
        
        <n-list-item>
          <div class="flex flex-col w-full">
            <span class="mb-2">语言选择</span>
            <n-select v-model:value="language" :options="languageOptions" />
          </div>
        </n-list-item>
        
        <n-list-item>
          <div class="flex flex-col w-full">
            <span class="mb-2">自动刷新间隔</span>
            <n-slider v-model:value="refreshInterval" :min="5" :max="60" :step="5">
              <template #thumb>
                {{ refreshInterval }}秒
              </template>
            </n-slider>
          </div>
        </n-list-item>
      </n-list>
      
      <template #footer>
        <div class="flex justify-end">
          <n-button type="primary" @click="saveSettings">保存设置</n-button>
        </div>
      </template>
    </n-drawer-content>
  </n-drawer>
  
  <!-- 个人信息对话框 (新增) -->
  <n-modal v-model:show="showProfile" preset="card" style="width: 700px" class="profile-modal">
    <template #header>
      <div class="flex items-center">
        <div class="w-12 h-12 rounded-full overflow-hidden mr-4 border-2 border-primary">
          <img :src="userProfile.avatar || defaultAvatar" alt="用户头像" class="w-full h-full object-cover" />
        </div>
        <div>
          <h2 class="text-xl font-bold">{{ userProfile.name || '未设置姓名' }}</h2>
          <div class="flex items-center">
            <n-tag size="small" type="success" class="mr-2">{{ getRoleName(userInfo.role) }}</n-tag>
            <span class="text-gray-500 text-sm">{{ userProfile.department || '未设置部门' }}</span>
          </div>
        </div>
      </div>
    </template>
    
    <div class="profile-content">
      <!-- 视图/编辑模式切换 -->
      <div class="flex justify-end mb-4">
        <n-button v-if="!isEditMode" secondary size="small" @click="toggleEditMode">
          <template #icon><n-icon><edit-outlined /></n-icon></template>
          修改个人信息
        </n-button>
        <div v-else class="flex space-x-2">
          <n-button size="small" @click="cancelEdit">
            取消
          </n-button>
          <n-button type="primary" size="small" @click="saveProfile" :loading="loading">
            <template #icon><n-icon><save-outlined /></n-icon></template>
            保存
          </n-button>
        </div>
      </div>
      
      <!-- 基本信息部分 -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
        <div class="info-item flex flex-col">
          <div class="text-sm text-gray-500 mb-1">用户名</div>
          <div v-if="!isEditMode" class="font-medium">{{ userProfile.username }}</div>
          <n-input v-else v-model:value="editingProfile.username" placeholder="请输入用户名" />
        </div>
        
        <div class="info-item flex flex-col">
          <div class="text-sm text-gray-500 mb-1">姓名</div>
          <div v-if="!isEditMode" class="font-medium">{{ userProfile.name }}</div>
          <n-input v-else v-model:value="editingProfile.name" placeholder="请输入姓名" />
        </div>
        
        <div class="info-item flex flex-col">
          <div class="text-sm text-gray-500 mb-1">电子邮箱</div>
          <div v-if="!isEditMode" class="font-medium">{{ userProfile.email }}</div>
          <n-input v-else v-model:value="editingProfile.email" placeholder="请输入电子邮箱" />
        </div>
        
        <div class="info-item flex flex-col">
          <div class="text-sm text-gray-500 mb-1">手机号码</div>
          <div v-if="!isEditMode" class="font-medium">{{ userProfile.phone }}</div>
          <n-input v-else v-model:value="editingProfile.phone" placeholder="请输入手机号码" />
        </div>
        
        <div class="info-item flex flex-col">
          <div class="text-sm text-gray-500 mb-1">部门</div>
          <div v-if="!isEditMode" class="font-medium">{{ userProfile.department }}</div>
          <n-select v-else v-model:value="editingProfile.department" :options="departmentOptions" placeholder="请选择部门" />
        </div>
        
        <div class="info-item flex flex-col">
          <div class="text-sm text-gray-500 mb-1">职位</div>
          <div v-if="!isEditMode" class="font-medium">{{ userProfile.position }}</div>
          <n-input v-else v-model:value="editingProfile.position" placeholder="请输入职位" />
        </div>
      </div>
      
      <!-- 账号信息部分 -->
      <div class="bg-slate-100 dark:bg-slate-800 p-4 rounded-lg">
        <h3 class="text-lg font-medium mb-3">账号信息</h3>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div class="info-item">
            <div class="text-sm text-gray-500 mb-1">账号ID</div>
            <div class="font-medium">{{ userInfo.id }}</div>
          </div>
          <div class="info-item">
            <div class="text-sm text-gray-500 mb-1">账号状态</div>
            <n-tag :type="userInfo.status === 'active' ? 'success' : 'warning'">
              {{ userInfo.status === 'active' ? '正常' : '已禁用' }}
            </n-tag>
          </div>
          <div class="info-item">
            <div class="text-sm text-gray-500 mb-1">创建时间</div>
            <div class="font-medium">{{ formatDate(userInfo.createdAt) }}</div>
          </div>
          <div class="info-item">
            <div class="text-sm text-gray-500 mb-1">最后登录</div>
            <div class="font-medium">{{ formatDateTime(userInfo.lastLogin) }}</div>
          </div>
        </div>
      </div>
      
      <!-- 修改密码部分 -->
      <n-divider />
      <div class="mt-4">
        <div class="flex justify-between items-center">
          <h3 class="text-lg font-medium">修改密码</h3>
          <n-button 
            v-if="!showPasswordForm" 
            text 
            @click="showPasswordForm = true"
          >
            点击修改
          </n-button>
        </div>
        
        <n-collapse-transition :show="showPasswordForm">
          <div class="mt-3 space-y-3">
            <n-input 
              v-model:value="passwordForm.currentPassword" 
              type="password" 
              placeholder="当前密码"
              show-password-on="click"
            />
            <n-input 
              v-model:value="passwordForm.newPassword" 
              type="password" 
              placeholder="新密码"
              show-password-on="click"
            />
            <n-input 
              v-model:value="passwordForm.confirmPassword" 
              type="password" 
              placeholder="确认新密码"
              show-password-on="click"
            />
            <div class="flex justify-end space-x-2">
              <n-button size="small" @click="showPasswordForm = false">
                取消
              </n-button>
              <n-button 
                type="primary" 
                size="small" 
                @click="changePassword"
                :disabled="!canChangePassword"
              >
                确认修改
              </n-button>
            </div>
          </div>
        </n-collapse-transition>
      </div>
    </div>
  </n-modal>
</template>

<script setup>
import { ref, inject, computed, h, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { format } from 'date-fns'
import {
  SearchOutlined,
  BellOutlined,
  SettingOutlined,
  FileOutlined,
  RocketOutlined,
  RobotOutlined,
  ScheduleOutlined,
  EnvironmentOutlined,
  AlertOutlined,
  EditOutlined,
  SaveOutlined,
  UserOutlined,
  LockOutlined
} from '@vicons/antd'
import { useMessage } from 'naive-ui'
import { useUserStore } from '@/store/userStore'

// 消息提示服务
const message = useMessage()

// 注入主题切换函数
const isDarkMode = inject('isDarkMode', ref(false))
const toggleDarkMode = inject('toggleDarkMode', () => {})

// 搜索功能
const showSearch = ref(false)
const searchQuery = ref('')
const searchResults = ref([])
const hasSearched = ref(false)
const recentSearches = ref(['无人机状态', '飞行任务', '安全巡逻', '紧急事件'])

// 通知功能
const showNotifications = ref(false)
const unreadCount = ref(3)
const notificationsEnabled = ref(true)
const soundEnabled = ref(true)

// 设置功能
const showSettings = ref(false)
const language = ref('zh-CN')
const refreshInterval = ref(30)
const languageOptions = [
  { label: '简体中文', value: 'zh-CN' },
  { label: 'English', value: 'en-US' }
]

// 用户信息
const userStore = useUserStore()
const router = useRouter()
const route = useRoute()

// 模拟通知数据
const notifications = ref([
  {
    id: 1,
    title: '发现可疑人员活动',
    message: '在北区工业园附近检测到可疑人员活动，已派出无人机前往',
    time: '14:39',
    read: false,
    type: 'security'
  },
  {
    id: 2,
    title: '交通拥堵预警',
    message: '东部主干道检测到交通拥堵情况，拥堵指数达到75%',
    time: '14:05',
    read: false,
    type: 'traffic'
  },
  {
    id: 3,
    title: '紧急火灾报警',
    message: '南区仓储区域检测到火灾隐患，温度异常升高，烟雾检测器报警',
    time: '12:30',
    read: false,
    type: 'emergency'
  },
  {
    id: 4,
    title: '无人机低电量警告',
    message: '无人机 #DJI-005 电量低于20%，请及时充电或更换电池',
    time: '10:15',
    read: true,
    type: 'drone'
  },
  {
    id: 5,
    title: '系统升级通知',
    message: '系统将于今晚22:00进行例行升级维护，预计持续1小时',
    time: '09:30',
    read: true,
    type: 'system'
  }
])

// 未读通知
const unreadNotifications = computed(() => {
  return notifications.value.filter(notification => !notification.read)
})

// 个人信息相关 (新增)
const showProfile = ref(false)
const isEditMode = ref(false)
const loading = ref(false)
const showPasswordForm = ref(false)
const defaultAvatar = 'https://cdn.jsdelivr.net/gh/ruilisi/naiveui-vue-icon@master/svg/person-outline.svg'

// 用户资料
const userProfile = ref({
  username: 'admin',
  name: '管理员',
  email: 'admin@example.com',
  phone: '13800138000',
  department: '技术部',
  position: '系统管理员',
  avatar: 'https://randomuser.me/api/portraits/men/32.jpg'
})

// 用于编辑的副本
const editingProfile = ref({})

// 账号信息
const userInfo = ref({
  id: 'user_12345',
  role: 'admin',
  status: 'active',
  createdAt: '2024-01-15T08:00:00Z',
  lastLogin: '2024-04-15T10:30:45Z'
})

// 密码表单
const passwordForm = ref({
  currentPassword: '',
  newPassword: '',
  confirmPassword: ''
})

// 部门选项
const departmentOptions = [
  { label: '运营部', value: '运营部' },
  { label: '技术部', value: '技术部' },
  { label: '管理部', value: '管理部' },
  { label: '安全部', value: '安全部' },
  { label: '无人机管理中心', value: '无人机管理中心' }
]

// 搜索处理函数
function handleSearch() {
  if (!searchQuery.value) return
  
  hasSearched.value = true
  // 模拟搜索，实际应用中可能是API调用
  setTimeout(() => {
    // 基于搜索词过滤模拟结果
    const query = searchQuery.value.toLowerCase()
    
    // 模拟结果数据
    const allResults = [
      {
        id: 'drone-1',
        title: '雄鹰-001',
        description: '无人机 - DJI Mavic 3 - 飞行中',
        type: 'drone'
      },
      {
        id: 'drone-2',
        title: '雄鹰-002',
        description: '无人机 - Yuneec H520 - 飞行中',
        type: 'drone'
      },
      {
        id: 'drone-3', 
        title: '雄鹰-003',
        description: '无人机 - DJI Phantom 4 Pro V2.0 - 飞行中',
        type: 'drone'
      },
      {
        id: 'event-1',
        title: '发现可疑人员活动',
        description: '安全事件 - 北区工业园',
        type: 'security'
      },
      {
        id: 'event-2',
        title: '交通拥堵预警',
        description: '交通事件 - 东部主干道',
        type: 'traffic'
      },
      {
        id: 'task-1',
        title: '定时巡逻任务',
        description: '巡逻任务 - 每日例行巡逻',
        type: 'task'
      },
      {
        id: 'task-2',
        title: '紧急消防支援',
        description: '紧急任务 - 南区仓储区域',
        type: 'emergency'
      }
    ]
    
    // 过滤匹配结果
    searchResults.value = allResults.filter(result => 
      result.title.toLowerCase().includes(query) || 
      result.description.toLowerCase().includes(query)
    )
    
    // 如果有搜索结果，将搜索词添加到最近搜索中
    if (searchResults.value.length > 0 && !recentSearches.value.includes(searchQuery.value)) {
      recentSearches.value.unshift(searchQuery.value)
      if (recentSearches.value.length > 5) {
        recentSearches.value.pop()
      }
    }
  }, 300) // 添加短暂延迟模拟实际搜索
}

// 快速搜索
function quickSearch(term) {
  searchQuery.value = term
  handleSearch()
}

// 处理搜索结果点击
function handleResultClick(result) {
  // 根据结果类型导航到相应页面
  showSearch.value = false
  
  switch(result.type) {
    case 'drone':
      router.push(`/drones?id=${result.id}`)
      break
    case 'security':
      router.push('/security')
      break
    case 'traffic':
      router.push('/')
      break
    case 'task':
      router.push('/tasks')
      break
    case 'emergency':
      router.push('/emergency')
      break
    default:
      router.push('/')
  }
  
  message.success(`正在跳转到: ${result.title}`)
}

// 根据结果类型获取图标
function getResultTypeIcon(type) {
  switch(type) {
    case 'drone': return RobotOutlined
    case 'security': return AlertOutlined
    case 'traffic': return EnvironmentOutlined
    case 'task': return ScheduleOutlined
    case 'emergency': return RocketOutlined
    default: return FileOutlined
  }
}

// 根据结果类型获取图标样式
function getResultTypeClass(type) {
  switch(type) {
    case 'drone': return 'bg-blue-100 text-blue-500'
    case 'security': return 'bg-yellow-100 text-yellow-500'
    case 'traffic': return 'bg-green-100 text-green-500'
    case 'task': return 'bg-purple-100 text-purple-500'
    case 'emergency': return 'bg-red-100 text-red-500'
    default: return 'bg-gray-100 text-gray-500'
  }
}

// 标记所有通知为已读
function markAllAsRead() {
  notifications.value.forEach(notification => {
    notification.read = true
  })
  unreadCount.value = 0
  message.success('已将所有消息标记为已读')
}

// 查看通知详情
function viewNotification(notification) {
  // 标记为已读
  if (!notification.read) {
    notification.read = true
    unreadCount.value = Math.max(0, unreadCount.value - 1)
  }
  
  // 根据通知类型导航到相应页面
  switch(notification.type) {
    case 'security':
      router.push('/security')
      break
    case 'traffic':
      router.push('/')
      break
    case 'emergency':
      router.push('/emergency')
      break
    case 'drone':
      router.push('/drones')
      break
    case 'system':
      showSettings.value = true
      break
  }
  
  showNotifications.value = false
}

// 保存设置
function saveSettings() {
  message.success('设置已保存')
  showSettings.value = false
}

// 检查当前路由是否活跃
const isActiveRoute = (path) => {
  return route.path === path || route.path.startsWith(`${path}/`)
}

// 用户头像显示的首字母
const userInitials = computed(() => {
  return userStore.user?.username?.substring(0, 2).toUpperCase() || 'AD'
})

// 主导航菜单项
const mainNavItems = [
  { title: '监控中心', path: '/' },
  { title: '应急响应', path: '/emergency' },
  { title: '安防巡检', path: '/security' },
  { title: '无人机管理', path: '/drones' }
]

// 用户菜单选项
const userMenuOptions = [
  {
    label: '个人信息',
    key: 'profile',
    icon: () => h('i', { class: 'fas fa-user' })
  },
  {
    type: 'divider',
    key: 'd1'
  },
  {
    label: '退出登录',
    key: 'logout',
    icon: () => h('i', { class: 'fas fa-sign-out-alt' })
  }
]

// 个人信息相关函数 (新增)
// 切换编辑模式
function toggleEditMode() {
  isEditMode.value = true
  // 创建待编辑的个人信息副本
  editingProfile.value = JSON.parse(JSON.stringify(userProfile.value))
}

// 取消编辑
function cancelEdit() {
  isEditMode.value = false
  // 丢弃更改
  editingProfile.value = {}
}

// 保存个人信息
function saveProfile() {
  loading.value = true
  
  // 模拟API调用
  setTimeout(() => {
    // 更新个人信息
    userProfile.value = { ...editingProfile.value }
    isEditMode.value = false
    loading.value = false
    message.success('个人信息已更新')
  }, 500)
}

// 修改密码
function changePassword() {
  if (passwordForm.value.newPassword !== passwordForm.value.confirmPassword) {
    message.error('两次输入的密码不一致')
    return
  }
  
  // 模拟API调用
  setTimeout(() => {
    // 成功后清空表单并隐藏
    passwordForm.value = {
      currentPassword: '',
      newPassword: '',
      confirmPassword: ''
    }
    showPasswordForm.value = false
    message.success('密码已成功修改')
  }, 500)
}

// 判断是否可以修改密码
const canChangePassword = computed(() => {
  return passwordForm.value.currentPassword && 
         passwordForm.value.newPassword && 
         passwordForm.value.confirmPassword &&
         passwordForm.value.newPassword === passwordForm.value.confirmPassword
})

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

// 监听用户菜单操作 (修改)
const handleUserMenuSelect = (key) => {
  if (key === 'logout') {
    userStore.logout()
    router.push('/login')
  } else if (key === 'profile') {
    // 修改为显示个人信息弹窗，而不是导航到个人资料页面
    showProfile.value = true
  }
}

// 在组件挂载时初始化未读通知数
watch(notifications, () => {
  unreadCount.value = unreadNotifications.value.length
}, { immediate: true })
</script>

<style scoped>
/* 个人资料模态框样式 */
.profile-modal :deep(.n-card-header) {
  padding-bottom: 16px;
  border-bottom: 1px solid rgba(128, 128, 128, 0.2);
}

.profile-content {
  padding: 16px 0;
}

.info-item {
  transition: all 0.2s ease;
  padding: 6px;
  border-radius: 4px;
}

.info-item:hover {
  background-color: rgba(128, 128, 128, 0.1);
}
</style>