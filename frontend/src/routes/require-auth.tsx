import { Navigate, Outlet } from 'react-router'

import { useAuthStore } from '@/stores/auth-store'

export function RequireAuth() {
  const accessToken = useAuthStore((state) => state.accessToken)

  if (!accessToken) {
    return <Navigate to="/login" replace />
  }

  return <Outlet />
}
