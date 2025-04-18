import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, '/api/v1'),
        timeout: 30000,
        ws: true,
        onError: (err, req, res) => {
          console.error('API代理错误:', err);
        }
      },
      '/ws': {
        target: 'ws://localhost:8000',
        ws: true,
        changeOrigin: true
      }
    }
  }
}) 