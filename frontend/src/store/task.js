import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import * as taskApi from '@/api/task'

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
   * Reset the store to its initial state
   */
  function reset() {
    tasks.value = []
    loading.value = false
    error.value = null
    lastUpdated.value = null
  }
  
  return {
    // State
    tasks,
    loading,
    error,
    lastUpdated,
    
    // Computed
    activeTasks,
    completedTasks,
    failedTasks,
    tasksByStatus,
    tasksByType,
    tasksByDroneId,
    totalTaskCount,
    activeTaskCount,
    
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
    reset
  }
}) 