import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { InspectionShowcase } from '../components/landing/InspectionShowcase'

const fadeUp = {
  hidden: { opacity: 0, y: 24 },
  show: { opacity: 1, y: 0 },
}

function Logo() {
  return (
    <div className="flex items-center gap-2">
      <span className="relative flex h-7 w-7 items-center justify-center rounded-md bg-gradient-to-br from-brand to-accent">
        <span className="h-2.5 w-2.5 rounded-sm bg-surface" />
      </span>
      <span className="text-base font-semibold tracking-wide">SentinelQ</span>
    </div>
  )
}

const CAPABILITIES = [
  { value: '6', label: 'defect classes' },
  { value: '4', label: 'data modalities' },
  { value: 'real-time', label: 'live camera' },
  { value: 'mAP 0.76', label: 'detection accuracy' },
]

interface Feature {
  title: string
  desc: string
  icon: JSX.Element
}

const stroke = 'currentColor'
const FEATURES: Feature[] = [
  {
    title: 'Image detection',
    desc: 'Upload a product photo — each defect is localized with a labeled bounding box and confidence.',
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke={stroke} strokeWidth="1.6">
        <rect x="3" y="4" width="18" height="16" rx="2" />
        <rect x="8" y="9" width="7" height="6" rx="1" className="text-brand" />
        <circle cx="7" cy="8" r="1" />
      </svg>
    ),
  },
  {
    title: 'Video inspection',
    desc: 'Scan a clip frame by frame, count defects across the whole video and pull the worst frames.',
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke={stroke} strokeWidth="1.6">
        <rect x="3" y="5" width="14" height="14" rx="2" />
        <path d="M17 9l4-2v10l-4-2" />
      </svg>
    ),
  },
  {
    title: 'Live camera',
    desc: 'Point a camera at the line and see defects boxed in real time with a running tally.',
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke={stroke} strokeWidth="1.6">
        <path d="M4 7h3l2-2h6l2 2h3v12H4z" />
        <circle cx="12" cy="13" r="3.2" />
      </svg>
    ),
  },
  {
    title: 'Multimodal fusion',
    desc: 'Vision, process data and machine health fuse into one 0–100 Health Score with drivers.',
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke={stroke} strokeWidth="1.6">
        <circle cx="8" cy="8" r="4" />
        <circle cx="16" cy="16" r="4" />
        <path d="M8 12v0M12 8h0" />
      </svg>
    ),
  },
  {
    title: 'Explainable AI',
    desc: 'Grad-CAM, SHAP and Integrated Gradients show why — never a black-box verdict.',
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke={stroke} strokeWidth="1.6">
        <path d="M4 19V5M4 15l4-4 4 3 6-7" />
        <circle cx="18" cy="7" r="1.4" />
      </svg>
    ),
  },
  {
    title: 'Self-learning',
    desc: 'Inspector corrections retrain a new model version — human-gated promotion, full audit trail.',
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke={stroke} strokeWidth="1.6">
        <path d="M20 12a8 8 0 1 1-2.3-5.6" />
        <path d="M20 4v4h-4" />
      </svg>
    ),
  },
]

const PIPELINE = ['Capture', 'Detect', 'Explain', 'Decide', 'Report']

export function LandingPage() {
  return (
    <div className="relative min-h-screen overflow-hidden bg-surface text-ink">
      {/* Ambient glows */}
      <div className="pointer-events-none absolute -left-40 -top-40 h-[520px] w-[520px] rounded-full bg-brand/10 blur-[150px]" />
      <div className="pointer-events-none absolute -right-40 top-40 h-[460px] w-[460px] rounded-full bg-accent/10 blur-[150px]" />
      <div
        className="pointer-events-none absolute inset-0 opacity-[0.04]"
        style={{
          backgroundImage:
            'linear-gradient(#1f2733 1px, transparent 1px), linear-gradient(90deg, #1f2733 1px, transparent 1px)',
          backgroundSize: '48px 48px',
        }}
      />

      {/* Nav */}
      <header className="relative z-10 mx-auto flex max-w-6xl items-center justify-between px-6 py-5">
        <Logo />
        <Link
          to="/inspect"
          className="rounded-md bg-gradient-to-r from-brand to-accent px-4 py-2 text-sm font-semibold text-white transition-transform hover:scale-105"
        >
          Launch Dashboard
        </Link>
      </header>

      {/* Hero */}
      <section className="relative z-10 mx-auto grid max-w-6xl items-center gap-8 px-6 pb-16 pt-6 md:grid-cols-2 md:pt-12">
        <motion.div initial="hidden" animate="show" variants={fadeUp} transition={{ duration: 0.6 }}>
          <div className="mb-5 inline-flex items-center gap-2 rounded-full border border-brand/30 bg-brand/10 px-3 py-1 text-xs font-medium text-brand-deep">
            <span className="h-1.5 w-1.5 animate-pulseGlow rounded-full bg-brand" />
            AI Co-Pilot for Manufacturing Quality
          </div>
          <h1 className="text-4xl font-bold leading-tight tracking-tight md:text-5xl">
            See every defect,{' '}
            <span className="bg-gradient-to-r from-brand via-brand-glow to-accent bg-clip-text text-transparent">
              before it ships
            </span>
          </h1>
          <p className="mt-5 max-w-md text-base text-ink-muted">
            SentinelQ inspects products from images, video and a live camera — localizing defects
            with labeled boxes, explaining every call, and fusing sensor data into one health score.
          </p>
          <div className="mt-7 flex flex-wrap items-center gap-3">
            <Link
              to="/inspect"
              className="rounded-md bg-gradient-to-r from-brand to-accent px-5 py-2.5 text-sm font-semibold text-white transition-transform hover:scale-105"
            >
              Go to Dashboard →
            </Link>
            <Link
              to="/live"
              className="rounded-md border border-surface-border bg-surface-raised px-5 py-2.5 text-sm font-medium text-ink-muted transition-colors hover:text-ink"
            >
              Try live camera
            </Link>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, scale: 0.94 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.7, delay: 0.15 }}
        >
          <InspectionShowcase />
        </motion.div>
      </section>

      {/* Capabilities strip */}
      <section className="relative z-10 mx-auto max-w-6xl px-6">
        <div className="grid grid-cols-2 gap-4 rounded-xl border border-surface-border bg-surface-raised/60 p-6 backdrop-blur md:grid-cols-4">
          {CAPABILITIES.map((cap) => (
            <div key={cap.label} className="text-center">
              <div className="bg-gradient-to-r from-brand to-brand-glow bg-clip-text font-mono text-2xl font-bold text-transparent">
                {cap.value}
              </div>
              <div className="mt-1 text-xs uppercase tracking-wide text-ink-faint">{cap.label}</div>
            </div>
          ))}
        </div>
      </section>

      {/* Features */}
      <section className="relative z-10 mx-auto max-w-6xl px-6 py-20">
        <motion.h2
          initial="hidden"
          whileInView="show"
          viewport={{ once: true }}
          variants={fadeUp}
          transition={{ duration: 0.5 }}
          className="mb-3 text-center text-2xl font-bold md:text-3xl"
        >
          One co-pilot, the whole inspection loop
        </motion.h2>
        <p className="mx-auto mb-12 max-w-xl text-center text-sm text-ink-muted">
          Deep-learning models make every prediction. The language layer only narrates them.
        </p>
        <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {FEATURES.map((feature, i) => (
            <motion.div
              key={feature.title}
              initial="hidden"
              whileInView="show"
              viewport={{ once: true }}
              variants={fadeUp}
              transition={{ duration: 0.5, delay: i * 0.06 }}
              className="group rounded-xl border border-surface-border bg-surface-raised/70 p-6 backdrop-blur transition-colors hover:border-brand/40"
            >
              <div className="mb-4 flex h-11 w-11 items-center justify-center rounded-lg bg-brand/10 text-brand transition-colors group-hover:bg-brand/20">
                <span className="h-6 w-6">{feature.icon}</span>
              </div>
              <h3 className="mb-1.5 text-base font-semibold">{feature.title}</h3>
              <p className="text-sm text-ink-muted">{feature.desc}</p>
            </motion.div>
          ))}
        </div>
      </section>

      {/* Pipeline */}
      <section className="relative z-10 mx-auto max-w-6xl px-6 pb-20">
        <div className="rounded-2xl border border-surface-border bg-gradient-to-br from-surface-raised to-surface p-8">
          <h2 className="mb-8 text-center text-xl font-semibold">How it works</h2>
          <div className="flex flex-wrap items-center justify-center gap-3">
            {PIPELINE.map((step, i) => (
              <div key={step} className="flex items-center gap-3">
                <div className="flex items-center gap-2 rounded-lg border border-surface-border bg-surface-panel px-4 py-2.5 text-sm">
                  <span className="font-mono text-xs text-brand">{String(i + 1).padStart(2, '0')}</span>
                  {step}
                </div>
                {i < PIPELINE.length - 1 && <span className="text-brand">→</span>}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Final CTA */}
      <section className="relative z-10 mx-auto max-w-6xl px-6 pb-24">
        <motion.div
          initial="hidden"
          whileInView="show"
          viewport={{ once: true }}
          variants={fadeUp}
          transition={{ duration: 0.5 }}
          className="relative overflow-hidden rounded-2xl border border-brand/30 bg-gradient-to-r from-brand/10 to-accent/10 p-10 text-center"
        >
          <h2 className="text-2xl font-bold md:text-3xl">Ready to inspect?</h2>
          <p className="mx-auto mt-3 max-w-md text-sm text-ink-muted">
            Open the dashboard and run a detection, a multimodal session, or watch the live line.
          </p>
          <Link
            to="/inspect"
            className="mt-6 inline-block rounded-md bg-gradient-to-r from-brand to-accent px-6 py-3 text-sm font-semibold text-white transition-transform hover:scale-105"
          >
            Go to Dashboard →
          </Link>
        </motion.div>
      </section>

      <footer className="relative z-10 border-t border-surface-border">
        <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-3 px-6 py-6 text-xs text-ink-faint sm:flex-row">
          <Logo />
          <span>Manufacturing Quality Inspection Co-Pilot</span>
        </div>
      </footer>
    </div>
  )
}
