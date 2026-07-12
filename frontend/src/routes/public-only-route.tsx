import { Navigate, Outlet } from 'react-router'

import { useAuthStore } from '@/stores/auth-store'

/** Keeps an already-authenticated user away from /login and /register. */
export function PublicOnlyRoute() {
  const accessToken = useAuthStore((state) => state.accessToken)

  if (accessToken) {
    return <Navigate to="/" replace />
  }

  return <Outlet />
}
