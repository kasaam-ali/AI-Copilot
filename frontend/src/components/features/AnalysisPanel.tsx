import { useMutation } from '@tanstack/react-query'
import { analyzeInspection, type AnalyzeResult } from '../../api/client'
import { Badge, Button, Card } from '../primitives'

function ProviderChain({ result }: { result: AnalyzeResult }) {
  return (
    <div className="mt-4 flex flex-wrap items-center gap-2 border-t border-surface-border pt-3 text-xs">
      <span className="text-ink-faint">Provider:</span>
      <Badge color={result.provider_used === 'mock' ? 'neutral' : 'healthy'}>
        {result.provider_used}
        {result.model ? ` · ${result.model}` : ''}
      </Badge>
      <span className="text-ink-faint">
        {result.attempts.map((a) => `${a.provider}${a.ok ? ' ✓' : ' ✗'}`).join('  →  ')}
      </span>
    </div>
  )
}

export function AnalysisPanel({ inspectionId }: { inspectionId: number }) {
  const mutation = useMutation({ mutationFn: () => analyzeInspection(inspectionId) })
  const result = mutation.data

  return (
    <Card className="p-6">
      <div className="mb-3 flex items-center justify-between">
        <h3 className="text-base font-semibold">AI analysis &amp; report</h3>
        <div className="flex items-center gap-2">
          <a
            href={`/api/v1/reports/${inspectionId}/download?format=pdf`}
            className="rounded-md border border-surface-border bg-surface-panel px-3 py-1.5 text-xs text-ink-muted hover:text-ink"
          >
            Download PDF
          </a>
          <a
            href={`/api/v1/reports/${inspectionId}/download?format=docx`}
            className="rounded-md border border-surface-border bg-surface-panel px-3 py-1.5 text-xs text-ink-muted hover:text-ink"
          >
            Download DOCX
          </a>
        </div>
      </div>

      {!result && (
        <>
          <p className="mb-4 text-sm text-ink-muted">
            Generate a grounded root-cause narrative from the model outputs. Works offline
            (falls back to a deterministic summary if no LLM provider is reachable).
          </p>
          <Button onClick={() => mutation.mutate()} disabled={mutation.isPending}>
            {mutation.isPending ? 'Analyzing…' : 'Explain with AI'}
          </Button>
        </>
      )}

      {mutation.isError && (
        <p className="mt-3 text-sm text-status-defect">Analysis failed. Is the backend running?</p>
      )}

      {result && (
        <div>
          <div className="mb-3">
            <div className="text-xs uppercase tracking-wide text-ink-faint">Root cause</div>
            <p className="mt-1 text-sm text-ink">{result.root_cause}</p>
          </div>
          {result.contributing_factors.length > 0 && (
            <div className="mb-3">
              <div className="text-xs uppercase tracking-wide text-ink-faint">
                Contributing factors
              </div>
              <ul className="mt-1 list-disc space-y-1 pl-5 text-sm text-ink-muted">
                {result.contributing_factors.map((factor) => (
                  <li key={factor}>{factor}</li>
                ))}
              </ul>
            </div>
          )}
          {result.recommendations.length > 0 && (
            <div className="mb-3">
              <div className="text-xs uppercase tracking-wide text-ink-faint">Recommendations</div>
              <ul className="mt-1 list-disc space-y-1 pl-5 text-sm text-ink-muted">
                {result.recommendations.map((rec) => (
                  <li key={rec}>{rec}</li>
                ))}
              </ul>
            </div>
          )}
          <p className="text-xs italic text-ink-faint">{result.confidence_note}</p>
          <ProviderChain result={result} />
          <button
            onClick={() => mutation.mutate()}
            disabled={mutation.isPending}
            className="mt-3 text-xs text-accent hover:underline"
          >
            {mutation.isPending ? 'Regenerating…' : 'Regenerate'}
          </button>
        </div>
      )}
    </Card>
  )
}
