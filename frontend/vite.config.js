import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { resolve } from 'path'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      // Enables @/ imports throughout the codebase (ADR-010 convention)
      '@': resolve(__dirname, './src'),
    },
  },
  server: {
    port: 5173,
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (!id.includes('node_modules')) return undefined
          if (/[\\/]node_modules[\\/](react|react-dom|react-router-dom|scheduler)[\\/]/.test(id)) {
            return 'vendor-react'
          }
          if (id.includes('/node_modules/@supabase/')) {
            return 'vendor-supabase'
          }
          if (id.includes('/node_modules/recharts/') || id.includes('/node_modules/d3-')) {
            return 'vendor-charts'
          }
          if (id.includes('/node_modules/jspdf/')) {
            return 'vendor-jspdf'
          }
          if (id.includes('/node_modules/html2canvas/')) {
            return 'vendor-html2canvas'
          }
          if (id.includes('/node_modules/dompurify/')) {
            return 'vendor-sanitize'
          }
          if (
            id.includes('/node_modules/axios/') ||
            id.includes('/node_modules/zustand/') ||
            id.includes('/node_modules/i18next/') ||
            id.includes('/node_modules/react-i18next/') ||
            id.includes('/node_modules/lucide-react/')
          ) {
            return 'vendor-ui'
          }
          return undefined
        },
      },
    },
  },
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: './src/test/setup.js',
  },
  esbuild: {
    drop: ['console', 'debugger'],
  },
})
