import type { ShapContribution } from '../../api/client'

export function ShapBarChart({ contributions }: { contributions: ShapContribution[] }) {
  const max = Math.max(...contributions.map((c) => Math.abs(c.contribution)), 1e-6)

  return (
    <div>
      <div className="mb-3 text-sm font-medium text-ink">Feature contributions (SHAP)</div>
      <div className="space-y-2">
        {contributions.map((item) => {
          const width = (Math.abs(item.contribution) / max) * 50
          const raisesRisk = item.contribution >= 0
          return (
            <div key={item.feature} className="text-xs">
              <div className="mb-0.5 flex items-center justify-between">
                <span className="capitalize text-ink-muted">
                  {item.feature.replace(/_/g, ' ')}
                </span>
                <span className="font-mono tabular-nums text-ink-faint">{item.value}</span>
              </div>
              <div className="relative h-3 rounded bg-surface-panel">
                <div className="absolute left-1/2 top-0 h-full w-px bg-surface-border" />
                <div
                  className={`absolute top-0 h-full ${
                    raisesRisk ? 'bg-status-defect' : 'bg-status-healthy'
                  }`}
                  style={
                    raisesRisk
                      ? { left: '50%', width: `${width}%` }
                      : { right: '50%', width: `${width}%` }
                  }
                />
              </div>
            </div>
          )
        })}
      </div>
      <div className="mt-2 flex justify-between text-[10px] text-ink-faint">
        <span>← lowers defect risk</span>
        <span>raises defect risk →</span>
      </div>
    </div>
  )
}
