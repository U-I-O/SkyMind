import api from './index'

/**
 * Get all tasks
 * @param {Object} params - Query parameters (status, type, limit, skip, etc.)
 * @returns {Promise} List of tasks
 */
export function getTasks(params = {}) {
  return api.get('/api/v1/tasks', { params })
}

/**
 * Get specific task details
 * @param {string} id - Task ID
 * @returns {Promise} Task details
 */
export function getTaskById(id) {
  return api.get(`/api/v1/tasks/${id}`)
}

/**
 * Create a new task
 * @param {Object} data - Task information
 * @returns {Promise} Creation result
 */
export function createTask(data) {
  return api.post('/api/v1/tasks', data)
}

/**
 * Update task information
 * @param {string} id - Task ID
 * @param {Object} data - Updated information
 * @returns {Promise} Update result
 */
export function updateTask(id, data) {
  return api.put(`/api/v1/tasks/${id}`, data)
}

/**
 * Cancel a task
 * @param {string} id - Task ID
 * @param {Object} data - Cancellation details (reason, etc.)
 * @returns {Promise} Cancellation result
 */
export function cancelTask(id, data = {}) {
  return api.post(`/api/v1/tasks/${id}/cancel`, data)
}

/**
 * Get tasks for a specific drone
 * @param {string} droneId - Drone ID
 * @param {Object} params - Query parameters (status, etc.)
 * @returns {Promise} List of tasks assigned to the drone
 */
export function getTasksByDrone(droneId, params = {}) {
  return api.get(`/drones/${droneId}/tasks`, { params })
}

/**
 * Assign a task to a drone
 * @param {string} taskId - Task ID
 * @param {string} droneId - Drone ID
 * @returns {Promise} Assignment result
 */
export function assignTask(taskId, droneId) {
  return api.post(`/api/v1/tasks/${taskId}/assign`, { drone_id: droneId })
}

/**
 * Update task status
 * @param {string} id - Task ID
 * @param {string} status - New status
 * @returns {Promise} Update result
 */
export function updateTaskStatus(id, status) {
  return api.post(`/api/v1/tasks/${id}/status`, { status })
}

/**
 * Get task status statistics
 * @returns {Promise} Task statistics by status
 */
export function getTaskStatusStatistics() {
  return api.get('/api/v1/tasks/statistics/status')
}

/**
 * Get task type statistics
 * @returns {Promise} Task statistics by type
 */
export function getTaskTypeStatistics() {
  return api.get('/api/v1/tasks/statistics/type')
}

/**
 * Get a batch of tasks by IDs
 * @param {Array} taskIds - Array of task IDs
 * @returns {Promise} Array of task details
 */
export function batchGetTasks(taskIds) {
  return api.post('/api/v1/tasks/batch', { task_ids: taskIds })
}

/**
 * Create a delivery task
 * @param {Object} data - Delivery task information
 * @returns {Promise} Creation result
 */
export function createDeliveryTask(data) {
  return createTask({
    ...data,
    type: 'delivery'
  })
}

/**
 * Create an inspection task
 * @param {Object} data - Inspection task information
 * @returns {Promise} Creation result
 */
export function createInspectionTask(data) {
  return createTask({
    ...data,
    type: 'inspection'
  })
}

/**
 * Create a surveillance task
 * @param {Object} data - Surveillance task information
 * @returns {Promise} Creation result
 */
export function createSurveillanceTask(data) {
  return createTask({
    ...data,
    type: 'surveillance'
  })
}

/**
 * Create an emergency response task
 * @param {Object} data - Emergency task information
 * @returns {Promise} Creation result
 */
export function createEmergencyTask(data) {
  return createTask({
    ...data,
    type: 'emergency',
    priority: data.priority || 10 // Default to highest priority
  })
} 