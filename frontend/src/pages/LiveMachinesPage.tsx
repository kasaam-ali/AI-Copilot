import { useEffect, useRef, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { getTabularSchema, scoreMachines, type TabularSchema } from '../api/client'
import { Button, Card, Stat } from '../components/primitives'

const MACHINE_COUNT = 16
const TICK_MS = 1500

// How much each risk feature is pushed up as a machine's severity rises.
const RISK_BUMP: Record<string, number> = {
  machine_temp_c: 14,
  vibration_rms: 2.2,
  tool_wear_hours: 380,
  line_speed_mpm: 14,
  material_purity_pct: -3.0,
  fill_pressure_bar: 0.6,
}

interface Machine {
  id: number
  name: string
  severity: number
  rising: boolean
}

interface Reading {
  prob: number
  uncertainty: number
}

function makeMachines(): Machine[] {
  return Array.from({ length: MACHINE_COUNT }, (_, i) => {
    const severity = Math.random() < 0.35 ? 0.4 + Math.random() * 0.4 : Math.random() * 0.3
    return {
      id: i + 1,
      name: `M-${String(i + 1).padStart(2, '0')}`,
      severity,
      rising: Math.random() < 0.2, // a few machines drift toward failure over time
    }
  })
}

function reading(machine: Machine, schema: TabularSchema): Record<string, number> {
  const row: Record<string, number> = {}
  for (const feature of schema.features) {
    const base = schema.defaults[feature] ?? 0
    const noise = (Math.random() - 0.5) * Math.abs(base) * 0.04
    let value = base + (RISK_BUMP[feature] ?? 0) * machine.severity + noise
    if (feature === 'material_purity_pct') value = Math.min(100, value)
    row[feature] = Number(value.toFixed(3))
  }
  return row
}

function statusOf(prob: number): { label: string; color: string } {
  if (prob >= 0.65) return { label: 'defect', color: '#ef4444' }
  if (prob >= 0.4) return { label: 'watch', color: '#f5a623' }
  return { label: 'ok', color: '#10b981' }
}

export function LiveMachinesPage() {
  const { data: schema } = useQuery({ queryKey: ['tabular-schema'], queryFn: getTabularSchema })
  const machinesRef = useRef<Machine[]>(makeMachines())
  const timerRef = useRef<number | null>(null)
  const busyRef = useRef(false)

  const [readings, setReadings] = useState<Record<number, Reading>>({})
  const [running, setRunning] = useState(true)
  const [lastUpdate, setLastUpdate] = useState<string | null>(null)

  useEffect(() => {
    if (!schema || !running) return
    async function tick() {
      if (busyRef.current) return
      busyRef.current = true
      try {
        const machines = machinesRef.current
        for (const machine of machines) {
          if (machine.rising) machine.severity = Math.min(1, machine.severity + 0.03)
        }
        const rows = machines.map((m) => reading(m, schema as TabularSchema))
        const response = await scoreMachines(rows)
        const next: Record<number, Reading> = {}
        response.results.forEach((result, index) => {
          next[machines[index].id] = {
            prob: result.defect_probability,
            uncertainty: result.uncertainty,
          }
        })
        setReadings(next)
        setLastUpdate(new Date().toLocaleTimeString())
      } catch {
        // skip this tick
      } finally {
        busyRef.current = false
      }
    }
    tick()
    timerRef.current = window.setInterval(tick, TICK_MS)
    return () => {
      if (timerRef.current) window.clearInterval(timerRef.current)
    }
  }, [schema, running])

  const machines = machinesRef.current
  const probs = machines.map((m) => readings[m.id]?.prob ?? 0)
  const defectCount = probs.filter((p) => p >= 0.65).length
  const watchCount = probs.filter((p) => p >= 0.4 && p < 0.65).length
  const avgHealth =
    probs.length > 0 ? Math.round((1 - probs.reduce((a, b) => a + b, 0) / probs.length) * 100) : 0

  const alerts = machines
    .map((m) => ({ machine: m, prob: readings[m.id]?.prob ?? 0 }))
    .filter((x) => x.prob >= 0.65)
    .sort((a, b) => b.prob - a.prob)

  return (
    <div className="max-w-4xl">
      <div className="mb-1 flex items-center justify-between">
        <h2 className="text-lg font-semibold">Live machines</h2>
        <div className="flex items-center gap-3">
          {lastUpdate && <span className="text-xs text-ink-faint">updated {lastUpdate}</span>}
          <Button variant="ghost" onClick={() => setRunning((r) => !r)}>
            {running ? 'Pause' : 'Resume'}
          </Button>
        </div>
      </div>
      <p className="mb-5 text-sm text-ink-muted">
        {MACHINE_COUNT} machines stream sensor readings automatically — each is scored for defect
        risk in real time. No manual entry.
      </p>

      <div className="mb-6 grid grid-cols-3 gap-4">
        <Stat label="Avg health" value={`${avgHealth}`} sub="across all machines" />
        <Stat label="At risk" value={watchCount} sub="watch level" />
        <Stat
          label="Defect alerts"
          value={<span className={defectCount > 0 ? 'text-status-defect' : undefined}>{defectCount}</span>}
        />
      </div>

      {alerts.length > 0 && (
        <Card className="mb-6 border-status-defect/30 bg-status-defect/5 p-4">
          <div className="mb-2 text-xs uppercase tracking-wide text-status-defect">Active alerts</div>
          <div className="flex flex-wrap gap-2">
            {alerts.map(({ machine, prob }) => (
              <span
                key={machine.id}
                className="rounded-md bg-status-defect/15 px-2.5 py-1 text-xs text-status-defect"
              >
                {machine.name} · {(prob * 100).toFixed(0)}% defect risk
              </span>
            ))}
          </div>
        </Card>
      )}

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4">
        {machines.map((machine) => {
          const r = readings[machine.id]
          const prob = r?.prob ?? 0
          const status = statusOf(prob)
          return (
            <div key={machine.id} className="rounded-lg border border-surface-border bg-surface-raised p-4">
              <div className="mb-2 flex items-center justify-between">
                <span className="font-mono text-sm text-ink">{machine.name}</span>
                <span
                  className="rounded-full px-2 py-0.5 text-[10px] uppercase"
                  style={{ backgroundColor: `${status.color}22`, color: status.color }}
                >
                  {status.label}
                </span>
              </div>
              <div className="mb-1 flex items-baseline justify-between">
                <span className="text-xs text-ink-faint">defect risk</span>
                <span className="font-mono text-sm tabular-nums" style={{ color: status.color }}>
                  {r ? `${(prob * 100).toFixed(0)}%` : '—'}
                </span>
              </div>
              <div className="h-1.5 overflow-hidden rounded-full bg-surface-panel">
                <div
                  className="h-full rounded-full transition-all"
                  style={{ width: `${prob * 100}%`, backgroundColor: status.color }}
                />
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
