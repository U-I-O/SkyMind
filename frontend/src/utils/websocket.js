/**
 * Enhanced WebSocket client service
 * Used for real-time communication with the backend
 */

import { ref, reactive, onUnmounted } from 'vue'
import { v4 as uuidv4 } from 'uuid'

// Connection states
export const ConnectionStatus = {
  CONNECTING: 'connecting',
  CONNECTED: 'connected',
  DISCONNECTED: 'disconnected',
  ERROR: 'error'
}

// Message types used throughout the application
export const MessageType = {
  PING: 'ping',
  PONG: 'pong',
  SUBSCRIBE: 'subscribe',
  INITIAL_DATA: 'initial_data',
  DRONE_UPDATE: 'drone_update',
  DRONE_OFFLINE: 'drone_offline',
  TASK_UPDATE: 'task_update',
  EVENT_UPDATE: 'event_update',
  COMMAND_RESPONSE: 'command_response',
  ERROR: 'error'
}

// Client-side generated ID for this session
const clientId = uuidv4()

// WebSocket connection settings
const RECONNECT_DELAY = 3000 // ms
const PING_INTERVAL = 30000  // ms
const MAX_RECONNECT_ATTEMPTS = 5

// WebSocket singleton instance
let socket = null
let reconnectTimeout = null
let pingInterval = null
let reconnectAttempts = 0

// State tracking
const subscriptions = new Map()
const messageHandlers = new Map()
const messageQueue = []

// Reactive state
export const connectionStatus = ref(ConnectionStatus.DISCONNECTED)
export const lastMessage = ref(null)
export const connectionMetrics = reactive({
  latency: 0,
  lastPingSent: null,
  messagesReceived: 0,
  messagesSent: 0,
  errorCount: 0,
  reconnections: 0
})

/**
 * Initialize and manage WebSocket connection
 * @param {string} url - WebSocket service URL
 * @param {string} type - Connection type (user, admin)
 * @returns {Object} WebSocket methods and state
 */
export function useWebSocket(url = `ws://${window.location.host}/ws/${clientId}`, type = 'user') {
  // Initialize connection
  const connect = () => {
    if (socket && (socket.readyState === WebSocket.OPEN || socket.readyState === WebSocket.CONNECTING)) {
      return
    }
    
    try {
      connectionStatus.value = ConnectionStatus.CONNECTING
      
      // Add protocol version and auth data if available
      const token = localStorage.getItem('auth_token')
      const queryParams = new URLSearchParams({
        type,
        version: '1.0',
        ...(token ? { token } : {})
      }).toString()
      
      socket = new WebSocket(`${url}?${queryParams}`)
      
      socket.onopen = handleOpen
      socket.onmessage = handleMessage
      socket.onerror = handleError
      socket.onclose = handleClose
    } catch (error) {
      console.error('WebSocket connection failed:', error)
      connectionStatus.value = ConnectionStatus.ERROR
      connectionMetrics.errorCount++
      scheduleReconnect()
    }
  }
  
  // Handle successful connection
  const handleOpen = () => {
    console.log('WebSocket connected successfully')
    connectionStatus.value = ConnectionStatus.CONNECTED
    reconnectAttempts = 0
    
    // Process any queued messages
    while (messageQueue.length > 0) {
      const queuedMessage = messageQueue.shift()
      send(queuedMessage)
    }
    
    // Resubscribe to previous topics
    subscriptions.forEach((callback, topic) => {
      subscribe(topic, callback)
    })
    
    // Start heartbeat
    startPingInterval()
  }
  
  // Handle incoming messages
  const handleMessage = (event) => {
    try {
      const data = JSON.parse(event.data)
      lastMessage.value = data
      connectionMetrics.messagesReceived++
      
      // Process different message types
      switch (data.type) {
        case MessageType.PONG:
          if (connectionMetrics.lastPingSent) {
            connectionMetrics.latency = Date.now() - new Date(connectionMetrics.lastPingSent).getTime()
          }
          break
          
        case MessageType.INITIAL_DATA:
          if (data.topic && subscriptions.has(data.topic)) {
            const callback = subscriptions.get(data.topic)
            callback(data.data)
          }
          break
          
        default:
          // Process message with registered handlers
          if (data.type && messageHandlers.has(data.type)) {
            messageHandlers.get(data.type).forEach(handler => handler(data))
          }
          break
      }
    } catch (error) {
      console.error('WebSocket message parsing error:', error)
      connectionMetrics.errorCount++
    }
  }
  
  // Handle connection errors
  const handleError = (error) => {
    console.error('WebSocket error:', error)
    connectionStatus.value = ConnectionStatus.ERROR
    connectionMetrics.errorCount++
  }
  
  // Handle connection closure
  const handleClose = (event) => {
    console.log(`WebSocket connection closed: ${event.code} ${event.reason}`)
    connectionStatus.value = ConnectionStatus.DISCONNECTED
    
    // Clear intervals
    if (pingInterval) {
      clearInterval(pingInterval)
      pingInterval = null
    }
    
    // Attempt reconnection if not a clean close (code 1000)
    if (event.code !== 1000) {
      scheduleReconnect()
    }
  }
  
  /**
   * Send data to the WebSocket server
   * @param {Object} data - Data to send
   * @returns {boolean} Success status
   */
  const send = (data) => {
    if (socket && socket.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify(data))
      connectionMetrics.messagesSent++
      return true
    } else if (connectionStatus.value === ConnectionStatus.CONNECTING) {
      // Queue message to send when connection opens
      messageQueue.push(data)
      return true
    }
    return false
  }
  
  /**
   * Subscribe to a specific topic
   * @param {string} topic - Topic to subscribe to
   * @param {Function} callback - Callback for initial data
   * @returns {Function} Unsubscribe function
   */
  const subscribe = (topic, callback) => {
    subscriptions.set(topic, callback)
    
    // Send subscription request if connected
    if (connectionStatus.value === ConnectionStatus.CONNECTED) {
      send({
        type: MessageType.SUBSCRIBE,
        topic
      })
    }
    
    return () => {
      subscriptions.delete(topic)
    }
  }
  
  /**
   * Register a handler for a specific message type
   * @param {string} type - Message type to handle
   * @param {Function} handler - Handler function
   * @returns {Function} Function to remove handler
   */
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
  
  /**
   * Send a command to a drone
   * @param {string} droneId - Target drone ID
   * @param {string} command - Command to execute
   * @param {Object} params - Command parameters
   * @returns {Promise} Command result promise
   */
  const sendDroneCommand = (droneId, command, params = {}) => {
    return new Promise((resolve, reject) => {
      const commandId = uuidv4()
      
      // Create one-time handler for this command response
      const handler = (response) => {
        if (response.commandId === commandId) {
          // Remove the handler once response is received
          const removeHandler = onMessageType(MessageType.COMMAND_RESPONSE, handler)
          removeHandler()
          
          if (response.status === 'success') {
            resolve(response.data)
          } else {
            reject(new Error(response.error || 'Command failed'))
          }
        }
      }
      
      // Register the handler
      onMessageType(MessageType.COMMAND_RESPONSE, handler)
      
      // Send the command
      const success = send({
        type: 'drone_command',
        droneId,
        command,
        params,
        commandId
      })
      
      if (!success) {
        reject(new Error('Failed to send command: not connected'))
      }
      
      // Set timeout for command response
      setTimeout(() => {
        const removeHandler = onMessageType(MessageType.COMMAND_RESPONSE, handler)
        removeHandler()
        reject(new Error('Command timed out'))
      }, 10000) // 10s timeout
    })
  }
  
  // Close and clean up connection
  const disconnect = () => {
    if (socket) {
      socket.close(1000, 'Client disconnected')
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
  
  // Schedule reconnection attempt
  const scheduleReconnect = () => {
    if (reconnectTimeout) {
      clearTimeout(reconnectTimeout)
    }
    
    reconnectAttempts++
    
    if (reconnectAttempts <= MAX_RECONNECT_ATTEMPTS) {
      // Exponential backoff with jitter
      const delay = Math.min(RECONNECT_DELAY * Math.pow(1.5, reconnectAttempts - 1), 30000) 
        + Math.floor(Math.random() * 1000);
      
      console.log(`Scheduling WebSocket reconnection attempt ${reconnectAttempts} in ${delay}ms...`)
      
      reconnectTimeout = setTimeout(() => {
        connectionMetrics.reconnections++
        connect()
      }, delay)
    } else {
      console.error(`Maximum reconnection attempts (${MAX_RECONNECT_ATTEMPTS}) reached`)
      // Could dispatch an app-level event here
    }
  }
  
  // Start heartbeat mechanism
  const startPingInterval = () => {
    if (pingInterval) {
      clearInterval(pingInterval)
    }
    
    pingInterval = setInterval(() => {
      if (socket && socket.readyState === WebSocket.OPEN) {
        connectionMetrics.lastPingSent = new Date().toISOString()
        send({ 
          type: MessageType.PING, 
          timestamp: connectionMetrics.lastPingSent 
        })
      }
    }, PING_INTERVAL)
  }
  
  // Initial connection
  connect()
  
  // Clean up on component unmount
  onUnmounted(() => {
    disconnect()
  })
  
  return {
    // State
    status: connectionStatus,
    lastMessage,
    metrics: connectionMetrics,
    
    // Methods
    connect,
    disconnect,
    send,
    subscribe,
    onMessageType,
    sendDroneCommand
  }
} 