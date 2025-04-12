import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const systemApi = {
  /**
   * 获取系统资源状态
   * @returns {Promise} 包含系统资源状态的Promise
   */
  getSystemStatus() {
    return axios.get(`${API_URL}/api/v1/system/status`);
  },
  
  /**
   * 获取智能体状态列表
   * @returns {Promise} 包含智能体状态的Promise
   */
  getAgentsStatus() {
    return axios.get(`${API_URL}/api/v1/system/agents`);
  },
  
  /**
   * 获取资源历史使用数据
   * @param {string} resourceType - 资源类型：cpu, memory, disk, network
   * @param {number} hours - 查询过去多少小时的数据
   * @returns {Promise} 包含资源历史数据的Promise
   */
  getResourceHistory(resourceType, hours = 24) {
    return axios.get(`${API_URL}/api/v1/system/history/${resourceType}`, {
      params: { hours }
    });
  }
};