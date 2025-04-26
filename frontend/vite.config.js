import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'
import mkcert from 'vite-plugin-mkcert';

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    // host: "2001:250:4001:108:3b8e:ddea:df0a:5765",
    port: "5173",
    // https: true,
    // host:true,
    allowedHosts: ['skymind.uio520.site',"https://skymind.uio520.site"],
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