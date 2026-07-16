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
  image: string
  boxes: Box[]
}

// Real product photographs (Creative Commons, see public/showcase/ATTRIBUTIONS.md).
// Detection boxes are illustrative overlays positioned in percentages of the frame.
const SCENES: Scene[] = [
  {
    name: 'Circuit board',
    image: '/showcase/circuit.jpg',
    boxes: [
      { x: 18, y: 34, w: 24, h: 34, label: 'solder defect', conf: 0.9 },
      { x: 58, y: 34, w: 13, h: 22, label: 'missing part', conf: 0.84 },
    ],
  },
  {
    name: 'Silicon chip',
    image: '/showcase/chip.jpg',
    boxes: [
      { x: 24, y: 22, w: 26, h: 26, label: 'surface defect', conf: 0.89 },
      { x: 64, y: 58, w: 20, h: 22, label: 'pin damage', conf: 0.82 },
    ],
  },
  {
    name: 'Textile',
    image: '/showcase/textile.jpg',
    boxes: [
      { x: 34, y: 30, w: 16, h: 22, label: 'weave flaw', conf: 0.86 },
      { x: 62, y: 20, w: 14, h: 16, label: 'stain', conf: 0.78 },
    ],
  },
  {
    name: 'Metal surface',
    image: '/showcase/metal.jpg',
    boxes: [
      { x: 50, y: 32, w: 22, h: 24, label: 'corrosion', conf: 0.91 },
      { x: 18, y: 44, w: 14, h: 18, label: 'pitting', conf: 0.82 },
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
              <img src={scene.image} alt={scene.name} className="h-full w-full object-cover" />
              {/* bottom scrim (also hides source watermarks) */}
              <div className="pointer-events-none absolute inset-x-0 bottom-0 h-1/4 bg-gradient-to-t from-surface/90 to-transparent" />

              {!reduce && (
                <motion.div
                  initial={{ top: '-6%' }}
                  animate={{ top: '106%' }}
                  transition={{ duration: 1.3, ease: 'easeInOut' }}
                  className="absolute left-0 h-10 w-full bg-gradient-to-b from-transparent via-brand/45 to-transparent"
                />
              )}

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
