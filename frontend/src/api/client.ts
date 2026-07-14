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
