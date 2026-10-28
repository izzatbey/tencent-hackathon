import type { Flag } from './types'

// Label tiap jenis flag dari detect_conflicts(), risk_flags(), dan ask_bridge
// (klarifikasi, permintaan aksi, verdict aturan). Arti tidak pernah hanya dari
// warna: selalu ada teks label + ikon.
const FLAG_LABELS: Record<string, string> = {
  CONFLICT: 'Sumber saling bertentangan',
  REVIEW: 'Catatan dari pemilik dokumen',
  SUPERSEDED_BY: 'Sudah digantikan versi baru',
  SUPERSEDES: 'Menggantikan versi lama',
  STATUS: 'Status dokumen tidak aktif',
  RISK: 'Di atas batas risiko akses Anda',
  CLARIFY: 'Perlu klarifikasi',
  ACTION_REQUEST: 'Permintaan aksi tidak dijalankan',
  POLICY_BLOCK: 'Dilarang aturan perusahaan',
  POLICY_PREVIEW: 'Pratinjau aturan perusahaan',
}

const WARNING_FLAGS = new Set(['CONFLICT', 'RISK', 'SUPERSEDED_BY', 'POLICY_BLOCK'])

export function flagLabel(flag: Flag): string {
  return FLAG_LABELS[flag.type] ?? 'Perlu diperhatikan'
}

export function flagTone(flag: Flag): 'conflict' | 'note' {
  return WARNING_FLAGS.has(flag.type) ? 'conflict' : 'note'
}

const MONTHS = ['Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni', 'Juli', 'Agustus',
  'September', 'Oktober', 'November', 'Desember']

// "2026-03-15" -> "15 Maret 2026". Tanggal tak valid ditampilkan apa adanya,
// tidak digulirkan ke tanggal lain seperti perilaku Date.
export function formatDate(value: string | null): string | null {
  if (!value) return null
  const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(value.trim())
  if (!m) return value
  const [, y, mo, d] = m.map(Number)
  const probe = new Date(Date.UTC(y, mo - 1, d))
  if (probe.getUTCMonth() !== mo - 1 || probe.getUTCDate() !== d) return value
  return `${d} ${MONTHS[mo - 1]} ${y}`
}

const RISK_LABELS: Record<string, string> = {
  low: 'Risiko rendah', medium: 'Risiko sedang', high: 'Risiko tinggi', critical: 'Risiko kritis',
}

export function riskLabel(value: string | null): string | null {
  return value ? RISK_LABELS[value.toLowerCase()] ?? `Risiko ${value}` : null
}

export function personaLabel(p: { user: string | null; role: string | null }): string {
  if (!p.user) return 'Tamu tanpa identitas'
  return p.role ? `${p.user}, ${p.role}` : p.user
}
