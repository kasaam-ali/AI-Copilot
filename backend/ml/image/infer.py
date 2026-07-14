"""Inference for the image defect classifier, with MC-Dropout uncertainty."""

from __future__ import annotations

from dataclasses import dataclass

import torch
from PIL import Image

from ml import registry
from ml.image.dataset import inference_transform
from ml.image.model import CLASS_NAMES, DEFECT_INDEX, DefectCNN


@dataclass
class ImagePrediction:
    label: str
    label_index: int
    confidence: float
    uncertainty: float
    defect_probability: float
    class_probs: dict[str, float]


class ImageModelBundle:
    """A loaded model plus the metadata needed for traceability."""

    def __init__(self, model: DefectCNN, version: str, weights_sha256: str) -> None:
        self.model = model
        self.version = version
        self.weights_sha256 = weights_sha256
        self.transform = inference_transform()


_bundle_cache: dict[str, ImageModelBundle] = {}


def load_active_bundle(force_reload: bool = False) -> ImageModelBundle:
    """Load the active image model, caching by version + weights hash."""
    active = registry.get_active("image")
    if active is None:
        raise RuntimeError(
            "No active image model. Train one with: python -m ml.image.train"
        )
    key = f"{active['version']}:{active['weights_sha256']}"
    if not force_reload and key in _bundle_cache:
        return _bundle_cache[key]

    model = DefectCNN(pretrained=False)
    state = torch.load(registry.resolve(active["weights_path"]), map_location="cpu")
    model.load_state_dict(state)
    model.eval()

    bundle = ImageModelBundle(model, active["version"], active["weights_sha256"])
    _bundle_cache.clear()
    _bundle_cache[key] = bundle
    return bundle


def _enable_mc_dropout(model: torch.nn.Module) -> None:
    """Keep BatchNorm in eval mode but re-enable Dropout for MC sampling."""
    for module in model.modules():
        if isinstance(module, torch.nn.Dropout):
            module.train()


@torch.no_grad()
def _mc_forward(model: torch.nn.Module, x: torch.Tensor, passes: int) -> torch.Tensor:
    samples = [torch.softmax(model(x), dim=1) for _ in range(passes)]
    return torch.stack(samples, dim=0)  # (passes, 1, num_classes)


def predict_image(
    image: Image.Image,
    mc_passes: int = 20,
) -> tuple[ImagePrediction, torch.Tensor, ImageModelBundle]:
    """Predict on a PIL image. Returns the prediction, the input tensor and the bundle."""
    bundle = load_active_bundle()
    model = bundle.model
    x = bundle.transform(image.convert("RGB")).unsqueeze(0)

    _enable_mc_dropout(model)
    probs = _mc_forward(model, x, mc_passes)
    model.eval()

    mean = probs.mean(dim=0)[0]
    std = probs.std(dim=0)[0]

    label_index = int(torch.argmax(mean).item())
    prediction = ImagePrediction(
        label=CLASS_NAMES[label_index],
        label_index=label_index,
        confidence=float(mean[label_index]),
        uncertainty=float(std[label_index]),
        defect_probability=float(mean[DEFECT_INDEX]),
        class_probs={CLASS_NAMES[i]: float(mean[i]) for i in range(len(CLASS_NAMES))},
    )
    return prediction, x, bundle
