import createClient from 'openapi-fetch'

import { useAuthStore } from '@/stores/auth-store'

import type { paths } from './schema'

// Path keys from the generated schema already include the /api/v1 prefix (that's how
// FastAPI reports them, since the router is mounted under that prefix), so baseUrl here
// must be just the origin — do not append /api/v1 again.
const baseUrl = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

export const apiClient = createClient<paths>({ baseUrl })

function decodeJwtExpMs(token: string): number | null {
  try {
    const payload = JSON.parse(atob(token.split('.')[1]))
    return typeof payload.exp === 'number' ? payload.exp * 1000 : null
  } catch {
    return null
  }
}

function isExpiringSoon(token: string, bufferMs = 10_000): boolean {
  const expMs = decodeJwtExpMs(token)
  if (expMs === null) return false
  return Date.now() + bufferMs >= expMs
}

let refreshPromise: Promise<string | null> | null = null

async function refreshAccessToken(): Promise<string | null> {
  const { refreshToken, setSession, clearSession } = useAuthStore.getState()
  if (!refreshToken) return null

  const { data, error } = await apiClient.POST('/api/v1/auth/refresh', {
    body: { refresh_token: refreshToken },
  })
  if (error || !data) {
    clearSession()
    return null
  }
  setSession({ accessToken: data.access_token, refreshToken: data.refresh_token })
  return data.access_token
}

async function ensureFreshAccessToken(): Promise<string | null> {
  const { accessToken, refreshToken } = useAuthStore.getState()
  if (!accessToken) return null
  if (!isExpiringSoon(accessToken)) return accessToken
  if (!refreshToken) return accessToken

  if (!refreshPromise) {
    refreshPromise = refreshAccessToken().finally(() => {
      refreshPromise = null
    })
  }
  return refreshPromise
}

apiClient.use({
  async onRequest({ request }) {
    const token = await ensureFreshAccessToken()
    if (token) {
      request.headers.set('Authorization', `Bearer ${token}`)
    }
    return request
  },
  async onResponse({ response }) {
    // Proactive refresh above should prevent most 401s; if one still slips through
    // (token revoked server-side, clock skew), drop the session so the app redirects
    // to login instead of silently keeping stale/invalid credentials around.
    if (response.status === 401) {
      useAuthStore.getState().clearSession()
    }
    return response
  },
})
