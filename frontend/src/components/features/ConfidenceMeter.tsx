export function ConfidenceMeter({
  confidence,
  uncertainty,
}: {
  confidence: number
  uncertainty: number
}) {
  const pct = Math.round(confidence * 100)
  return (
    <div>
      <div className="mb-1 flex items-center justify-between text-xs text-ink-muted">
        <span>Confidence</span>
        <span className="font-mono tabular-nums text-ink">{pct}%</span>
      </div>
      <div className="h-2 w-full overflow-hidden rounded-full bg-surface-panel">
        <div className="h-full rounded-full bg-accent" style={{ width: `${pct}%` }} />
      </div>
      <div className="mt-1 text-xs text-ink-faint">
        ± {(uncertainty * 100).toFixed(1)}% uncertainty (MC-Dropout)
      </div>
    </div>
  )
}
