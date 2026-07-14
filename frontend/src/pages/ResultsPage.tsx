import { Link, useLocation } from 'react-router-dom'
import type { ImageInspectionResult, TabularInspectionResult } from '../api/client'
import { Badge, Card, Stat } from '../components/primitives'
import { ConfidenceMeter } from '../components/features/ConfidenceMeter'
import { GradCamViewer } from '../components/features/GradCamViewer'
import { ShapBarChart } from '../components/features/ShapBarChart'

interface ResultsState {
  image?: ImageInspectionResult
  tabular?: TabularInspectionResult
}

function ImageResultCard({ result }: { result: ImageInspectionResult }) {
  const isDefect = result.label === 'defect'
  return (
    <section>
      <div className="mb-4 flex items-center justify-between">
        <h3 className="text-base font-semibold">Vision inspection</h3>
        <Badge color={isDefect ? 'defect' : 'healthy'}>
          {isDefect ? 'Defect detected' : 'No defect'}
        </Badge>
      </div>
      <div className="mb-4 grid grid-cols-3 gap-4">
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
          <ConfidenceMeter confidence={result.confidence} uncertainty={result.uncertainty} />
          <div className="mt-4 mb-2 text-sm font-medium text-ink">Class probabilities</div>
          <ul className="space-y-2">
            {Object.entries(result.class_probs).map(([name, probability]) => (
              <li key={name} className="flex items-center justify-between text-sm">
                <span className="capitalize text-ink-muted">{name}</span>
                <span className="font-mono tabular-nums">{(probability * 100).toFixed(1)}%</span>
              </li>
            ))}
          </ul>
        </Card>
      </div>
    </section>
  )
}

function TabularResultCard({ result }: { result: TabularInspectionResult }) {
  const isDefect = result.label === 'defect'
  return (
    <section>
      <div className="mb-4 flex items-center justify-between">
        <h3 className="text-base font-semibold">Process-data inspection</h3>
        <Badge color={isDefect ? 'defect' : 'healthy'}>
          {isDefect ? 'Likely defect' : 'Within tolerance'}
        </Badge>
      </div>
      <div className="mb-4 grid grid-cols-3 gap-4">
        <Stat
          label="Defect probability"
          value={`${(result.defect_probability * 100).toFixed(1)}%`}
        />
        <Stat label="Prediction" value={<span className="uppercase">{result.label}</span>} />
        <Stat
          label="Inference"
          value={`${result.inference_ms} ms`}
          sub={`model ${result.model_version}`}
        />
      </div>
      <div className="grid grid-cols-1 gap-5 md:grid-cols-2">
        <Card className="p-5">
          <ShapBarChart contributions={result.shap} />
        </Card>
        <Card className="p-5">
          <ConfidenceMeter confidence={result.confidence} uncertainty={result.uncertainty} />
          <div className="mt-4 break-all border-t border-surface-border pt-3 text-xs text-ink-faint">
            weights {result.weights_sha256.slice(0, 16)}…
          </div>
        </Card>
      </div>
    </section>
  )
}

export function ResultsPage() {
  const location = useLocation()
  const state = (location.state as ResultsState | null) ?? {}
  const hasResult = state.image || state.tabular

  if (!hasResult) {
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

  const inspectionId = state.image?.inspection_id ?? state.tabular?.inspection_id

  return (
    <div className="max-w-4xl">
      <h2 className="mb-5 text-lg font-semibold">Inspection #{inspectionId}</h2>
      <div className="space-y-8">
        {state.image && <ImageResultCard result={state.image} />}
        {state.tabular && <TabularResultCard result={state.tabular} />}
      </div>
      <div className="mt-6">
        <Link to="/inspect" className="text-sm text-accent">
          ← Inspect another
        </Link>
      </div>
    </div>
  )
}
