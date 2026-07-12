import { useEffect } from 'react'
import { RouterProvider } from 'react-router'

import { bootstrapSession } from '@/api/auth'
import { router } from '@/routes/router'
import { useAuthStore } from '@/stores/auth-store'

/** Attempts a silent session restore (via the persisted refresh token) before the router
 * renders, so a page reload doesn't force the user back to the login screen. */
export function AppBootstrap() {
  const isBootstrapping = useAuthStore((state) => state.isBootstrapping)

  useEffect(() => {
    void bootstrapSession()
  }, [])

  if (isBootstrapping) {
    return (
      <div className="flex min-h-svh items-center justify-center">
        <p className="text-sm text-muted-foreground">Carregando…</p>
      </div>
    )
  }

  return <RouterProvider router={router} />
}
