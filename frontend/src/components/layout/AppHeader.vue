<template>
  <header class="bg-white shadow-sm border-b border-gray-200 z-10">
    <div class="container mx-auto px-4 py-2 flex justify-between items-center">
      <!-- 左侧Logo和菜单 -->
      <div class="flex items-center space-x-10">
        <!-- Logo和标题 -->
        <router-link to="/" class="flex items-center space-x-2">
          <div class="w-10 h-10 rounded-lg bg-gradient-to-r from-primary to-secondary flex items-center justify-center text-white text-lg font-bold">
            SM
          </div>
          <h1 class="text-xl font-bold text-gray-800">SkyMind</h1>
        </router-link>
        
        <!-- 主导航菜单 -->
        <nav class="hidden md:flex space-x-6">
          <router-link v-for="item in mainNavItems" :key="item.path" :to="item.path" class="text-gray-600 hover:text-primary font-medium transition-colors">
            {{ item.title }}
          </router-link>
        </nav>
      </div>
      
      <!-- 右侧功能区 -->
      <div class="flex items-center space-x-4">
        <!-- 搜索按钮 -->
        <n-button circle secondary @click="showSearch = true">
          <template #icon>
            <n-icon><search-outlined /></n-icon>
          </template>
        </n-button>
        
        <!-- 消息通知 -->
        <n-badge :value="unreadCount" :max="99" :show="unreadCount > 0">
          <n-button circle secondary>
            <template #icon>
              <n-icon><bell-outlined /></n-icon>
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
        
        <!-- 主题切换 (Using SettingOutlined for now) -->
        <n-button circle secondary @click="toggleTheme">
          <template #icon>
            <n-icon>
              <setting-outlined />
            </n-icon>
          </template>
        </n-button>
      </div>
    </div>
  </header>
  
  <!-- 搜索对话框 -->
  <n-modal v-model:show="showSearch" preset="card" title="全局搜索" style="width: 600px">
    <n-input v-model:value="searchQuery" placeholder="搜索事件、任务、无人机..." size="large">
      <template #prefix>
        <n-icon><search-outlined /></n-icon>
      </template>
    </n-input>
    
    <template #footer>
      <div class="text-xs text-gray-500">按 ESC 键关闭</div>
    </template>
  </n-modal>
</template>

<script setup>
import { ref, inject, computed, h } from 'vue'
import { useRouter } from 'vue-router'
import {
  SearchOutlined,
  BellOutlined,
  SettingOutlined // Only import icons guaranteed to exist
} from '@vicons/antd'
import { useUserStore } from '@/store/userStore'

// 注入主题切换函数
const isDarkMode = inject('isDarkMode')
const toggleDarkMode = inject('toggleDarkMode')

const toggleTheme = () => {
  toggleDarkMode()
}

// 搜索功能
const showSearch = ref(false)
const searchQuery = ref('')

// 用户信息
const userStore = useUserStore()
const router = useRouter()

// 用户头像显示的首字母
const userInitials = computed(() => {
  return userStore.user?.username?.substring(0, 2).toUpperCase() || 'U'
})

// 未读消息数
const unreadCount = ref(3)

// 主导航菜单项
const mainNavItems = [
  { title: '监控中心', path: '/monitor' },
  { title: '应急响应', path: '/emergency' },
  { title: '物流调度', path: '/logistics' },
  { title: '安防巡检', path: '/security' },
  { title: '无人机管理', path: '/drones' }
]

// 用户菜单选项
const userMenuOptions = [
  {
    label: '个人信息',
    key: 'profile',
    // Note: Using fas classes might require FontAwesome setup
    icon: () => h('i', { class: 'fas fa-user' })
  },
  {
    label: '设置',
    key: 'settings',
    icon: () => h('i', { class: 'fas fa-cog' })
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

// 监听用户菜单操作
const handleUserMenuSelect = (key) => {
  if (key === 'logout') {
    userStore.logout()
    router.push('/login')
  } else if (key === 'profile') {
    router.push('/profile')
  } else if (key === 'settings') {
    router.push('/settings')
  }
}
</script> 