import { useQuery } from '@tanstack/react-query'
import { getReadiness } from '../api/client'

export function HealthPage() {
  const { data, isLoading, isError, refetch, isFetching } = useQuery({
    queryKey: ['readiness'],
    queryFn: getReadiness,
    refetchInterval: 10000,
  })

  return (
    <div className="max-w-2xl">
      <div className="mb-5 flex items-center justify-between">
        <h2 className="text-lg font-semibold">System Status</h2>
        <button
          onClick={() => refetch()}
          className="rounded-md border border-surface-border bg-surface-panel px-3 py-1.5 text-sm text-ink-muted hover:text-ink"
        >
          {isFetching ? 'Refreshing…' : 'Refresh'}
        </button>
      </div>

      {isLoading && <p className="text-ink-muted">Checking backend…</p>}

      {isError && (
        <div className="rounded-lg border border-status-defect/40 bg-status-defect/10 p-4 text-sm text-status-defect">
          Backend unreachable. Is the API running on port 8000?
        </div>
      )}

      {data && (
        <div className="rounded-lg border border-surface-border bg-surface-raised p-5">
          <div className="mb-4 flex items-center gap-3">
            <span
              className={`h-2.5 w-2.5 rounded-full ${
                data.ready ? 'bg-status-healthy' : 'bg-status-defect'
              }`}
            />
            <span className="text-sm font-medium">
              {data.ready ? 'All systems operational' : 'Degraded'}
            </span>
          </div>
          <ul className="divide-y divide-surface-border">
            {Object.entries(data.checks).map(([name, ok]) => (
              <li
                key={name}
                className="flex items-center justify-between py-2.5 text-sm"
              >
                <span className="capitalize text-ink-muted">
                  {name.replace(/_/g, ' ')}
                </span>
                <span className={ok ? 'text-status-healthy' : 'text-status-defect'}>
                  {ok ? 'OK' : 'FAIL'}
                </span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}
