import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { getInspections, type InspectionSummary } from '../api/client'
import { Badge, Card } from '../components/primitives'

export const STATUS_BADGE: Record<string, 'healthy' | 'watch' | 'risk' | 'defect' | 'neutral'> = {
  pending_review: 'watch',
  approved: 'healthy',
  rejected: 'defect',
  modified: 'risk',
  processing: 'neutral',
  failed: 'defect',
}

const CATEGORY_LABEL: Record<string, string> = {
  image: 'Vision',
  tabular: 'Process',
  timeseries: 'Machine',
  session: 'Multimodal',
}

function statusText(status: string) {
  return status.replace(/_/g, ' ')
}

function Row({ item }: { item: InspectionSummary }) {
  const navigate = useNavigate()
  const uncertainty = item.max_uncertainty
  return (
    <tr
      onClick={() => navigate(`/review/${item.id}`)}
      className="cursor-pointer border-t border-surface-border hover:bg-surface-panel"
    >
      <td className="px-4 py-3 font-mono text-sm text-ink">#{item.id}</td>
      <td className="px-4 py-3 text-sm text-ink-muted">
        {CATEGORY_LABEL[item.category ?? ''] ?? item.category ?? '—'}
      </td>
      <td className="px-4 py-3">
        <Badge color={STATUS_BADGE[item.status] ?? 'neutral'}>{statusText(item.status)}</Badge>
      </td>
      <td className="px-4 py-3 text-sm">
        {item.health_score !== null ? (
          <span className="font-mono tabular-nums text-ink">{Math.round(item.health_score)}</span>
        ) : item.label ? (
          <span className="capitalize text-ink-muted">{item.label}</span>
        ) : (
          <span className="text-ink-faint">—</span>
        )}
      </td>
      <td className="px-4 py-3">
        {uncertainty !== null ? (
          <div className="flex items-center gap-2">
            <div className="h-1.5 w-24 overflow-hidden rounded-full bg-surface-panel">
              <div
                className="h-full rounded-full bg-accent"
                style={{ width: `${Math.min(100, uncertainty * 100 * 3)}%` }}
              />
            </div>
            <span className="font-mono text-xs tabular-nums text-ink-faint">
              {(uncertainty * 100).toFixed(1)}%
            </span>
          </div>
        ) : (
          <span className="text-ink-faint">—</span>
        )}
      </td>
      <td className="px-4 py-3 text-xs text-ink-faint">
        {new Date(item.created_at).toLocaleString()}
      </td>
    </tr>
  )
}

export function ReviewQueuePage() {
  const [sort, setSort] = useState<'uncertainty' | 'recent'>('uncertainty')
  const { data, isLoading, isError } = useQuery({
    queryKey: ['inspections', sort],
    queryFn: () => getInspections(sort),
  })

  return (
    <div className="max-w-4xl">
      <div className="mb-1 flex items-center justify-between">
        <h2 className="text-lg font-semibold">Review queue</h2>
        <div className="flex items-center gap-1 text-xs">
          {(['uncertainty', 'recent'] as const).map((option) => (
            <button
              key={option}
              onClick={() => setSort(option)}
              className={`rounded-md px-2.5 py-1 capitalize transition-colors ${
                sort === option
                  ? 'bg-surface-panel text-ink'
                  : 'text-ink-muted hover:text-ink'
              }`}
            >
              {option === 'uncertainty' ? 'Most uncertain' : 'Most recent'}
            </button>
          ))}
        </div>
      </div>
      <p className="mb-5 text-sm text-ink-muted">
        Least-confident predictions first — review, then approve, reject or correct.
      </p>

      {isLoading && <p className="text-sm text-ink-muted">Loading queue…</p>}
      {isError && <p className="text-sm text-status-defect">Could not load the queue.</p>}
      {data && data.length === 0 && (
        <p className="text-sm text-ink-muted">No inspections yet. Run one from Inspect.</p>
      )}
      {data && data.length > 0 && (
        <Card className="overflow-hidden">
          <table className="w-full">
            <thead>
              <tr className="text-left text-xs uppercase tracking-wide text-ink-faint">
                <th className="px-4 py-3 font-medium">ID</th>
                <th className="px-4 py-3 font-medium">Type</th>
                <th className="px-4 py-3 font-medium">Status</th>
                <th className="px-4 py-3 font-medium">Result</th>
                <th className="px-4 py-3 font-medium">Uncertainty</th>
                <th className="px-4 py-3 font-medium">Time</th>
              </tr>
            </thead>
            <tbody>
              {data.map((item) => (
                <Row key={item.id} item={item} />
              ))}
            </tbody>
          </table>
        </Card>
      )}
    </div>
  )
}
