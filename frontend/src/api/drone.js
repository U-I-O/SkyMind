import api from './index'

/**
 * Get all drones
 * @returns {Promise<Array<object>>} A list of drones
 */
export function getDrones() {
  return new Promise((resolve, reject) => {
    try {
      // 在开发环境中直接使用模拟数据，避免401错误
      const useMockDataDirectly = true; // 设置为 true 跳过API调用，直接使用模拟数据
      
      if (!useMockDataDirectly) {
        // First try to get from API
        api.get('/drones')
          .then(response => resolve(response))
          .catch(error => generateMockDrones());
      } else {
        // 跳过API调用，直接使用模拟数据
        generateMockDrones();
      }
      
      function generateMockDrones() {
        console.warn('Using mock drones data for development');
        
        // Generate mock data for development
        const mockDrones = [];
        const droneCount = 14; // 固定为14架无人机
        const flyingDroneCount = 3; // 固定飞行中的无人机数量
        const flyingDroneBaseName = '雄鹰';
        const otherDroneTypes = ['天行', '天空', '神鹰', '飞马'];
        
        for (let i = 0; i < droneCount; i++) {
          const id = `drone-${i}`;
          const model = Math.random() > 0.6 ? 'DJI Mavic 3' : (Math.random() > 0.5 ? 'Yuneec H520' : 'DJI Phantom 4 Pro V2.0');
          
          let name;
          let status;

          if (i < flyingDroneCount) {
            // 固定飞行中的无人机
            status = 'flying';
            name = `${flyingDroneBaseName}-${(i + 1).toString().padStart(3, '0')}`;
          } else {
            // 其他状态的无人机
            const statusOptions = ['idle', 'charging', 'maintenance'];
            status = statusOptions[Math.floor(Math.random() * statusOptions.length)];
            // 使用不同的名称模式
            const droneType = otherDroneTypes[Math.floor(Math.random() * otherDroneTypes.length)];
            name = `${droneType}-${(i + 1).toString().padStart(3, '0')}`;
          }
          
          // 根据型号设置不同的性能参数
          let max_flight_time = 0;
          let max_speed = 0;
          let max_altitude = 0;
          
          if (model === 'DJI Mavic 3') {
            max_flight_time = 46; // 46分钟飞行时间
            max_speed = 19;      // 19 m/s
            max_altitude = 6000;  // 6000米最大高度
          } else if (model === 'Yuneec H520') {
            max_flight_time = 28; // 28分钟飞行时间
            max_speed = 15;      // 15 m/s
            max_altitude = 4000;  // 4000米最大高度
          } else if (model === 'DJI Phantom 4 Pro V2.0') {
            max_flight_time = 30; // 30分钟飞行时间
            max_speed = 20;      // 20 m/s
            max_altitude = 6000;  // 6000米最大高度
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
            camera_equipped: true,
            payload_capacity: model === 'DJI Mavic 3' ? 2.0 : (model === 'Yuneec H520' ? 2.5 : 1.5),
            current_location: {
              type: 'Point',
              coordinates: [114.3 + Math.random() * 0.3, 30.5 + Math.random() * 0.2, 100 + Math.random() * 50]
            },
            // 额外的详细信息字段
            last_maintenance_date: `2023-${Math.floor(Math.random() * 12) + 1}-${Math.floor(Math.random() * 28) + 1}`,
            next_maintenance_date: `2023-${Math.floor(Math.random() * 12) + 1}-${Math.floor(Math.random() * 28) + 1}`,
            total_flights: Math.floor(Math.random() * 250) + 50,
            total_flight_time: Math.floor(Math.random() * 500) + 100
          });
        }
        
        resolve(mockDrones);
      }
    } catch (error) {
      reject(error);
    }
  });
}

/**
 * Get a specific drone by ID
 * @param {string} id - The ID of the drone
 * @returns {Promise<object>} The drone data
 */
// 在文件顶部添加一个缓存对象
const droneDetailsCache = {};

export function getDroneById(id, baseData = null) {
  return new Promise((resolve, reject) => {
    try {
      // 如果缓存中已有该无人机的详情数据，直接返回
      if (droneDetailsCache[id]) {
        console.log(`Using cached data for drone ${id}`);
        resolve(droneDetailsCache[id]);
        return;
      }

      // 在开发环境中直接使用模拟数据，避免401错误
      const useMockDataDirectly = true; // 设置为 true 跳过API调用，直接使用模拟数据
      
      if (!useMockDataDirectly) {
        // 首先尝试从API获取数据
        api.get(`/drones/${id}`)
          .then(response => {
            // 缓存API返回的数据
            droneDetailsCache[id] = response;
            resolve(response);
          })
          .catch(error => generateMockDrone());
      } else {
        // 跳过API调用，直接使用模拟数据
        generateMockDrone();
      }
      
      function generateMockDrone() {
        console.warn(`Generating mock data for drone ${id}`);
        
        // 固定飞行中的无人机 ID 和名称
        const flyingDroneCount = 3;
        const flyingDroneBaseName = '雄鹰';
        const flyingDroneIds = Array.from({ length: flyingDroneCount }, (_, i) => `drone-${i}`);

        // 如果传入了基础数据，优先使用
        let name = baseData?.name;
        let status = baseData?.status;
        let model = baseData?.model;
        let battery_level = baseData?.battery_level;
        let max_flight_time = baseData?.max_flight_time || 0;
        let max_speed = baseData?.max_speed || 0;
        let max_altitude = baseData?.max_altitude || 0;
        let payload_capacity = baseData?.payload_capacity || 0;
        let camera_equipped = baseData?.camera_equipped;
        
        // 如果没有传入基础数据，则按照原来的逻辑生成
        if (!baseData) {
          const droneIndex = parseInt(id.split('-')[1]); // 从 id (e.g., 'drone-5') 中提取索引

          // Generate a random model
          model = Math.random() > 0.6 ? 'DJI Mavic 3' : (Math.random() > 0.5 ? 'Yuneec H520' : 'DJI Phantom 4 Pro V2.0');

          if (flyingDroneIds.includes(id)) {
            // 如果是预设的飞行中无人机
            status = 'flying';
            name = `${flyingDroneBaseName}-${(droneIndex + 1).toString().padStart(3, '0')}`;
          } else {
            // 其他无人机
            const statusOptions = ['idle', 'charging', 'maintenance'];
            status = statusOptions[Math.floor(Math.random() * statusOptions.length)];
            // 确保名称与其他无人机一致 (如果需要)
            const otherDroneTypes = ['天行', '天空', '神鹰', '飞马'];
            const droneType = otherDroneTypes[Math.floor(Math.random() * otherDroneTypes.length)];
            name = `${droneType}-${(droneIndex + 1).toString().padStart(3, '0')}`;
          }

          // 根据型号设置不同的性能参数
          if (model === 'DJI Mavic 3') {
            max_flight_time = 46; // 46分钟飞行时间
            max_speed = 19;      // 19 m/s
            max_altitude = 6000;  // 6000米最大高度
            payload_capacity = 2.0; // 2.0kg
          } else if (model === 'Yuneec H520') {
            max_flight_time = 28; // 28分钟飞行时间
            max_speed = 15;      // 15 m/s
            max_altitude = 4000;  // 4000米最大高度
            payload_capacity = 2.5; // 2.5kg
          } else if (model === 'DJI Phantom 4 Pro V2.0') {
            max_flight_time = 30; // 30分钟飞行时间
            max_speed = 20;      // 20 m/s
            max_altitude = 6000;  // 6000米最大高度
            payload_capacity = 1.5; // 1.5kg
          }
          
          battery_level = Math.floor(Math.random() * 100);
          camera_equipped = Math.random() > 0.2;
        }
        
        // Create detailed mock data
        const mockDrone = {
          drone_id: id,
          name: name,
          model: model,
          status: status,
          battery_level: battery_level,
          max_flight_time: max_flight_time,
          max_speed: max_speed,
          max_altitude: max_altitude,
          camera_equipped: camera_equipped,
          payload_capacity: payload_capacity,
          current_location: baseData?.current_location || {
            type: 'Point',
            coordinates: [114.3 + Math.random() * 0.3, 30.5 + Math.random() * 0.2, 100 + Math.random() * 50]
          },
          firmware_version: baseData?.firmware_version || `v${Math.floor(Math.random() * 5) + 1}.${Math.floor(Math.random() * 10)}.${Math.floor(Math.random() * 10)}`,
          last_maintenance_date: baseData?.last_maintenance_date || `2023-${Math.floor(Math.random() * 12) + 1}-${Math.floor(Math.random() * 28) + 1}`,
          next_maintenance_date: baseData?.next_maintenance_date || `2023-${Math.floor(Math.random() * 12) + 1}-${Math.floor(Math.random() * 28) + 1}`,
          total_flights: baseData?.total_flights || Math.floor(Math.random() * 250) + 50,
          total_flight_time: baseData?.total_flight_time || Math.floor(Math.random() * 500) + 100,
          flight_log: generateFlightLogs(6 + Math.floor(Math.random() * 5)) // 6-10条飞行记录
        };
        
        // 生成模拟飞行记录
        function generateFlightLogs(count) {
          const logs = [];
          
          // 生成过去30天内的随机日期
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
          
          // 飞行任务类型
          const missionTypes = ['常规巡逻', '区域勘测', '安全监控', '紧急响应', '设备运输', '自动导航测试'];
          
          // 生成指定数量的飞行记录
          for (let i = 0; i < count; i++) {
            const duration = Math.floor(Math.random() * 50) + 10; // 10-60分钟
            const maxAltitude = Math.floor(Math.random() * 300) + 100; // 100-400米
            const distance = Math.floor(Math.random() * 15000) + 1000; // 1-16公里
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
              battery_consumption: Math.floor(Math.random() * 80) + 10, // 10-90%
              avg_speed: Math.floor(Math.random() * 10) + 5 // 5-15 m/s
            });
          }
          
          // 按日期排序，最新的在前面
          logs.sort((a, b) => new Date(b.date) - new Date(a.date));
          
          return logs;
        }
        
        // 将生成的模拟数据存入缓存
        droneDetailsCache[id] = mockDrone;
        resolve(mockDrone);
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