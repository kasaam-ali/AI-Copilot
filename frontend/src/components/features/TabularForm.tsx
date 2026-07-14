import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation, useQuery } from '@tanstack/react-query'
import { getTabularSchema, inspectTabular } from '../../api/client'
import { Button } from '../primitives'

export function TabularForm() {
  const navigate = useNavigate()
  const { data: schema, isLoading, isError } = useQuery({
    queryKey: ['tabular-schema'],
    queryFn: getTabularSchema,
  })
  const [values, setValues] = useState<Record<string, number>>({})

  useEffect(() => {
    if (schema) setValues(schema.defaults)
  }, [schema])

  const mutation = useMutation({
    mutationFn: inspectTabular,
    onSuccess: (result) => navigate('/results', { state: { tabular: result } }),
  })

  if (isLoading) return <p className="text-sm text-ink-muted">Loading process parameters…</p>
  if (isError || !schema)
    return (
      <p className="text-sm text-status-defect">
        Tabular model unavailable. Train it with <code>python -m ml.tabular.train</code>.
      </p>
    )

  return (
    <div>
      <div className="grid grid-cols-2 gap-3">
        {schema.features.map((feature) => (
          <label key={feature} className="text-xs">
            <span className="mb-1 block capitalize text-ink-muted">
              {feature.replace(/_/g, ' ')}
            </span>
            <input
              type="number"
              step="any"
              value={values[feature] ?? ''}
              onChange={(event) =>
                setValues((prev) => ({ ...prev, [feature]: Number(event.target.value) }))
              }
              className="w-full rounded-md border border-surface-border bg-surface-panel px-2.5 py-1.5 font-mono text-sm text-ink outline-none focus:border-accent"
            />
          </label>
        ))}
      </div>
      <div className="mt-4 flex items-center gap-3">
        <Button onClick={() => mutation.mutate(values)} disabled={mutation.isPending}>
          {mutation.isPending ? 'Analyzing…' : 'Analyze process data'}
        </Button>
        <button
          onClick={() => setValues(schema.defaults)}
          className="text-xs text-ink-muted hover:text-ink"
        >
          Reset to defaults
        </button>
      </div>
      {mutation.isError && (
        <p className="mt-3 text-sm text-status-defect">Analysis failed. Is the backend running?</p>
      )}
    </div>
  )
}
