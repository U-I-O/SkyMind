import api from './index'

/**
 * 获取所有事件列表
 * @param {Object} params - 查询参数
 * @returns {Promise} 事件列表
 */
export function getEvents(params = {}) {
  return api.get('/events', { params })
}

/**
 * 获取指定事件详情
 * @param {string} id - 事件ID
 * @returns {Promise} 事件详情
 */
export function getEventById(id) {
  return api.get(`/events/${id}`)
}

/**
 * 创建新事件
 * @param {Object} data - 事件信息
 * @returns {Promise} 创建结果
 */
export function createEvent(data) {
  return api.post('/events', data)
}

/**
 * 更新事件信息
 * @param {string} id - 事件ID
 * @param {Object} data - 更新的信息
 * @returns {Promise} 更新结果
 */
export function updateEvent(id, data) {
  return api.put(`/events/${id}`, data)
}

/**
 * 删除事件
 * @param {string} id - 事件ID
 * @returns {Promise} 删除结果
 */
export function deleteEvent(id) {
  return api.delete(`/events/${id}`)
}

/**
 * 标记事件为已处理
 * @param {string} id - 事件ID
 * @param {Object} data - 处理信息
 * @param {string} data.resolution_notes - 处理说明
 * @returns {Promise} 处理结果
 */
export function resolveEvent(id, data) {
  return api.post(`/events/${id}/resolve`, data)
}

/**
 * 获取事件相关的任务
 * @param {string} id - 事件ID
 * @returns {Promise} 相关任务列表
 */
export function getEventTasks(id) {
  return api.get(`/events/${id}/tasks`)
}

/**
 * 获取事件图像证据
 * @param {string} id - 事件ID
 * @returns {Promise} 图像证据列表
 */
export function getEventImages(id) {
  return api.get(`/events/${id}/images`)
}

/**
 * 为事件创建应急响应任务
 * @param {string} id - 事件ID
 * @param {Object} data - 任务信息
 * @returns {Promise} 创建结果
 */
export function createEmergencyTask(id, data) {
  return api.post(`/events/${id}/emergency-task`, data)
} 