import { defineConfig, devices } from '@playwright/test'
import base from './playwright.config'

// Hanya untuk menghasilkan bukti hasil tes (docs/test-results/), satu viewport desktop.
export default defineConfig({
  ...base,
  testMatch: 'evidence.spec.ts',
  testIgnore: [],
  reporter: [['list']],
  projects: [{ name: 'desktop', use: { ...devices['Desktop Chrome'], viewport: { width: 1100, height: 900 } } }],
})
