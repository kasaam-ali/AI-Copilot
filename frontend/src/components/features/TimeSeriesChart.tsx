import { useQuery } from '@tanstack/react-query'
import { getTimeseriesExplanation } from '../../api/client'

// Diverging scale, neutral midpoint: green raises remaining life, red shortens it.
function cellColor(value: number, max: number): string {
  if (max <= 0) return '#eef1f4'
  const intensity = Math.min(1, Math.abs(value) / max)
  const alpha = 0.12 + intensity * 0.78
  const hex = value >= 0 ? '16,185,129' : '239,68,68'
  return `rgba(${hex},${alpha.toFixed(3)})`
}

export function TimeSeriesChart({ predictionId }: { predictionId: number }) {
  const { data, isLoading, isError } = useQuery({
    queryKey: ['ts-explain', predictionId],
    queryFn: () => getTimeseriesExplanation(predictionId),
  })

  if (isLoading) return <p className="text-sm text-ink-muted">Loading attributions…</p>
  if (isError || !data)
    return <p className="text-sm text-status-defect">Attributions unavailable.</p>

  const { sensors, attributions } = data
  const steps = attributions.length
  const max = Math.max(
    ...attributions.flat().map((v) => Math.abs(v)),
    1e-6,
  )

  return (
    <div>
      <div className="mb-3 text-sm font-medium text-ink">
        Sensor attributions over time (Integrated Gradients)
      </div>
      <div className="overflow-x-auto">
        <div className="min-w-[420px]">
          {sensors.map((sensor, sIdx) => (
            <div key={sensor} className="mb-1 flex items-center gap-2">
              <span className="w-28 shrink-0 truncate text-right text-[11px] capitalize text-ink-muted">
                {sensor.replace(/_/g, ' ')}
              </span>
              <div className="flex flex-1 gap-px">
                {Array.from({ length: steps }).map((_, tIdx) => (
                  <div
                    key={tIdx}
                    className="h-4 flex-1 rounded-[1px]"
                    style={{ backgroundColor: cellColor(attributions[tIdx][sIdx], max) }}
                    title={`${sensor} @ t${tIdx}: ${attributions[tIdx][sIdx].toFixed(4)}`}
                  />
                ))}
              </div>
            </div>
          ))}
          <div className="mt-1 flex items-center gap-2">
            <span className="w-28 shrink-0" />
            <div className="flex flex-1 justify-between text-[10px] text-ink-faint">
              <span>oldest</span>
              <span>most recent →</span>
            </div>
          </div>
        </div>
      </div>
      <div className="mt-3 flex items-center gap-4 text-[10px] text-ink-faint">
        <span className="flex items-center gap-1">
          <span className="h-2 w-3 rounded-sm bg-status-healthy" /> extends life
        </span>
        <span className="flex items-center gap-1">
          <span className="h-2 w-3 rounded-sm bg-status-defect" /> shortens life
        </span>
      </div>
    </div>
  )
}
