const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

let token: string | null = null
let shopId: number | null = Number(localStorage.getItem('shopId')) || null

export function setToken(value: string) {
  token = value
}

export function setShopId(value: number | null) {
  shopId = value
  if (value) localStorage.setItem('shopId', String(value))
  else localStorage.removeItem('shopId')
}

export function getShopId() {
  return shopId
}

export class ApiError extends Error {
  status: number
  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

export async function api<T>(path: string, options: { method?: string; body?: unknown; query?: Record<string, unknown> } = {}): Promise<T> {
  const url = new URL(path, API_URL)
  for (const [key, value] of Object.entries(options.query ?? {})) {
    if (value !== undefined && value !== null && value !== '') url.searchParams.set(key, String(value))
  }
  const headers: Record<string, string> = { 'Content-Type': 'application/json' }
  if (token) headers.Authorization = `Bearer ${token}`
  if (shopId) headers['X-Shop-Id'] = String(shopId)

  const res = await fetch(url, {
    method: options.method ?? (options.body ? 'POST' : 'GET'),
    headers,
    body: options.body ? JSON.stringify(options.body) : undefined,
  })
  if (!res.ok) {
    let message = res.statusText
    try {
      const data = await res.json()
      message = typeof data.detail === 'string' ? data.detail : JSON.stringify(data.detail)
    } catch {
      /* not json */
    }
    throw new ApiError(res.status, message)
  }
  return res.json() as Promise<T>
}
