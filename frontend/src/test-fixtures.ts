import type { AskResponse, Citation } from './lib/types'

export const citation = (over: Partial<Citation> = {}): Citation => ({
  doc_id: 'CTRL-09',
  title: 'A.8.20 Networks security',
  section: 'A.8.20 Networks security',
  quote: 'SSH (port 22) from the internet to any internal server is classified as CRITICAL risk — requires jump-host with MFA.',
  owner: 'Citra Kusuma (SOC Analyst)',
  effective_date: '2026-08-01',
  status: 'active',
  risk_level: 'critical',
  ...over,
})

export const okResponse = (over: Partial<AskResponse> = {}): AskResponse => ({
  q_id: 'Q-0123456789ab',
  status: 'OK',
  rc: 0,
  answer: null,
  citations: [citation()],
  flags: [],
  escalation: 'Citra Kusuma (SOC Analyst)',
  question_masked: 'Boleh buka port 22 ke db-hr-jkt-01?',
  identity: { user: 'Andini Pratama', role: 'IT Admin' },
  pii_masked: '',
  ...over,
})

export const noMatch = (over: Partial<AskResponse> = {}): AskResponse => ({
  q_id: 'Q-aaaaaaaaaaaa',
  status: 'NO_MATCH',
  rc: 3,
  answer: 'Saya tidak tahu. Hal ini belum tercakup di knowledge base, dan saya tidak akan menebak.',
  citations: [],
  flags: [],
  escalation: 'Andini Pratama (IT Admin)',
  question_masked: 'Siapa owner Proyek Falcon?',
  identity: { user: 'Sari Lestari', role: 'HR Staff' },
  pii_masked: '',
  ...over,
})

export const injection = (): AskResponse => ({
  q_id: 'Q-bbbbbbbbbbbb',
  status: 'INJECTION_DETECTED',
  rc: 4,
  answer: 'Pertanyaan ini berisi perintah yang ditujukan langsung ke sistem, jadi tidak diproses.',
  citations: [],
  flags: [],
  escalation: null,
  question_masked: null,
  identity: { user: null, role: null },
  pii_masked: '',
})

export function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  })
}
