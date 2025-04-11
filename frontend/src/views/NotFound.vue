<template>
  <div class="min-h-screen flex flex-col items-center justify-center text-center p-4">
    <div class="mb-8">
      <div class="text-9xl font-bold text-primary">404</div>
      <div class="text-2xl font-bold text-gray-700 mt-4">页面未找到</div>
      <div class="text-gray-500 mt-2">您请求的页面不存在或已被移除</div>
    </div>
    
    <div class="max-w-md mx-auto">
      <n-image
        src="/images/drone-lost.svg"
        alt="Lost Drone"
        preview-disabled
        class="max-w-xs mx-auto"
      />
    </div>
    
    <div class="mt-8">
      <n-button type="primary" size="large" @click="goHome">
        返回首页
      </n-button>
    </div>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'

const router = useRouter()

function goHome() {
  router.push('/')
}
</script> 