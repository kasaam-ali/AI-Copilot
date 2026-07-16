import axios from 'axios'

export const apiClient = axios.create({
  baseURL: '/api/v1',
})

export interface ReadinessResponse {
  ready: boolean
  checks: Record<string, boolean>
}

export async function getReadiness(): Promise<ReadinessResponse> {
  const { data } = await apiClient.get<ReadinessResponse>('/health/ready')
  return data
}

export interface ImageInspectionResult {
  inspection_id: number
  prediction_id: number
  label: string
  label_index: number
  confidence: number
  uncertainty: number
  defect_probability: number
  class_probs: Record<string, number>
  model_version: string
  weights_sha256: string
  inference_ms: number
  gradcam_url: string
}

export async function inspectImage(file: File): Promise<ImageInspectionResult> {
  const form = new FormData()
  form.append('file', file)
  const { data } = await apiClient.post<ImageInspectionResult>('/inspect/image', form)
  return data
}

export interface ShapContribution {
  feature: string
  value: number
  contribution: number
}

export interface TabularInspectionResult {
  inspection_id: number
  prediction_id: number
  label: string
  defect_probability: number
  confidence: number
  uncertainty: number
  base_value: number
  shap: ShapContribution[]
  model_version: string
  weights_sha256: string
  inference_ms: number
}

export interface TabularSchema {
  features: string[]
  defaults: Record<string, number>
}

export async function getTabularSchema(): Promise<TabularSchema> {
  const { data } = await apiClient.get<TabularSchema>('/inspect/tabular/schema')
  return data
}

export async function inspectTabular(
  features: Record<string, number>,
): Promise<TabularInspectionResult> {
  const { data } = await apiClient.post<TabularInspectionResult>('/inspect/tabular', {
    features,
  })
  return data
}

export interface SensorImportance {
  sensor: string
  importance: number
  magnitude: number
}

export interface TimeSeriesInspectionResult {
  inspection_id: number
  prediction_id: number
  label: string
  rul: number
  rul_cap: number
  risk: number
  confidence: number
  uncertainty: number
  sensors: string[]
  sensor_importance: SensorImportance[]
  model_version: string
  weights_sha256: string
  inference_ms: number
}

export interface TimeSeriesExplanation {
  sensors: string[]
  attributions: number[][]
  sensor_importance: SensorImportance[]
  rul: number
}

export async function inspectTimeseries(
  series: number[][],
): Promise<TimeSeriesInspectionResult> {
  const { data } = await apiClient.post<TimeSeriesInspectionResult>('/inspect/timeseries', {
    series,
  })
  return data
}

export async function getTimeseriesExplanation(
  predictionId: number,
): Promise<TimeSeriesExplanation> {
  const { data } = await apiClient.get<TimeSeriesExplanation>(
    `/explain/timeseries/${predictionId}`,
  )
  return data
}

export interface HealthDriver {
  modality: string
  weight: number
  risk: number
  uncertainty: number
  contribution: number
  share: number
}

export interface SessionInspectionResult {
  inspection_id: number
  health_score: number | null
  health_band: string
  drivers: HealthDriver[]
  image: ImageInspectionResult | null
  tabular: TabularInspectionResult | null
  timeseries: TimeSeriesInspectionResult | null
  errors: Record<string, string>
}

export interface SessionInput {
  image?: File
  tabular?: Record<string, number>
  series?: number[][]
}

export async function inspectSession(input: SessionInput): Promise<SessionInspectionResult> {
  const form = new FormData()
  if (input.image) form.append('image', input.image)
  if (input.tabular) form.append('tabular', JSON.stringify(input.tabular))
  if (input.series) form.append('timeseries', JSON.stringify({ series: input.series }))
  const { data } = await apiClient.post<SessionInspectionResult>('/inspect/session', form)
  return data
}

export interface InspectionSummary {
  id: number
  created_at: string
  category: string | null
  status: string
  health_score: number | null
  health_band: string
  max_uncertainty: number | null
  label: string | null
  n_predictions: number
}

export interface PredictionSummary {
  prediction_id: number
  model_type: string
  model_version: string
  label: string | null
  confidence: number | null
  uncertainty: number | null
  output: Record<string, unknown>
  gradcam_url: string | null
  inference_ms: number | null
}

export interface DecisionSummary {
  id: number
  created_at: string
  decision: 'approve' | 'reject' | 'modify'
  reviewer: string
  corrected_label: string | null
  corrected_fields: Record<string, unknown>
  note: string | null
}

export interface InspectionDetail extends InspectionSummary {
  product_ref: string | null
  predictions: PredictionSummary[]
  decisions: DecisionSummary[]
}

export interface FeedbackRequest {
  inspection_id: number
  decision: 'approve' | 'reject' | 'modify'
  corrected_label?: string
  corrected_fields?: Record<string, number>
  note?: string
}

export async function getInspections(
  sort: 'uncertainty' | 'recent' = 'uncertainty',
  statusFilter?: string,
): Promise<InspectionSummary[]> {
  const { data } = await apiClient.get<InspectionSummary[]>('/inspections', {
    params: { sort, status: statusFilter },
  })
  return data
}

export async function getInspection(id: number): Promise<InspectionDetail> {
  const { data } = await apiClient.get<InspectionDetail>(`/inspections/${id}`)
  return data
}

export async function submitFeedback(payload: FeedbackRequest) {
  const { data } = await apiClient.post('/feedback', payload)
  return data
}

export interface ShapExplanation {
  base_value: number
  shap: ShapContribution[]
}

export async function getShapExplanation(predictionId: number): Promise<ShapExplanation> {
  const { data } = await apiClient.get<ShapExplanation>(`/explain/shap/${predictionId}`)
  return data
}

// Named sensors match scripts/synth_timeseries.py, in scaler order.
const SENSOR_PRESETS: Record<string, number[]> = {
  healthy: [61, 1.6, 42, 66, 10.2, 2.98],
  degrading: [70, 2.6, 56, 73, 12.5, 2.7],
  critical: [78, 3.9, 70, 79, 14.5, 2.35],
}

export type SeriesPreset = keyof typeof SENSOR_PRESETS

/** Build a 30-step sensor run that ramps from healthy toward the chosen end-state. */
export function buildSeriesPreset(level: SeriesPreset, window = 30): number[][] {
  const target = SENSOR_PRESETS[level]
  const start = SENSOR_PRESETS.healthy
  const rows: number[][] = []
  for (let t = 0; t < window; t += 1) {
    const alpha = level === 'healthy' ? 1 : t / (window - 1)
    rows.push(
      target.map((value, i) => {
        const ramped = start[i] + (value - start[i]) * alpha
        const wobble = Math.sin(t / 3 + i) * 0.015 * value
        return Number((ramped + wobble).toFixed(3))
      }),
    )
  }
  return rows
}
