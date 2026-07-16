import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { submitFeedback, type FeedbackRequest } from '../../api/client'
import { Button } from '../primitives'

export function DecisionButtons({ inspectionId }: { inspectionId: number }) {
  const queryClient = useQueryClient()
  const [modifying, setModifying] = useState(false)
  const [correctedLabel, setCorrectedLabel] = useState('defect')
  const [note, setNote] = useState('')

  const mutation = useMutation({
    mutationFn: (payload: FeedbackRequest) => submitFeedback(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['inspection', inspectionId] })
      queryClient.invalidateQueries({ queryKey: ['inspections'] })
      setModifying(false)
      setNote('')
    },
  })

  const disabled = mutation.isPending

  return (
    <div>
      <div className="flex flex-wrap items-center gap-3">
        <Button
          onClick={() => mutation.mutate({ inspection_id: inspectionId, decision: 'approve', note: note || undefined })}
          disabled={disabled}
        >
          Approve
        </Button>
        <Button
          variant="ghost"
          onClick={() => mutation.mutate({ inspection_id: inspectionId, decision: 'reject', note: note || undefined })}
          disabled={disabled}
        >
          Reject
        </Button>
        <Button variant="ghost" onClick={() => setModifying((prev) => !prev)} disabled={disabled}>
          Modify…
        </Button>
      </div>

      {modifying && (
        <div className="mt-4 space-y-3 rounded-md border border-surface-border bg-surface-panel p-4">
          <label className="block text-xs">
            <span className="mb-1 block text-ink-muted">Corrected label</span>
            <select
              value={correctedLabel}
              onChange={(event) => setCorrectedLabel(event.target.value)}
              className="w-full rounded-md border border-surface-border bg-surface-raised px-2.5 py-1.5 text-sm text-ink outline-none focus:border-accent"
            >
              <option value="defect">defect</option>
              <option value="ok">ok</option>
              <option value="good">good</option>
            </select>
          </label>
          <label className="block text-xs">
            <span className="mb-1 block text-ink-muted">Note (optional)</span>
            <input
              value={note}
              onChange={(event) => setNote(event.target.value)}
              placeholder="Why is this being corrected?"
              className="w-full rounded-md border border-surface-border bg-surface-raised px-2.5 py-1.5 text-sm text-ink outline-none focus:border-accent"
            />
          </label>
          <Button
            onClick={() =>
              mutation.mutate({
                inspection_id: inspectionId,
                decision: 'modify',
                corrected_label: correctedLabel,
                note: note || undefined,
              })
            }
            disabled={disabled}
          >
            Save correction
          </Button>
        </div>
      )}

      {mutation.isError && (
        <p className="mt-3 text-sm text-status-defect">Could not save the decision.</p>
      )}
    </div>
  )
}
