import { render, screen, waitFor, within } from '@testing-library/svelte'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import App from './App.svelte'
import { jsonResponse, okResponse } from './test-fixtures'

const PERSONAS = [
  { user: 'Andini Pratama', role: 'IT Admin' },
  { user: 'Bimo Nugroho', role: 'New Employee' },
]

type Handler = (body: { question: string; user: string | null }) => Promise<Response> | Response

function mockServer(handler: Handler, personas: () => Response = () => jsonResponse({ personas: PERSONAS })) {
  const fetchMock = vi.fn(async (url: string, init?: RequestInit) => {
    if (url === '/api/personas') return personas()
    return handler(JSON.parse(String(init?.body)))
  })
  vi.stubGlobal('fetch', fetchMock)
  return fetchMock
}

const asks = (f: ReturnType<typeof mockServer>) => f.mock.calls.filter(([url]) => url === '/api/ask')

beforeEach(() => {
  Element.prototype.scrollIntoView = vi.fn()
})

afterEach(() => {
  vi.unstubAllGlobals()
  localStorage.clear()
  sessionStorage.clear()
})

async function askQuestion(text: string) {
  const user = userEvent.setup()
  await user.type(screen.getByLabelText('Pertanyaan'), text + '{Enter}')
  return user
}

describe('App', () => {
  it('alur lengkap: pilih persona, bertanya, menerima lembar bukti', async () => {
    const fetchMock = mockServer(() => jsonResponse(okResponse()))
    render(App)
    const user = userEvent.setup()
    await screen.findByRole('option', { name: 'Andini Pratama, IT Admin' })
    await user.selectOptions(screen.getByLabelText('Bertanya sebagai'), 'Andini Pratama, IT Admin')
    await askQuestion('Boleh buka port 22 ke db-hr-jkt-01?')

    expect(await screen.findByText('Bukti ditemukan')).toBeInTheDocument()
    expect(asks(fetchMock)[0][1]?.body).toContain('"user":"Andini Pratama"')
    expect(document.querySelector('.asker')?.textContent).toBe('Andini Pratama, IT Admin')
  })

  it('pertanyaan yang ditampilkan adalah versi tersamarkan dari server, bukan teks mentah', async () => {
    mockServer(() => jsonResponse(okResponse({
      question_masked: 'NIK saya [NIK: ****7890], boleh akses HR?',
      pii_masked: 'NIK x1',
    })))
    const { container } = render(App)
    await askQuestion('NIK saya 3175091234567890, boleh akses HR?')
    await screen.findByText('Bukti ditemukan')
    expect(container.textContent).not.toContain('3175091234567890')
    expect(screen.getByText('NIK saya [NIK: ****7890], boleh akses HR?')).toBeInTheDocument()
  })

  it('teks mentah juga tidak tampil selama menunggu jawaban', async () => {
    let release!: (r: Response) => void
    mockServer(() => new Promise((r) => (release = r)))
    const { container } = render(App)
    await askQuestion('hp saya 081234567890')
    expect(await screen.findByText(/sedang disamarkan/)).toBeInTheDocument()
    expect(container.textContent).not.toContain('081234567890')
    release(jsonResponse(okResponse()))
    await screen.findByText('Bukti ditemukan')
  })

  it('tidak ada pertanyaan yang ditulis ke localStorage atau sessionStorage', async () => {
    mockServer(() => jsonResponse(okResponse()))
    render(App)
    await askQuestion('NIK saya 3175091234567890')
    await screen.findByText('Bukti ditemukan')
    expect(localStorage.length + sessionStorage.length).toBe(0)
  })

  it('selama menunggu, kerangka lembar tampil dan kirim kedua diblokir', async () => {
    let release!: (r: Response) => void
    const fetchMock = mockServer(() => new Promise((r) => (release = r)))
    render(App)
    const user = await askQuestion('pertanyaan pertama')
    expect(await screen.findByRole('status')).toHaveTextContent('Mencari bukti')
    await user.type(screen.getByLabelText('Pertanyaan'), 'pertanyaan kedua{Enter}')
    expect(asks(fetchMock)).toHaveLength(1)
    expect(screen.getByLabelText('Bertanya sebagai')).toBeDisabled()
    release(jsonResponse(okResponse()))
    await screen.findByText('Bukti ditemukan')
  })

  it('galat server tampil dengan tombol coba lagi yang mengulang pertanyaan yang sama', async () => {
    let calls = 0
    const fetchMock = mockServer(() =>
      ++calls === 1
        ? jsonResponse({ error: { code: 'internal', message: 'Terjadi kesalahan di server.' } }, 500)
        : jsonResponse(okResponse()),
    )
    render(App)
    const user = await askQuestion('boleh install Chrome?')
    const alert = await screen.findByRole('alert')
    expect(alert).toHaveTextContent('Terjadi kesalahan di server.')
    await user.click(within(alert).getByRole('button', { name: /Coba lagi/ }))
    await screen.findByText('Bukti ditemukan')
    const bodies = asks(fetchMock).map(([, init]) => JSON.parse(String(init?.body)).question)
    expect(bodies).toEqual(['boleh install Chrome?', 'boleh install Chrome?'])
  })

  it('daftar persona gagal dimuat tidak menghalangi bertanya sebagai tamu', async () => {
    const fetchMock = mockServer(() => jsonResponse(okResponse()), () => new Response('x', { status: 500 }))
    render(App)
    expect(await screen.findByText(/Daftar persona tidak bisa dimuat/)).toBeInTheDocument()
    await askQuestion('boleh install Chrome?')
    await screen.findByText('Bukti ditemukan')
    expect(JSON.parse(String(asks(fetchMock)[0][1]?.body)).user).toBeNull()
  })

  it('contoh pertanyaan mengisi kotak tanpa langsung mengirim', async () => {
    const fetchMock = mockServer(() => jsonResponse(okResponse()))
    render(App)
    await userEvent.setup().click(screen.getByRole('button', { name: 'Siapa owner Proyek Garuda?' }))
    expect(screen.getByLabelText('Pertanyaan')).toHaveValue('Siapa owner Proyek Garuda?')
    expect(asks(fetchMock)).toHaveLength(0)
  })

  it('persona yang dipakai tercatat per giliran, walau persona diganti sesudahnya', async () => {
    mockServer(() => jsonResponse(okResponse()))
    render(App)
    const user = userEvent.setup()
    await screen.findByRole('option', { name: 'Bimo Nugroho, New Employee' })
    await user.selectOptions(screen.getByLabelText('Bertanya sebagai'), 'Bimo Nugroho, New Employee')
    await askQuestion('boleh install Chrome?')
    await screen.findByText('Bukti ditemukan')
    await user.selectOptions(screen.getByLabelText('Bertanya sebagai'), 'Tamu (tanpa identitas)')
    await waitFor(() => expect(document.querySelector('.asker')?.textContent).toBe('Bimo Nugroho, New Employee'))
  })
})
