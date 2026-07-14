import { Link, useLocation } from 'react-router-dom'
import type { ImageInspectionResult } from '../api/client'
import { Badge, Card, Stat } from '../components/primitives'
import { ConfidenceMeter } from '../components/features/ConfidenceMeter'
import { GradCamViewer } from '../components/features/GradCamViewer'

export function ResultsPage() {
  const location = useLocation()
  const result = (location.state as { result?: ImageInspectionResult } | null)?.result

  if (!result) {
    return (
      <div className="max-w-2xl">
        <p className="text-ink-muted">
          No inspection to show.{' '}
          <Link to="/inspect" className="text-accent">
            Run an inspection.
          </Link>
        </p>
      </div>
    )
  }

  const isDefect = result.label === 'defect'

  return (
    <div className="max-w-4xl">
      <div className="mb-5 flex items-center justify-between">
        <h2 className="text-lg font-semibold">Inspection #{result.inspection_id}</h2>
        <Badge color={isDefect ? 'defect' : 'healthy'}>
          {isDefect ? 'Defect detected' : 'No defect'}
        </Badge>
      </div>

      <div className="mb-5 grid grid-cols-3 gap-4">
        <Stat label="Prediction" value={<span className="capitalize">{result.label}</span>} />
        <Stat
          label="Defect probability"
          value={`${(result.defect_probability * 100).toFixed(1)}%`}
        />
        <Stat
          label="Inference"
          value={`${result.inference_ms} ms`}
          sub={`model ${result.model_version}`}
        />
      </div>

      <div className="grid grid-cols-1 gap-5 md:grid-cols-2">
        <Card className="p-5">
          <GradCamViewer src={result.gradcam_url} label={result.label} />
        </Card>
        <Card className="p-5">
          <div className="mb-4">
            <ConfidenceMeter confidence={result.confidence} uncertainty={result.uncertainty} />
          </div>
          <div className="mb-2 text-sm font-medium text-ink">Class probabilities</div>
          <ul className="space-y-2">
            {Object.entries(result.class_probs).map(([name, probability]) => (
              <li key={name} className="flex items-center justify-between text-sm">
                <span className="capitalize text-ink-muted">{name}</span>
                <span className="font-mono tabular-nums">{(probability * 100).toFixed(1)}%</span>
              </li>
            ))}
          </ul>
          <div className="mt-4 break-all border-t border-surface-border pt-3 text-xs text-ink-faint">
            weights {result.weights_sha256.slice(0, 16)}…
          </div>
        </Card>
      </div>

      <div className="mt-5">
        <Link to="/inspect" className="text-sm text-accent">
          ← Inspect another
        </Link>
      </div>
    </div>
  )
}
