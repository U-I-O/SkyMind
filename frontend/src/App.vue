<template>
  <n-config-provider :theme="theme">
    <n-loading-bar-provider>
      <n-dialog-provider>
        <n-notification-provider>
          <n-message-provider>
            <div class="h-screen flex flex-col">
              <!-- 顶部导航栏 -->
              <AppHeader v-if="showHeader" />
              
              <!-- 主内容区 - 包含全局地图和路由视图 -->
              <main class="flex-1 overflow-hidden relative">
                <!-- 全局共享地图组件 - 安全模式 (UIO) -->
                <div v-if="showHeader && isSecurityMode" class="absolute inset-0 w-full h-full">
                  <Map3D_UIO 
                    ref="mapRef"
                    :show-drones="true"
                    :show-live-updates="true"
                    :show-patrol-areas="true"
                    :center-on-selected="selectedDrone !== null"
                    :selected-drone-id="selectedDrone?.drone_id"
                    @drone-clicked="handleDroneClicked"
                    @patrol-area-clicked="handlePatrolAreaClicked"
                  />
                </div>

                <!-- 全局共享地图组件 - 常规模式 (WG) -->
                <div v-if="showHeader && !isSecurityMode" class="absolute inset-0 w-full h-full">
                  <Map3D_WG 
                    ref="mapRef"
                    :show-drones="true"
                    :show-live-updates="true"
                    :center-on-selected="selectedDrone !== null"
                    :selected-drone-id="selectedDrone?.drone_id"
                    :events="mapEvents"
                    @drone-clicked="handleDroneClicked"
                    @event-clicked="handleEventClicked"
                    @map-clicked="handleMapClicked"
                  />
                </div>
                
                <!-- 路由视图 - 漂浮在地图上方 -->
                <div class="absolute inset-0" :class="{ 'pointer-events-none': showHeader }">
                  <router-view v-slot="{ Component }">
                    <transition name="fade" mode="out-in">
                      <component :is="Component" />
                    </transition>
                  </router-view>
                </div>
              </main>
            </div>
          </n-message-provider>
        </n-notification-provider>
      </n-dialog-provider>
    </n-loading-bar-provider>
  </n-config-provider>
</template>

<script setup>
import { computed, provide, ref, watch, onMounted, onUnmounted, watchEffect } from 'vue'
import { useRoute, useRouter, onBeforeRouteUpdate } from 'vue-router'
import { darkTheme } from 'naive-ui'
import AppHeader from '@/components/layout/AppHeader.vue'
import Map3D_UIO from '@/components/map/Map3D_UIO.vue'
import Map3D_WG from '@/components/map/Map3D_WG.vue'

// 主题配置
const isDarkMode = ref(false)
const theme = computed(() => isDarkMode.value ? darkTheme : null)

// 提供切换主题的函数给子组件
const toggleDarkMode = () => {
  isDarkMode.value = !isDarkMode.value
}
provide('toggleDarkMode', toggleDarkMode)
provide('isDarkMode', isDarkMode)

// 路由相关
const route = useRoute()
// 根据路由决定是否显示顶部导航
const showHeader = computed(() => route.path !== '/login')
// 根据路由判断是否为安全模式
const isSecurityMode = computed(() => route.path.includes('/security'))

// 地图相关状态
const mapRef = ref(null)
const selectedDrone = ref(null)
const mapEvents = ref([]) // 全局事件状态（仅在WG模式下使用）

// 在window上暴露地图实例，方便组件间访问
onMounted(() => {
  // 创建一个调试工具，方便在浏览器控制台访问地图实例
  window.skymindDebug = window.skymindDebug || {};
  window.skymindDebug.mapRef = mapRef;

  // 监听地图加载完成事件
  watchEffect(() => {
    if (mapRef.value) {
      console.info('全局地图实例已加载完成', mapRef.value);
    }
  });

  // 添加页面可见性监听（WG模式使用）
  document.addEventListener('visibilitychange', handleVisibilityChange)
});

// 移除事件监听
onUnmounted(() => {
  document.removeEventListener('visibilitychange', handleVisibilityChange)
})

// ---- UIO模式相关方法 ----
// 处理巡逻区域点击事件（仅UIO模式）
const handlePatrolAreaClicked = (area) => {
  if (isSecurityMode.value) {
    // 触发事件通知子组件
    window.dispatchEvent(new CustomEvent('patrol-area-selected', { detail: { area } }))
  }
}

// ---- WG模式相关方法 ----
// 处理事件点击（仅WG模式）
const handleEventClicked = (event) => {
  if (!isSecurityMode.value) {
    // 触发事件通知子组件
    window.dispatchEvent(new CustomEvent('event-selected', { detail: { eventId: event.id } }))
  }
}

// 处理地图点击 - 关闭弹窗（仅WG模式）
const handleMapClicked = () => {
  if (!isSecurityMode.value && mapRef.value && mapRef.value.closeEventInfo) {
    mapRef.value.closeEventInfo()
  }
}

// 页面可见性变化处理（仅WG模式使用）
const handleVisibilityChange = () => {
  if (!isSecurityMode.value && document.hidden && mapRef.value && mapRef.value.closeEventInfo) {
    mapRef.value.closeEventInfo()
  }
}

// ---- 通用方法 ----
// 处理无人机点击事件（两种模式都使用）
const handleDroneClicked = (droneId) => {
  // 触发事件通知子组件
  window.dispatchEvent(new CustomEvent('drone-selected', { detail: { droneId } }))
}

// 提供地图相关方法给子组件
provide('mapRef', mapRef)
provide('flyToLocation', (coordinates) => {
  if (mapRef.value && mapRef.value.flyTo) {
    mapRef.value.flyTo(coordinates)
  }
})

// 提供事件相关方法给子组件（WG模式使用）
provide('setMapEvents', (events) => {
  if (!isSecurityMode.value) {
    mapEvents.value = events
  }
})

// 监听路由变化，关闭事件弹窗（WG模式使用）
watch(() => route.path, (newPath) => {
  // 当模式切换时，清除地图上的事件信息
  if (mapRef.value && mapRef.value.closeEventInfo) {
    mapRef.value.closeEventInfo()
  }
})

// 路由守卫，处理页面切换（WG模式使用）
onBeforeRouteUpdate((to, from, next) => {
  if (mapRef.value && mapRef.value.closeEventInfo) {
    mapRef.value.closeEventInfo()
  }
  next()
})
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