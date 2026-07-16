import { useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation, useQuery } from '@tanstack/react-query'
import {
  buildSeriesPreset,
  getTabularSchema,
  inspectSession,
  type SeriesPreset,
} from '../../api/client'
import { Button } from '../primitives'

const PRESETS: { id: SeriesPreset; label: string; hint: string }[] = [
  { id: 'healthy', label: 'Healthy run', hint: 'stable sensors, long life left' },
  { id: 'degrading', label: 'Degrading', hint: 'drifting upward, wearing in' },
  { id: 'critical', label: 'Near failure', hint: 'high load, low life left' },
]

export function SessionPanel() {
  const navigate = useNavigate()
  const inputRef = useRef<HTMLInputElement>(null)
  const [image, setImage] = useState<File | null>(null)
  const [includeTabular, setIncludeTabular] = useState(true)
  const [preset, setPreset] = useState<SeriesPreset>('degrading')

  const { data: schema } = useQuery({ queryKey: ['tabular-schema'], queryFn: getTabularSchema })

  const mutation = useMutation({
    mutationFn: inspectSession,
    onSuccess: (result) => navigate('/results', { state: { session: result } }),
  })

  function run() {
    mutation.mutate({
      image: image ?? undefined,
      tabular: includeTabular ? schema?.defaults : undefined,
      series: buildSeriesPreset(preset),
    })
  }

  return (
    <div className="space-y-5">
      <div>
        <div className="mb-2 text-sm font-medium text-ink">Product image (optional)</div>
        <div
          onClick={() => inputRef.current?.click()}
          className="flex cursor-pointer items-center justify-between rounded-md border border-dashed border-surface-border px-4 py-3 text-sm text-ink-muted hover:border-accent"
        >
          <span>{image ? image.name : 'Click to attach a product photo'}</span>
          {image && (
            <button
              onClick={(event) => {
                event.stopPropagation()
                setImage(null)
              }}
              className="text-xs text-ink-faint hover:text-ink"
            >
              remove
            </button>
          )}
          <input
            ref={inputRef}
            type="file"
            accept="image/*"
            className="hidden"
            onChange={(event) => setImage(event.target.files?.[0] ?? null)}
          />
        </div>
      </div>

      <label className="flex items-center gap-2 text-sm text-ink-muted">
        <input
          type="checkbox"
          checked={includeTabular}
          onChange={(event) => setIncludeTabular(event.target.checked)}
          className="accent-accent"
        />
        Include process parameters (default sensor readings)
      </label>

      <div>
        <div className="mb-2 text-sm font-medium text-ink">Machine sensor history</div>
        <div className="grid grid-cols-1 gap-2 sm:grid-cols-3">
          {PRESETS.map((item) => (
            <button
              key={item.id}
              onClick={() => setPreset(item.id)}
              className={`rounded-md border px-3 py-2 text-left transition-colors ${
                preset === item.id
                  ? 'border-accent bg-surface-panel'
                  : 'border-surface-border hover:border-ink-faint'
              }`}
            >
              <div className="text-sm text-ink">{item.label}</div>
              <div className="text-[11px] text-ink-faint">{item.hint}</div>
            </button>
          ))}
        </div>
      </div>

      <div className="flex items-center gap-3">
        <Button onClick={run} disabled={mutation.isPending}>
          {mutation.isPending ? 'Fusing modalities…' : 'Run full multimodal session'}
        </Button>
        <span className="text-xs text-ink-faint">
          Runs every supplied modality and fuses one Health Score.
        </span>
      </div>
      {mutation.isError && (
        <p className="text-sm text-status-defect">Session failed. Are all models trained?</p>
      )}
    </div>
  )
}
