import { NavLink, Outlet } from 'react-router-dom'

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
      <aside className="w-60 shrink-0 border-r border-surface-border bg-surface-raised">
        <div className="flex h-14 items-center gap-2 border-b border-surface-border px-5">
          <span className="h-2.5 w-2.5 rounded-sm bg-accent" />
          <span className="text-sm font-semibold tracking-wide">SentinelQ</span>
        </div>
        <nav className="flex flex-col gap-1 p-3">
          {navItems.map((item) =>
            item.ready ? (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) =>
                  `rounded-md px-3 py-2 text-sm transition-colors ${
                    isActive
                      ? 'bg-surface-panel text-ink'
                      : 'text-ink-muted hover:bg-surface-panel hover:text-ink'
                  }`
                }
              >
                {item.label}
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
      </aside>
      <div className="flex flex-1 flex-col overflow-hidden">
        <header className="flex h-14 shrink-0 items-center justify-between border-b border-surface-border px-6">
          <h1 className="text-sm font-medium text-ink-muted">
            Manufacturing Quality Inspection Co-Pilot
          </h1>
        </header>
        <main className="flex-1 overflow-auto p-6">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
