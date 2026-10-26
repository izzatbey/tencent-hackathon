import { defineConfig } from 'vitest/config'
import { svelte } from '@sveltejs/vite-plugin-svelte'

// API Python (backend/api/server.py) jalan di 8787; dev server meneruskan /api ke sana.
export default defineConfig(({ mode }) => ({
  plugins: [svelte()],
  server: { proxy: { '/api': 'http://127.0.0.1:8787' } },
  // Komponen Svelte 5 harus dimuat versi browser-nya saat dites di jsdom.
  resolve: mode === 'test' ? { conditions: ['browser'] } : undefined,
  test: {
    environment: 'jsdom',
    include: ['src/**/*.test.ts'],
    setupFiles: ['src/test-setup.ts'],
  },
}))
