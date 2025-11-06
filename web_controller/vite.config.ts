import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': {
        target: 'http://discord_bot:8000',
        changeOrigin: true,
        secure: false,
      }
    }
  }
})
