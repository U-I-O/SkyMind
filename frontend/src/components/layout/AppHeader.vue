<template>
  <header class="light-header">
    <div class="container mx-auto px-6 py-2 flex justify-between items-center">
      <!-- 左侧Logo -->
      <div class="flex-shrink-0 ml-2">
        <router-link to="/" class="flex items-center space-x-2">
          <div class="logo-container">
            <div class="logo-glow"></div>
            <div class="logo-inner">SG</div>
          </div>
          <h1 class="text-xl font-bold text-slate-700 tracking-wider">SkyGuard</h1>
        </router-link>
      </div>
      
      <!-- 居中的主导航菜单 -->
      <nav class="hidden md:flex flex-1 justify-center">
        <div class="flex space-x-8">
          <router-link 
            v-for="item in mainNavItems" 
            :key="item.path" 
            :to="item.path" 
            class="py-2 px-4 relative transition-all duration-300 ease-in-out group hover:bg-blue-50 rounded nav-link"
            :class="[
              isActiveRoute(item.path) 
                ? 'text-blue-600 font-bold text-lg active-nav-link' 
                : 'text-slate-600 hover:text-blue-600 font-medium text-base'
            ]"
          >
            {{ item.title }}
            <div 
              class="nav-indicator"
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
        <n-button circle class="light-button" @click="showSearch = true">
          <template #icon>
            <n-icon><search-outlined /></n-icon>
          </template>
        </n-button>
        
        <!-- 消息通知 -->
        <n-badge :value="unreadCount" :max="99" :show="unreadCount > 0" processing color="#3b82f6">
          <n-button circle class="light-button">
            <template #icon>
              <n-icon><bell-outlined /></n-icon>
            </template>
          </n-button>
        </n-badge>
        
        <!-- 用户菜单 -->
        <n-dropdown :options="userMenuOptions" placement="bottom-end" trigger="click" @select="handleUserMenuSelect">
          <div class="flex items-center cursor-pointer">
            <div class="user-avatar">
              {{ userInitials }}
            </div>
          </div>
        </n-dropdown>
        
        <!-- 主题切换 -->
        <n-button circle class="light-button" @click="toggleTheme">
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
  <n-modal v-model:show="showSearch" preset="card" title="全局搜索" class="light-modal" style="width: 600px">
    <n-input v-model:value="searchQuery" placeholder="搜索事件、任务、无人机..." size="large" class="light-input">
      <template #prefix>
        <n-icon><search-outlined /></n-icon>
      </template>
    </n-input>
    
    <template #footer>
      <div class="text-xs text-blue-500">按 ESC 键关闭</div>
    </template>
  </n-modal>
</template>

<script setup>
import { ref, inject, computed, h } from 'vue'
import { useRouter, useRoute } from 'vue-router'
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
const route = useRoute()

// 检查当前路由是否活跃
const isActiveRoute = (path) => {
  return route.path === path || route.path.startsWith(`${path}/`)
}

// 用户头像显示的首字母
const userInitials = computed(() => {
  return userStore.user?.username?.substring(0, 2).toUpperCase() || 'U'
})

// 未读消息数
const unreadCount = ref(3)

// 主导航菜单项
const mainNavItems = [
  { title: '监控中心', path: '/' },
  { title: '应急响应', path: '/emergency' },
 // { title: '物流调度', path: '/logistics' },
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

<style scoped>
.light-header {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid rgba(59, 130, 246, 0.1);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05);
  position: relative;
  z-index: 50;
}

.light-header::before {
  content: "";
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 1px;
  background: linear-gradient(to right, 
    transparent, 
    rgba(59, 130, 246, 0.2) 20%, 
    rgba(59, 130, 246, 0.2) 80%, 
    transparent
  );
}

.logo-container {
  position: relative;
  width: 40px;
  height: 40px;
  border-radius: 8px;
  background: linear-gradient(135deg, #93c5fd, #3b82f6);
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  color: white;
  overflow: hidden;
  box-shadow: 0 4px 10px rgba(59, 130, 246, 0.3);
}

.logo-glow {
  position: absolute;
  top: -20px;
  left: -20px;
  width: 80px;
  height: 80px;
  background: radial-gradient(circle, rgba(255, 255, 255, 0.7) 0%, rgba(255, 255, 255, 0) 70%);
  animation: rotate 8s linear infinite;
  opacity: 0.6;
}

.logo-inner {
  position: relative;
  z-index: 2;
  font-size: 16px;
  letter-spacing: 1px;
  text-shadow: 0 2px 5px rgba(0, 0, 0, 0.2);
}

.nav-link {
  position: relative;
  overflow: hidden;
}

.active-nav-link {
  position: relative;
}

.active-nav-link::before {
  content: "";
  position: absolute;
  top: 0;
  left: 0;
  width: 4px;
  height: 100%;
  background: #3b82f6;
  border-radius: 0 2px 2px 0;
}

.nav-indicator {
  position: absolute;
  bottom: 0;
  left: 0;
  width: 100%;
  height: 2px;
  background: linear-gradient(to right, #93c5fd, #3b82f6);
  transform-origin: left;
  transition: transform 0.3s ease;
}

.light-button {
  background: white !important;
  border: 1px solid rgba(59, 130, 246, 0.2) !important;
  transition: all 0.3s ease;
}

.light-button:hover {
  border-color: rgba(59, 130, 246, 0.5) !important;
  box-shadow: 0 0 10px rgba(59, 130, 246, 0.15);
  transform: translateY(-1px);
}

.light-button:active {
  transform: translateY(0);
}

.user-avatar {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  background: linear-gradient(135deg, #93c5fd, #3b82f6);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-weight: bold;
  border: 1px solid rgba(59, 130, 246, 0.3);
  box-shadow: 0 2px 8px rgba(59, 130, 246, 0.2);
  transition: all 0.3s ease;
}

.user-avatar:hover {
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
  transform: scale(1.05);
}

.light-modal :deep(.n-card__content),
.light-modal :deep(.n-card__footer),
.light-modal :deep(.n-card__header) {
  background: white;
  color: #1e293b;
}

.light-modal :deep(.n-card__header__main) {
  color: #3b82f6;
  font-weight: bold;
}

.light-modal :deep(.n-card) {
  border: 1px solid rgba(59, 130, 246, 0.1);
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.1);
}

.light-input :deep(.n-input__border),
.light-input :deep(.n-input__state-border) {
  border-color: rgba(59, 130, 246, 0.2) !important;
}

.light-input :deep(.n-input-wrapper) {
  background: white !important;
}

.light-input :deep(.n-input__input-el) {
  color: #1e293b !important;
}

.light-input:hover :deep(.n-input__border) {
  border-color: rgba(59, 130, 246, 0.5) !important;
}

@keyframes rotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
</style>