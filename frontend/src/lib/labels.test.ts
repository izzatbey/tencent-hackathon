import { describe, expect, it } from 'vitest'
import { flagLabel, flagTone, formatDate, personaLabel, riskLabel } from './labels'

describe('formatDate', () => {
  it.each([
    ['2026-03-15', '15 Maret 2026'],
    ['2024-02-29', '29 Februari 2024'],
    ['2026-12-31', '31 Desember 2026'],
    [' 2026-01-01 ', '1 Januari 2026'],
  ])('%s menjadi %s', (input, expected) => {
    expect(formatDate(input)).toBe(expected)
  })

  it.each(['2026-02-31', '2025-02-29', '2026-13-01', '2026-00-10', '15/03/2026', 'kemarin'])(
    'tanggal mustahil atau format lain %s ditampilkan apa adanya, tidak digulirkan',
    (input) => {
      expect(formatDate(input)).toBe(input)
    },
  )

  it('null dan string kosong tidak menghasilkan teks', () => {
    expect(formatDate(null)).toBeNull()
    expect(formatDate('')).toBeNull()
  })
})

describe('flag', () => {
  it('setiap jenis flag dari engine punya label teks', () => {
    for (const type of ['CONFLICT', 'REVIEW', 'SUPERSEDED_BY', 'SUPERSEDES', 'STATUS', 'RISK',
      'CLARIFY', 'ACTION_REQUEST', 'POLICY_BLOCK', 'POLICY_PREVIEW']) {
      expect(flagLabel({ type, doc: 'X', detail: '' })).not.toBe('Perlu diperhatikan')
    }
  })

  it('jenis flag baru yang belum dikenal tetap diberi label umum', () => {
    expect(flagLabel({ type: 'BARU', doc: 'X', detail: '' })).toBe('Perlu diperhatikan')
  })

  it('konflik dan risiko memakai nada peringatan', () => {
    expect(flagTone({ type: 'CONFLICT', doc: '', detail: '' })).toBe('conflict')
    expect(flagTone({ type: 'RISK', doc: '', detail: '' })).toBe('conflict')
    expect(flagTone({ type: 'REVIEW', doc: '', detail: '' })).toBe('note')
    expect(flagTone({ type: 'POLICY_BLOCK', doc: '', detail: '' })).toBe('conflict')
    expect(flagTone({ type: 'CLARIFY', doc: '', detail: '' })).toBe('note')
  })
})

describe('riskLabel dan personaLabel', () => {
  it('menerjemahkan tingkat risiko tanpa peduli huruf besar', () => {
    expect(riskLabel('CRITICAL')).toBe('Risiko kritis')
    expect(riskLabel('extreme')).toBe('Risiko extreme')
    expect(riskLabel(null)).toBeNull()
  })

  it('identitas kosong disebut tamu, bukan nama karangan', () => {
    expect(personaLabel({ user: null, role: null })).toBe('Tamu tanpa identitas')
    expect(personaLabel({ user: 'Bimo Nugroho', role: 'New Employee' })).toBe('Bimo Nugroho, New Employee')
    expect(personaLabel({ user: 'Bimo Nugroho', role: null })).toBe('Bimo Nugroho')
  })
})
