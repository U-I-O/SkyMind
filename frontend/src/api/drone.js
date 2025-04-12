import api from './index'

/**
 * Get all drones
 * @returns {Promise<Array<object>>} A list of drones
 */
export function getDrones() {
  return api.get('/drones')
}

/**
 * Get a specific drone by ID
 * @param {string} id - The ID of the drone
 * @returns {Promise<object>} The drone data
 */
export function getDroneById(id) {
  return api.get(`/drones/${id}`)
}

/**
 * Create a new drone
 * @param {object} data - The data for the new drone
 * @returns {Promise<object>} The created drone data
 */
export function createDrone(data) {
  return api.post('/drones', data)
}

/**
 * Update an existing drone
 * @param {string} id - The ID of the drone to update
 * @param {object} data - The updated drone data
 * @returns {Promise<object>} The updated drone data
 */
export function updateDrone(id, data) {
  return api.put(`/drones/${id}`, data)
}

/**
 * Delete a drone
 * @param {string} id - The ID of the drone to delete
 * @returns {Promise<void>}
 */
export function deleteDrone(id) {
  return api.delete(`/drones/${id}`)
}

/**
 * Assign a task to a drone
 * @param {string} id - The ID of the drone
 * @param {string} taskId - The ID of the task to assign
 * @returns {Promise<object>} The result of the assignment
 */
export function assignTask(id, taskId) {
  return api.post(`/drones/${id}/tasks`, { task_id: taskId })
}

/**
 * Remove a task from a drone
 * @param {string} id - The ID of the drone
 * @param {string} taskId - The ID of the task to remove
 * @returns {Promise<void>}
 */
export function removeTask(id, taskId) {
  return api.delete(`/drones/${id}/tasks/${taskId}`)
}

/**
 * Get the status of a specific drone
 * @param {string} id - The ID of the drone
 * @returns {Promise<object>} The drone status data
 */
export function getDroneStatus(id) {
  return api.get(`/drones/${id}/status`)
}

/**
 * Get the telemetry data for a specific drone
 * @param {string} id - The ID of the drone
 * @returns {Promise<object>} The drone telemetry data
 */
export function getDroneTelemetry(id) {
  return api.get(`/drones/${id}/telemetry`)
}

/**
 * Get flight records for a specific drone
 * @param {string} id - The ID of the drone
 * @param {object} params - Query parameters (e.g., { limit: 10, skip: 0 })
 * @returns {Promise<Array<object>>} A list of flight records
 */
export function getDroneFlightHistory(id, params = {}) {
  return api.get(`/drones/${id}/flights`, { params })
}

/**
 * Get tasks assigned to a specific drone
 * @param {string} id - The ID of the drone
 * @returns {Promise<Array<object>>} A list of assigned tasks
 */
export function getDroneTasks(id) {
  return api.get(`/drones/${id}/tasks`)
}

/**
 * Find available drones based on task requirements
 * @param {object} requirements - Task requirements (e.g., { capabilities: ['camera', 'delivery'] })
 * @returns {Promise<Array<object>>} A list of available drones
 */
export function getAvailableDrones(requirements = {}) {
  return api.post('/drones/available', requirements)
}

/**
 * Send a control command to a drone
 * @param {string} id - The ID of the drone
 * @param {string} command - The command to send (e.g., 'takeoff', 'land', 'return_to_home')
 * @param {object} params - Optional parameters for the command
 * @returns {Promise<object>} The result of the command
 */
export function controlDrone(id, command, params = {}) {
  return api.post(`/drones/${id}/control`, { 
    command, 
    params 
  })
}

/**
 * Start a mission for a drone based on a task ID
 * @param {string} id - The ID of the drone
 * @param {string} taskId - The ID of the task defining the mission
 * @returns {Promise<object>} The result of starting the mission
 */
export function startMission(id, taskId) {
  return api.post(`/drones/${id}/mission/start`, { task_id: taskId })
}

/**
 * Pause the current mission for a drone
 * @param {string} id - The ID of the drone
 * @returns {Promise<object>} The result of pausing the mission
 */
export function pauseMission(id) {
  return api.post(`/drones/${id}/mission/pause`)
}

/**
 * Resume the paused mission for a drone
 * @param {string} id - The ID of the drone
 * @returns {Promise<object>} The result of resuming the mission
 */
export function resumeMission(id) {
  return api.post(`/drones/${id}/mission/resume`)
}

/**
 * Cancel the current mission for a drone
 * @param {string} id - The ID of the drone
 * @returns {Promise<object>} The result of canceling the mission
 */
export function cancelMission(id) {
  return api.post(`/drones/${id}/mission/cancel`)
}

export const DroneAPI = {
  getAllDrones: () => {
    return api.get('/drones')
  },

  /**
   * Get a specific drone by ID
   * @param {string} id - The ID of the drone
   * @returns {Promise<object>} The drone data
   */
  getDroneById: (id) => {
    return api.get(`/drones/${id}`)
  },

  /**
   * Add a new drone
   * @param {object} data - The data for the new drone
   * @returns {Promise<object>} The newly added drone data
   */
  addDrone: (data) => {
    return api.post('/drones', data)
  },

  /**
   * Update an existing drone
   * @param {string} id - The ID of the drone to update
   * @param {object} data - The updated drone data
   * @returns {Promise<object>} The updated drone data
   */
  updateDrone: (id, data) => {
    return api.put(`/drones/${id}`, data)
  },

  /**
   * Delete a drone
   * @param {string} id - The ID of the drone to delete
   * @returns {Promise<void>}
   */
  deleteDrone: (id) => {
    return api.delete(`/drones/${id}`)
  },

  /**
   * Assign a task to a drone
   * @param {string} id - The ID of the drone
   * @param {string} taskId - The ID of the task to assign
   * @returns {Promise<object>} The result of the assignment
   */
  assignTaskToDrone: (id, taskId) => {
    return api.post(`/drones/${id}/tasks`, { task_id: taskId })
  },

  /**
   * Unassign a task from a drone
   * @param {string} id - The ID of the drone
   * @param {string} taskId - The ID of the task to unassign
   * @returns {Promise<void>}
   */
  unassignTaskFromDrone: (id, taskId) => {
    return api.delete(`/drones/${id}/tasks/${taskId}`)
  },

  /**
   * Get the status of a specific drone
   * @param {string} id - The ID of the drone
   * @returns {Promise<object>} The drone status data
   */
  getDroneStatus: (id) => {
    return api.get(`/drones/${id}/status`)
  },

  /**
   * Get the telemetry data for a specific drone
   * @param {string} id - The ID of the drone
   * @returns {Promise<object>} The drone telemetry data
   */
  getDroneTelemetry: (id) => {
    return api.get(`/drones/${id}/telemetry`)
  },

  /**
   * Get flight records for a specific drone
   * @param {string} id - The ID of the drone
   * @param {object} params - Query parameters (e.g., { limit: 10, skip: 0 })
   * @returns {Promise<Array<object>>} A list of flight records
   */
  getDroneFlights: (id, params = {}) => {
    return api.get(`/drones/${id}/flights`, { params })
  },

  /**
   * Get tasks assigned to a specific drone
   * @param {string} id - The ID of the drone
   * @returns {Promise<Array<object>>} A list of assigned tasks
   */
  getDroneTasks: (id) => {
    return api.get(`/drones/${id}/tasks`)
  },

  /**
   * Find available drones based on task requirements
   * @param {object} requirements - Task requirements
   * @returns {Promise<Array<object>>} A list of available drones
   */
  findAvailableDrones: (requirements) => {
    return api.post('/drones/available', requirements)
  },

  /**
   * Send a control command to a drone
   * @param {string} id - The ID of the drone
   * @param {string} command - The command to send (e.g., 'takeoff', 'land', 'return_to_home')
   * @param {object} args - Optional arguments for the command
   * @returns {Promise<object>} The result of the command
   */
  controlDrone: (id, command, args = {}) => {
    return api.post(`/drones/${id}/control`, {
      command,
      ...args
    })
  },

  /**
   * Start a mission for a drone based on a task ID
   * @param {string} id - The ID of the drone
   * @param {string} taskId - The ID of the task defining the mission
   * @returns {Promise<object>} The result of starting the mission
   */
  startDroneMission: (id, taskId) => {
    return api.post(`/drones/${id}/mission/start`, { task_id: taskId })
  },

  /**
   * Pause the current mission for a drone
   * @param {string} id - The ID of the drone
   * @returns {Promise<object>} The result of pausing the mission
   */
  pauseDroneMission: (id) => {
    return api.post(`/drones/${id}/mission/pause`)
  },

  /**
   * Resume the paused mission for a drone
   * @param {string} id - The ID of the drone
   * @returns {Promise<object>} The result of resuming the mission
   */
  resumeDroneMission: (id) => {
    return api.post(`/drones/${id}/mission/resume`)
  },

  /**
   * Cancel the current mission for a drone
   * @param {string} id - The ID of the drone
   * @returns {Promise<object>} The result of canceling the mission
   */
  cancelDroneMission: (id) => {
    return api.post(`/drones/${id}/mission/cancel`)
  },
}