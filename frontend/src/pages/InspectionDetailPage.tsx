import { Link, useParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import {
  getInspection,
  getShapExplanation,
  type PredictionSummary,
} from '../api/client'
import { Badge, Card, Stat } from '../components/primitives'
import { ConfidenceMeter } from '../components/features/ConfidenceMeter'
import { GradCamViewer } from '../components/features/GradCamViewer'
import { ShapBarChart } from '../components/features/ShapBarChart'
import { TimeSeriesChart } from '../components/features/TimeSeriesChart'
import { HealthScoreGauge } from '../components/features/HealthScoreGauge'
import { DecisionButtons } from '../components/features/DecisionButtons'
import { STATUS_BADGE } from './ReviewQueuePage'

const MODEL_TITLE: Record<string, string> = {
  image: 'Vision (CNN + Grad-CAM)',
  tabular: 'Process data (ANN + SHAP)',
  timeseries: 'Machine health (LSTM + Integrated Gradients)',
}

function TabularEvidence({ predictionId }: { predictionId: number }) {
  const { data, isLoading } = useQuery({
    queryKey: ['shap', predictionId],
    queryFn: () => getShapExplanation(predictionId),
  })
  if (isLoading) return <p className="text-sm text-ink-muted">Loading SHAP…</p>
  if (!data) return <p className="text-sm text-status-defect">SHAP unavailable.</p>
  return <ShapBarChart contributions={data.shap.slice(0, 8)} />
}

function EvidenceCard({ prediction }: { prediction: PredictionSummary }) {
  return (
    <section>
      <div className="mb-3 flex items-center justify-between">
        <h3 className="text-base font-semibold">{MODEL_TITLE[prediction.model_type] ?? prediction.model_type}</h3>
        {prediction.label && (
          <Badge color={prediction.label === 'defect' ? 'defect' : 'healthy'}>
            <span className="capitalize">{prediction.label}</span>
          </Badge>
        )}
      </div>
      <div className="grid grid-cols-1 gap-5 md:grid-cols-2">
        <Card className="p-5">
          {prediction.model_type === 'image' && prediction.gradcam_url && (
            <GradCamViewer src={prediction.gradcam_url} label={prediction.label ?? ''} />
          )}
          {prediction.model_type === 'tabular' && (
            <TabularEvidence predictionId={prediction.prediction_id} />
          )}
          {prediction.model_type === 'timeseries' && (
            <TimeSeriesChart predictionId={prediction.prediction_id} />
          )}
        </Card>
        <Card className="p-5">
          {prediction.confidence !== null && prediction.uncertainty !== null && (
            <ConfidenceMeter
              confidence={prediction.confidence}
              uncertainty={prediction.uncertainty}
            />
          )}
          <div className="mt-4 border-t border-surface-border pt-3 text-xs text-ink-faint">
            model {prediction.model_version}
            {prediction.inference_ms !== null && <> · {prediction.inference_ms} ms</>}
          </div>
        </Card>
      </div>
    </section>
  )
}

export function InspectionDetailPage() {
  const { id } = useParams()
  const inspectionId = Number(id)
  const { data, isLoading, isError } = useQuery({
    queryKey: ['inspection', inspectionId],
    queryFn: () => getInspection(inspectionId),
    enabled: Number.isFinite(inspectionId),
  })

  if (isLoading) return <p className="text-sm text-ink-muted">Loading inspection…</p>
  if (isError || !data)
    return (
      <p className="text-sm text-status-defect">
        Inspection not found.{' '}
        <Link to="/review" className="text-accent">
          Back to queue
        </Link>
      </p>
    )

  return (
    <div className="max-w-4xl">
      <div className="mb-5 flex items-center justify-between">
        <h2 className="text-lg font-semibold">Inspection #{data.id}</h2>
        <Badge color={STATUS_BADGE[data.status] ?? 'neutral'}>{data.status.replace(/_/g, ' ')}</Badge>
      </div>

      <div className="space-y-8">
        {data.health_score !== null && (
          <Card className="p-6">
            <div className="grid grid-cols-1 items-center gap-6 md:grid-cols-[auto,1fr]">
              <HealthScoreGauge score={data.health_score} band={data.health_band} />
              <div className="grid grid-cols-2 gap-4">
                <Stat label="Modalities" value={data.n_predictions} />
                <Stat
                  label="Max uncertainty"
                  value={
                    data.max_uncertainty !== null
                      ? `${(data.max_uncertainty * 100).toFixed(1)}%`
                      : '—'
                  }
                />
              </div>
            </div>
          </Card>
        )}

        {data.predictions.map((prediction) => (
          <EvidenceCard key={prediction.prediction_id} prediction={prediction} />
        ))}

        <Card className="p-6">
          <h3 className="mb-1 text-base font-semibold">Inspector decision</h3>
          <p className="mb-4 text-sm text-ink-muted">
            Confirm, reject, or correct this prediction. Corrections are stored for retraining.
          </p>
          <DecisionButtons inspectionId={data.id} />

          {data.decisions.length > 0 && (
            <div className="mt-6 border-t border-surface-border pt-4">
              <div className="mb-2 text-xs uppercase tracking-wide text-ink-faint">
                Decision history
              </div>
              <ul className="space-y-2 text-sm">
                {data.decisions.map((decision) => (
                  <li key={decision.id} className="flex items-start justify-between gap-4">
                    <span>
                      <span className="capitalize text-ink">{decision.decision}</span>
                      {decision.corrected_label && (
                        <span className="text-ink-muted"> → {decision.corrected_label}</span>
                      )}
                      {decision.note && (
                        <span className="block text-xs text-ink-faint">{decision.note}</span>
                      )}
                    </span>
                    <span className="shrink-0 text-xs text-ink-faint">
                      {new Date(decision.created_at).toLocaleString()}
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </Card>
      </div>

      <div className="mt-6">
        <Link to="/review" className="text-sm text-accent">
          ← Back to review queue
        </Link>
      </div>
    </div>
  )
}
