import { defineConfig } from 'vite'
import veauryVitePlugins from 'veaury/vite/index.js'

export default defineConfig({
  plugins: [
    veauryVitePlugins({
      type: 'vue'
    })
  ],
  define: {
    // Excalidraw and React often depend on process.env
    'process.env': {}
  },
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
})
