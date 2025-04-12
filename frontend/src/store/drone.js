import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import * as droneApi from '@/api/drone'

/**
 * Store for managing drone state
 * 
 * This store centralizes all drone-related data and operations,
 * making it easy to access drone information from anywhere in the app.
 */
export const useDroneStore = defineStore('drone', () => {
  // State
  const drones = ref([])
  const loading = ref(false)
  const error = ref(null)
  const lastUpdated = ref(null)
  
  // Computed
  const activeDrones = computed(() => 
    drones.value.filter(drone => drone.status !== 'offline')
  )
  
  const availableDrones = computed(() => 
    drones.value.filter(drone => drone.status === 'idle')
  )
  
  const dronesByStatus = computed(() => {
    const result = {
      idle: [],
      flying: [],
      charging: [],
      maintenance: [],
      offline: []
    }
    
    drones.value.forEach(drone => {
      if (result[drone.status]) {
        result[drone.status].push(drone)
      }
    })
    
    return result
  })
  
  const totalDroneCount = computed(() => drones.value.length)
  const activeDroneCount = computed(() => activeDrones.value.length)
  
  // Actions
  
  /**
   * Fetch all drones from the API
   */
  async function fetchDrones() {
    loading.value = true
    error.value = null
    
    try {
      const response = await droneApi.getDrones()
      
      // 添加响应数据结构的日志便于调试
      console.log('API响应数据结构:', response)
      
      // The API response could be directly the data array or wrapped in a data property
      if (Array.isArray(response)) {
        drones.value = response
      } else if (response && response.data) {
        if (Array.isArray(response.data)) {
          drones.value = response.data
        } else {
          console.warn('API返回的data不是数组:', response.data)
          drones.value = []
        }
      } else {
        console.warn('API返回了非预期的格式:', response)
        drones.value = []
      }
      
      // 如果没有获取到无人机数据，添加一个模拟无人机用于UI测试
      if (drones.value.length === 0) {
        console.log('没有真实无人机数据，添加模拟数据')
        drones.value = getMockDrones()
      }
      
      // Update lastUpdated timestamp
      lastUpdated.value = new Date()
      
      // Log successful fetch for debugging
      console.log(`成功获取 ${drones.value.length} 架无人机数据`)
      return drones.value
    } catch (err) {
      console.error('获取无人机数据失败:', err)
      error.value = err.message || '获取无人机数据失败'
      
      // Don't discard previous drone data on error
      if (drones.value.length === 0) {
        console.log('使用模拟无人机数据')
        drones.value = getMockDrones()
      }
      
      // Re-throw the error so the caller can handle it
      throw err
    } finally {
      loading.value = false
    }
  }
  
  /**
   * Get mock drone data for testing
   */
  function getMockDrones() {
    return [
      {
        drone_id: 'mock-drone-1',
        name: '模拟无人机 1',
        model: 'DJI Mavic 3',
        status: 'idle',
        battery_level: 85,
        camera_equipped: true,
        capabilities: ['camera', 'delivery'],
        max_flight_time: 45,
        max_altitude: 500,
        current_location: {
          coordinates: [114.367, 30.54, 100]
        }
      },
      {
        drone_id: 'mock-drone-2',
        name: '模拟无人机 2',
        model: 'DJI Phantom 4',
        status: 'flying',
        battery_level: 62,
        camera_equipped: true,
        capabilities: ['camera', 'security'],
        max_flight_time: 30,
        max_altitude: 400,
        current_location: {
          coordinates: [114.363, 30.535, 120]
        }
      },
      {
        drone_id: 'mock-drone-3',
        name: '模拟无人机 3',
        model: 'Autel EVO II',
        status: 'charging',
        battery_level: 24,
        camera_equipped: true,
        capabilities: ['camera', 'inspection'],
        max_flight_time: 40,
        max_altitude: 450, 
        current_location: {
          coordinates: [114.37, 30.545, 0]
        }
      }
    ]
  }
  
  /**
   * Get a drone by its ID
   * @param {string} droneId - The drone ID to find
   * @returns {Object|null} The drone object or null if not found
   */
  function getDroneById(droneId) {
    return drones.value.find(drone => drone.drone_id === droneId) || null
  }
  
  /**
   * Add a new drone to the store
   * @param {Object} drone The drone object to add
   */
  function addDrone(drone) {
    if (!drone || !drone.drone_id) {
      console.error('添加无人机失败：缺少drone_id')
      return
    }
    
    // 检查是否已存在
    const existingIndex = drones.value.findIndex(d => d.drone_id === drone.drone_id)
    if (existingIndex >= 0) {
      // 更新现有无人机
      drones.value[existingIndex] = { ...drones.value[existingIndex], ...drone }
      console.log(`更新现有无人机: ${drone.drone_id}`)
    } else {
      // 添加新无人机
      drones.value.push(drone)
      console.log(`添加新无人机: ${drone.drone_id}`)
    }
  }
  
  /**
   * Update an existing drone
   * @param {Object} updatedDrone - The updated drone data
   */
  function updateDrone(updatedDrone) {
    const index = drones.value.findIndex(d => d.drone_id === updatedDrone.drone_id)
    
    if (index !== -1) {
      // Merge the existing drone with updated values
      drones.value[index] = { 
        ...drones.value[index], 
        ...updatedDrone,
        // Ensure lastUpdated is set
        lastUpdated: new Date()
      }
    } else {
      // If drone doesn't exist, add it
      addDrone({
        ...updatedDrone,
        lastUpdated: new Date()
      })
    }
  }
  
  /**
   * Remove a drone from the store
   * @param {string} droneId - ID of the drone to remove
   */
  function removeDrone(droneId) {
    const index = drones.value.findIndex(d => d.drone_id === droneId)
    if (index !== -1) {
      drones.value.splice(index, 1)
    }
  }
  
  /**
   * Send a command to a drone
   * @param {string} droneId - The target drone's ID
   * @param {string} command - The command to send
   * @param {Object} params - Command parameters
   * @returns {Promise} Command result
   */
  async function sendDroneCommand(droneId, command, params = {}) {
    try {
      const response = await droneApi.controlDrone(droneId, command, params)
      
      // Update local drone state if the response includes updated drone data
      if (response.data && response.data.drone) {
        updateDrone(response.data.drone)
      }
      
      return response.data
    } catch (err) {
      console.error(`Failed to send command ${command} to drone ${droneId}:`, err)
      throw err
    }
  }
  
  /**
   * Reset the store to its initial state
   */
  function reset() {
    drones.value = []
    loading.value = false
    error.value = null
    lastUpdated.value = null
  }
  
  return {
    // State
    drones,
    loading,
    error,
    lastUpdated,
    
    // Computed
    activeDrones,
    availableDrones,
    dronesByStatus,
    totalDroneCount,
    activeDroneCount,
    
    // Actions
    fetchDrones,
    getDroneById,
    addDrone,
    updateDrone,
    removeDrone,
    sendDroneCommand,
    reset
  }
}) 