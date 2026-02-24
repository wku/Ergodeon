import { defineConfig } from 'vite'
import { svelte } from '@sveltejs/vite-plugin-svelte'

export default defineConfig({
  plugins: [svelte()],
  server: {
    proxy: {
      '/socket.io': {
        target: 'http://localhost:8000',
        ws: true,
      },
    },
  },
})
