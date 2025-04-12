<template>
  <!-- 使用 n-layout-header 替代 div 以更好地适应主题 -->
  <n-layout-header bordered class="z-10">
    <div class="container mx-auto px-4 h-16 flex justify-between items-center">
      <!-- 左侧Logo和菜单 -->
      <div class="flex items-center space-x-10">
        <!-- Logo和标题 -->
        <router-link to="/" class="flex items-center space-x-2">
          <div class="w-10 h-10 rounded-lg bg-gradient-to-r from-primary to-secondary flex items-center justify-center text-white text-lg font-bold">
            SM
          </div>
          <!-- 使用 n-text 保证标题颜色随主题变化 -->
          <n-text tag="h1" class="text-xl font-bold">SkyMind</n-text>
        </router-link>
        
        <!-- 主导航菜单 -->
        <nav class="hidden md:flex space-x-6">
          <!-- 使用 n-button 或 n-text 来确保链接颜色适应主题 -->
          <router-link v-for="item in mainNavItems" :key="item.path" :to="item.path" v-slot="{ navigate, isActive }">
            <n-button text :type="isActive ? 'primary' : 'default'" @click="navigate">
              {{ item.title }}
            </n-button>
          </router-link>
        </nav>
      </div>
      
      <!-- 右侧功能区 -->
      <div class="flex items-center space-x-4">
        <!-- 搜索按钮 -->
        <n-button circle quaternary @click="showSearch = true">
          <template #icon>
            <n-icon><search-outline /></n-icon>
          </template>
        </n-button>
        
        <!-- 消息通知 -->
        <n-badge :value="unreadCount" :max="99" :show="unreadCount > 0">
          <n-button circle quaternary @click="handleMessageClick">
            <template #icon>
              <n-icon><notifications-outline /></n-icon>
            </template>
          </n-button>
        </n-badge>
        
        <!-- 用户菜单 -->
        <n-dropdown :options="userMenuOptions" placement="bottom-end" trigger="click" @select="handleUserMenuSelect">
          <n-avatar round size="small" class="cursor-pointer bg-primary">
            {{ userInitials }}
          </n-avatar>
        </n-dropdown>
        
        <!-- 主题切换 -->
        <n-button circle quaternary @click="toggleTheme">
          <template #icon>
            <n-icon>
              <component :is="isDarkMode ? MoonIcon : SunnyIcon" />
            </n-icon>
          </template>
        </n-button>
      </div>
    </div>
  </n-layout-header>
  
  <!-- 搜索对话框 -->
  <n-modal v-model:show="showSearch" preset="card" title="全局搜索" style="width: 600px">
    <n-input 
      v-model:value="searchQuery" 
      placeholder="搜索事件、任务、无人机..." 
      size="large" 
      clearable 
      @keyup.enter="handleSearch"
    >
      <template #prefix>
        <n-icon><search-outline /></n-icon>
      </template>
      <template #suffix>
        <n-button text @click="handleSearch">搜索</n-button>
      </template>
    </n-input>
    
    <template #footer>
      <div class="text-xs text-gray-500">按 Enter 或点击搜索按钮进行搜索，按 ESC 关闭</div>
    </template>
  </n-modal>
</template>

<script setup>
import { ref, inject, computed, h } from 'vue'
import { useRouter } from 'vue-router'
import { useMessage } from 'naive-ui' // 导入 message
import {
  SearchOutline,
  NotificationsOutline as BellOutline,
  SettingsOutline as SettingOutlined,
  PersonOutline as UserOutline,
  LogOutOutline as LogoutOutline,
  MoonOutline as MoonIcon,
  SunnyOutline as SunnyIcon
} from '@vicons/ionicons5'
import { NIcon, NText, NButton, NLayoutHeader, NBadge, NDropdown, NAvatar, NModal, NInput } from 'naive-ui'
import { useUserStore } from '@/store/userStore'

const message = useMessage() // 初始化 message

// 注入主题切换函数
const isDarkMode = inject('isDarkMode')
const toggleDarkMode = inject('toggleDarkMode')

const toggleTheme = () => {
  toggleDarkMode()
}

// 搜索功能
const showSearch = ref(false)
const searchQuery = ref('')

function handleSearch() {
  if (!searchQuery.value.trim()) {
    message.warning('请输入搜索内容')
    return
  }
  message.info(`正在搜索: ${searchQuery.value}`)
  // 在这里可以添加实际的搜索逻辑，例如跳转到搜索结果页或调用API
  // showSearch.value = false // 可以选择在搜索后关闭弹窗
}

// 用户信息
const userStore = useUserStore()
const router = useRouter()

// 用户头像显示的首字母
const userInitials = computed(() => {
  return userStore.user?.username?.substring(0, 2).toUpperCase() || 'U'
})

// 未读消息数
const unreadCount = ref(3) // 示例数据

// 处理消息按钮点击
function handleMessageClick() {
  message.info('消息中心功能暂未开放')
}

// 主导航菜单项
const mainNavItems = [
  { title: '监控中心', path: '/monitor' },
  { title: '应急响应', path: '/emergency' },
  { title: '物流调度', path: '/logistics' },
  { title: '安防巡检', path: '/security' },
  { title: '无人机管理', path: '/drones' }
]

// 用户菜单选项 - 使用 Naive UI 图标
const renderIcon = (icon) => {
  return () => h(NIcon, null, { default: () => h(icon) })
}

const userMenuOptions = [
  {
    label: '个人信息',
    key: 'profile',
    icon: renderIcon(UserOutline)
  },
  {
    label: '设置',
    key: 'settings',
    icon: renderIcon(SettingOutlined)
  },
  {
    type: 'divider',
    key: 'd1'
  },
  {
    label: '退出登录',
    key: 'logout',
    icon: renderIcon(LogoutOutline)
  }
]

// 监听用户菜单操作
const handleUserMenuSelect = (key) => {
  if (key === 'logout') {
    userStore.logout()
    router.push('/login')
    message.success('已退出登录')
  } else if (key === 'profile') {
    // router.push('/profile') // 暂时注释，因为 profile 页面可能不存在
    message.info('个人信息功能暂未开放')
  } else if (key === 'settings') {
    // router.push('/settings') // 暂时注释，因为 settings 页面可能不存在
    message.info('设置功能暂未开放') // 修改为提示信息
  }
}
</script> 