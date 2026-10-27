import type { AskResponse, Persona } from './types'

export const MAX_QUESTION = 2000
const TIMEOUT_MS = 30_000

export class ApiError extends Error {
  constructor(
    message: string,
    readonly kind: 'invalid' | 'server' | 'network' | 'timeout',
  ) {
    super(message)
  }
}

type Fetch = typeof fetch

async function errorMessage(res: Response): Promise<string> {
  try {
    const body = await res.json()
    if (typeof body?.error?.message === 'string') return body.error.message
  } catch {
    // body bukan JSON: jatuh ke pesan umum di bawah
  }
  return 'Server sedang bermasalah. Coba lagi sebentar lagi.'
}

export async function ask(
  question: string,
  persona: Persona | null,
  fetchImpl: Fetch = fetch,
): Promise<AskResponse> {
  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), TIMEOUT_MS)
  let res: Response
  try {
    res = await fetchImpl('/api/ask', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question, user: persona?.user ?? null, role: persona?.role ?? null }),
      signal: controller.signal,
    })
  } catch (err) {
    if ((err as Error)?.name === 'AbortError') {
      throw new ApiError('Server tidak menjawab dalam 30 detik.', 'timeout')
    }
    throw new ApiError('Tidak bisa terhubung ke server. Periksa koneksi Anda.', 'network')
  } finally {
    clearTimeout(timer)
  }
  if (!res.ok) {
    throw new ApiError(await errorMessage(res), res.status < 500 ? 'invalid' : 'server')
  }
  try {
    return (await res.json()) as AskResponse
  } catch {
    // 200 berisi HTML (proxy, halaman login, captive portal) bukan jawaban
    throw new ApiError('Server mengirim balasan yang tidak dikenali. Coba lagi.', 'server')
  }
}

export async function loadPersonas(fetchImpl: Fetch = fetch): Promise<Persona[]> {
  const res = await fetchImpl('/api/personas')
  if (!res.ok) throw new ApiError(await errorMessage(res), 'server')
  const body = await res.json()
  return Array.isArray(body?.personas) ? body.personas : []
}
