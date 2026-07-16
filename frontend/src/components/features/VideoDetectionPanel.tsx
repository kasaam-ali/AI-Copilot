import { useRef, useState } from 'react'
import { detectVideo, type VideoDetectionResult } from '../../api/client'

const PALETTE = ['#c5221f', '#b06000', '#1a73e8', '#8430ce', '#188038', '#c26a1d']

function colorFor(label: string): string {
  let sum = 0
  for (let i = 0; i < label.length; i += 1) sum += label.charCodeAt(i)
  return PALETTE[sum % PALETTE.length]
}

interface Item {
  name: string
  result?: VideoDetectionResult
  error?: boolean
}

export function VideoDetectionPanel() {
  const inputRef = useRef<HTMLInputElement>(null)
  const [items, setItems] = useState<Item[]>([])
  const [busy, setBusy] = useState(false)
  const [progress, setProgress] = useState({ done: 0, total: 0 })

  async function handleFiles(fileList: FileList | null) {
    const files = Array.from(fileList ?? [])
    if (!files.length) return
    setBusy(true)
    setProgress({ done: 0, total: files.length })
    const collected: Item[] = []
    for (let i = 0; i < files.length; i += 1) {
      try {
        const result = await detectVideo(files[i])
        collected.push({ name: files[i].name, result })
      } catch {
        collected.push({ name: files[i].name, error: true })
      }
      setProgress({ done: i + 1, total: files.length })
      setItems([...collected])
    }
    setBusy(false)
  }

  const totalDefects = items.reduce((s, it) => s + (it.result?.total_defects ?? 0), 0)

  return (
    <div>
      <div
        onClick={() => inputRef.current?.click()}
        className="flex cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-dashed border-surface-border p-8 text-center hover:border-brand"
      >
        <div className="mb-1 text-ink-muted">Click to upload product videos (MP4, MOV, AVI)</div>
        <div className="text-xs text-ink-faint">
          Select one or many — frames are sampled and defects counted across each clip.
        </div>
        <input
          ref={inputRef}
          type="file"
          accept="video/*"
          multiple
          className="hidden"
          onChange={(e) => handleFiles(e.target.files)}
        />
      </div>

      {busy && (
        <p className="mt-4 text-sm text-ink-muted">
          Scanning clips… {progress.done}/{progress.total}
        </p>
      )}

      {items.length > 0 && (
        <div className="mt-5 space-y-4">
          <div className="text-sm text-ink-muted">
            <span className="font-semibold text-ink">{items.length}</span> clip
            {items.length === 1 ? '' : 's'} · {' '}
            <span className="font-semibold text-ink">{totalDefects}</span> total detections
          </div>

          {items.map((item, index) => (
            <div key={index} className="rounded-lg border border-surface-border bg-surface-raised p-4">
              <div className="mb-3 flex items-center justify-between">
                <span className="truncate text-sm font-medium text-ink">{item.name}</span>
                {item.result && (
                  <span className="text-xs text-ink-faint">
                    {item.result.frames_sampled} frames · {item.result.total_defects} detections
                  </span>
                )}
              </div>

              {item.error ? (
                <p className="text-sm text-status-defect">Could not process this clip.</p>
              ) : (
                item.result && (
                  <>
                    <div className="mb-3 flex flex-wrap gap-1.5">
                      {Object.entries(item.result.counts).map(([label, count]) => (
                        <span
                          key={label}
                          className="inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[11px]"
                          style={{ backgroundColor: `${colorFor(label)}1f`, color: colorFor(label) }}
                        >
                          <span className="h-1.5 w-1.5 rounded-full" style={{ backgroundColor: colorFor(label) }} />
                          {label.replace(/_/g, ' ')} · {count}
                        </span>
                      ))}
                      {item.result.total_defects === 0 && (
                        <span className="text-xs text-status-healthy">No defects detected</span>
                      )}
                    </div>
                    {item.result.sample_frame_urls.length > 0 && (
                      <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
                        {item.result.sample_frame_urls.map((url) => (
                          <div key={url} className="overflow-hidden rounded-md border border-surface-border">
                            <img src={url} alt="frame" className="w-full" />
                          </div>
                        ))}
                      </div>
                    )}
                  </>
                )
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
