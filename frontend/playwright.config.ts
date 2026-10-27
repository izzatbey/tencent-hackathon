import { defineConfig, devices } from '@playwright/test'
import { tmpdir } from 'node:os'
import { join } from 'node:path'

const PORT = 8799
const PYTHON = process.env.PYTHON ?? (process.platform === 'win32' ? 'python' : 'python3')

// E2E berjalan terhadap build produksi yang dilayani API Python asli (satu origin, CSP aktif),
// jadi yang dites adalah engine sungguhan, bukan mock.
export default defineConfig({
  testDir: 'e2e',
  testIgnore: ['**/evidence.spec.ts'], // bukti submission: npm run evidence
  fullyParallel: false,
  workers: 1,
  retries: 0,
  reporter: [['list'], ['html', { open: 'never' }]],
  use: {
    baseURL: `http://127.0.0.1:${PORT}`,
    locale: 'id-ID',
    screenshot: 'only-on-failure',
    trace: 'retain-on-failure',
  },
  projects: [
    { name: 'desktop', use: { ...devices['Desktop Chrome'] } },
    { name: 'ponsel', use: { ...devices['Pixel 7'] } },
  ],
  webServer: {
    command: `npm run build && ${PYTHON} ../backend/api/server.py --port ${PORT} --static dist`,
    url: `http://127.0.0.1:${PORT}/api/health`,
    reuseExistingServer: false,
    timeout: 120_000,
    env: {
      SECURITY_SAHABAT_AUDIT_LOG: join(tmpdir(), 'sahabat-e2e-audit.jsonl'),
      PYTHONUTF8: '1',
      PYTHONIOENCODING: 'utf-8',
    },
  },
})
