import type { ButtonHTMLAttributes, ReactNode } from 'react'

export function Card({
  children,
  className = '',
  hover = false,
}: {
  children: ReactNode
  className?: string
  hover?: boolean
}) {
  return (
    <div
      className={`rounded-xl border border-surface-border bg-surface-raised shadow-lg shadow-black/20 ${
        hover ? 'transition-colors hover:border-brand/40' : ''
      } ${className}`}
    >
      {children}
    </div>
  )
}

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: 'primary' | 'ghost'
}

export function Button({ children, className = '', variant = 'primary', ...props }: ButtonProps) {
  const base =
    'inline-flex cursor-pointer items-center justify-center rounded-lg px-4 py-2 text-sm font-semibold transition-all disabled:cursor-not-allowed disabled:opacity-50'
  const styles =
    variant === 'primary'
      ? 'bg-brand text-surface hover:bg-brand-glow hover:shadow-md hover:shadow-brand/20'
      : 'border border-surface-border bg-surface-panel text-ink-muted hover:border-ink-faint hover:text-ink'
  return (
    <button className={`${base} ${styles} ${className}`} {...props}>
      {children}
    </button>
  )
}

type BadgeColor = 'healthy' | 'watch' | 'risk' | 'defect' | 'neutral' | 'brand'

export function Badge({ children, color = 'neutral' }: { children: ReactNode; color?: BadgeColor }) {
  const map: Record<BadgeColor, string> = {
    healthy: 'bg-status-healthy/15 text-status-healthy',
    watch: 'bg-status-watch/15 text-status-watch',
    risk: 'bg-status-risk/15 text-status-risk',
    defect: 'bg-status-defect/15 text-status-defect',
    neutral: 'bg-surface-panel text-ink-muted',
    brand: 'bg-brand/15 text-brand-glow',
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
    <div className="rounded-xl border border-surface-border bg-surface-panel p-4">
      <div className="text-xs uppercase tracking-wide text-ink-faint">{label}</div>
      <div className="mt-1 font-mono text-2xl tabular-nums text-ink">{value}</div>
      {sub && <div className="mt-0.5 text-xs text-ink-muted">{sub}</div>}
    </div>
  )
}

export function PageHeader({ title, subtitle }: { title: string; subtitle?: string }) {
  return (
    <div className="mb-6">
      <div className="flex items-center gap-2.5">
        <span className="h-4 w-1 rounded-full bg-gradient-to-b from-brand to-accent" />
        <h2 className="text-xl font-semibold tracking-tight">{title}</h2>
      </div>
      {subtitle && <p className="mt-1.5 pl-3.5 text-sm text-ink-muted">{subtitle}</p>}
    </div>
  )
}
