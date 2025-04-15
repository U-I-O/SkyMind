import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import * as taskApi from '@/api/task'
import { calculateConvexHull, coordsToGeoJSON } from '@/utils/map/patrolAreaManager'

/**
 * Store for managing task state
 * 
 * This store centralizes all task-related data and operations,
 * making it easy to access task information from anywhere in the app.
 */
export const useTaskStore = defineStore('task', () => {
  // State
  const tasks = ref([])
  const loading = ref(false)
  const error = ref(null)
  const lastUpdated = ref(null)
  
  // 巡逻区域草稿状态
  const patrolAreaDraft = ref({
    isDrawing: false,     // 是否正在绘制巡逻区域
    points: [],           // 绘制的点数组 [[lng, lat], ...]
    geojson: null,        // GeoJSON 格式的巡逻区域
    taskFormId: null      // 关联的任务表单ID
  })
  
  // Computed
  const activeTasks = computed(() => 
    tasks.value.filter(task => ['pending', 'assigned', 'in_progress'].includes(task.status))
  )
  
  const completedTasks = computed(() => 
    tasks.value.filter(task => task.status === 'completed')
  )
  
  const failedTasks = computed(() => 
    tasks.value.filter(task => ['failed', 'cancelled'].includes(task.status))
  )
  
  const tasksByStatus = computed(() => {
    const result = {
      pending: [],
      assigned: [],
      in_progress: [],
      completed: [],
      failed: [],
      cancelled: []
    }
    
    tasks.value.forEach(task => {
      if (result[task.status]) {
        result[task.status].push(task)
      }
    })
    
    return result
  })
  
  const tasksByType = computed(() => {
    const result = {}
    
    tasks.value.forEach(task => {
      if (!result[task.type]) {
        result[task.type] = []
      }
      result[task.type].push(task)
    })
    
    return result
  })
  
  const tasksByDroneId = computed(() => {
    const result = {}
    
    tasks.value.forEach(task => {
      if (task.assigned_drones && task.assigned_drones.length > 0) {
        task.assigned_drones.forEach(droneId => {
          if (!result[droneId]) {
            result[droneId] = []
          }
          result[droneId].push(task)
        })
      }
    })
    
    return result
  })
  
  const totalTaskCount = computed(() => tasks.value.length)
  const activeTaskCount = computed(() => activeTasks.value.length)
  
  // 获取巡逻区域GeoJSON数据
  const patrolAreaGeoJSON = computed(() => {
    return patrolAreaDraft.value.geojson
  })
  
  // 获取巡逻区域坐标数组
  const patrolAreaCoordinates = computed(() => {
    return patrolAreaDraft.value.points
  })
  
  // 是否正在绘制巡逻区域
  const isDrawingPatrolArea = computed(() => {
    return patrolAreaDraft.value.isDrawing
  })
  
  // 获取巡逻区域凸包(最外围点)
  const patrolAreaConvexHull = computed(() => {
    if (patrolAreaDraft.value.points.length < 3) return [];
    return calculateConvexHull(patrolAreaDraft.value.points);
  })
  
  // Actions
  
  /**
   * Fetch all tasks from the API
   */
  async function fetchTasks() {
    loading.value = true
    error.value = null
    
    try {
      const response = await taskApi.getTasks()
      tasks.value = response.data
      lastUpdated.value = new Date()
    } catch (err) {
      console.error('Failed to fetch tasks:', err)
      error.value = err.message || 'Failed to fetch tasks'
      throw err
    } finally {
      loading.value = false
    }
  }
  
  /**
   * Fetch tasks for a specific drone
   * @param {string} droneId - The drone ID
   * @returns {Promise<Array>} Tasks assigned to the drone
   */
  async function fetchTasksForDrone(droneId) {
    loading.value = true
    error.value = null
    
    try {
      const response = await taskApi.getTasksByDrone(droneId)
      
      // Merge the fetched tasks with existing tasks
      response.data.forEach(task => {
        updateTask(task)
      })
      
      return response.data
    } catch (err) {
      console.error(`Failed to fetch tasks for drone ${droneId}:`, err)
      error.value = err.message || 'Failed to fetch drone tasks'
      throw err
    } finally {
      loading.value = false
    }
  }
  
  /**
   * Get a task by its ID
   * @param {string} taskId - The task ID to find
   * @returns {Object|null} The task object or null if not found
   */
  function getTaskById(taskId) {
    return tasks.value.find(task => task.task_id === taskId) || null
  }
  
  /**
   * Get all tasks for a drone
   * @param {string} droneId - The drone ID
   * @returns {Array} Tasks assigned to the drone
   */
  function getTasksForDrone(droneId) {
    return tasks.value.filter(task => 
      task.assigned_drones && task.assigned_drones.includes(droneId)
    )
  }
  
  /**
   * Add a new task to the store
   * @param {Object} task - The task object to add
   */
  function addTask(task) {
    const exists = tasks.value.some(t => t.task_id === task.task_id)
    if (!exists) {
      tasks.value.push(task)
    } else {
      // If task exists, update it
      updateTask(task)
    }
  }
  
  /**
   * Update an existing task
   * @param {Object} updatedTask - The updated task data
   */
  function updateTask(updatedTask) {
    const index = tasks.value.findIndex(t => t.task_id === updatedTask.task_id)
    
    if (index !== -1) {
      // Merge the existing task with updated values
      tasks.value[index] = { 
        ...tasks.value[index], 
        ...updatedTask 
      }
    } else {
      // If task doesn't exist, add it
      addTask(updatedTask)
    }
  }
  
  /**
   * Create a new task
   * @param {Object} taskData - Task data to create
   * @returns {Promise<Object>} Created task
   */
  async function createTask(taskData) {
    try {
      const response = await taskApi.createTask(taskData)
      addTask(response.data)
      return response.data
    } catch (err) {
      console.error('Failed to create task:', err)
      error.value = err.message || 'Failed to create task'
      throw err
    }
  }
  
  /**
   * Update a task's status
   * @param {string} taskId - Task ID
   * @param {string} status - New status
   * @returns {Promise<Object>} Updated task
   */
  async function updateTaskStatus(taskId, status) {
    try {
      const response = await taskApi.updateTaskStatus(taskId, status)
      updateTask(response.data)
      return response.data
    } catch (err) {
      console.error(`Failed to update task ${taskId} status:`, err)
      error.value = err.message || 'Failed to update task status'
      throw err
    }
  }
  
  /**
   * Assign a task to a drone
   * @param {string} taskId - Task ID
   * @param {string} droneId - Drone ID
   * @returns {Promise<Object>} Updated task
   */
  async function assignTaskToDrone(taskId, droneId) {
    try {
      const response = await taskApi.assignTask(taskId, droneId)
      updateTask(response.data)
      return response.data
    } catch (err) {
      console.error(`Failed to assign task ${taskId} to drone ${droneId}:`, err)
      error.value = err.message || 'Failed to assign task'
      throw err
    }
  }
  
  /**
   * Remove a task from the store
   * @param {string} taskId - ID of the task to remove
   */
  function removeTask(taskId) {
    const index = tasks.value.findIndex(t => t.task_id === taskId)
    if (index !== -1) {
      tasks.value.splice(index, 1)
    }
  }
  
  /**
   * 开始绘制巡逻区域
   * @param {string} taskFormId - 关联的任务表单ID
   */
  function startDrawingPatrolArea(taskFormId) {
    patrolAreaDraft.value = {
      isDrawing: true,
      points: [],
      geojson: null,
      taskFormId
    }
  }
  
  /**
   * 取消绘制巡逻区域
   */
  function cancelDrawingPatrolArea() {
    patrolAreaDraft.value = {
      isDrawing: false,
      points: [],
      geojson: null,
      taskFormId: null
    }
  }
  
  /**
   * 添加巡逻区域点位
   * @param {Array} point - 点位坐标 [lng, lat]
   */
  function addPatrolAreaPoint(point) {
    patrolAreaDraft.value.points.push(point)
    // 每次添加点位后更新GeoJSON
    updatePatrolAreaGeoJSON()
  }
  
  /**
   * 移除最后一个巡逻区域点位
   * @returns {Boolean} 是否成功移除
   */
  function removeLastPatrolAreaPoint() {
    if (patrolAreaDraft.value.points.length === 0) {
      return false
    }
    
    // 移除最后一个点
    patrolAreaDraft.value.points.pop()
    
    // 更新GeoJSON
    updatePatrolAreaGeoJSON()
    return true
  }
  
  /**
   * 更新GeoJSON数据
   * 使用凸包算法创建最外围的巡逻区域
   * 并更新点位数组，只保留凸包上的点
   */
  function updatePatrolAreaGeoJSON() {
    if (patrolAreaDraft.value.points.length < 3) {
      patrolAreaDraft.value.geojson = null
      return
    }
    
    // 计算凸包（最外围的点）
    const hullPoints = calculateConvexHull(patrolAreaDraft.value.points);
    
    // 使用凸包创建GeoJSON
    patrolAreaDraft.value.geojson = coordsToGeoJSON(hullPoints, {
      taskFormId: patrolAreaDraft.value.taskFormId
    });
    
    // 更新点位数组，只保留凸包上的点
    // 这样用户添加的内部点会被自动移除
    patrolAreaDraft.value.points = [...hullPoints];
  }
  
  /**
   * 完成巡逻区域绘制
   * @returns {Object} 完成的巡逻区域GeoJSON
   */
  function completePatrolArea() {
    updatePatrolAreaGeoJSON()
    
    // 获取凸包（最外围点）- 此时 patrolAreaDraft.value.points 已经只包含凸包上的点
    const convexHull = patrolAreaDraft.value.points;
    
    const result = { 
      ...patrolAreaDraft.value,
      convexHull // 添加凸包数据
    }
    
    // 提交后重置状态
    patrolAreaDraft.value.isDrawing = false
    
    return {
      geojson: result.geojson,
      points: [...convexHull], // 只包含凸包上的点
      convexHull: [...convexHull], // 包含凸包
      taskFormId: result.taskFormId
    }
  }

  /**
   * Reset the store to its initial state
   */
  function reset() {
    tasks.value = []
    loading.value = false
    error.value = null
    lastUpdated.value = null
    
    // 重置巡逻区域草稿
    patrolAreaDraft.value = {
      isDrawing: false,
      points: [],
      geojson: null,
      taskFormId: null
    }
  }
  
  return {
    // State
    tasks,
    loading,
    error,
    lastUpdated,
    patrolAreaDraft,
    
    // Computed
    activeTasks,
    completedTasks,
    failedTasks,
    tasksByStatus,
    tasksByType,
    tasksByDroneId,
    totalTaskCount,
    activeTaskCount,
    patrolAreaGeoJSON,
    patrolAreaCoordinates,
    isDrawingPatrolArea,
    patrolAreaConvexHull,
    
    // Actions
    fetchTasks,
    fetchTasksForDrone,
    getTaskById,
    getTasksForDrone,
    addTask,
    updateTask,
    createTask,
    updateTaskStatus,
    assignTaskToDrone,
    removeTask,
    reset,
    
    // 巡逻区域相关方法
    startDrawingPatrolArea,
    cancelDrawingPatrolArea,
    addPatrolAreaPoint,
    removeLastPatrolAreaPoint,
    updatePatrolAreaGeoJSON,
    completePatrolArea
  }
}) 