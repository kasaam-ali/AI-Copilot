import { useQuery } from '@tanstack/react-query'
import { getReports } from '../api/client'
import { Card } from '../components/primitives'

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

export function ReportsPage() {
  const { data, isLoading, isError } = useQuery({ queryKey: ['reports'], queryFn: getReports })

  return (
    <div className="max-w-3xl">
      <h2 className="mb-1 text-lg font-semibold">Reports</h2>
      <p className="mb-5 text-sm text-ink-muted">
        Generated inspection reports. Open an inspection result to create one.
      </p>

      {isLoading && <p className="text-sm text-ink-muted">Loading reports…</p>}
      {isError && <p className="text-sm text-status-defect">Could not load reports.</p>}
      {data && data.length === 0 && (
        <p className="text-sm text-ink-muted">
          No reports yet. Run an inspection, then use “Download PDF / DOCX” on the results.
        </p>
      )}
      {data && data.length > 0 && (
        <Card className="overflow-hidden">
          <table className="w-full">
            <thead>
              <tr className="text-left text-xs uppercase tracking-wide text-ink-faint">
                <th className="px-4 py-3 font-medium">Inspection</th>
                <th className="px-4 py-3 font-medium">Format</th>
                <th className="px-4 py-3 font-medium">Size</th>
                <th className="px-4 py-3 font-medium" />
              </tr>
            </thead>
            <tbody>
              {data.map((report) => (
                <tr
                  key={`${report.inspection_id}-${report.format}`}
                  className="border-t border-surface-border"
                >
                  <td className="px-4 py-3 font-mono text-sm text-ink">
                    #{report.inspection_id}
                  </td>
                  <td className="px-4 py-3 text-sm uppercase text-ink-muted">{report.format}</td>
                  <td className="px-4 py-3 text-sm text-ink-muted">
                    {formatSize(report.size_bytes)}
                  </td>
                  <td className="px-4 py-3 text-right">
                    <a href={report.download_url} className="text-sm text-accent hover:underline">
                      Download
                    </a>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      )}
    </div>
  )
}
