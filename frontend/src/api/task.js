import api from './index';
import { useUserStore } from '@/store/userStore';
import router from '@/router';

// 创建巡逻任务
export const createTask = async (taskData) => {
  try {
    // 先检查登录状态
    console.log('登录状态检查结果:', testLoginStatus());
    
    // 记录请求前的状态
    console.log('准备创建巡逻任务, 请求数据:', taskData);
    console.log('请求数据(JSON格式):', JSON.stringify(taskData, null, 2));
    
    // 获取当前token
    const token = localStorage.getItem('auth_token');
    console.log('当前认证状态:', token ? '已登录' : '未登录');
    console.log('认证Token前20字符:', token?.substring(0, 20) + '...');
    if (!token) {
      throw new Error('未登录或token不存在，请先登录');
    }
    // 检查api实例的baseURL配置
    console.log('API baseURL:', api.defaults.baseURL);
    // 请求路径
    const url = '/security/patrol-tasks';
    console.log('请求URL将为:', url);
    
    // 确保数据正确性
    // 1. 确保assigned_drones和schedule字段存在并且格式正确
    const enrichedTaskData = {
      ...taskData,
      // 确保描述字段存在
      description: taskData.description || `巡逻任务 ${new Date().toLocaleString('zh-CN')}`,
      // 确保无人机字段名称正确
      assigned_drones: taskData.assigned_drones || taskData.droneIds || [],
      // 确保调度信息正确
      schedule: taskData.schedule || { type: 'once' },
      // 确保优先级字段
      priority: taskData.priority || 1,
    };
    
    // 检查关键字段是否存在
    if (!enrichedTaskData.patrol_area) {
      throw new Error('缺少巡逻区域数据');
    }
    
    // 再次记录经过处理的请求数据
    // console.log('处理后的请求数据(JSON格式):', JSON.stringify(enrichedTaskData, null, 2));
    
    // 直接发送请求，让请求拦截器添加token
    const axiosConfig = {
      headers: {
        'Content-Type': 'application/json',
        // 显式设置Authorization头
        'Authorization': `Bearer ${token}`
      }
    };
    
    // 发送请求
    const response = await api.post(url, enrichedTaskData, axiosConfig);
    
    console.log('任务创建成功, 响应:', response);
    return response.data || response;
  } catch (error) {
    console.error('创建任务失败:', error);
    console.error('错误详情:', {
      status: error.response?.status,
      statusText: error.response?.statusText,
      data: error.response?.data,
      headers: error.response?.headers,
      config: error.config
    });
    throw error;
  }
};

// 增强 getPatrolTasks 函数
export const getPatrolTasks = async (params = {}) => {
  const maxRetries = 1;
  let retries = 0;
  
  const fetchTasks = async () => {
    try {
      // 在请求前检查登录状态
      if (!testLoginStatus()) {
        // 如果登录状态失效，重新登录
        const userStore = useUserStore();
        await userStore.logout();
        router.push('/login');
        throw new Error('登录状态已失效，请重新登录');
      }
      
      // 显式添加认证头
      const token = localStorage.getItem('auth_token');
      const headers = {
        'Authorization': `Bearer ${token}`
      };
      
      console.log('发送请求到：/security/patrol-tasks');
      const response = await api.get('/security/patrol-tasks', { 
        params,
        headers 
      });
      
      const tasks = Array.isArray(response.data) ? response.data : [];
      console.log(`成功获取${tasks.length}个巡逻任务`);
      return tasks;
    } catch (error) {
      console.error('获取巡逻任务列表失败:', error);
      
      // 如果是认证错误，重定向到登录页
      if (error.response && error.response.status === 401) {
        console.error('认证失败，需要重新登录');
        const userStore = useUserStore();
        await userStore.logout();
        router.push('/login');
        throw new Error('认证失败，请重新登录');
      }
      
      // 重试逻辑
      if (retries < maxRetries) {
        retries++;
        console.log(`正在重试 (${retries}/${maxRetries})...`);
        return fetchTasks();
      }
      
      throw error;
    }
  };
  
  return fetchTasks();
};

// 直接获取所有巡逻任务（surveillance类型）
export const getAllSurveillanceTasks = async () => {
  const maxRetries = 1;
  let retries = 0;
  const fetchTasks = async () => {
    try {
      // 获取认证token
      const token = localStorage.getItem('auth_token');
      if (!token) {
        console.error('未登录状态，无法获取任务列表');
        throw new Error('未登录状态，请先登录');
      }
      
      // 请求配置
      const config = {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      };
  
      // console.info('【API】正在获取所有surveillance类型任务...');
      
      // 发送请求
      const response = await api.get('/security/patrol-tasks', config);
      console.info('【API】请求结果:', response);
      
      // 确保返回数据是数组
      const tasks = Array.isArray(response) ? response : 
      (Array.isArray(response.data) ? response.data : []);
      return tasks;
    } catch (error) {
      console.error('【API】获取任务列表失败:', error);
      
      if (error.response?.status === 401) {
        console.error('【API】认证失败，需要重新登录');
        return [];
      }
      
      // 简单的重试机制
      if (retries < maxRetries) {
        retries++;
        console.info(`【API】正在重试 (${retries}/${maxRetries})...`);
        return fetchTasks();
      }
      
      return [];
    }
  };
  
  return fetchTasks();
};

// 增强 getPatrolTaskById 函数
export const getPatrolTaskById = async (taskId) => {
  if (!taskId) {
    console.error('获取巡逻任务详情失败: 未提供任务ID');
    return null;
  }
  
  try {
    console.log(`正在获取巡逻任务详情: ${taskId}`);
    const response = await api.get(`/security/patrol-tasks/${taskId}`);
    return response.data;
  } catch (error) {
    console.error(`获取巡逻任务${taskId}详情失败:`, error);
    throw error;
  }
};

// 更新巡逻任务
export const updatePatrolTask = async (taskId, taskData) => {
  try {
    // 记录操作
    console.log(`正在更新巡逻任务: ${taskId}`);
    console.log('更新数据:', JSON.stringify(taskData, null, 2));
    
    // 获取当前token
    const token = localStorage.getItem('auth_token');
    if (!token) {
      throw new Error('未登录或token不存在，请先登录');
    }
    
    // 请求配置
    const axiosConfig = {
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      }
    };
    
    // 处理数据，确保所有必要字段都存在
    const updatedTaskData = {
      ...taskData,
      // 确保描述字段存在
      description: taskData.description || `更新于${new Date().toLocaleString('zh-CN')}`,
      // 确保有调度信息
      schedule: taskData.schedule || { type: 'once', weekdays: [], date: null, time: null },
      // 确保优先级存在
      priority: taskData.priority || 1
    };
    
    // 发送请求
    const response = await api.put(`/security/patrol-tasks/${taskId}`, updatedTaskData, axiosConfig);
    
    console.log(`巡逻任务 ${taskId} 已成功更新:`, response.data);
    return response.data || response;
  } catch (error) {
    console.error('更新巡逻任务失败:', error);
    console.error('错误详情:', {
      status: error.response?.status,
      statusText: error.response?.statusText,
      data: error.response?.data,
      headers: error.response?.headers,
      config: error.config
    });
    throw error;
  }
};

// 删除巡逻任务
export const deletePatrolTask = async (taskId) => {
  try {
    // 记录操作
    console.log(`正在删除巡逻任务: ${taskId}`);
    
    // 获取当前token
    const token = localStorage.getItem('auth_token');
    if (!token) {
      throw new Error('未登录或token不存在，请先登录');
    }
    
    // 请求配置
    const axiosConfig = {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    };
    
    // 发送删除请求
    await api.delete(`/security/patrol-tasks/${taskId}`, axiosConfig);
    console.log(`巡逻任务 ${taskId} 已成功删除`);
    return true;
  } catch (error) {
    console.error('删除巡逻任务失败:', error);
    console.error('错误详情:', {
      status: error.response?.status,
      statusText: error.response?.statusText,
      data: error.response?.data,
      headers: error.response?.headers,
      config: error.config
    });
    throw error;
  }
};

// 获取任务列表（原有）
export const getTasks = async (params = {}) => {
  try {
    const response = await api.get('/tasks/', { params });
    return response.data;
  } catch (error) {
    console.error('获取任务列表失败:', error);
    throw error;
  }
};

// 获取任务详情（原有）
export const getTaskById = async (taskId) => {
  try {
    const response = await api.get(`/tasks/${taskId}`);
    return response.data;
  } catch (error) {
    console.error(`获取任务${taskId}详情失败:`, error);
    throw error;
  }
};

// 更新任务（原有）
export const updateTask = async (taskId, taskData) => {
  try {
    const response = await api.put(`/tasks/${taskId}`, taskData);
    return response.data;
  } catch (error) {
    console.error('更新任务失败:', error);
    throw error;
  }
};

// 取消任务
export const cancelTask = async (taskId, reason = {}) => {
  try {
    const response = await api.post(`/tasks/${taskId}/cancel`, reason);
    return response.data;
  } catch (error) {
    console.error('取消任务失败:', error);
    throw error;
  }
};

// 分配无人机到任务
export const assignDroneToTask = async (taskId, droneIds) => {
  try {
    const response = await api.post(`/tasks/${taskId}/assign`, { drone_ids: droneIds });
    return response.data;
  } catch (error) {
    console.error('分配无人机失败:', error);
    throw error;
  }
};

// 测试登录状态
export const testLoginStatus = () => {
  const token = localStorage.getItem('auth_token');
  if (!token) {
    console.error('未登录状态：token不存在');
    return false;
  }
  
  // 解析token
  try {
    const base64Url = token.split('.')[1];
    const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
    const payload = JSON.parse(atob(base64));
    
    // 检查是否过期
    const exp = payload.exp;
    const now = Math.floor(Date.now() / 1000);
    
    console.log('Token信息:', {
      username: payload.sub,
      role: payload.role,
      过期时间: new Date(exp * 1000).toLocaleString(),
      当前时间: new Date(now * 1000).toLocaleString(),
      是否有效: exp > now
    });
    
    return exp > now;
  } catch (e) {
    console.error('Token解析失败:', e);
    return false;
  }
}; 