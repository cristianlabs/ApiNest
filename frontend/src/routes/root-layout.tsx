import { useMutation } from '@tanstack/react-query'
import { Link, Outlet, useNavigate } from 'react-router'

import { logout } from '@/api/auth'
import { Button } from '@/components/ui/button'
import { useAuthStore } from '@/stores/auth-store'

export function RootLayout() {
  const navigate = useNavigate()
  const user = useAuthStore((state) => state.user)

  const logoutMutation = useMutation({
    mutationFn: logout,
    onSuccess: () => navigate('/login', { replace: true }),
  })

  return (
    <div className="flex min-h-svh flex-col">
      <header className="flex items-center justify-between border-b border-border px-6 py-4">
        <div className="flex items-center gap-6">
          <span className="text-lg font-semibold">ApiNest</span>
          <nav className="flex items-center gap-4 text-sm">
            <Link to="/dashboard" className="text-muted-foreground hover:text-foreground">
              Dashboard
            </Link>
            <Link to="/organizations" className="text-muted-foreground hover:text-foreground">
              Organizações
            </Link>
          </nav>
        </div>
        <div className="flex items-center gap-3">
          {user && (
            <span className="text-sm text-muted-foreground">{user.full_name ?? user.email}</span>
          )}
          <Button
            variant="outline"
            size="sm"
            onClick={() => logoutMutation.mutate()}
            disabled={logoutMutation.isPending}
          >
            Sair
          </Button>
        </div>
      </header>
      <main className="flex-1 p-6">
        <Outlet />
      </main>
    </div>
  )
}
