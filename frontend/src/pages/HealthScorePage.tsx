import { Card, PageHeader } from '../components/primitives'
import { SessionPanel } from '../components/features/SessionPanel'
import { DocSummaryCard } from '../components/features/DocSummaryCard'

export function HealthScorePage() {
  return (
    <div className="max-w-3xl">
      <PageHeader
        title="Fused health score"
        subtitle="Combine vision, process data and machine health into a single 0–100 score with a per-modality breakdown."
      />
      <Card className="mb-10 p-6">
        <SessionPanel />
      </Card>

      <PageHeader
        title="Document summary"
        subtitle="Extract key points, entities and risks from a maintenance log or spec sheet (PDF) — the fourth data modality."
      />
      <Card className="p-6">
        <DocSummaryCard />
      </Card>
    </div>
  )
}
