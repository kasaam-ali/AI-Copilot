import { useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation } from '@tanstack/react-query'
import { inspectImage } from '../api/client'
import { Card } from '../components/primitives'
import { TabularForm } from '../components/features/TabularForm'
import { SessionPanel } from '../components/features/SessionPanel'
import { DocSummaryCard } from '../components/features/DocSummaryCard'

export function InspectPage() {
  const navigate = useNavigate()
  const inputRef = useRef<HTMLInputElement>(null)
  const [preview, setPreview] = useState<string | null>(null)
  const [fileName, setFileName] = useState<string | null>(null)
  const [dragOver, setDragOver] = useState(false)

  const mutation = useMutation({
    mutationFn: inspectImage,
    onSuccess: (result) => navigate('/results', { state: { image: result } }),
  })

  function handleFile(file: File) {
    setPreview(URL.createObjectURL(file))
    setFileName(file.name)
    mutation.mutate(file)
  }

  return (
    <div className="max-w-2xl">
      <h2 className="mb-1 text-lg font-semibold">Full multimodal inspection</h2>
      <p className="mb-4 text-sm text-ink-muted">
        Fuse vision, process data and machine health into a single Health Score with a
        per-modality breakdown.
      </p>
      <Card className="mb-10 p-6">
        <SessionPanel />
      </Card>

      <h2 className="mb-1 text-lg font-semibold">Inspect a product image</h2>
      <p className="mb-5 text-sm text-ink-muted">
        Upload a product photo to detect defects with a CNN and a Grad-CAM explanation.
      </p>

      <Card className="p-6">
        <div
          onDragOver={(event) => {
            event.preventDefault()
            setDragOver(true)
          }}
          onDragLeave={() => setDragOver(false)}
          onDrop={(event) => {
            event.preventDefault()
            setDragOver(false)
            const file = event.dataTransfer.files?.[0]
            if (file) handleFile(file)
          }}
          onClick={() => inputRef.current?.click()}
          className={`flex cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-dashed p-10 text-center transition-colors ${
            dragOver ? 'border-accent bg-surface-panel' : 'border-surface-border'
          }`}
        >
          {preview ? (
            <img src={preview} alt="preview" className="mb-3 max-h-40 rounded" />
          ) : (
            <div className="mb-2 text-ink-muted">
              Drag &amp; drop an image here, or click to browse
            </div>
          )}
          <div className="text-xs text-ink-faint">
            {fileName ?? 'PNG, JPG, BMP — up to 20 MB'}
          </div>
          <input
            ref={inputRef}
            type="file"
            accept="image/*"
            className="hidden"
            onChange={(event) => {
              const file = event.target.files?.[0]
              if (file) handleFile(file)
            }}
          />
        </div>

        {mutation.isPending && <p className="mt-4 text-sm text-ink-muted">Analyzing…</p>}
        {mutation.isError && (
          <p className="mt-4 text-sm text-status-defect">
            Inspection failed. Is a model trained and the backend running?
          </p>
        )}
      </Card>

      <h3 className="mb-1 mt-8 text-base font-semibold">Process parameters</h3>
      <p className="mb-4 text-sm text-ink-muted">
        Enter production-line sensor readings to predict defect probability with SHAP
        feature attributions.
      </p>
      <Card className="p-6">
        <TabularForm />
      </Card>

      <h3 className="mb-1 mt-8 text-base font-semibold">Document summary</h3>
      <p className="mb-4 text-sm text-ink-muted">
        Extract key points, entities and risks from a maintenance log or spec sheet (PDF).
      </p>
      <Card className="p-6">
        <DocSummaryCard />
      </Card>
    </div>
  )
}
