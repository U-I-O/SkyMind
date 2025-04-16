<template>
  <div class="drone-video-container" :class="{ 'loading': isLoading, 'error': hasError }">
    <!-- 视频播放器 -->
    <video 
      v-if="!hasError" 
      ref="videoRef" 
      autoplay 
      muted 
      playsinline 
      class="drone-video-player"
      @loadeddata="handleVideoLoaded"
      @error="handleVideoError"
    ></video>
    
    <!-- 加载状态 -->
    <div v-if="isLoading" class="video-loader">
      <div class="spinner"></div>
      <p class="loading-text">{{ loadingText }}</p>
    </div>
    
    <!-- 错误状态 -->
    <div v-if="hasError" class="video-error">
      <n-icon size="36" class="error-icon"><warning-outlined /></n-icon>
      <p>{{ errorMessage }}</p>
      <n-button size="small" @click="reconnect">重试</n-button>
    </div>
    
    <!-- 未连接状态 -->
    <div v-if="!isConnected && !isLoading && !hasError" class="video-not-connected">
      <n-icon size="36"><video-camera-outlined /></n-icon>
      <p>无人机视频未连接</p>
      <n-button type="primary" size="small" @click="connect">连接</n-button>
    </div>
    
    <!-- 视频控制按钮 -->
    <div v-if="isConnected && !hasError && !isLoading" class="video-controls">
      <n-button-group size="small">
        <n-button @click="toggleFullscreen">
          <template #icon><n-icon><fullscreen-outlined /></n-icon></template>
        </n-button>
        <n-button @click="takeSnapshot">
          <template #icon><n-icon><camera-outlined /></n-icon></template>
        </n-button>
        <n-button @click="disconnect">
          <template #icon><n-icon><disconnect-outlined /></n-icon></template>
        </n-button>
      </n-button-group>
    </div>
    
    <!-- 无人机信息覆盖层 -->
    <div v-if="isConnected && !hasError && showOverlay" class="video-info-overlay">
      <div class="drone-info">
        <div class="drone-name">{{ droneName }}</div>
        <div class="drone-status">{{ statusText }}</div>
      </div>
      <div class="time-info">{{ currentTime }}</div>
      <div class="location-info">
        {{ formatCoordinates(droneLocation) }}
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue';
import { NIcon, NButton, NButtonGroup, useMessage } from 'naive-ui';
import { 
  WarningOutlined, 
  VideoCameraOutlined,
  FullscreenOutlined,
  CameraOutlined,
  DisconnectOutlined
} from '@vicons/antd';

// 组件参数
const props = defineProps({
  droneId: {
    type: String,
    required: true
  },
  droneName: {
    type: String,
    default: '未知无人机'
  },
  status: {
    type: String,
    default: 'idle'
  },
  droneLocation: {
    type: Object,
    default: () => null
  },
  autoConnect: {
    type: Boolean,
    default: false
  },
  showOverlay: {
    type: Boolean,
    default: true
  }
});

// 事件
const emit = defineEmits(['connected', 'disconnected', 'error', 'snapshot']);

// 内部状态
const videoRef = ref(null);
const isConnected = ref(false);
const isLoading = ref(false);
const hasError = ref(false);
const errorMessage = ref('');
const loadingText = ref('正在连接无人机视频流...');
const currentTime = ref('--:--:--');
const statusText = computed(() => {
  const statusMap = {
    'idle': '待命',
    'flying': '飞行中',
    'charging': '充电中',
    'maintenance': '维护中',
    'error': '故障'
  };
  return statusMap[props.status] || props.status;
});

// 消息提示
const message = useMessage();

// 时钟计时器
let clockTimer = null;

// 更新时钟
const updateClock = () => {
  const now = new Date();
  currentTime.value = now.toTimeString().slice(0, 8);
};

// 格式化坐标
const formatCoordinates = (geoPoint) => {
  if (!geoPoint || !geoPoint.coordinates) return '未知位置';
  const [lng, lat, alt] = geoPoint.coordinates;
  return `坐标: ${lat.toFixed(5)}, ${lng.toFixed(5)} | 高度: ${alt || 0}m`;
};

// 连接到视频流
const connect = async () => {
  if (isConnected.value || isLoading.value) return;

  isLoading.value = true;
  hasError.value = false;
  errorMessage.value = '';
  loadingText.value = `连接 ${props.droneName} 视频...`;

  // 构造本地视频文件路径 (假设视频放在 public/videos/ 目录下)
  // Vite 会将 public 目录下的文件视为根目录
  const videoPath = `/videos/${props.droneId}.mp4`;

  try {
    // 添加短暂延迟以模拟网络连接
    await new Promise(resolve => setTimeout(resolve, 500 + Math.random() * 1000));

    if (videoRef.value) {
      // 尝试加载本地视频
      videoRef.value.src = videoPath;
      videoRef.value.load(); // 开始加载视频
      
      // 监听视频是否能播放，处理加载错误
      // 注意: loadeddata 事件在视频元数据加载后触发，但不保证能播放
      // canplay 事件更可靠，但 onerror 已经处理了加载失败的情况
      
      // 视频加载成功后（通过loadeddata事件处理），启动时钟
      // isConnected 状态会在 handleVideoLoaded 中设置
      if (!clockTimer) {
          clockTimer = setInterval(updateClock, 1000);
          updateClock();
      }
      // 注意：isConnected 状态将在 handleVideoLoaded 中设置
      // emit('connected') 也会在 handleVideoLoaded 中触发
    } else {
        throw new Error("视频播放器引用丢失");
    }
  } catch (error) {
    console.error(`加载视频 ${videoPath} 失败:`, error);
    hasError.value = true;
    errorMessage.value = `无法加载 ${props.droneName} 的视频`;
    emit('error', { droneId: props.droneId, error: errorMessage.value });
    isLoading.value = false; // 确保错误时停止加载状态
    if (clockTimer) {
        clearInterval(clockTimer);
        clockTimer = null;
    }
  }
};

// 断开连接
const disconnect = () => {
  if (!isConnected.value) return;
  
  if (videoRef.value) {
    videoRef.value.pause();
    videoRef.value.src = '';
    videoRef.value.load();
  }
  
  if (clockTimer) {
    clearInterval(clockTimer);
    clockTimer = null;
  }
  
  isConnected.value = false;
  emit('disconnected', props.droneId);
  message.success('已断开视频连接');
};

// 重新连接
const reconnect = () => {
  disconnect();
  connect();
};

// 处理视频加载完成
const handleVideoLoaded = () => {
  // 确保视频确实加载了数据
  if (videoRef.value && videoRef.value.readyState >= 2) { // HAVE_CURRENT_DATA or higher
    isLoading.value = false;
    isConnected.value = true;
    hasError.value = false;
    message.success(`${props.droneName} 视频流连接成功`);
    emit('connected', props.droneId);
  } else {
    // 如果视频状态不足，可能只是元数据加载，继续等待或标记错误
    // 这里我们先假设 loadeddata 足够，但实际可能需要更复杂的处理
    console.warn("视频元数据已加载，但可能尚未准备好播放");
    // 可以选择在这里继续显示加载状态，或者等待 canplay 事件
  }
};

// 处理视频错误
const handleVideoError = (event) => {
  console.error('视频播放错误:', event.target.error);
  hasError.value = true;
  isLoading.value = false; // 停止加载状态
  isConnected.value = false;
  errorMessage.value = `无法播放 ${props.droneName} 的视频`;
  emit('error', { droneId: props.droneId, error: errorMessage.value });
  if (clockTimer) {
      clearInterval(clockTimer);
      clockTimer = null;
  }
};

// 切换全屏
const toggleFullscreen = () => {
  const container = videoRef.value.parentElement;
  
  if (!document.fullscreenElement) {
    container.requestFullscreen().catch(err => {
      message.error('无法进入全屏模式: ' + err.message);
    });
  } else {
    document.exitFullscreen();
  }
};

// 截图
const takeSnapshot = () => {
  if (!videoRef.value || !isConnected.value) return;
  
  try {
    const canvas = document.createElement('canvas');
    canvas.width = videoRef.value.videoWidth;
    canvas.height = videoRef.value.videoHeight;
    
    const ctx = canvas.getContext('2d');
    ctx.drawImage(videoRef.value, 0, 0, canvas.width, canvas.height);
    
    // 将图像转换为base64数据URL
    const dataUrl = canvas.toDataURL('image/jpeg');
    
    // 发送截图事件
    emit('snapshot', { 
      droneId: props.droneId, 
      image: dataUrl,
      timestamp: new Date().toISOString()
    });
    
    message.success('截图已保存');
  } catch (error) {
    console.error('截图失败:', error);
    message.error('截图失败');
  }
};

// 生命周期钩子
onMounted(() => {
  if (props.autoConnect) {
    connect();
  }
});

onUnmounted(() => {
  if (clockTimer) {
    clearInterval(clockTimer);
  }
  
  // 确保断开连接
  if (isConnected.value) {
    disconnect();
  }
});

// 监听droneId变化，如果变化则重新连接
watch(() => props.droneId, (newId, oldId) => {
  if (newId !== oldId && isConnected.value) {
    disconnect();
    if (props.autoConnect) {
      connect();
    }
  }
});

// 导出方法
defineExpose({
  connect,
  disconnect,
  reconnect,
  takeSnapshot
});
</script>

<style scoped>
.drone-video-container {
  position: relative;
  width: 100%;
  height: 100%;
  overflow: hidden;
  border-radius: 0.5rem;
  background-color: #1a1a2e;
  display: flex;
  align-items: center;
  justify-content: center;
}

.drone-video-player {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.video-loader,
.video-error,
.video-not-connected {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #fff;
  text-align: center;
  background-color: rgba(26, 26, 46, 0.8);
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid rgba(255, 255, 255, 0.1);
  border-top-color: #3b82f6;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 1rem;
}

.error-icon {
  color: #ef4444;
  margin-bottom: 0.5rem;
}

.loading-text,
.video-error p,
.video-not-connected p {
  margin-bottom: 1rem;
  font-size: 0.875rem;
}

.video-controls {
  position: absolute;
  bottom: 1rem;
  right: 1rem;
  z-index: 10;
  opacity: 0.6;
  transition: opacity 0.3s ease;
}

.video-controls:hover {
  opacity: 1;
}

.video-info-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  color: white;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.8);
}

.drone-info {
  position: absolute;
  top: 1rem;
  left: 1rem;
}

.drone-name {
  font-size: 1rem;
  font-weight: 600;
}

.drone-status {
  font-size: 0.75rem;
  opacity: 0.8;
}

.time-info {
  position: absolute;
  top: 1rem;
  right: 1rem;
  font-family: monospace;
  font-size: 0.875rem;
}

.location-info {
  position: absolute;
  bottom: 1rem;
  left: 1rem;
  font-size: 0.75rem;
  background-color: rgba(0, 0, 0, 0.5);
  padding: 0.25rem 0.5rem;
  border-radius: 0.25rem;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style> 