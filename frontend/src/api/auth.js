import api from './index'

/**
 * 用户登录
 * @param {Object} data - 登录信息
 * @param {string} data.username - 用户名
 * @param {string} data.password - 密码
 * @returns {Promise} 登录结果
 */
export function login(data) {
  return api.post('/auth/login', data)
}

/**
 * 用户注册
 * @param {Object} data - 注册信息
 * @param {string} data.username - 用户名
 * @param {string} data.email - 邮箱
 * @param {string} data.password - 密码
 * @param {string} data.full_name - 姓名
 * @returns {Promise} 注册结果
 */
export function register(data) {
  return api.post('/auth/register', data)
}

/**
 * 获取当前用户信息
 * @returns {Promise} 用户信息
 */
export function getUserInfo() {
  return api.get('/auth/me')
}

/**
 * 修改密码
 * @param {Object} data - 密码信息
 * @param {string} data.old_password - 旧密码
 * @param {string} data.new_password - 新密码
 * @returns {Promise} 修改结果
 */
export function changePassword(data) {
  return api.post('/auth/change-password', data)
}

/**
 * 登出
 * @returns {Promise} 登出结果
 */
export function logout() {
  return api.post('/auth/logout')
} 