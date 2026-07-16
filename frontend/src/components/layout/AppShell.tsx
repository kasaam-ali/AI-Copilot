import { Link, NavLink, Outlet } from 'react-router-dom'

interface NavItem {
  label: string
  to: string
  ready: boolean
}

const navItems: NavItem[] = [
  { label: 'Inspect', to: '/inspect', ready: true },
  { label: 'Live Inspection', to: '/live', ready: true },
  { label: 'Live Machines', to: '/machines', ready: true },
  { label: 'Review Queue', to: '/review', ready: true },
  { label: 'Models', to: '/models', ready: true },
  { label: 'Analytics', to: '/analytics', ready: false },
  { label: 'Reports', to: '/reports', ready: true },
  { label: 'System', to: '/system', ready: true },
]

export function AppShell() {
  return (
    <div className="flex h-screen bg-surface text-ink">
      <aside className="flex w-60 shrink-0 flex-col border-r border-surface-border bg-surface-raised">
        <Link to="/" className="flex h-14 items-center gap-2 border-b border-surface-border px-5">
          <span className="flex h-6 w-6 items-center justify-center rounded-md bg-gradient-to-br from-brand to-accent">
            <span className="h-2 w-2 rounded-sm bg-surface" />
          </span>
          <span className="text-sm font-semibold tracking-wide">SentinelQ</span>
        </Link>
        <nav className="flex flex-1 flex-col gap-1 p-3">
          {navItems.map((item) =>
            item.ready ? (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) =>
                  `relative rounded-md px-3 py-2 text-sm transition-colors ${
                    isActive
                      ? 'bg-brand/10 text-brand-glow'
                      : 'text-ink-muted hover:bg-surface-panel hover:text-ink'
                  }`
                }
              >
                {({ isActive }) => (
                  <>
                    {isActive && (
                      <span className="absolute left-0 top-1/2 h-5 w-0.5 -translate-y-1/2 rounded-full bg-brand" />
                    )}
                    {item.label}
                  </>
                )}
              </NavLink>
            ) : (
              <span
                key={item.to}
                className="cursor-not-allowed rounded-md px-3 py-2 text-sm text-ink-faint"
                title="Coming soon"
              >
                {item.label}
              </span>
            ),
          )}
        </nav>
        <Link
          to="/"
          className="border-t border-surface-border px-5 py-3 text-xs text-ink-faint transition-colors hover:text-ink"
        >
          ← Back to home
        </Link>
      </aside>
      <div className="flex flex-1 flex-col overflow-hidden">
        <header className="flex h-14 shrink-0 items-center justify-between border-b border-surface-border px-6">
          <h1 className="text-sm font-medium text-ink-muted">
            Manufacturing Quality Inspection Co-Pilot
          </h1>
          <span className="hidden items-center gap-2 text-xs text-ink-faint sm:flex">
            <span className="h-1.5 w-1.5 animate-pulseGlow rounded-full bg-status-healthy" />
            system online
          </span>
        </header>
        <main className="flex-1 overflow-auto p-6">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
