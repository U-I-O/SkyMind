import axios from 'axios'
import { useNotification } from 'naive-ui'
import { useUserStore } from '@/store/userStore'

// Create axios instance with base configuration
const api = axios.create({
  // 添加前导斜杠，确保URL正确
  baseURL: '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// Global notification instance (will be set by init function)
let notification = null

/**
 * Initialize the API module with notification provider
 * Call this from a component with access to the Naive UI context
 */
export function initApi() {
  try {
    // This will only work when called from a component using useNotification()
    notification = useNotification()
  } catch (error) {
    console.warn('Notification provider not available. API error notifications disabled.')
  }
}

// Request interceptor
api.interceptors.request.use(
  config => {
    // 使用userStore中的token
    try {
      const userStore = useUserStore()
      // 记录当前token
      // console.log('拦截器检查token:', userStore.token ? `${userStore.token.substring(0, 20)}...` : 'null');
      
      // 首先检查请求配置中是否已经有Authorization头
      if (config.headers && config.headers['Authorization']) {
        // console.log('请求已包含Authorization头，不再添加');
        return config;
      }
      
      if (userStore.token) {
        config.headers = config.headers || {};
        config.headers.Authorization = `Bearer ${userStore.token}`;
        // console.log('拦截器添加认证头:', `Bearer ${userStore.token.substring(0, 20)}...`);
      } else {
        // 尝试从localStorage直接获取
        const localToken = localStorage.getItem('auth_token');
        if (localToken) {
          config.headers = config.headers || {};
          config.headers.Authorization = `Bearer ${localToken}`;
          // console.log('拦截器从localStorage添加认证头:', `Bearer ${localToken.substring(0, 20)}...`);
        } else {
          console.warn('无法获取认证token');
        }
      }
    } catch (error) {
      console.error('设置认证头时出错:', error);
      
      // 回退方案：直接从localStorage获取
      const token = localStorage.getItem('auth_token');
      if (token) {
        config.headers = config.headers || {};
        config.headers.Authorization = `Bearer ${token}`;
        // console.log('拦截器回退方案添加认证头:', `Bearer ${token.substring(0, 20)}...`);
      }
    }
    
    // 记录完整请求信息
    console.log(`发送请求: ${config.method?.toUpperCase() || 'GET'} ${config.baseURL || ''}${config.url || ''}`);
    console.log('请求头:', JSON.stringify(config.headers || {}));
    
    // Ensure trailing slashes for API endpoints (except those with file extensions or query parameters)
    if (config.url && !config.url.includes('.') && !config.url.includes('?') && !config.url.endsWith('/')) {
      config.url = `${config.url}/`;
    }
    
    return config;
  },
  error => {
    console.error('Request error:', error);
    return Promise.reject(error);
  }
);

// Response interceptor
api.interceptors.response.use(
  response => {
    // Some APIs might return { data: ... } structure while others return direct data
    // This normalizes the response
    return response.data
  },
  error => {
    // Handle error responses
    const errorMessage = error.response?.data?.detail || error.message || 'Unknown error'
    const statusCode = error.response?.status

    console.error(`API Error (${statusCode}):`, errorMessage)
    
    // Show error notification if notification provider is available
    if (notification) {
      notification.error({
        title: `Error ${statusCode || ''}`,
        content: errorMessage,
        duration: 5000
      })
    }

    // Handle authentication errors
    if (statusCode === 401) {
      try {
        // 检查token是否存在，避免重复处理
        const token = localStorage.getItem('auth_token')
        if (token) {
          // 安全地获取userStore
          const userStore = useUserStore()
          if (userStore) {
            // 将错误信息记录到控制台
            console.log('收到401响应，执行自动登出')
            // 调用userStore的logout方法
            userStore.logout()
          } else {
            // 如果无法获取store，直接清除token并跳转
            localStorage.removeItem('auth_token')
            localStorage.removeItem('user')
            // 仅当在浏览器环境中执行时
            if (typeof window !== 'undefined' && window.location.pathname !== '/login') {
              window.location.href = '/login'
            }
          }
        }
      } catch (e) {
        console.error('处理401错误时出现异常:', e)
        // 最简单的回退策略：直接跳转到登录页
        if (typeof window !== 'undefined' && window.location.pathname !== '/login') {
          window.location.href = '/login'
        }
      }
    }
    
    return Promise.reject(error)
  }
)

// Helper for simpler implementation of common API methods
export const apiService = {
  get: (url, params = {}) => api.get(url, { params }),
  post: (url, data = {}) => api.post(url, data),
  put: (url, data = {}) => api.put(url, data),
  delete: (url) => api.delete(url),
  
  // Upload file with progress tracking
  upload: (url, file, onProgress) => {
    const formData = new FormData()
    formData.append('file', file)
    
    return api.post(url, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      },
      onUploadProgress: progressEvent => {
        if (onProgress) {
          const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total)
          onProgress(percentCompleted)
        }
      }
    })
  }
}

export default api 