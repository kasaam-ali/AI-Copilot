import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  activateVersion,
  getModelVersions,
  getRetrainJob,
  startRetrain,
  type RetrainJob,
} from '../api/client'
import { Badge, Button, Card, Stat } from '../components/primitives'

const MODEL_TYPE = 'tabular'

function MetricsDiff({ job }: { job: RetrainJob }) {
  const { auroc_old, auroc_new, delta, eval_size } = job.metrics
  const improved = (delta ?? 0) >= 0
  return (
    <div className="mt-4 grid grid-cols-3 gap-4">
      <Stat label="Current AUROC" value={auroc_old !== undefined ? auroc_old.toFixed(3) : '—'} />
      <Stat
        label="Retrained AUROC"
        value={auroc_new !== undefined ? auroc_new.toFixed(3) : '—'}
        sub={`held-out ${eval_size ?? '—'} samples`}
      />
      <Stat
        label="Δ AUROC"
        value={
          <span className={improved ? 'text-status-healthy' : 'text-status-defect'}>
            {delta === null || delta === undefined ? '—' : `${delta >= 0 ? '+' : ''}${delta.toFixed(3)}`}
          </span>
        }
      />
    </div>
  )
}

export function ModelsPage() {
  const queryClient = useQueryClient()
  const [jobId, setJobId] = useState<number | null>(null)

  const versionsQuery = useQuery({
    queryKey: ['models', MODEL_TYPE],
    queryFn: () => getModelVersions(MODEL_TYPE),
  })

  const jobQuery = useQuery({
    queryKey: ['retrain-job', jobId],
    queryFn: () => getRetrainJob(jobId as number),
    enabled: jobId !== null,
    refetchInterval: (query) => {
      const status = query.state.data?.status
      return status === 'succeeded' || status === 'failed' ? false : 1200
    },
  })

  const retrain = useMutation({
    mutationFn: () => startRetrain(MODEL_TYPE),
    onSuccess: (job) => setJobId(job.id),
  })

  const activate = useMutation({
    mutationFn: (version: string) => activateVersion(MODEL_TYPE, version),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['models', MODEL_TYPE] }),
  })

  const job = jobQuery.data
  const running = job && (job.status === 'queued' || job.status === 'running')

  // Refresh the version list once a job finishes.
  if (job?.status === 'succeeded' && versionsQuery.data && job.new_version) {
    if (!versionsQuery.data.versions.some((v) => v.version === job.new_version)) {
      queryClient.invalidateQueries({ queryKey: ['models', MODEL_TYPE] })
    }
  }

  return (
    <div className="max-w-3xl">
      <h2 className="mb-1 text-lg font-semibold">Models &amp; retraining</h2>
      <p className="mb-5 text-sm text-ink-muted">
        Inspector corrections retrain a new version of the process-data model. The new version
        is registered inactive with a metrics comparison — you decide whether to promote it.
      </p>

      <Card className="mb-6 p-6">
        <div className="flex items-center justify-between">
          <div>
            <div className="text-sm font-medium text-ink">Active-learning retrain</div>
            <div className="text-xs text-ink-muted">
              Assembles original data + your corrections (oversampled), trains, and evaluates.
            </div>
          </div>
          <Button onClick={() => retrain.mutate()} disabled={retrain.isPending || !!running}>
            {running ? 'Retraining…' : 'Retrain from feedback'}
          </Button>
        </div>

        {retrain.isError && (
          <p className="mt-3 text-sm text-status-defect">
            {(retrain.error as { response?: { data?: { detail?: string } } })?.response?.data
              ?.detail ?? 'Retrain could not start (collect a correction first).'}
          </p>
        )}

        {job && (
          <div className="mt-5">
            <div className="mb-1 flex items-center justify-between text-xs">
              <span className="text-ink-muted">
                Job #{job.id} · {job.status} · {job.num_corrections} corrections ·{' '}
                {job.num_samples} samples
              </span>
              <span className="font-mono tabular-nums text-ink-faint">{job.progress}%</span>
            </div>
            <div className="h-2 overflow-hidden rounded-full bg-surface-panel">
              <div
                className={`h-full rounded-full ${
                  job.status === 'failed' ? 'bg-status-defect' : 'bg-accent'
                }`}
                style={{ width: `${job.progress}%` }}
              />
            </div>
            {job.status === 'failed' && (
              <p className="mt-2 text-sm text-status-defect">{job.message}</p>
            )}
            {job.status === 'succeeded' && (
              <>
                <MetricsDiff job={job} />
                {job.new_version && (
                  <div className="mt-4">
                    <Button onClick={() => activate.mutate(job.new_version as string)} disabled={activate.isPending}>
                      Activate {job.new_version}
                    </Button>
                  </div>
                )}
              </>
            )}
          </div>
        )}
      </Card>

      <h3 className="mb-3 text-base font-semibold">Versions</h3>
      {versionsQuery.data && (
        <Card className="overflow-hidden">
          <table className="w-full">
            <thead>
              <tr className="text-left text-xs uppercase tracking-wide text-ink-faint">
                <th className="px-4 py-3 font-medium">Version</th>
                <th className="px-4 py-3 font-medium">Status</th>
                <th className="px-4 py-3 font-medium">Metrics</th>
                <th className="px-4 py-3 font-medium" />
              </tr>
            </thead>
            <tbody>
              {versionsQuery.data.versions.map((version) => {
                const metrics = version.metrics as {
                  test?: { auroc?: number }
                  retrain?: { auroc_new?: number }
                }
                const auroc = metrics.test?.auroc ?? metrics.retrain?.auroc_new
                return (
                  <tr key={version.version} className="border-t border-surface-border">
                    <td className="px-4 py-3 font-mono text-sm text-ink">{version.version}</td>
                    <td className="px-4 py-3">
                      {version.is_active ? (
                        <Badge color="healthy">active</Badge>
                      ) : (
                        <Badge color="neutral">inactive</Badge>
                      )}
                    </td>
                    <td className="px-4 py-3 text-sm text-ink-muted">
                      {auroc !== undefined ? `AUROC ${auroc.toFixed(3)}` : '—'}
                    </td>
                    <td className="px-4 py-3 text-right">
                      {!version.is_active && (
                        <button
                          onClick={() => activate.mutate(version.version)}
                          disabled={activate.isPending}
                          className="text-sm text-accent hover:underline"
                        >
                          Activate
                        </button>
                      )}
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </Card>
      )}
    </div>
  )
}
