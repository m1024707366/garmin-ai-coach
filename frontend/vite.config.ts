import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
  build: {
    chunkSizeWarningLimit: 1000,
    rollupOptions: {
      output: {
        manualChunks: {
          react: ['react', 'react-dom'],
          reactRouter: ['react-router-dom'],
          axios: ['axios'],
          reactQuery: ['@tanstack/react-query'],
          recharts: ['recharts'],
          markdown: ['react-markdown', 'remark-gfm'],
          dateFns: ['date-fns'],
          zustand: ['zustand'],
          heroicons: ['@heroicons/react'],
        },
      },
    },
  },
})
