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
      console.log('开始登录请求...');
      
      // 发送 x-www-form-urlencoded 数据
      const response = await axios.post('/api/auth/login', params, {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded'
        }
      });
      
      const data = response.data;
      console.log('登录成功，获取到token:', data.access_token ? `${data.access_token.substring(0, 20)}...` : 'null');
      
      // 保存token和用户信息
      token.value = data.access_token;
      localStorage.setItem('auth_token', data.access_token);
      console.log('已保存token到localStorage');
      
      // 配置axios默认请求头
      setAuthHeader(data.access_token);
      console.log('已配置axios默认请求头');
      
      // 尝试从token解析用户信息 (如果后端不直接返回user)
      try {
        const decoded = JSON.parse(atob(data.access_token.split('.')[1]));
        user.value = { username: decoded.sub, role: decoded.role }; // 假设token包含sub和role
        localStorage.setItem('user', JSON.stringify(user.value));
        console.log('从token解析用户信息成功:', user.value);
      } catch (e) {
        console.error("Failed to parse token for user info, fetching /me");
        // 如果解析失败，尝试从 /me 获取
        await fetchUser(); 
      }
      
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
      const userResponse = await axios.get('/api/auth/me');
      user.value = userResponse.data;
      localStorage.setItem('user', JSON.stringify(user.value));
      console.log("User info fetched from /me:", user.value)
      return user.value;
    } catch (error) {
      console.error("Failed to fetch user info:", error);
      if (error.response && error.response.status === 401) {
        // Token无效时自动注销
        console.warn("Token无效，执行自动注销");
        logout();
      }
      return null;
    }
  }
  
  function logout() {
    token.value = ''
    user.value = null
    
    localStorage.removeItem('auth_token')
    localStorage.removeItem('user')
    
    // 清除axios请求头
    setAuthHeader('')
    
    // 使用window.location而不是router
    // 这样在任何环境中都能工作，不仅限于组件内部
    try {
      // 仅当在浏览器环境中执行时
      if (typeof window !== 'undefined') {
        // 保存当前URL作为重定向参数
        const currentPath = window.location.pathname + window.location.search
        if (currentPath !== '/login') {
          // window.location.href = `/login?redirect=${encodeURIComponent(currentPath)}`
        }
      }
    } catch (error) {
      console.error('重定向到登录页面失败:', error)
    }
  }
  
  // 设置全局axios认证头
  function setAuthHeader(token) {
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`
    } else {
      delete axios.defaults.headers.common['Authorization']
    }
  }
  
  // 检查是否需要刷新token
  async function checkTokenValidity() {
    if (!token.value) return false;
    
    try {
      // 简单的方法是尝试获取用户信息，如果失败则token无效
      const userInfo = await fetchUser();
      return !!userInfo;
    } catch (error) {
      console.error("Token validity check failed:", error);
      return false;
    }
  }
  
  async function register(userData) {
    // userData should contain username, email, password
    try {
      const response = await axios.post('/api/auth/register', userData);
      
      if (response.status === 201 || response.status === 200) {
         return { success: true };
      } else {
         return { success: false, error: `Unexpected status code: ${response.status}` };
      }
      
    } catch (error) {
      console.error('Registration error:', error);
      let errorMessage = '注册失败，请稍后重试。';
      if (error.response) {
        if (error.response.status === 400) {
          errorMessage = error.response.data?.detail || '用户名或邮箱已存在。';
        } else if (error.response.status === 403) {
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
  
  // 设置请求拦截器，自动处理401错误
  axios.interceptors.response.use(
    response => response,
    error => {
      if (error.response && error.response.status === 401 && token.value) {
        // 如果是401错误且当前有token，说明token过期或无效
        console.warn("收到401响应，Token可能已过期");
        logout();
        
        // 获取router实例，重定向到登录页
        // 注意：这里使用的是直接设置window.location，因为在某些情况下无法访问router实例
        window.location.href = '/login';
      }
      return Promise.reject(error);
    }
  );
  
  // 初始化时尝试获取用户信息和设置认证头
  if (token.value) {
    setAuthHeader(token.value);
    if (!user.value) {
      fetchUser();
    }
  }
  
  return { 
    token, 
    user, 
    isLoggedIn, 
    login, 
    logout, 
    fetchUser,
    checkTokenValidity, 
    register
  }
}) 