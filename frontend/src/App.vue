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
                <!-- 全局共享地图组件 -->
                <div v-if="showHeader" class="absolute inset-0 w-full h-full">
                  <Map3D 
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
import { computed, provide, ref, watch, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter, onBeforeRouteUpdate } from 'vue-router'
import { darkTheme } from 'naive-ui'
import AppHeader from '@/components/layout/AppHeader.vue'
import Map3D from '@/components/map/Map3D.vue'

// 主题配置
const isDarkMode = ref(false)
const theme = computed(() => isDarkMode.value ? darkTheme : null)

// 提供切换主题的函数给子组件
const toggleDarkMode = () => {
  isDarkMode.value = !isDarkMode.value
}
provide('toggleDarkMode', toggleDarkMode)
provide('isDarkMode', isDarkMode)

// 地图相关状态
const mapRef = ref(null)
const selectedDrone = ref(null)
const mapEvents = ref([]) // 全局事件状态

// 处理无人机点击事件
const handleDroneClicked = (droneId) => {
  // 这里可以通过store获取无人机信息
  // 示例: const drone = droneStore.getDroneById(droneId)
  // selectedDrone.value = drone
  
  // 触发事件通知子组件
  window.dispatchEvent(new CustomEvent('drone-selected', { detail: { droneId } }))
}

// 处理事件点击
const handleEventClicked = (event) => {
  // 触发事件通知子组件
  window.dispatchEvent(new CustomEvent('event-selected', { detail: { eventId: event.id } }))
}

// 处理地图点击 - 关闭弹窗
const handleMapClicked = () => {
  if (mapRef.value && mapRef.value.closeEventInfo) {
    mapRef.value.closeEventInfo()
  }
}

// 提供地图相关方法给子组件
provide('mapRef', mapRef)
provide('flyToLocation', (coordinates) => {
  if (mapRef.value && mapRef.value.flyTo) {
    mapRef.value.flyTo(coordinates)
  }
})

// 提供事件相关方法给子组件
provide('setMapEvents', (events) => {
  mapEvents.value = events
})

// 根据路由决定是否显示顶部导航
const route = useRoute()
const showHeader = computed(() => route.path !== '/login')

// 监听路由变化，关闭事件弹窗
watch(() => route.path, () => {
  if (mapRef.value && mapRef.value.closeEventInfo) {
    mapRef.value.closeEventInfo()
  }
})

// 路由守卫，处理页面切换
onBeforeRouteUpdate((to, from, next) => {
  if (mapRef.value && mapRef.value.closeEventInfo) {
    mapRef.value.closeEventInfo()
  }
  next()
})

// 监听页面可见性变化，用于处理标签页切换或窗口最小化的情况
const handleVisibilityChange = () => {
  if (document.hidden && mapRef.value && mapRef.value.closeEventInfo) {
    mapRef.value.closeEventInfo()
  }
}

// 添加页面可见性监听
onMounted(() => {
  document.addEventListener('visibilitychange', handleVisibilityChange)
})

// 移除事件监听
onUnmounted(() => {
  document.removeEventListener('visibilitychange', handleVisibilityChange)
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