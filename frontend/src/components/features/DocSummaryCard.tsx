import { useRef } from 'react'
import { useMutation } from '@tanstack/react-query'
import { summarizeDoc } from '../../api/client'
import { Badge } from '../primitives'

export function DocSummaryCard() {
  const inputRef = useRef<HTMLInputElement>(null)
  const mutation = useMutation({ mutationFn: summarizeDoc })
  const result = mutation.data

  return (
    <div>
      <div
        onClick={() => inputRef.current?.click()}
        className="flex cursor-pointer items-center justify-between rounded-md border border-dashed border-surface-border px-4 py-3 text-sm text-ink-muted hover:border-accent"
      >
        <span>{mutation.isPending ? 'Reading document…' : 'Click to upload a PDF (maintenance log, spec sheet)'}</span>
        <input
          ref={inputRef}
          type="file"
          accept="application/pdf"
          className="hidden"
          onChange={(event) => {
            const file = event.target.files?.[0]
            if (file) mutation.mutate(file)
          }}
        />
      </div>

      {mutation.isError && (
        <p className="mt-3 text-sm text-status-defect">
          Could not read the PDF. Is it text (not a scanned image)?
        </p>
      )}

      {result && (
        <div className="mt-4 space-y-4">
          <div className="flex items-center gap-2 text-xs">
            <Badge color={result.provider_used === 'mock' ? 'neutral' : 'healthy'}>
              {result.provider_used}
            </Badge>
            <span className="text-ink-faint">{result.char_count} characters read</span>
          </div>
          {(
            [
              ['Key points', result.key_points],
              ['Entities', result.entities],
              ['Risks', result.risks],
            ] as const
          ).map(([title, items]) => (
            <div key={title}>
              <div className="text-xs uppercase tracking-wide text-ink-faint">{title}</div>
              {items.length > 0 ? (
                <ul className="mt-1 list-disc space-y-1 pl-5 text-sm text-ink-muted">
                  {items.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              ) : (
                <p className="mt-1 text-sm text-ink-faint">None found.</p>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
