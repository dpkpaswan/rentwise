import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/analyze': 'http://localhost:8000',
      '/ask': 'http://localhost:8000',
      '/health': 'http://localhost:8000',
      '/sample': 'http://localhost:8000',
    },
  },
})

