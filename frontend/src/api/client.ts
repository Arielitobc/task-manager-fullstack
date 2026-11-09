const API_URL = (import.meta.env.VITE_API_URL as string | undefined) ?? 'http://localhost:8000/api/v1'

const TOKEN_KEY = 'task-manager.token'

/** localStorage can throw (private mode, blocked storage): never let that break the app. */
export const tokenStorage = {
  get(): string | null {
    try {
      return localStorage.getItem(TOKEN_KEY)
    } catch {
      return null
    }
  },
  set(token: string): void {
    try {
      localStorage.setItem(TOKEN_KEY, token)
    } catch {
      /* ignore */
    }
  },
  clear(): void {
    try {
      localStorage.removeItem(TOKEN_KEY)
    } catch {
      /* ignore */
    }
  },
}

export class ApiError extends Error {
  readonly status: number

  constructor(status: number, message: string) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

type FastApiDetail = string | { msg: string; loc?: (string | number)[] }[] | undefined

function toMessage(detail: FastApiDetail, fallback: string): string {
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail) && detail.length > 0) {
    return detail
      .map((d) => {
        const field = d.loc?.filter((l) => l !== 'body' && l !== 'query').join('.')
        return field ? `${field}: ${d.msg}` : d.msg
      })
      .join('; ')
  }
  return fallback
}

let unauthorizedHandler: (() => void) | null = null

/** Registered by the AuthProvider so an expired token logs the user out everywhere. */
export function onUnauthorized(handler: (() => void) | null): void {
  unauthorizedHandler = handler
}

type Query = Record<string, string | number | undefined | null>

interface RequestOptions {
  method?: 'GET' | 'POST' | 'PATCH' | 'DELETE'
  json?: unknown
  form?: Record<string, string>
  query?: Query
}

function buildUrl(path: string, query?: Query): string {
  const url = new URL(`${API_URL}${path}`)
  Object.entries(query ?? {}).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') {
      url.searchParams.set(key, String(value))
    }
  })
  return url.toString()
}

export async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const headers: Record<string, string> = { Accept: 'application/json' }
  let body: BodyInit | undefined

  if (options.json !== undefined) {
    headers['Content-Type'] = 'application/json'
    body = JSON.stringify(options.json)
  } else if (options.form) {
    body = new URLSearchParams(options.form)
  }

  const token = tokenStorage.get()
  if (token) headers.Authorization = `Bearer ${token}`

  let response: Response
  try {
    response = await fetch(buildUrl(path, options.query), {
      method: options.method ?? 'GET',
      headers,
      body,
    })
  } catch {
    throw new ApiError(0, 'Cannot reach the server. Is the API running?')
  }

  if (response.status === 401 && token) unauthorizedHandler?.()

  if (!response.ok) {
    const data = (await response.json().catch(() => ({}))) as { detail?: FastApiDetail; error?: string }
    const fallback =
      response.status === 429 ? 'Too many requests, please wait a moment.' : response.statusText
    throw new ApiError(response.status, toMessage(data.detail ?? data.error, fallback))
  }

  if (response.status === 204) return undefined as T
  return (await response.json()) as T
}
