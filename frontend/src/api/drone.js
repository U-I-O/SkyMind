import api from './index'

const LOCAL_STORAGE_KEY = 'skyMindDroneList';

// 生成模拟飞行记录 (移到外部以便共享)
function generateFlightLogs(count) {
  const logs = [];
  const generateRandomDate = () => {
    const today = new Date();
    const pastDaysCount = Math.floor(Math.random() * 30);
    const pastDate = new Date(today);
    pastDate.setDate(today.getDate() - pastDaysCount);
    const year = pastDate.getFullYear();
    const month = String(pastDate.getMonth() + 1).padStart(2, '0');
    const day = String(pastDate.getDate()).padStart(2, '0');
    const hour = String(Math.floor(Math.random() * 24)).padStart(2, '0');
    const minute = String(Math.floor(Math.random() * 60)).padStart(2, '0');
    return `${year}-${month}-${day} ${hour}:${minute}`;
  };
  const missionTypes = ['常规巡逻', '区域勘测', '安全监控', '紧急响应', '设备运输', '自动导航测试'];
  for (let i = 0; i < count; i++) {
    const duration = Math.floor(Math.random() * 50) + 10;
    const maxAltitude = Math.floor(Math.random() * 300) + 100;
    const distance = Math.floor(Math.random() * 15000) + 1000;
    const flightDate = generateRandomDate();
    const missionType = missionTypes[Math.floor(Math.random() * missionTypes.length)];
    logs.push({
      flight_id: `FLT-${Math.random().toString(36).substring(2, 10).toUpperCase()}`,
      date: flightDate,
      duration: duration,
      max_altitude_reached: maxAltitude,
      distance_covered: distance,
      mission_type: missionType,
      status: 'completed',
      battery_consumption: Math.floor(Math.random() * 80) + 10,
      avg_speed: Math.floor(Math.random() * 10) + 5
    });
  }
  logs.sort((a, b) => new Date(b.date) - new Date(a.date));
  return logs;
}

// 获取或生成并存储模拟无人机数据
function getOrGenerateMockDrones() {
  let storedDrones = localStorage.getItem(LOCAL_STORAGE_KEY);
  if (storedDrones) {
    try {
      console.log('Using drones data from localStorage');
      return JSON.parse(storedDrones);
    } catch (e) {
      console.error('Failed to parse drones data from localStorage', e);
      localStorage.removeItem(LOCAL_STORAGE_KEY); // 清除损坏的数据
    }
  }

  console.warn('Generating new mock drones data and storing in localStorage');
  const mockDrones = [];
  const droneCount = 14;
  const flyingDroneCount = 3;
  const flyingDroneBaseName = '雄鹰';
  const otherDroneTypes = ['天行', '天空', '神鹰', '飞马'];

  for (let i = 0; i < droneCount; i++) {
    const id = `drone-${i}`;
    const model = Math.random() > 0.6 ? 'DJI Mavic 3' : (Math.random() > 0.5 ? 'Yuneec H520' : 'DJI Phantom 4 Pro V2.0');
    let name;
    let status;

    if (i < flyingDroneCount) {
      status = 'flying';
      name = `${flyingDroneBaseName}-${(i + 1).toString().padStart(3, '0')}`;
    } else {
      const statusOptions = ['idle', 'charging', 'maintenance'];
      status = statusOptions[Math.floor(Math.random() * statusOptions.length)];
      const droneType = otherDroneTypes[Math.floor(Math.random() * otherDroneTypes.length)];
      name = `${droneType}-${(i + 1).toString().padStart(3, '0')}`;
    }

    let max_flight_time = 0;
    let max_speed = 0;
    let max_altitude = 0;
    let payload_capacity = 0;

    if (model === 'DJI Mavic 3') {
      max_flight_time = 46;
      max_speed = 19;
      max_altitude = 6000;
      payload_capacity = 2.0;
    } else if (model === 'Yuneec H520') {
      max_flight_time = 28;
      max_speed = 15;
      max_altitude = 4000;
      payload_capacity = 2.5;
    } else if (model === 'DJI Phantom 4 Pro V2.0') {
      max_flight_time = 30;
      max_speed = 20;
      max_altitude = 6000;
      payload_capacity = 1.5;
    }

    mockDrones.push({
      drone_id: id,
      name: name,
      model: model,
      status: status,
      battery_level: Math.floor(Math.random() * 100),
      max_flight_time: max_flight_time,
      max_speed: max_speed,
      max_altitude: max_altitude,
      camera_equipped: Math.random() > 0.2,
      payload_capacity: payload_capacity,
      current_location: {
        type: 'Point',
        coordinates: [114.3 + Math.random() * 0.3, 30.5 + Math.random() * 0.2, 100 + Math.random() * 50]
      },
      firmware_version: `v${Math.floor(Math.random() * 5) + 1}.${Math.floor(Math.random() * 10)}.${Math.floor(Math.random() * 10)}`,
      last_maintenance_date: `2023-${Math.floor(Math.random() * 12) + 1}-${Math.floor(Math.random() * 28) + 1}`,
      next_maintenance_date: `2023-${Math.floor(Math.random() * 12) + 1}-${Math.floor(Math.random() * 28) + 1}`,
      total_flights: Math.floor(Math.random() * 250) + 50,
      total_flight_time: Math.floor(Math.random() * 500) + 100,
      flight_log: generateFlightLogs(6 + Math.floor(Math.random() * 5))
    });
  }

  try {
    localStorage.setItem(LOCAL_STORAGE_KEY, JSON.stringify(mockDrones));
  } catch (e) {
    console.error('Failed to save drones data to localStorage', e);
  }
  return mockDrones;
}

/**
 * Get all drones
 * @returns {Promise<Array<object>>} A list of drones
 */
export function getDrones() {
  return new Promise((resolve, reject) => {
    try {
      const useMockDataDirectly = true; // 始终使用模拟数据
      
      if (!useMockDataDirectly) {
        api.get('/drones')
          .then(response => resolve(response))
          .catch(error => {
            // 如果API失败，则使用localStorage或生成的数据
            resolve(getOrGenerateMockDrones());
          });
      } else {
        resolve(getOrGenerateMockDrones());
      }
    } catch (error) {
      console.error('Error in getDrones:', error);
      reject(error);
    }
  });
}

/**
 * Get a specific drone by ID
 * @param {string} id - The ID of the drone
 * @returns {Promise<object>} The drone data
 */
export function getDroneById(id) {
  return new Promise((resolve, reject) => {
    try {
      const useMockDataDirectly = true; // 始终使用模拟数据

      if (!useMockDataDirectly) {
        api.get(`/drones/${id}`)
          .then(response => resolve(response))
          .catch(error => {
            // API失败时查找本地数据
            const allDrones = getOrGenerateMockDrones();
            const drone = allDrones.find(d => d.drone_id === id);
            if (drone) {
              resolve(drone);
            } else {
              console.error(`Mock drone with id ${id} not found`);
              reject(new Error(`Drone with id ${id} not found`));
            }
          });
      } else {
        const allDrones = getOrGenerateMockDrones();
        const drone = allDrones.find(d => d.drone_id === id);
        if (drone) {
          resolve(drone);
        } else {
          console.error(`Mock drone with id ${id} not found`);
          reject(new Error(`Drone with id ${id} not found`));
        }
      }
    } catch (error) {
      console.error('Error in getDroneById:', error);
      reject(error);
    }
  });
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