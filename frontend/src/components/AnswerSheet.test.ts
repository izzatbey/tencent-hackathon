import { render, screen } from '@testing-library/svelte'
import { describe, expect, it } from 'vitest'
import AnswerSheet from './AnswerSheet.svelte'
import { citation, injection, noMatch, okResponse } from '../test-fixtures'
import type { AskResponse } from '../lib/types'

describe('AnswerSheet: SOURCES', () => {
  it('menampilkan stempel, nomor catatan, doc_id, dan kutipan verbatim', () => {
    render(AnswerSheet, { response: okResponse() })
    expect(screen.getByText('Bukti ditemukan')).toBeInTheDocument()
    expect(screen.getByText('Q-0123456789ab')).toBeInTheDocument()
    expect(screen.getByText('CTRL-09')).toBeInTheDocument()
    expect(screen.getByText(citation().quote)).toBeInTheDocument()
  })

  it('kutipan panjang tidak dipotong dan whitespace-nya tidak diringkas jadi parafrase', () => {
    const quote = 'Baris pertama.\n' + 'kata '.repeat(400) + 'AKHIR'
    const { container } = render(AnswerSheet, { response: okResponse({ citations: [citation({ quote })] }) })
    expect(container.querySelector('blockquote')?.textContent).toBe(quote)
  })

  it('judul dan section yang sama hanya ditulis sekali', () => {
    render(AnswerSheet, { response: okResponse() })
    expect(screen.getByText('A.8.20 Networks security')).toBeInTheDocument()
  })

  it('semua kutipan ditampilkan dengan urutan dari server', () => {
    const citations = ['SOP-7', 'TOPO-REMOTE-ACCESS', 'SOP-7'].map((doc_id, i) =>
      citation({ doc_id, section: `Bagian ${i}`, quote: `kutipan ${i}` }),
    )
    const { container } = render(AnswerSheet, { response: okResponse({ citations }) })
    expect([...container.querySelectorAll('.doc-id')].map((n) => n.textContent)).toEqual([
      'SOP-7', 'TOPO-REMOTE-ACCESS', 'SOP-7',
    ])
  })

  it('tanpa answer composer, lembar tidak mengarang kesimpulan boleh atau tidak', () => {
    const { container } = render(AnswerSheet, { response: okResponse({ answer: null }) })
    const text = container.querySelector('.answer')?.textContent ?? ''
    expect(text).toContain('1 kutipan')
    expect(text).not.toMatch(/^(Boleh|Tidak boleh)/)
  })

  it('jawaban dari composer ditampilkan bila ada', () => {
    render(AnswerSheet, { response: okResponse({ answer: 'Tidak boleh. Risiko CRITICAL.' }) })
    expect(screen.getByText('Tidak boleh. Risiko CRITICAL.')).toBeInTheDocument()
  })

  it('flag konflik punya label teks, bukan hanya warna', () => {
    render(AnswerSheet, {
      response: okResponse({
        flags: [{ type: 'CONFLICT', doc: 'SOP-FUEL vs MEMO-HR-10', detail: 'dua versi ditemukan' }],
      }),
    })
    expect(screen.getByText('Sumber saling bertentangan')).toBeInTheDocument()
    expect(screen.getByText('SOP-FUEL vs MEMO-HR-10')).toBeInTheDocument()
  })

  it('blokir aturan tampil sebagai peringatan, pratinjau sebagai catatan', () => {
    const { container } = render(AnswerSheet, {
      response: okResponse({
        flags: [
          { type: 'POLICY_BLOCK', doc: 'policy register', detail: 'Diblokir aturan POL-x001.' },
          { type: 'POLICY_PREVIEW', doc: 'policy register', detail: 'Pratinjau: risiko MEDIUM.' },
        ],
      }),
    })
    const items = [...container.querySelectorAll('.flags li')]
    const tone = (li: Element) => (li.classList.contains('conflict') ? 'conflict' : 'note')
    expect(items.map((li) => [tone(li), li.querySelector('strong')?.textContent])).toEqual([
      ['conflict', 'Diblokir aturan perusahaan'],
      ['note', 'Pratinjau aturan Pra-CAB'],
    ])
  })

  it('tanggal mustahil di metadata ditampilkan apa adanya', () => {
    render(AnswerSheet, { response: okResponse({ citations: [citation({ effective_date: '2026-02-31' })] }) })
    expect(screen.getByText('2026-02-31')).toBeInTheDocument()
  })
})

describe('AnswerSheet: LIMITS dan PERMISSIONS', () => {
  it('tidak tahu menyebut orang yang bisa ditanya', () => {
    render(AnswerSheet, { response: noMatch() })
    expect(screen.getByText('Tidak tahu')).toBeInTheDocument()
    expect(screen.getByText('Andini Pratama (IT Admin)')).toBeInTheDocument()
    expect(screen.queryByText('Landasan')).not.toBeInTheDocument()
  })

  it('dua NO_MATCH yang hanya beda nomor catatan menghasilkan markup yang sama', () => {
    // Topik restricted dan topik fiktif sampai sebagai NO_MATCH yang identik;
    // UI tidak boleh menambahkan perbedaan apa pun.
    const a = render(AnswerSheet, { response: noMatch({ question_masked: 'Proyek Garuda' }) }).container.innerHTML
    const b = render(AnswerSheet, { response: noMatch({ question_masked: 'Proyek Falcon' }) }).container.innerHTML
    expect(a).toBe(b)
  })

  it('identitas kosong ditulis sebagai tamu', () => {
    render(AnswerSheet, { response: okResponse({ identity: { user: null, role: null } }) })
    expect(screen.getByText(/Tamu tanpa identitas/)).toBeInTheDocument()
  })
})

describe('AnswerSheet: injection, PII, XSS', () => {
  it('injection ditolak tanpa kutipan dan tanpa langkah eskalasi', () => {
    render(AnswerSheet, { response: injection() })
    expect(screen.getByText('Ditolak')).toBeInTheDocument()
    expect(screen.queryByText('Landasan')).not.toBeInTheDocument()
    expect(screen.queryByText(/Langkah berikutnya/)).not.toBeInTheDocument()
  })

  it('status baru dari server yang belum dikenal UI tampil sebagai tidak tahu, bukan crash', () => {
    const response = { ...noMatch(), status: 'NEEDS_APPROVAL' } as unknown as AskResponse
    render(AnswerSheet, { response })
    expect(screen.getByText('Tidak tahu')).toBeInTheDocument()
  })

  it('kutipan berbahasa Arab mengikuti arah teksnya sendiri', () => {
    const { container } = render(AnswerSheet, {
      response: okResponse({ citations: [citation({ quote: 'السلام عليكم' })] }),
    })
    expect(container.querySelector('blockquote')).toHaveAttribute('dir', 'auto')
  })

  it('ringkasan penyamaran PII ditampilkan', () => {
    render(AnswerSheet, { response: okResponse({ pii_masked: 'NIK x1, PHONE x1' }) })
    expect(screen.getByText(/Data pribadi disamarkan \(NIK x1, PHONE x1\)/)).toBeInTheDocument()
  })

  it('HTML di kutipan atau flag dirender sebagai teks, bukan markup', () => {
    const payload = '<img src=x onerror="window.__xss=1"><script>window.__xss=1</script>'
    const { container } = render(AnswerSheet, {
      response: okResponse({
        citations: [citation({ quote: payload, title: payload, owner: payload })],
        flags: [{ type: 'REVIEW', doc: payload, detail: payload }],
      }),
    })
    expect(container.querySelector('.evidence img, .evidence script, .flags img')).toBeNull()
    expect(container.querySelector('blockquote')?.textContent).toBe(payload)
  })
})
