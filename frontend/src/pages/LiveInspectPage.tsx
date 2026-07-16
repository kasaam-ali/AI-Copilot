import { useEffect, useRef, useState } from 'react'
import { detectFrame } from '../api/client'
import { Button, Card, Stat } from '../components/primitives'

const PALETTE = ['#ef4444', '#f5a623', '#10b981', '#3b82f6', '#a855f7', '#ec4899', '#14b8a6', '#f97316']
const INTERVAL_MS = 400

function colorFor(label: string): string {
  let sum = 0
  for (let i = 0; i < label.length; i += 1) sum += label.charCodeAt(i)
  return PALETTE[sum % PALETTE.length]
}

export function LiveInspectPage() {
  const videoRef = useRef<HTMLVideoElement>(null)
  const overlayRef = useRef<HTMLCanvasElement>(null)
  const captureRef = useRef<HTMLCanvasElement | null>(null)
  const streamRef = useRef<MediaStream | null>(null)
  const timerRef = useRef<number | null>(null)
  const busyRef = useRef(false)

  const [running, setRunning] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [currentCount, setCurrentCount] = useState(0)
  const [latency, setLatency] = useState(0)
  const [isFallback, setIsFallback] = useState(false)
  const [peak, setPeak] = useState<Record<string, number>>({})

  function stop() {
    if (timerRef.current) window.clearInterval(timerRef.current)
    timerRef.current = null
    streamRef.current?.getTracks().forEach((track) => track.stop())
    streamRef.current = null
    const ctx = overlayRef.current?.getContext('2d')
    if (ctx && overlayRef.current) ctx.clearRect(0, 0, overlayRef.current.width, overlayRef.current.height)
    setRunning(false)
  }

  useEffect(() => () => stop(), [])

  async function start() {
    setError(null)
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' } })
      streamRef.current = stream
      if (videoRef.current) {
        videoRef.current.srcObject = stream
        await videoRef.current.play()
      }
      setRunning(true)
      timerRef.current = window.setInterval(tick, INTERVAL_MS)
    } catch {
      setError('Camera access denied or unavailable. Allow the camera and use localhost/https.')
    }
  }

  async function tick() {
    const video = videoRef.current
    if (!video || busyRef.current || video.videoWidth === 0) return
    busyRef.current = true
    try {
      if (!captureRef.current) captureRef.current = document.createElement('canvas')
      const capture = captureRef.current
      capture.width = video.videoWidth
      capture.height = video.videoHeight
      capture.getContext('2d')?.drawImage(video, 0, 0)
      const blob: Blob | null = await new Promise((resolve) =>
        capture.toBlob((b) => resolve(b), 'image/jpeg', 0.6),
      )
      if (!blob) return
      const result = await detectFrame(blob)
      setLatency(result.inference_ms)
      setIsFallback(result.is_fallback)
      setCurrentCount(result.detections.length)
      setPeak((prev) => {
        const next = { ...prev }
        const perClass: Record<string, number> = {}
        for (const d of result.detections) perClass[d.label] = (perClass[d.label] ?? 0) + 1
        for (const [label, count] of Object.entries(perClass)) {
          next[label] = Math.max(next[label] ?? 0, count)
        }
        return next
      })
      draw(result.detections, result.width, result.height)
    } catch {
      // Drop this frame; the next tick retries.
    } finally {
      busyRef.current = false
    }
  }

  function draw(detections: { label: string; confidence: number; box: number[] }[], w: number, h: number) {
    const video = videoRef.current
    const canvas = overlayRef.current
    if (!video || !canvas) return
    const rect = video.getBoundingClientRect()
    canvas.width = rect.width
    canvas.height = rect.height
    const ctx = canvas.getContext('2d')
    if (!ctx) return
    ctx.clearRect(0, 0, canvas.width, canvas.height)
    const sx = rect.width / w
    const sy = rect.height / h
    ctx.lineWidth = 2
    ctx.font = '13px monospace'
    for (const d of detections) {
      const [x1, y1, x2, y2] = d.box
      const color = colorFor(d.label)
      ctx.strokeStyle = color
      ctx.strokeRect(x1 * sx, y1 * sy, (x2 - x1) * sx, (y2 - y1) * sy)
      const label = `${d.label} ${(d.confidence * 100).toFixed(0)}%`
      ctx.fillStyle = color
      const tw = ctx.measureText(label).width
      ctx.fillRect(x1 * sx, y1 * sy - 16, tw + 8, 16)
      ctx.fillStyle = '#0b0f14'
      ctx.fillText(label, x1 * sx + 4, y1 * sy - 4)
    }
  }

  return (
    <div className="max-w-3xl">
      <h2 className="mb-1 text-lg font-semibold">Live inspection</h2>
      <p className="mb-5 text-sm text-ink-muted">
        Point your camera at a product — defects are detected and boxed in real time.
      </p>

      {isFallback && running && (
        <div className="mb-4 rounded-md border border-status-watch/30 bg-status-watch/10 p-3 text-xs text-status-watch">
          Using a generic pretrained detector (demo). Train and activate the defect model for
          defect-class labels.
        </div>
      )}

      <Card className="mb-5 overflow-hidden p-0">
        <div className="relative bg-black">
          <video ref={videoRef} className="w-full" muted playsInline />
          <canvas ref={overlayRef} className="pointer-events-none absolute left-0 top-0 h-full w-full" />
          {!running && (
            <div className="absolute inset-0 flex items-center justify-center text-sm text-ink-faint">
              Camera off
            </div>
          )}
        </div>
      </Card>

      {error && <p className="mb-4 text-sm text-status-defect">{error}</p>}

      <div className="mb-5 flex items-center gap-3">
        {running ? (
          <Button variant="ghost" onClick={stop}>
            Stop camera
          </Button>
        ) : (
          <Button onClick={start}>Start camera</Button>
        )}
        <span className="text-xs text-ink-faint">Runs ~{Math.round(1000 / INTERVAL_MS)} checks/sec on CPU.</span>
      </div>

      <div className="mb-5 grid grid-cols-2 gap-4">
        <Stat label="Defects in frame" value={currentCount} />
        <Stat label="Latency" value={`${latency} ms`} />
      </div>

      {Object.keys(peak).length > 0 && (
        <div>
          <div className="mb-2 text-xs uppercase tracking-wide text-ink-faint">Peak per class</div>
          <div className="flex flex-wrap gap-2">
            {Object.entries(peak).map(([label, count]) => (
              <span
                key={label}
                className="inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs"
                style={{ backgroundColor: `${colorFor(label)}22`, color: colorFor(label) }}
              >
                <span className="h-2 w-2 rounded-full" style={{ backgroundColor: colorFor(label) }} />
                {label.replace(/_/g, ' ')} · {count}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
