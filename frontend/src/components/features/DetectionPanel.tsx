import { useRef, useState } from 'react'
import { detectImage, type DetectionResult } from '../../api/client'

const PALETTE = ['#c5221f', '#b06000', '#1a73e8', '#8430ce', '#188038', '#c26a1d']

function colorFor(label: string): string {
  let sum = 0
  for (let i = 0; i < label.length; i += 1) sum += label.charCodeAt(i)
  return PALETTE[sum % PALETTE.length]
}

interface Item {
  name: string
  result?: DetectionResult
  error?: boolean
}

export function DetectionPanel() {
  const inputRef = useRef<HTMLInputElement>(null)
  const [dragOver, setDragOver] = useState(false)
  const [items, setItems] = useState<Item[]>([])
  const [busy, setBusy] = useState(false)
  const [progress, setProgress] = useState({ done: 0, total: 0 })

  async function handleFiles(fileList: FileList | null) {
    const files = Array.from(fileList ?? [])
    if (!files.length) return
    setBusy(true)
    setProgress({ done: 0, total: files.length })
    setItems(files.map((f) => ({ name: f.name })))

    const collected: Item[] = []
    for (let i = 0; i < files.length; i += 1) {
      try {
        const result = await detectImage(files[i])
        collected.push({ name: files[i].name, result })
      } catch {
        collected.push({ name: files[i].name, error: true })
      }
      setProgress({ done: i + 1, total: files.length })
      setItems([...collected, ...files.slice(i + 1).map((f) => ({ name: f.name }))])
    }
    setItems(collected)
    setBusy(false)
  }

  const done = items.filter((it) => it.result || it.error)
  const totalDefects = done.reduce((s, it) => s + (it.result?.n_defects ?? 0), 0)
  const isFallback = done.some((it) => it.result?.is_fallback)

  return (
    <div>
      <div
        onDragOver={(e) => {
          e.preventDefault()
          setDragOver(true)
        }}
        onDragLeave={() => setDragOver(false)}
        onDrop={(e) => {
          e.preventDefault()
          setDragOver(false)
          handleFiles(e.dataTransfer.files)
        }}
        onClick={() => inputRef.current?.click()}
        className={`flex cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-dashed p-8 text-center transition-colors ${
          dragOver ? 'border-brand bg-brand/5' : 'border-surface-border'
        }`}
      >
        <div className="mb-1 text-ink-muted">Drag &amp; drop product photos, or click to browse</div>
        <div className="text-xs text-ink-faint">
          Select one or many — each defect is boxed and labeled with a confidence score.
        </div>
        <input
          ref={inputRef}
          type="file"
          accept="image/*"
          multiple
          className="hidden"
          onChange={(e) => handleFiles(e.target.files)}
        />
      </div>

      {busy && (
        <p className="mt-4 text-sm text-ink-muted">
          Detecting… {progress.done}/{progress.total}
        </p>
      )}

      {done.length > 0 && (
        <div className="mt-5">
          {isFallback && (
            <div className="mb-4 rounded-md border border-status-watch/40 bg-status-watch/10 p-3 text-xs text-status-watch">
              Using a generic pretrained detector for at least one image. Train and activate the
              defect model for defect-class labels.
            </div>
          )}

          <div className="mb-4 flex flex-wrap gap-4 text-sm">
            <span className="text-ink-muted">
              <span className="font-semibold text-ink">{done.length}</span> image
              {done.length === 1 ? '' : 's'}
            </span>
            <span className="text-ink-muted">
              <span className="font-semibold text-ink">{totalDefects}</span> total detection
              {totalDefects === 1 ? '' : 's'}
            </span>
          </div>

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            {done.map((item, index) => (
              <div key={index} className="overflow-hidden rounded-lg border border-surface-border bg-surface-raised">
                {item.error ? (
                  <div className="p-4 text-sm text-status-defect">Failed: {item.name}</div>
                ) : (
                  <>
                    <img src={item.result!.annotated_url} alt={item.name} className="w-full" />
                    <div className="p-3">
                      <div className="mb-2 truncate text-xs text-ink-faint">{item.name}</div>
                      <div className="flex flex-wrap gap-1.5">
                        {Object.entries(item.result!.counts).map(([label, count]) => (
                          <span
                            key={label}
                            className="inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[11px]"
                            style={{ backgroundColor: `${colorFor(label)}1f`, color: colorFor(label) }}
                          >
                            <span className="h-1.5 w-1.5 rounded-full" style={{ backgroundColor: colorFor(label) }} />
                            {label.replace(/_/g, ' ')} · {count}
                          </span>
                        ))}
                        {item.result!.n_defects === 0 && (
                          <span className="text-xs text-status-healthy">No defects</span>
                        )}
                      </div>
                    </div>
                  </>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
