// Kontrak POST /api/ask (docs/architecture.md §4). Hanya field ini yang
// dikirim backend. Topik restricted tidak punya status sendiri: bagi yang tidak
// berwenang hasilnya sama persis dengan topik yang tidak ada.

export type Status = 'OK' | 'NO_MATCH' | 'INJECTION_DETECTED'

export interface Citation {
  doc_id: string
  title: string | null
  section: string | null
  quote: string
  owner: string | null
  effective_date: string | null
  status: string | null
  risk_level: string | null
}

export interface Flag {
  type: string
  doc: string
  detail: string
}

export interface AskResponse {
  q_id: string
  status: Status
  rc: number
  answer: string | null
  citations: Citation[]
  flags: Flag[]
  escalation: string | null
  question_masked: string | null
  identity: { user: string | null; role: string | null }
  pii_masked: string
}

export interface Persona {
  user: string
  role: string
}
