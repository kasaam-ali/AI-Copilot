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

export interface Detection {
  label: string
  confidence: number
  box: number[]
}

export interface DetectionResult {
  inspection_id: number
  prediction_id: number
  detections: Detection[]
  counts: Record<string, number>
  n_defects: number
  annotated_url: string
  model_version: string
  is_fallback: boolean
  inference_ms: number
}

export async function detectImage(file: File): Promise<DetectionResult> {
  const form = new FormData()
  form.append('file', file)
  const { data } = await apiClient.post<DetectionResult>('/inspect/detect', form)
  return data
}

export interface VideoDetectionResult {
  inspection_id: number
  prediction_id: number
  frames_sampled: number
  total_defects: number
  counts: Record<string, number>
  sample_frame_urls: string[]
  model_version: string
  is_fallback: boolean
  inference_ms: number
}

export async function detectVideo(file: File): Promise<VideoDetectionResult> {
  const form = new FormData()
  form.append('file', file)
  const { data } = await apiClient.post<VideoDetectionResult>('/inspect/detect/video', form)
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

export interface LLMAttempt {
  provider: string
  ok: boolean
  detail: string
}

export interface AnalyzeResult {
  inspection_id: number
  root_cause: string
  contributing_factors: string[]
  recommendations: string[]
  confidence_note: string
  provider_used: string
  model: string | null
  attempts: LLMAttempt[]
}

export interface DocSummaryResult {
  key_points: string[]
  entities: string[]
  risks: string[]
  char_count: number
  provider_used: string
  model: string | null
  attempts: LLMAttempt[]
}

export interface ReportInfo {
  inspection_id: number
  format: string
  size_bytes: number
  download_url: string
}

export async function analyzeInspection(inspectionId: number): Promise<AnalyzeResult> {
  const { data } = await apiClient.post<AnalyzeResult>('/llm/analyze', {
    inspection_id: inspectionId,
  })
  return data
}

export async function summarizeDoc(file: File): Promise<DocSummaryResult> {
  const form = new FormData()
  form.append('file', file)
  const { data } = await apiClient.post<DocSummaryResult>('/llm/summarize-doc', form)
  return data
}

export async function generateReport(
  inspectionId: number,
  format: 'pdf' | 'docx',
): Promise<ReportInfo> {
  const { data } = await apiClient.post<ReportInfo>(`/reports/${inspectionId}`, null, {
    params: { format },
  })
  return data
}

export async function getReports(): Promise<ReportInfo[]> {
  const { data } = await apiClient.get<ReportInfo[]>('/reports')
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

export interface RetrainJob {
  id: number
  created_at: string
  finished_at: string | null
  model_type: string
  status: 'queued' | 'running' | 'succeeded' | 'failed'
  progress: number
  base_version: string | null
  new_version: string | null
  num_corrections: number
  num_samples: number
  metrics: { auroc_new?: number; auroc_old?: number; eval_size?: number; delta?: number | null }
  message: string | null
}

export interface ModelVersion {
  version: string
  created_at: string | null
  is_active: boolean
  metrics: Record<string, unknown>
}

export interface ModelVersions {
  model_type: string
  active: string | null
  versions: ModelVersion[]
}

export async function getModelVersions(modelType: string): Promise<ModelVersions> {
  const { data } = await apiClient.get<ModelVersions>(`/models/${modelType}`)
  return data
}

export async function startRetrain(modelType: string): Promise<RetrainJob> {
  const { data } = await apiClient.post<RetrainJob>(`/retrain/${modelType}`)
  return data
}

export async function getRetrainJob(jobId: number): Promise<RetrainJob> {
  const { data } = await apiClient.get<RetrainJob>(`/retrain/jobs/${jobId}`)
  return data
}

export async function activateVersion(
  modelType: string,
  version: string,
): Promise<ModelVersions> {
  const { data } = await apiClient.post<ModelVersions>(`/models/${modelType}/${version}/activate`)
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
