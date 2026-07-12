import { create } from 'zustand'

export interface AuthUser {
  id: string
  email: string
  full_name: string | null
}

interface AuthState {
  accessToken: string | null
  refreshToken: string | null
  user: AuthUser | null
  /** True until the boot-time silent refresh attempt (see bootstrapSession) has settled. */
  isBootstrapping: boolean
  setSession: (params: {
    accessToken: string
    refreshToken: string
    user?: AuthUser | null
  }) => void
  setUser: (user: AuthUser | null) => void
  clearSession: () => void
  finishBootstrapping: () => void
}

const REFRESH_TOKEN_STORAGE_KEY = 'apinest.refresh_token'

export const useAuthStore = create<AuthState>((set) => ({
  accessToken: null,
  refreshToken: localStorage.getItem(REFRESH_TOKEN_STORAGE_KEY),
  user: null,
  isBootstrapping: true,
  setSession: ({ accessToken, refreshToken, user }) => {
    localStorage.setItem(REFRESH_TOKEN_STORAGE_KEY, refreshToken)
    set((state) => ({ accessToken, refreshToken, user: user ?? state.user }))
  },
  setUser: (user) => set({ user }),
  clearSession: () => {
    localStorage.removeItem(REFRESH_TOKEN_STORAGE_KEY)
    set({ accessToken: null, refreshToken: null, user: null })
  },
  finishBootstrapping: () => set({ isBootstrapping: false }),
}))
