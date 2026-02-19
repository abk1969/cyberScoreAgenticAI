import type { ApiError } from '@/types/api'

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'

type RequestInterceptor = (config: RequestInit) => RequestInit
type ResponseInterceptor = (response: Response) => Response | Promise<Response>

class ApiClient {
  private baseUrl: string
  private requestInterceptors: RequestInterceptor[] = []
  private responseInterceptors: ResponseInterceptor[] = []

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl
  }

  onRequest(interceptor: RequestInterceptor) {
    this.requestInterceptors.push(interceptor)
  }

  onResponse(interceptor: ResponseInterceptor) {
    this.responseInterceptors.push(interceptor)
  }

  private getToken(): string | null {
    if (typeof window === 'undefined') return null
    try {
      const raw = localStorage.getItem('auth-storage')
      if (raw) {
        const parsed = JSON.parse(raw)
        return parsed?.state?.token ?? null
      }
    } catch {
      // fall through
    }
    return localStorage.getItem('auth_token')
  }

  private getHeaders(): HeadersInit {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    }
    const token = this.getToken()
    if (token) {
      headers['Authorization'] = `Bearer ${token}`
    }
    return headers
  }

  async request<T>(path: string, options: RequestInit = {}): Promise<T> {
    const url = `${this.baseUrl}${path}`

    let config: RequestInit = {
      ...options,
      headers: {
        ...this.getHeaders(),
        ...options.headers,
      },
    }

    for (const interceptor of this.requestInterceptors) {
      config = interceptor(config)
    }

    let response = await fetch(url, config)

    for (const interceptor of this.responseInterceptors) {
      response = await interceptor(response)
    }

    if (!response.ok) {
      const error: ApiError = await response.json().catch(() => ({
        message: response.statusText,
        code: 'UNKNOWN_ERROR',
        status: response.status,
      }))
      throw error
    }

    if (response.status === 204) {
      return undefined as T
    }

    return response.json()
  }

  get<T>(path: string): Promise<T> {
    return this.request<T>(path, { method: 'GET' })
  }

  post<T>(path: string, body?: unknown): Promise<T> {
    return this.request<T>(path, {
      method: 'POST',
      body: body !== undefined ? JSON.stringify(body) : undefined,
    })
  }

  put<T>(path: string, body: unknown): Promise<T> {
    return this.request<T>(path, {
      method: 'PUT',
      body: JSON.stringify(body),
    })
  }

  patch<T>(path: string, body: unknown): Promise<T> {
    return this.request<T>(path, {
      method: 'PATCH',
      body: JSON.stringify(body),
    })
  }

  delete<T>(path: string): Promise<T> {
    return this.request<T>(path, { method: 'DELETE' })
  }
}

export const api = new ApiClient(API_URL)

// Redirect to login on 401
api.onResponse(async (response) => {
  if (response.status === 401 && typeof window !== 'undefined') {
    const { useAuthStore } = await import('@/stores/auth-store')
    useAuthStore.getState().logout()
  }
  return response
})
