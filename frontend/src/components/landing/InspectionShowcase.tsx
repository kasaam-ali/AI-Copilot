import { useEffect, useState } from 'react'
import { AnimatePresence, motion, useReducedMotion } from 'framer-motion'

interface Box {
  x: number
  y: number
  w: number
  h: number
  label: string
  conf: number
}

interface Scene {
  name: string
  svg: JSX.Element
  boxes: Box[]
}

// Stylized but recognizable product renderings (viewBox 320x180), each with defect boxes
// positioned in percentages of the viewport.
const SCENES: Scene[] = [
  {
    name: 'Steel sheet',
    svg: (
      <svg viewBox="0 0 320 180" className="h-full w-full">
        <defs>
          <linearGradient id="steel" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0" stopColor="#6b7280" />
            <stop offset="0.5" stopColor="#9ca3af" />
            <stop offset="1" stopColor="#4b5563" />
          </linearGradient>
        </defs>
        <rect width="320" height="180" fill="url(#steel)" />
        {Array.from({ length: 9 }).map((_, i) => (
          <line key={i} x1={0} y1={i * 22} x2={320} y2={i * 22 + 6} stroke="#ffffff" strokeOpacity="0.05" />
        ))}
        <path d="M60 40 L120 70" stroke="#1f2937" strokeWidth="2" strokeOpacity="0.6" />
        <path d="M64 44 L118 72" stroke="#111827" strokeWidth="1" strokeOpacity="0.5" />
        <ellipse cx="235" cy="120" rx="10" ry="6" fill="#374151" opacity="0.7" />
      </svg>
    ),
    boxes: [
      { x: 16, y: 18, w: 24, h: 24, label: 'scratches', conf: 0.92 },
      { x: 66, y: 58, w: 16, h: 20, label: 'inclusion', conf: 0.85 },
    ],
  },
  {
    name: 'Metal casting',
    svg: (
      <svg viewBox="0 0 320 180" className="h-full w-full">
        <defs>
          <radialGradient id="cast" cx="0.4" cy="0.35" r="0.8">
            <stop offset="0" stopColor="#a8a29e" />
            <stop offset="1" stopColor="#57534e" />
          </radialGradient>
        </defs>
        <rect width="320" height="180" fill="#1c1917" />
        <circle cx="160" cy="90" r="66" fill="url(#cast)" />
        {Array.from({ length: 12 }).map((_, i) => {
          const a = (i / 12) * Math.PI * 2
          return (
            <rect
              key={i}
              x={160 + Math.cos(a) * 66 - 5}
              y={90 + Math.sin(a) * 66 - 5}
              width="10"
              height="10"
              fill="#78716c"
              transform={`rotate(${(a * 180) / Math.PI} ${160 + Math.cos(a) * 66} ${90 + Math.sin(a) * 66})`}
            />
          )
        })}
        <circle cx="160" cy="90" r="22" fill="#292524" />
        <circle cx="140" cy="72" r="4" fill="#1c1917" />
        <path d="M180 100 q10 8 4 20" stroke="#292524" strokeWidth="2" fill="none" />
      </svg>
    ),
    boxes: [
      { x: 38, y: 33, w: 14, h: 16, label: 'pitted_surface', conf: 0.88 },
      { x: 55, y: 55, w: 16, h: 16, label: 'crazing', conf: 0.79 },
    ],
  },
  {
    name: 'PCB',
    svg: (
      <svg viewBox="0 0 320 180" className="h-full w-full">
        <rect width="320" height="180" fill="#0f3d2e" />
        {Array.from({ length: 6 }).map((_, i) => (
          <line key={`h${i}`} x1={0} y1={20 + i * 28} x2={320} y2={20 + i * 28} stroke="#14b86a" strokeOpacity="0.25" />
        ))}
        {Array.from({ length: 8 }).map((_, i) => (
          <line key={`v${i}`} x1={30 + i * 36} y1={0} x2={30 + i * 36} y2={180} stroke="#14b86a" strokeOpacity="0.18" />
        ))}
        <rect x="40" y="40" width="46" height="30" rx="2" fill="#1f2937" />
        <rect x="150" y="90" width="60" height="34" rx="2" fill="#111827" />
        <circle cx="250" cy="50" r="10" fill="#334155" />
        <rect x="240" y="120" width="22" height="12" fill="#eab308" />
      </svg>
    ),
    boxes: [
      { x: 44, y: 48, w: 18, h: 22, label: 'solder defect', conf: 0.9 },
      { x: 74, y: 63, w: 12, h: 14, label: 'missing part', conf: 0.83 },
    ],
  },
  {
    name: 'Textile',
    svg: (
      <svg viewBox="0 0 320 180" className="h-full w-full">
        <defs>
          <pattern id="weave" width="12" height="12" patternUnits="userSpaceOnUse">
            <rect width="12" height="12" fill="#7c3f24" />
            <rect width="6" height="6" fill="#8a4a2c" />
            <rect x="6" y="6" width="6" height="6" fill="#8a4a2c" />
          </pattern>
        </defs>
        <rect width="320" height="180" fill="url(#weave)" />
        <path d="M120 60 q20 20 6 44" stroke="#1c1917" strokeWidth="3" fill="none" opacity="0.8" />
        <ellipse cx="235" cy="70" rx="14" ry="9" fill="#3f2213" opacity="0.7" />
      </svg>
    ),
    boxes: [
      { x: 33, y: 30, w: 14, h: 30, label: 'tear', conf: 0.86 },
      { x: 66, y: 32, w: 14, h: 14, label: 'stain', conf: 0.77 },
    ],
  },
]

const CYCLE_MS = 4200

function color(label: string): string {
  const palette = ['#ef4444', '#f5a623', '#22d3ee', '#a855f7', '#10b981']
  let s = 0
  for (let i = 0; i < label.length; i += 1) s += label.charCodeAt(i)
  return palette[s % palette.length]
}

export function InspectionShowcase() {
  const [active, setActive] = useState(0)
  const reduce = useReducedMotion()

  useEffect(() => {
    const timer = window.setInterval(() => setActive((a) => (a + 1) % SCENES.length), CYCLE_MS)
    return () => window.clearInterval(timer)
  }, [])

  const scene = SCENES[active]

  return (
    <div>
      <div className="relative overflow-hidden rounded-xl border border-surface-border bg-surface-panel shadow-2xl">
        {/* viewport header */}
        <div className="flex items-center justify-between border-b border-surface-border bg-surface-raised px-3 py-2 text-[11px] text-ink-faint">
          <span className="flex items-center gap-1.5">
            <span className="h-1.5 w-1.5 animate-pulseGlow rounded-full bg-status-healthy" />
            SentinelQ · live detection
          </span>
          <span className="font-mono">{scene.name}</span>
        </div>

        <div className="relative aspect-video">
          <AnimatePresence mode="wait">
            <motion.div
              key={active}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.4 }}
              className="absolute inset-0"
            >
              {scene.svg}

              {/* scan line */}
              {!reduce && (
                <motion.div
                  initial={{ top: '-6%' }}
                  animate={{ top: '106%' }}
                  transition={{ duration: 1.3, ease: 'easeInOut' }}
                  className="absolute left-0 h-8 w-full bg-gradient-to-b from-transparent via-brand/40 to-transparent"
                />
              )}

              {/* detection boxes */}
              {scene.boxes.map((box, i) => (
                <motion.div
                  key={box.label}
                  initial={{ opacity: 0, scale: 0.85 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ delay: reduce ? 0 : 1.35 + i * 0.18, duration: 0.3 }}
                  className="absolute"
                  style={{
                    left: `${box.x}%`,
                    top: `${box.y}%`,
                    width: `${box.w}%`,
                    height: `${box.h}%`,
                    border: `2px solid ${color(box.label)}`,
                    boxShadow: `0 0 12px ${color(box.label)}66`,
                  }}
                >
                  <span
                    className="absolute -top-5 left-0 whitespace-nowrap rounded px-1.5 py-0.5 text-[10px] font-medium"
                    style={{ backgroundColor: color(box.label), color: '#0b0f14' }}
                  >
                    {box.label} {(box.conf * 100).toFixed(0)}%
                  </span>
                </motion.div>
              ))}
            </motion.div>
          </AnimatePresence>
        </div>
      </div>

      {/* product switcher */}
      <div className="mt-3 flex items-center justify-center gap-2">
        {SCENES.map((s, i) => (
          <button
            key={s.name}
            onClick={() => setActive(i)}
            className={`rounded-md px-3 py-1.5 text-xs transition-colors ${
              i === active
                ? 'bg-brand/15 text-brand-glow'
                : 'text-ink-faint hover:bg-surface-panel hover:text-ink-muted'
            }`}
          >
            {s.name}
          </button>
        ))}
      </div>
    </div>
  )
}
