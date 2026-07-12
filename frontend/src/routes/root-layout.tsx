import { Outlet } from 'react-router'

export function RootLayout() {
  return (
    <div className="flex min-h-svh flex-col">
      <header className="border-border border-b px-6 py-4">
        <span className="text-lg font-semibold">ApiNest</span>
      </header>
      <main className="flex-1 p-6">
        <Outlet />
      </main>
    </div>
  )
}
