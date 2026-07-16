"""YOLOv8 defect detection inference.

Loads the active ``detection`` weights from the registry (e.g. a NEU-DET-trained YOLOv8n);
if none is registered yet it falls back to the pretrained ``yolov8n.pt`` so the pipeline is
never dead while the domain weights are trained on Colab.
"""

from __future__ import annotations

from dataclasses import dataclass

from PIL import Image

from ml import registry

FALLBACK_WEIGHTS = "yolov8n.pt"


@dataclass
class Detection:
    label: str
    confidence: float
    box: list[float]  # [x1, y1, x2, y2] in pixels


class DetectorBundle:
    def __init__(self, model, names, version, weights_sha256, is_fallback):  # noqa: ANN001
        self.model = model
        self.names = names
        self.version = version
        self.weights_sha256 = weights_sha256
        self.is_fallback = is_fallback


_cache: dict[str, DetectorBundle] = {}


def load_active_detector(force_reload: bool = False) -> DetectorBundle:
    from ultralytics import YOLO

    active = registry.get_active("detection")
    if active is not None:
        key = f"{active['version']}:{active['weights_sha256']}"
        if not force_reload and key in _cache:
            return _cache[key]
        model = YOLO(str(registry.resolve(active["weights_path"])))
        bundle = DetectorBundle(model, model.names, active["version"], active["weights_sha256"], False)
    else:
        key = "fallback:yolov8n"
        if not force_reload and key in _cache:
            return _cache[key]
        model = YOLO(FALLBACK_WEIGHTS)
        bundle = DetectorBundle(model, model.names, "pretrained-yolov8n", "", True)

    _cache.clear()
    _cache[key] = bundle
    return bundle


def detect(image: Image.Image, conf: float = 0.25, max_det: int = 100):
    """Return (list[Detection], bundle) for a PIL image."""
    bundle = load_active_detector()
    result = bundle.model.predict(image, conf=conf, max_det=max_det, verbose=False)[0]

    detections: list[Detection] = []
    for box in result.boxes:
        cls_index = int(box.cls[0])
        detections.append(
            Detection(
                label=str(bundle.names[cls_index]),
                confidence=float(box.conf[0]),
                box=[float(v) for v in box.xyxy[0]],
            )
        )
    detections.sort(key=lambda d: d.confidence, reverse=True)
    return detections, bundle
