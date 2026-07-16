import { useRef } from 'react'
import { useMutation } from '@tanstack/react-query'
import { detectVideo } from '../../api/client'
import { Stat } from '../primitives'

const PALETTE = ['#ef4444', '#f5a623', '#10b981', '#3b82f6', '#a855f7', '#ec4899', '#14b8a6', '#f97316']

function colorFor(label: string): string {
  let sum = 0
  for (let i = 0; i < label.length; i += 1) sum += label.charCodeAt(i)
  return PALETTE[sum % PALETTE.length]
}

export function VideoDetectionPanel() {
  const inputRef = useRef<HTMLInputElement>(null)
  const mutation = useMutation({ mutationFn: detectVideo })
  const result = mutation.data

  return (
    <div>
      <div
        onClick={() => inputRef.current?.click()}
        className="flex cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-dashed border-surface-border p-8 text-center hover:border-accent"
      >
        <div className="mb-1 text-ink-muted">Click to upload a product video (MP4, MOV, AVI)</div>
        <div className="text-xs text-ink-faint">
          Frames are sampled and scanned; defects are counted across the clip.
        </div>
        <input
          ref={inputRef}
          type="file"
          accept="video/*"
          className="hidden"
          onChange={(event) => {
            const file = event.target.files?.[0]
            if (file) mutation.mutate(file)
          }}
        />
      </div>

      {mutation.isPending && (
        <p className="mt-4 text-sm text-ink-muted">Scanning frames… (this can take a moment)</p>
      )}
      {mutation.isError && (
        <p className="mt-4 text-sm text-status-defect">
          Could not process the video. Try a shorter MP4/AVI clip.
        </p>
      )}

      {result && (
        <div className="mt-5">
          {result.is_fallback && (
            <div className="mb-4 rounded-md border border-status-watch/30 bg-status-watch/10 p-3 text-xs text-status-watch">
              Using a generic pretrained detector (demo). Train and activate the defect model
              for defect-class labels.
            </div>
          )}

          <div className="mb-4 grid grid-cols-3 gap-4">
            <Stat label="Frames scanned" value={result.frames_sampled} />
            <Stat label="Total detections" value={result.total_defects} />
            <Stat label="Time" value={`${result.inference_ms} ms`} />
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
            {result.total_defects === 0 && (
              <span className="text-sm text-status-healthy">No defects detected.</span>
            )}
          </div>

          {result.sample_frame_urls.length > 0 && (
            <>
              <div className="mb-2 text-xs uppercase tracking-wide text-ink-faint">
                Sample annotated frames
              </div>
              <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
                {result.sample_frame_urls.map((url) => (
                  <div key={url} className="overflow-hidden rounded-md border border-surface-border">
                    <img src={url} alt="frame" className="w-full" />
                  </div>
                ))}
              </div>
            </>
          )}
        </div>
      )}
    </div>
  )
}
