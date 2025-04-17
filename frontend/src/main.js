import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import { createPinia } from 'pinia'
import naive from 'naive-ui'

// 导入全局样式
import './assets/css/main.css'
// 导入全局暗色主题样式
import './assets/css/darkTheme.css'

// Make router available globally for the API interceptor
window.router = router

const app = createApp(App)
const pinia = createPinia()

app.use(router)
app.use(pinia)
app.use(naive)
app.mount('#app') 