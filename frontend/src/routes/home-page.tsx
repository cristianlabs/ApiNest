import { useAuthStore } from '@/stores/auth-store'

export function HomePage() {
  const user = useAuthStore((state) => state.user)

  return (
    <div className="space-y-2">
      <h1 className="text-2xl font-semibold">
        {user ? `Bem-vindo, ${user.full_name ?? user.email}` : 'Bem-vindo ao ApiNest'}
      </h1>
      <p className="text-muted-foreground">
        Organizações, projetos e o catálogo de APIs chegam nas próximas etapas.
      </p>
    </div>
  )
}
