<template>
  <n-config-provider :theme="theme">
    <n-loading-bar-provider>
      <n-dialog-provider>
        <n-notification-provider>
          <n-message-provider>
            <div class="h-screen flex flex-col">
              <!-- 顶部导航栏 -->
              <AppHeader v-if="showHeader" />
              
              <!-- 主内容区 -->
              <main class="flex-1 overflow-hidden">
                <router-view v-slot="{ Component }">
                  <transition name="fade" mode="out-in">
                    <component :is="Component" />
                  </transition>
                </router-view>
              </main>
            </div>
          </n-message-provider>
        </n-notification-provider>
      </n-dialog-provider>
    </n-loading-bar-provider>
  </n-config-provider>
</template>

<script setup>
import { computed, provide, ref } from 'vue'
import { useRoute } from 'vue-router'
import { darkTheme } from 'naive-ui'
import AppHeader from '@/components/layout/AppHeader.vue'

// 主题配置
const isDarkMode = ref(false)
const theme = computed(() => isDarkMode.value ? darkTheme : null)

// 提供切换主题的函数给子组件
const toggleDarkMode = () => {
  isDarkMode.value = !isDarkMode.value
}
provide('toggleDarkMode', toggleDarkMode)
provide('isDarkMode', isDarkMode)

// 根据路由决定是否显示顶部导航
const route = useRoute()
const showHeader = computed(() => route.path !== '/login')
</script>

<style>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style> 