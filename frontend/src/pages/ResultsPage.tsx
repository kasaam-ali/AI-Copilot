import { Link, useLocation } from 'react-router-dom'
import type {
  HealthDriver,
  ImageInspectionResult,
  SessionInspectionResult,
  TabularInspectionResult,
  TimeSeriesInspectionResult,
} from '../api/client'
import { Badge, Card, Stat } from '../components/primitives'
import { ConfidenceMeter } from '../components/features/ConfidenceMeter'
import { GradCamViewer } from '../components/features/GradCamViewer'
import { ShapBarChart } from '../components/features/ShapBarChart'
import { HealthScoreGauge } from '../components/features/HealthScoreGauge'
import { TimeSeriesChart } from '../components/features/TimeSeriesChart'

interface ResultsState {
  image?: ImageInspectionResult
  tabular?: TabularInspectionResult
  timeseries?: TimeSeriesInspectionResult
  session?: SessionInspectionResult
}

const TS_BADGE: Record<string, 'healthy' | 'watch' | 'risk' | 'defect'> = {
  healthy: 'healthy',
  monitor: 'watch',
  degrading: 'risk',
  critical: 'defect',
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

function TimeSeriesResultCard({ result }: { result: TimeSeriesInspectionResult }) {
  const rulPct = Math.round((result.rul / result.rul_cap) * 100)
  return (
    <section>
      <div className="mb-4 flex items-center justify-between">
        <h3 className="text-base font-semibold">Machine health (time-series)</h3>
        <Badge color={TS_BADGE[result.label] ?? 'watch'}>
          <span className="capitalize">{result.label}</span>
        </Badge>
      </div>
      <div className="mb-4 grid grid-cols-3 gap-4">
        <Stat
          label="Remaining life"
          value={`${result.rul.toFixed(0)}`}
          sub={`of ${result.rul_cap} cycles (${rulPct}%)`}
        />
        <Stat label="Failure risk" value={`${(result.risk * 100).toFixed(0)}%`} />
        <Stat
          label="Inference"
          value={`${result.inference_ms} ms`}
          sub={`model ${result.model_version}`}
        />
      </div>
      <div className="grid grid-cols-1 gap-5 md:grid-cols-2">
        <Card className="p-5">
          <TimeSeriesChart predictionId={result.prediction_id} />
        </Card>
        <Card className="p-5">
          <ConfidenceMeter confidence={result.confidence} uncertainty={result.uncertainty} />
          <div className="mt-4 mb-2 text-sm font-medium text-ink">Top sensor drivers</div>
          <ul className="space-y-2">
            {result.sensor_importance.slice(0, 5).map((item) => (
              <li key={item.sensor} className="flex items-center justify-between text-sm">
                <span className="capitalize text-ink-muted">
                  {item.sensor.replace(/_/g, ' ')}
                </span>
                <span
                  className={`font-mono tabular-nums ${
                    item.importance >= 0 ? 'text-status-healthy' : 'text-status-defect'
                  }`}
                >
                  {item.importance >= 0 ? '+' : ''}
                  {item.importance.toFixed(2)}
                </span>
              </li>
            ))}
          </ul>
        </Card>
      </div>
    </section>
  )
}

const MODALITY_LABEL: Record<string, string> = {
  image: 'Vision',
  tabular: 'Process data',
  timeseries: 'Machine health',
}

function HealthSummary({ session }: { session: SessionInspectionResult }) {
  return (
    <Card className="p-6">
      <div className="grid grid-cols-1 items-center gap-6 md:grid-cols-[auto,1fr]">
        <HealthScoreGauge score={session.health_score} band={session.health_band} />
        <div>
          <div className="mb-3 text-sm font-medium text-ink">Contribution by modality</div>
          <div className="space-y-3">
            {session.drivers.map((driver: HealthDriver) => (
              <div key={driver.modality}>
                <div className="mb-1 flex items-center justify-between text-xs">
                  <span className="text-ink-muted">
                    {MODALITY_LABEL[driver.modality] ?? driver.modality}
                  </span>
                  <span className="font-mono tabular-nums text-ink-faint">
                    risk {(driver.risk * 100).toFixed(0)}% · weight {driver.weight.toFixed(2)}
                  </span>
                </div>
                <div className="h-2 overflow-hidden rounded-full bg-surface-panel">
                  <div
                    className="h-full rounded-full bg-accent"
                    style={{ width: `${Math.round(driver.share * 100)}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
          {Object.keys(session.errors).length > 0 && (
            <div className="mt-4 rounded-md border border-status-defect/30 bg-status-defect/10 p-3 text-xs text-status-defect">
              {Object.entries(session.errors).map(([modality, message]) => (
                <div key={modality}>
                  {MODALITY_LABEL[modality] ?? modality} unavailable: {message}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </Card>
  )
}

export function ResultsPage() {
  const location = useLocation()
  const state = (location.state as ResultsState | null) ?? {}
  const session = state.session
  const image = session?.image ?? state.image
  const tabular = session?.tabular ?? state.tabular
  const timeseries = session?.timeseries ?? state.timeseries
  const hasResult = session || image || tabular || timeseries

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

  const inspectionId =
    session?.inspection_id ??
    image?.inspection_id ??
    tabular?.inspection_id ??
    timeseries?.inspection_id

  return (
    <div className="max-w-4xl">
      <h2 className="mb-5 text-lg font-semibold">Inspection #{inspectionId}</h2>
      <div className="space-y-8">
        {session && <HealthSummary session={session} />}
        {image && <ImageResultCard result={image} />}
        {tabular && <TabularResultCard result={tabular} />}
        {timeseries && <TimeSeriesResultCard result={timeseries} />}
      </div>
      <div className="mt-6">
        <Link to="/inspect" className="text-sm text-accent">
          ← Inspect another
        </Link>
      </div>
    </div>
  )
}
