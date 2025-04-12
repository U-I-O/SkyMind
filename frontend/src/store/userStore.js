import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import axios from 'axios'
import { useRouter } from 'vue-router'

export const useUserStore = defineStore('user', () => {
  // 状态
  const token = ref(localStorage.getItem('auth_token') || '')
  const user = ref(JSON.parse(localStorage.getItem('user') || 'null'))
  
  // 计算属性
  const isLoggedIn = computed(() => !!token.value)
  
  // 动作
  async function login(username, password) {
    // 准备表单数据
    const params = new URLSearchParams();
    params.append('username', username);
    params.append('password', password);

    try {
      // 发送 x-www-form-urlencoded 数据
      const response = await axios.post('/api/auth/login', params, {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded'
        }
      });
      
      const data = response.data
      
      // 保存token和用户信息
      token.value = data.access_token
      // 尝试从token解析用户信息 (如果后端不直接返回user)
      try {
        const decoded = JSON.parse(atob(data.access_token.split('.')[1]));
        user.value = { username: decoded.sub, role: decoded.role }; // 假设token包含sub和role
        localStorage.setItem('user', JSON.stringify(user.value));
      } catch (e) {
        console.error("Failed to parse token for user info, fetching /me");
        // 如果解析失败，尝试从 /me 获取
        await fetchUser(); 
      }
      
      localStorage.setItem('auth_token', data.access_token)
      
      // 配置axios默认请求头
      setAuthHeader(data.access_token)
      
      return { success: true }
    } catch (error) {
      console.error('Login error:', error);
      let errorMessage = '登录失败，请稍后重试。'; // 默认错误消息
      if (error.response) {
        // 处理后端返回的错误
        if (error.response.status === 401) {
          errorMessage = error.response.data?.detail || '用户名或密码错误';
        } else if (error.response.status === 422) {
          // 422 错误通常是验证问题，对登录来说还是凭证错误
          errorMessage = '用户名或密码格式错误';
        } else if (error.response.data?.detail) {
          // 尝试获取后端的detail，确保是字符串
          errorMessage = typeof error.response.data.detail === 'string' 
                           ? error.response.data.detail 
                           : JSON.stringify(error.response.data.detail); 
        }
      } else if (error.request) {
        // 请求已发出但没有收到响应 (网络错误, 后端未运行等)
        errorMessage = '无法连接到服务器，请检查网络或稍后再试。';
      } else {
        // 设置请求时发生了一些事情
        errorMessage = error.message;
      }
      return { 
        success: false, 
        error: errorMessage // 确保返回字符串
      }
    }
  }
  
  async function fetchUser() {
    if (!token.value) return;
    try {
      setAuthHeader(token.value); // 确保请求头已设置
      const response = await axios.get('/api/auth/me');
      user.value = response.data;
      localStorage.setItem('user', JSON.stringify(user.value));
      console.log("User info fetched from /me:", user.value)
    } catch (error) {
      console.error("Failed to fetch user info:", error);
      // 如果获取/me失败，可能token无效，执行登出
      logout();
    }
  }
  
  function logout() {
    token.value = ''
    user.value = null
    
    localStorage.removeItem('auth_token')
    localStorage.removeItem('user')
    
    // 清除axios请求头
    setAuthHeader('')
  }
  
  function setAuthHeader(token) {
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`
    } else {
      delete axios.defaults.headers.common['Authorization']
    }
  }
  
  async function register(userData) {
    // userData should contain username, email, password
    // The backend requires admin privileges to register, so this might need adjustment
    // For now, we'll assume the endpoint allows public registration or we're logged in as admin
    try {
      // Assuming the backend endpoint is /api/v1/auth/register
      const response = await axios.post('/api/auth/register', userData, {
        // We might need the admin token if the endpoint is protected
        // headers: { 'Authorization': `Bearer ${token.value}` } 
      });
      
      // Check if backend returns success indication
      // FastAPI usually returns 201 Created on success for POST
      if (response.status === 201 || response.status === 200) {
         return { success: true };
      } else {
         // Handle unexpected success status codes if necessary
         return { success: false, error: `Unexpected status code: ${response.status}` };
      }
      
    } catch (error) {
      console.error('Registration error:', error);
      let errorMessage = '注册失败，请稍后重试。';
      if (error.response) {
        if (error.response.status === 400) { // Bad Request (e.g., user exists)
          errorMessage = error.response.data?.detail || '用户名或邮箱已存在。';
        } else if (error.response.status === 403) { // Forbidden
          errorMessage = error.response.data?.detail || '权限不足，无法注册新用户。';
        } else if (error.response.data?.detail) {
          errorMessage = typeof error.response.data.detail === 'string' 
                           ? error.response.data.detail 
                           : JSON.stringify(error.response.data.detail);
        }
      } else if (error.request) {
        errorMessage = '无法连接到服务器，请检查网络或稍后再试。';
      } else {
        errorMessage = error.message;
      }
      return { 
        success: false, 
        error: errorMessage 
      };
    }
  }
  
  // 初始化时尝试获取用户信息
  if (isLoggedIn.value && !user.value) {
    fetchUser();
  } else if (token.value) {
    setAuthHeader(token.value);
  }
  
  // Helper function to set header on the specific api instance
  function setApiAuthHeader(token) {
    // We need to import the api instance or handle this differently
    // For now, let's assume api/index.js handles this via interceptors
    // If direct calls to api instance need header updates, this needs adjustment
    // Example (if api instance was available here):
    // import api from '@/api';
    // if (token) {
    //   api.defaults.headers.common['Authorization'] = `Bearer ${token}`;
    // } else {
    //   delete api.defaults.headers.common['Authorization'];
    // }
  }
  
  return { 
    token, 
    user, 
    isLoggedIn, 
    login, 
    logout, 
    fetchUser, 
    register // 导出 register 函数
  }
}) 