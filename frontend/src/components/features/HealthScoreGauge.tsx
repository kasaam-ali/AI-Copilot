const BAND_COLOR: Record<string, string> = {
  healthy: '#10b981',
  watch: '#f5a623',
  at_risk: '#f97316',
  defect: '#ef4444',
  unknown: '#5b6675',
}

const BAND_LABEL: Record<string, string> = {
  healthy: 'Healthy',
  watch: 'Watch',
  at_risk: 'At risk',
  defect: 'Defect',
  unknown: 'Unknown',
}

function polar(cx: number, cy: number, r: number, angleDeg: number) {
  const a = (angleDeg * Math.PI) / 180
  return { x: cx + r * Math.cos(a), y: cy - r * Math.sin(a) }
}

/** Semicircular arc path from `start`° to `end`° (measured CCW from the +x axis). */
function arc(cx: number, cy: number, r: number, start: number, end: number) {
  const s = polar(cx, cy, r, start)
  const e = polar(cx, cy, r, end)
  const large = Math.abs(end - start) > 180 ? 1 : 0
  // Sweep flag 0 draws clockwise, i.e. from 180° (left) down to 0° (right).
  return `M ${s.x} ${s.y} A ${r} ${r} 0 ${large} 0 ${e.x} ${e.y}`
}

export function HealthScoreGauge({
  score,
  band,
}: {
  score: number | null
  band: string
}) {
  const color = BAND_COLOR[band] ?? BAND_COLOR.unknown
  const width = 240
  const height = 132
  const cx = width / 2
  const cy = 120
  const r = 96
  const fraction = score === null ? 0 : Math.max(0, Math.min(1, score / 100))
  const valueEnd = 180 - fraction * 180

  return (
    <div className="flex flex-col items-center">
      <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`} role="img"
        aria-label={`Health score ${score === null ? 'unknown' : Math.round(score)} of 100, ${BAND_LABEL[band]}`}>
        <path d={arc(cx, cy, r, 180, 0)} fill="none" stroke="#e5e7eb" strokeWidth={14} strokeLinecap="round" />
        {score !== null && (
          <path
            d={arc(cx, cy, r, 180, valueEnd)}
            fill="none"
            stroke={color}
            strokeWidth={14}
            strokeLinecap="round"
          />
        )}
      </svg>
      <div className="-mt-16 flex flex-col items-center">
        <span className="font-mono text-4xl font-semibold tabular-nums text-ink">
          {score === null ? '—' : Math.round(score)}
        </span>
        <span className="text-xs uppercase tracking-wide text-ink-faint">Health score</span>
      </div>
      <span
        className="mt-3 inline-flex items-center gap-2 rounded-full px-3 py-1 text-sm font-medium"
        style={{ color, backgroundColor: `${color}22` }}
      >
        <span className="h-2 w-2 rounded-full" style={{ backgroundColor: color }} />
        {BAND_LABEL[band] ?? band}
      </span>
    </div>
  )
}
