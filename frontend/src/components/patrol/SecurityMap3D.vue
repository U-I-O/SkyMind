<template>
  <div class="security-map-container">
    <Map3D 
      ref="map3dRef"
      :showLiveUpdates="false"
      :showDrones="false"
      :initialView="initialView"
      @map-clicked="handleMapClick"
    />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import Map3D from '@/components/map/Map3D.vue'

const props = defineProps({
  initialView: {
    type: Object,
    default: () => ({
      center: [114.367, 30.54],
      zoom: 15
    })
  }
})

const emit = defineEmits(['waypoint-added'])
const map3dRef = ref(null)

const handleMapClick = (position) => {
  emit('waypoint-added', {
    lng: position.lng,
    lat: position.lat,
    altitude: position.altitude || 100
  })
}

const startWaypointSelection = (callback) => {
  if (map3dRef.value) {
    map3dRef.value.startWaypointSelection(callback)
  }
}

const stopWaypointSelection = () => {
  if (map3dRef.value) {
    map3dRef.value.stopWaypointSelection()
  }
}

defineExpose({
  startWaypointSelection,
  stopWaypointSelection
})
</script>

<style scoped>
.security-map-container {
  width: 100%;
  height: 100%;
  border-radius: 4px;
  overflow: hidden;
}
</style>