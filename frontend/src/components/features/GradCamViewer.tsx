export function GradCamViewer({ src, label }: { src: string; label: string }) {
  return (
    <div>
      <div className="mb-2 text-sm font-medium text-ink">Grad-CAM — {label}</div>
      <div className="overflow-hidden rounded-lg border border-surface-border bg-surface-panel">
        <img src={src} alt="Grad-CAM heatmap" className="block w-full" />
      </div>
      <div className="mt-2 text-xs text-ink-muted">
        Warm regions are where the model focused when deciding.
      </div>
    </div>
  )
}
