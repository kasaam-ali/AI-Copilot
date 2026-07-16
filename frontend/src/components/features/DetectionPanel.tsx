import { useRef, useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { detectImage } from '../../api/client'

const PALETTE = ['#ef4444', '#f5a623', '#10b981', '#3b82f6', '#a855f7', '#ec4899', '#14b8a6', '#f97316']

function colorFor(label: string): string {
  let sum = 0
  for (let i = 0; i < label.length; i += 1) sum += label.charCodeAt(i)
  return PALETTE[sum % PALETTE.length]
}

export function DetectionPanel() {
  const inputRef = useRef<HTMLInputElement>(null)
  const [dragOver, setDragOver] = useState(false)
  const mutation = useMutation({ mutationFn: detectImage })
  const result = mutation.data

  function handleFile(file: File) {
    mutation.mutate(file)
  }

  return (
    <div>
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
        className={`flex cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-dashed p-8 text-center transition-colors ${
          dragOver ? 'border-accent bg-surface-panel' : 'border-surface-border'
        }`}
      >
        <div className="mb-1 text-ink-muted">
          Drag &amp; drop a product photo, or click to browse
        </div>
        <div className="text-xs text-ink-faint">
          The detector draws a labeled box around each defect it finds.
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

      {mutation.isPending && <p className="mt-4 text-sm text-ink-muted">Detecting defects…</p>}
      {mutation.isError && (
        <p className="mt-4 text-sm text-status-defect">Detection failed. Is the backend running?</p>
      )}

      {result && (
        <div className="mt-5">
          {result.is_fallback && (
            <div className="mb-4 rounded-md border border-status-watch/30 bg-status-watch/10 p-3 text-xs text-status-watch">
              Using a generic pretrained detector (demo). Train the defect model
              (NEU-DET on Colab) and activate it to get defect-class labels.
            </div>
          )}

          <div className="grid grid-cols-1 gap-5 md:grid-cols-[1.4fr,1fr]">
            <div className="overflow-hidden rounded-lg border border-surface-border bg-surface-panel">
              <img src={result.annotated_url} alt="detections" className="w-full" />
            </div>
            <div>
              <div className="mb-2 flex items-baseline justify-between">
                <span className="text-sm font-medium text-ink">
                  {result.n_defects} detection{result.n_defects === 1 ? '' : 's'}
                </span>
                <span className="text-xs text-ink-faint">{result.inference_ms} ms</span>
              </div>

              <div className="mb-4 flex flex-wrap gap-2">
                {Object.entries(result.counts).map(([label, count]) => (
                  <span
                    key={label}
                    className="inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs"
                    style={{ backgroundColor: `${colorFor(label)}22`, color: colorFor(label) }}
                  >
                    <span className="h-2 w-2 rounded-full" style={{ backgroundColor: colorFor(label) }} />
                    {label.replace(/_/g, ' ')} · {count}
                  </span>
                ))}
                {result.n_defects === 0 && (
                  <span className="text-sm text-status-healthy">No defects detected.</span>
                )}
              </div>

              <ul className="space-y-1.5">
                {result.detections.slice(0, 12).map((det, index) => (
                  <li key={index} className="flex items-center justify-between text-sm">
                    <span className="flex items-center gap-2">
                      <span className="h-2.5 w-2.5 rounded-sm" style={{ backgroundColor: colorFor(det.label) }} />
                      <span className="capitalize text-ink-muted">{det.label.replace(/_/g, ' ')}</span>
                    </span>
                    <span className="font-mono tabular-nums text-ink-faint">
                      {(det.confidence * 100).toFixed(0)}%
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
