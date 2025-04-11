import api from './index'

/**
 * 获取所有任务列表
 * @param {Object} params - 查询参数
 * @returns {Promise} 任务列表
 */
export function getTasks(params = {}) {
  return api.get('/tasks', { params })
}

/**
 * 获取指定任务详情
 * @param {string} id - 任务ID
 * @returns {Promise} 任务详情
 */
export function getTaskById(id) {
  return api.get(`/tasks/${id}`)
}

/**
 * 创建新任务
 * @param {Object} data - 任务信息
 * @returns {Promise} 创建结果
 */
export function createTask(data) {
  return api.post('/tasks', data)
}

/**
 * 更新任务信息
 * @param {string} id - 任务ID
 * @param {Object} data - 更新的信息
 * @returns {Promise} 更新结果
 */
export function updateTask(id, data) {
  return api.put(`/tasks/${id}`, data)
}

/**
 * 删除任务
 * @param {string} id - 任务ID
 * @returns {Promise} 删除结果
 */
export function deleteTask(id) {
  return api.delete(`/tasks/${id}`)
}

/**
 * 取消任务
 * @param {string} id - 任务ID
 * @returns {Promise} 取消结果
 */
export function cancelTask(id) {
  return api.post(`/tasks/${id}/cancel`)
}

/**
 * 获取任务执行状态
 * @param {string} id - 任务ID
 * @returns {Promise} 任务状态
 */
export function getTaskStatus(id) {
  return api.get(`/tasks/${id}/status`)
}

/**
 * 分配任务给无人机或智能体
 * @param {string} id - 任务ID
 * @param {Object} data - 分配信息
 * @param {string[]} data.drone_ids - 无人机ID列表
 * @param {string[]} data.agent_ids - 智能体ID列表
 * @returns {Promise} 分配结果
 */
export function assignTask(id, data) {
  return api.post(`/tasks/${id}/assign`, data)
} 