import { Card, PageHeader } from '../components/primitives'
import { DetectionPanel } from '../components/features/DetectionPanel'
import { VideoDetectionPanel } from '../components/features/VideoDetectionPanel'

export function InspectPage() {
  return (
    <div className="max-w-3xl">
      <PageHeader
        title="Defect detection"
        subtitle="Upload a product photo — the detector localizes each defect with a labeled bounding box and a confidence score."
      />
      <Card className="mb-10 p-6">
        <DetectionPanel />
      </Card>

      <PageHeader
        title="Video inspection"
        subtitle="Upload a clip — frames are sampled and defects are counted across the whole video."
      />
      <Card className="p-6">
        <VideoDetectionPanel />
      </Card>
    </div>
  )
}
