import { apiClient } from '@/api/client'
import { errorMessage } from '@/lib/error-message'
import { useAuthStore } from '@/stores/auth-store'

async function refreshCurrentUser(): Promise<void> {
  const { data, error } = await apiClient.GET('/api/v1/users/me')
  if (!error && data) {
    useAuthStore.getState().setUser(data)
  }
}

export async function login(email: string, password: string): Promise<void> {
  const { data, error } = await apiClient.POST('/api/v1/auth/login', {
    body: { email, password },
  })
  if (error || !data) {
    throw new Error(errorMessage(error, 'E-mail ou senha inválidos.'))
  }
  useAuthStore.getState().setSession({
    accessToken: data.access_token,
    refreshToken: data.refresh_token,
  })
  await refreshCurrentUser()
}

export async function register(email: string, password: string, fullName: string): Promise<void> {
  const { error } = await apiClient.POST('/api/v1/auth/register', {
    body: { email, password, full_name: fullName || null },
  })
  if (error) {
    throw new Error(errorMessage(error, 'Não foi possível criar a conta.'))
  }
  await login(email, password)
}

export async function logout(): Promise<void> {
  const { refreshToken, clearSession } = useAuthStore.getState()
  if (refreshToken) {
    await apiClient
      .POST('/api/v1/auth/logout', { body: { refresh_token: refreshToken } })
      .catch(() => undefined)
  }
  clearSession()
}

let bootstrapPromise: Promise<void> | null = null

async function performBootstrap(): Promise<void> {
  const { refreshToken, setSession, clearSession, finishBootstrapping } = useAuthStore.getState()
  if (!refreshToken) {
    finishBootstrapping()
    return
  }

  const { data, error } = await apiClient.POST('/api/v1/auth/refresh', {
    body: { refresh_token: refreshToken },
  })
  if (error || !data) {
    clearSession()
    finishBootstrapping()
    return
  }

  setSession({ accessToken: data.access_token, refreshToken: data.refresh_token })
  await refreshCurrentUser()
  finishBootstrapping()
}

/** Runs once at app boot: if a refresh token was persisted from a previous session, use it
 * to obtain a fresh access token and restore the user's session without forcing a re-login.
 *
 * The refresh token is single-use (rotated server-side on every call), so this guards against
 * running the exchange more than once concurrently — e.g. React StrictMode double-invokes
 * effects in development, which would otherwise send two requests with the same token: the
 * first rotates it and succeeds, the second gets a 401 and wipes the session it just restored. */
export function bootstrapSession(): Promise<void> {
  if (!bootstrapPromise) {
    bootstrapPromise = performBootstrap()
  }
  return bootstrapPromise
}
