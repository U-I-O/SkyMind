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
                    @drone-clicked="handleDroneClicked"
                  />
                </div>
                
                <!-- 路由视图 - 漂浮在地图上方 -->
                <div class="absolute inset-0 z-10" :class="{ 'pointer-events-none': showHeader }">
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
import { computed, provide, ref } from 'vue'
import { useRoute } from 'vue-router'
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

// 处理无人机点击事件
const handleDroneClicked = (droneId) => {
  if (!droneId) return;
  
  // 通过全局事件通知组件
  window.dispatchEvent(new CustomEvent('drone-selected', { 
    detail: { droneId, source: 'map' } 
  }))
}

// 提供选择无人机的方法给子组件
const emitDroneSelected = (droneId) => {
  // 触发全局事件
  window.dispatchEvent(new CustomEvent('drone-selected', { 
    detail: { droneId, source: 'panel' } 
  }))
  
  // 更新选中的无人机
  selectedDrone.value = { drone_id: droneId }
  
  // 如果地图组件可用，飞向该无人机
  if (mapRef.value && mapRef.value.flyToDrone) {
    mapRef.value.flyToDrone(droneId);
  }
}
provide('emitDroneSelected', emitDroneSelected)

// 提供地图相关方法给子组件
provide('mapRef', mapRef)
provide('flyToLocation', (coordinates) => {
  if (mapRef.value && mapRef.value.flyTo) {
    mapRef.value.flyTo(coordinates)
  }
})

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