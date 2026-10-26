import { afterEach, describe, expect, it, vi } from 'vitest'
import { ApiError, ask, loadPersonas } from './api'
import { jsonResponse, okResponse } from '../test-fixtures'

afterEach(() => {
  vi.useRealTimers()
})

describe('ask', () => {
  it('mengirim pertanyaan dan persona sebagai JSON ke /api/ask', async () => {
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse(okResponse()))
    await ask('Boleh buka port 22?', { user: 'Andini Pratama', role: 'IT Admin' }, fetchMock)
    const [url, init] = fetchMock.mock.calls[0]
    expect(url).toBe('/api/ask')
    expect(init.method).toBe('POST')
    expect(init.headers['Content-Type']).toBe('application/json')
    expect(JSON.parse(init.body)).toEqual({
      question: 'Boleh buka port 22?',
      user: 'Andini Pratama',
      role: 'IT Admin',
    })
  })

  it('tamu dikirim dengan user dan role null', async () => {
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse(okResponse()))
    await ask('a', null, fetchMock)
    expect(JSON.parse(fetchMock.mock.calls[0][1].body)).toMatchObject({ user: null, role: null })
  })

  it('pesan galat 400 dari server diteruskan apa adanya', async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      jsonResponse({ error: { code: 'question_too_long', message: 'Pertanyaan maksimal 2000 karakter.' } }, 400),
    )
    await expect(ask('a', null, fetchMock)).rejects.toMatchObject({
      kind: 'invalid',
      message: 'Pertanyaan maksimal 2000 karakter.',
    })
  })

  it('500 dengan body bukan JSON menjadi pesan umum, bukan stack trace', async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response('<html>Traceback', { status: 502 }))
    const err = await ask('a', null, fetchMock).catch((e) => e)
    expect(err).toBeInstanceOf(ApiError)
    expect(err.kind).toBe('server')
    expect(err.message).not.toContain('Traceback')
  })

  it('koneksi putus menjadi galat jaringan', async () => {
    const fetchMock = vi.fn().mockRejectedValue(new TypeError('Failed to fetch'))
    await expect(ask('a', null, fetchMock)).rejects.toMatchObject({ kind: 'network' })
  })

  it('server yang diam lebih dari 30 detik dibatalkan', async () => {
    vi.useFakeTimers()
    const fetchMock = vi.fn((_url: string, init: RequestInit) =>
      new Promise<Response>((_resolve, reject) => {
        init.signal?.addEventListener('abort', () =>
          reject(Object.assign(new Error('aborted'), { name: 'AbortError' })),
        )
      }),
    )
    const pending = ask('a', null, fetchMock as unknown as typeof fetch).catch((e) => e)
    await vi.advanceTimersByTimeAsync(29_999)
    expect(fetchMock.mock.calls[0][1].signal?.aborted).toBe(false)
    await vi.advanceTimersByTimeAsync(1)
    expect((await pending).kind).toBe('timeout')
  })
})

describe('loadPersonas', () => {
  it('mengembalikan daftar persona', async () => {
    const personas = [{ user: 'Bimo Nugroho', role: 'New Employee' }]
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse({ personas }))
    expect(await loadPersonas(fetchMock)).toEqual(personas)
  })

  it('bentuk respons yang salah menjadi daftar kosong, bukan crash', async () => {
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse({ personas: 'bukan array' }))
    expect(await loadPersonas(fetchMock)).toEqual([])
  })
})
