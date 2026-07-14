import type { ButtonHTMLAttributes, ReactNode } from 'react'

export function Card({
  children,
  className = '',
}: {
  children: ReactNode
  className?: string
}) {
  return (
    <div className={`rounded-lg border border-surface-border bg-surface-raised ${className}`}>
      {children}
    </div>
  )
}

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: 'primary' | 'ghost'
}

export function Button({ children, className = '', variant = 'primary', ...props }: ButtonProps) {
  const base =
    'inline-flex items-center justify-center rounded-md px-4 py-2 text-sm font-medium transition-colors disabled:cursor-not-allowed disabled:opacity-50'
  const styles =
    variant === 'primary'
      ? 'bg-accent text-surface hover:bg-accent/90'
      : 'border border-surface-border bg-surface-panel text-ink-muted hover:text-ink'
  return (
    <button className={`${base} ${styles} ${className}`} {...props}>
      {children}
    </button>
  )
}

type BadgeColor = 'healthy' | 'watch' | 'risk' | 'defect' | 'neutral'

export function Badge({ children, color = 'neutral' }: { children: ReactNode; color?: BadgeColor }) {
  const map: Record<BadgeColor, string> = {
    healthy: 'bg-status-healthy/15 text-status-healthy',
    watch: 'bg-status-watch/15 text-status-watch',
    risk: 'bg-status-risk/15 text-status-risk',
    defect: 'bg-status-defect/15 text-status-defect',
    neutral: 'bg-surface-panel text-ink-muted',
  }
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${map[color]}`}
    >
      {children}
    </span>
  )
}

export function Stat({
  label,
  value,
  sub,
}: {
  label: string
  value: ReactNode
  sub?: ReactNode
}) {
  return (
    <div className="rounded-lg border border-surface-border bg-surface-panel p-4">
      <div className="text-xs uppercase tracking-wide text-ink-faint">{label}</div>
      <div className="mt-1 font-mono text-2xl tabular-nums text-ink">{value}</div>
      {sub && <div className="mt-0.5 text-xs text-ink-muted">{sub}</div>}
    </div>
  )
}
