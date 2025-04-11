import api from './index'

/**
 * 获取所有无人机列表
 * @returns {Promise} 无人机列表
 */
export function getDrones() {
  return api.get('/drones')
}

/**
 * 获取指定无人机详情
 * @param {string} id - 无人机ID
 * @returns {Promise} 无人机详情
 */
export function getDroneById(id) {
  return api.get(`/drones/${id}`)
}

/**
 * 创建新无人机
 * @param {Object} data - 无人机信息
 * @returns {Promise} 创建结果
 */
export function createDrone(data) {
  return api.post('/drones', data)
}

/**
 * 更新无人机信息
 * @param {string} id - 无人机ID
 * @param {Object} data - 更新的信息
 * @returns {Promise} 更新结果
 */
export function updateDrone(id, data) {
  return api.put(`/drones/${id}`, data)
}

/**
 * 删除无人机
 * @param {string} id - 无人机ID
 * @returns {Promise} 删除结果
 */
export function deleteDrone(id) {
  return api.delete(`/drones/${id}`)
}

/**
 * 分配任务给无人机
 * @param {string} id - 无人机ID
 * @param {string} taskId - 任务ID
 * @returns {Promise} 分配结果
 */
export function assignTask(id, taskId) {
  return api.post(`/drones/${id}/assign-task`, { task_id: taskId })
}

/**
 * 获取无人机实时状态
 * @param {string} id - 无人机ID
 * @returns {Promise} 无人机状态
 */
export function getDroneStatus(id) {
  return api.get(`/drones/${id}/status`)
}

/**
 * 控制无人机动作
 * @param {string} id - 无人机ID
 * @param {string} action - 动作类型 (takeoff, land, return_home, move_to)
 * @param {Object} params - 动作参数
 * @returns {Promise} 控制结果
 */
export function controlDrone(id, action, params = {}) {
  return api.post(`/drones/${id}/control`, { action, ...params })
} 