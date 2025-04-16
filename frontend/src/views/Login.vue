<template>
  <div class="min-h-screen flex items-center justify-center bg-gray-100">
    <div class="max-w-md w-full p-8 bg-white rounded-lg shadow-lg">
      <!-- 登录表单 -->
      <div class="text-center mb-8">
        <div class="w-20 h-20 mx-auto mb-4 rounded-lg bg-gradient-to-r from-primary to-secondary flex items-center justify-center text-white text-3xl font-bold">
          SM
        </div>
        <h1 class="text-3xl font-bold text-gray-800">SkyMind</h1>
        <p class="text-gray-600 mt-2">智慧城市低空AI平台</p>
      </div>
      
      <n-form ref="formRef" :model="formValue" :rules="rules">
        <n-form-item path="username" label="用户名">
          <n-input v-model:value="formValue.username" placeholder="请输入用户名" />
        </n-form-item>
        
        <n-form-item path="password" label="密码">
          <n-input
            v-model:value="formValue.password"
            type="password"
            placeholder="请输入密码"
            @keydown.enter="handleLogin"
            show-password-on="click"
          />
        </n-form-item>
        
        <div class="flex justify-between items-center mb-6">
          <n-checkbox v-model:checked="rememberMe">记住我</n-checkbox>
          <a href="#" class="text-sm text-primary hover:text-primary-dark">忘记密码?</a>
        </div>
        
        <n-button
          type="primary"
          block
          :loading="loading"
          @click="handleLogin"
        >
          登录
        </n-button>
      </n-form>
      
      <!-- 添加注册链接 -->
      <div class="mt-6 text-center">
        <span class="text-gray-600">还没有账户？</span>
        <router-link to="/register" class="text-primary hover:text-primary-dark font-medium">立即注册</router-link>
      </div>
      
      <!-- 系统提示 -->
      <div class="mt-8 pt-6 border-t border-gray-200 text-center text-sm text-gray-600">
        <p>© 2025 SkyMind 智慧城市低空AI平台</p>
        <p class="mt-1">多智能体协同系统 | YOLO实时检测 | 智能路径规划</p>
      </div>
    </div>
    
    <!-- 背景图形 -->
    <div class="fixed inset-0 -z-10 overflow-hidden">
      <div class="absolute -top-40 -right-40 w-96 h-96 bg-primary opacity-10 rounded-full"></div>
      <div class="absolute top-1/4 -left-20 w-60 h-60 bg-secondary opacity-10 rounded-full"></div>
      <div class="absolute -bottom-20 right-1/4 w-80 h-80 bg-warning opacity-10 rounded-full"></div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useMessage } from 'naive-ui'
import { useUserStore } from '../store/userStore'

const userStore = useUserStore()
const router = useRouter()
const route = useRoute()
const message = useMessage()

// 表单数据
const formRef = ref(null)
const formValue = reactive({
  username: '',
  password: ''
})

// 记住我选项
const rememberMe = ref(false)

// 加载状态
const loading = ref(false)

// 表单验证规则
const rules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' }
  ]
}

// 处理登录
const handleLogin = () => {
  formRef.value?.validate(async (errors) => {
    if (errors) return
    
    loading.value = true
    
    try {
      // 调用userStore的login方法
      const result = await userStore.login(formValue.username, formValue.password)
      
      if (result.success) {
        message.success('登录成功')
        
        // 获取重定向路径
        const redirectPath = route.query.redirect || '/'
        
        // 确保用户信息已加载
        await userStore.fetchUser()
        
        // 跳转到目标页面
        router.push(redirectPath)
      } else {
        // 显示具体的错误信息
        message.error(result.error || '登录失败')
      }
    } catch (error) {
      console.error('Login error:', error)
      message.error('登录失败: ' + (error.message || '未知错误'))
    } finally {
      loading.value = false
    }
  })
}
</script> 