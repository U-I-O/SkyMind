import axios from 'axios'
import { useNotification } from 'naive-ui'

// Create axios instance with base configuration
const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
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
    // Get token from localStorage
    const token = localStorage.getItem('auth_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    
    // Ensure trailing slashes for API endpoints (except those with file extensions or query parameters)
    if (config.url && !config.url.includes('.') && !config.url.includes('?') && !config.url.endsWith('/')) {
      config.url = `${config.url}/`
    }
    
    return config
  },
  error => {
    console.error('Request error:', error)
    return Promise.reject(error)
  }
)

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
      // Check if the token exists but is invalid/expired
      const token = localStorage.getItem('auth_token')
      
      // Only redirect if we have a token (means it's expired) and not already at login page
      if (token && !window.location.pathname.includes('/login')) {
        // Store the current path to redirect back after login
        localStorage.setItem('redirect_after_login', window.location.pathname)
        // Clear invalid token
        localStorage.removeItem('auth_token')
        localStorage.removeItem('user')
        
        // Use router for navigation if available to prevent page reload
        if (window.router) {
          window.router.push('/login')
        } else {
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