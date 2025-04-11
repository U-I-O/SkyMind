<template>
  <div class="min-h-screen flex items-center justify-center bg-gray-100">
    <div class="max-w-md w-full p-8 bg-white rounded-lg shadow-lg">
      <div class="text-center mb-8">
        <div class="w-20 h-20 mx-auto mb-4 rounded-lg bg-gradient-to-r from-primary to-secondary flex items-center justify-center text-white text-3xl font-bold">
          SM
        </div>
        <h1 class="text-3xl font-bold text-gray-800">注册 SkyMind 账户</h1>
        <p class="text-gray-600 mt-2">智慧城市低空AI平台</p>
      </div>
      
      <n-form ref="formRef" :model="formValue" :rules="rules">
        <n-form-item path="username" label="用户名">
          <n-input v-model:value="formValue.username" placeholder="请输入用户名" />
        </n-form-item>
        
        <n-form-item path="email" label="电子邮箱">
          <n-input v-model:value="formValue.email" placeholder="请输入电子邮箱" />
        </n-form-item>
        
        <n-form-item path="password" label="密码">
          <n-input
            v-model:value="formValue.password"
            type="password"
            placeholder="请输入密码 (至少6位)"
            show-password-on="click"
          />
        </n-form-item>
        
        <n-form-item path="confirmPassword" label="确认密码">
          <n-input
            v-model:value="formValue.confirmPassword"
            type="password"
            placeholder="请再次输入密码"
            @keydown.enter="handleRegister"
            show-password-on="click"
            :disabled="!formValue.password"
          />
        </n-form-item>
        
        <n-button
          type="primary"
          block
          :loading="loading"
          @click="handleRegister"
          class="mt-4"
        >
          注册
        </n-button>
      </n-form>
      
      <div class="mt-6 text-center">
        <span class="text-gray-600">已有账户？</span>
        <router-link to="/login" class="text-primary hover:text-primary-dark font-medium">点此登录</router-link>
      </div>
    </div>
    
    <!-- Background elements -->
    <div class="fixed inset-0 -z-10 overflow-hidden">
      <div class="absolute -top-40 -right-40 w-96 h-96 bg-primary opacity-10 rounded-full"></div>
      <div class="absolute top-1/4 -left-20 w-60 h-60 bg-secondary opacity-10 rounded-full"></div>
      <div class="absolute -bottom-20 right-1/4 w-80 h-80 bg-warning opacity-10 rounded-full"></div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useMessage } from 'naive-ui'
import { useUserStore } from '../store/userStore' // Assuming userStore has register function

const userStore = useUserStore()
const router = useRouter()
const message = useMessage()

// Form state
const formRef = ref(null)
const formValue = reactive({
  username: '',
  email: '',
  password: '',
  confirmPassword: ''
})

// Loading state
const loading = ref(false)

// Validation rules
const validatePasswordSame = (rule, value) => {
  return value === formValue.password
}

const rules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' }
  ],
  email: [
    { required: true, message: '请输入电子邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入有效的电子邮箱地址', trigger: ['input', 'blur'] }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码长度不能少于6位', trigger: ['input', 'blur'] }
  ],
  confirmPassword: [
    { required: true, message: '请再次输入密码', trigger: ['input', 'blur'] },
    {
      validator: validatePasswordSame,
      message: '两次输入的密码不一致',
      trigger: ['input', 'blur', 'password-input']
    }
  ]
}

// Handle registration
const handleRegister = async () => {
  formRef.value?.validate(async (errors) => {
    if (errors) {
      message.error('请检查表单输入');
      return;
    }
    
    loading.value = true;
    try {
      // Ensure register function exists in userStore
      if (typeof userStore.register !== 'function') {
          throw new Error("Register function not found in user store.");
      }

      const result = await userStore.register({
          username: formValue.username,
          email: formValue.email,
          password: formValue.password
          // Backend might expect full_name etc.
      });

      if (result.success) {
        message.success('注册成功！请登录。');
        router.push('/login');
      } else {
        message.error(result.error || '注册失败，请稍后再试。');
      }
    } catch (error) {
      console.error('Registration error:', error);
      message.error('注册失败: ' + (error.message || '未知错误'));
    } finally {
      loading.value = false;
    }
  });
};
</script> 