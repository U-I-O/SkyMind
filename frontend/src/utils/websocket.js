/**
 * WebSocket客户端服务
 * 用于实时通信，接收无人机状态、事件和任务更新
 */

import { ref, onUnmounted } from 'vue'
import { v4 as uuidv4 } from 'uuid'

// 连接状态
export const ConnectionStatus = {
  CONNECTING: 'connecting',
  CONNECTED: 'connected',
  DISCONNECTED: 'disconnected',
  ERROR: 'error'
}

let socket = null
let reconnectTimeout = null
let pingInterval = null
const RECONNECT_DELAY = 3000 // 重连延迟(毫秒)
const PING_INTERVAL = 30000  // 心跳间隔(毫秒)

const clientId = uuidv4() // 生成客户端唯一ID

// 订阅的主题
const subscriptions = new Map()
const messageHandlers = new Map()

// 状态引用，可在组件中使用
export const connectionStatus = ref(ConnectionStatus.DISCONNECTED)
export const lastMessage = ref(null)

/**
 * 初始化WebSocket连接
 * @param {string} url - WebSocket服务URL，默认为当前域名
 * @param {string} type - 连接类型(user, drone, admin等)
 * @returns {Object} WebSocket状态和方法
 */
export function useWebSocket(url = `ws://${window.location.host}/ws/${clientId}`, type = 'user') {
  // 初始化连接
  const connect = () => {
    if (socket && (socket.readyState === WebSocket.OPEN || socket.readyState === WebSocket.CONNECTING)) {
      return
    }
    
    try {
      connectionStatus.value = ConnectionStatus.CONNECTING
      socket = new WebSocket(`${url}?type=${type}`)
      
      socket.onopen = handleOpen
      socket.onmessage = handleMessage
      socket.onerror = handleError
      socket.onclose = handleClose
    } catch (error) {
      console.error('WebSocket连接失败:', error)
      connectionStatus.value = ConnectionStatus.ERROR
      scheduleReconnect()
    }
  }
  
  // 处理连接成功
  const handleOpen = () => {
    console.log('WebSocket连接成功')
    connectionStatus.value = ConnectionStatus.CONNECTED
    
    // 重新订阅之前的主题
    subscriptions.forEach((callback, topic) => {
      subscribe(topic, callback)
    })
    
    // 开始定时发送心跳
    startPingInterval()
  }
  
  // 处理接收到的消息
  const handleMessage = (event) => {
    try {
      const data = JSON.parse(event.data)
      lastMessage.value = data
      
      // 处理心跳响应
      if (data.type === 'pong') {
        return
      }
      
      // 处理初始数据
      if (data.type === 'initial_data' && data.topic && subscriptions.has(data.topic)) {
        const callback = subscriptions.get(data.topic)
        callback(data.data)
        return
      }
      
      // 处理特定类型消息
      if (data.type && messageHandlers.has(data.type)) {
        messageHandlers.get(data.type).forEach(handler => handler(data))
      }
    } catch (error) {
      console.error('WebSocket消息解析错误:', error)
    }
  }
  
  // 处理错误
  const handleError = (error) => {
    console.error('WebSocket错误:', error)
    connectionStatus.value = ConnectionStatus.ERROR
  }
  
  // 处理连接关闭
  const handleClose = () => {
    console.log('WebSocket连接关闭')
    connectionStatus.value = ConnectionStatus.DISCONNECTED
    clearInterval(pingInterval)
    scheduleReconnect()
  }
  
  // 发送消息
  const send = (data) => {
    if (socket && socket.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify(data))
      return true
    }
    return false
  }
  
  // 订阅主题
  const subscribe = (topic, callback) => {
    subscriptions.set(topic, callback)
    
    // 如果已连接，发送订阅请求
    if (connectionStatus.value === ConnectionStatus.CONNECTED) {
      send({
        type: 'subscribe',
        topic
      })
    }
    
    return () => {
      subscriptions.delete(topic)
    }
  }
  
  // 注册消息处理器
  const onMessageType = (type, handler) => {
    if (!messageHandlers.has(type)) {
      messageHandlers.set(type, new Set())
    }
    messageHandlers.get(type).add(handler)
    
    return () => {
      const handlers = messageHandlers.get(type)
      if (handlers) {
        handlers.delete(handler)
        if (handlers.size === 0) {
          messageHandlers.delete(type)
        }
      }
    }
  }
  
  // 关闭连接
  const disconnect = () => {
    if (socket) {
      socket.close()
      socket = null
    }
    
    if (reconnectTimeout) {
      clearTimeout(reconnectTimeout)
      reconnectTimeout = null
    }
    
    if (pingInterval) {
      clearInterval(pingInterval)
      pingInterval = null
    }
    
    connectionStatus.value = ConnectionStatus.DISCONNECTED
  }
  
  // 安排重连
  const scheduleReconnect = () => {
    if (reconnectTimeout) {
      clearTimeout(reconnectTimeout)
    }
    
    reconnectTimeout = setTimeout(() => {
      console.log('尝试重新连接WebSocket...')
      connect()
    }, RECONNECT_DELAY)
  }
  
  // 开始心跳定时器
  const startPingInterval = () => {
    if (pingInterval) {
      clearInterval(pingInterval)
    }
    
    pingInterval = setInterval(() => {
      if (socket && socket.readyState === WebSocket.OPEN) {
        send({ type: 'ping', timestamp: new Date().toISOString() })
      }
    }, PING_INTERVAL)
  }
  
  // 初始连接
  connect()
  
  // 组件卸载时清理
  onUnmounted(() => {
    disconnect()
  })
  
  return {
    status: connectionStatus,
    lastMessage,
    connect,
    disconnect,
    send,
    subscribe,
    onMessageType
  }
} 