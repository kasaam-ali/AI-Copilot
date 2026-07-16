"""Inference for the tabular defect model, with MC-Dropout uncertainty."""

from __future__ import annotations

import json
from dataclasses import dataclass

import joblib
import numpy as np
import torch

from ml import registry
from ml.tabular.model import DefectMLP


@dataclass
class TabularPrediction:
    label: str
    defect_probability: float
    confidence: float
    uncertainty: float


class TabularModelBundle:
    def __init__(self, model, scaler, features, defaults, background, version, weights_sha256):  # noqa: ANN001
        self.model = model
        self.scaler = scaler
        self.features = features
        self.defaults = defaults
        self.background = background
        self.version = version
        self.weights_sha256 = weights_sha256


_bundle_cache: dict[str, TabularModelBundle] = {}


def load_active_bundle(force_reload: bool = False) -> TabularModelBundle:
    active = registry.get_active("tabular")
    if active is None:
        raise RuntimeError(
            "No active tabular model. Train one with: python -m ml.tabular.train"
        )
    key = f"{active['version']}:{active['weights_sha256']}"
    if not force_reload and key in _bundle_cache:
        return _bundle_cache[key]

    vdir = registry.version_dir("tabular", active["version"])
    meta = json.loads((vdir / "meta.json").read_text(encoding="utf-8"))
    features = meta["features"]
    defaults = meta.get("defaults", {})
    scaler = joblib.load(vdir / "scaler.joblib")
    background = np.load(vdir / "background.npy")

    model = DefectMLP(len(features))
    model.load_state_dict(torch.load(registry.resolve(active["weights_path"]), map_location="cpu"))
    model.eval()

    bundle = TabularModelBundle(
        model, scaler, features, defaults, background, active["version"], active["weights_sha256"]
    )
    _bundle_cache.clear()
    _bundle_cache[key] = bundle
    return bundle


def _enable_mc_dropout(model: torch.nn.Module) -> None:
    for module in model.modules():
        if isinstance(module, torch.nn.Dropout):
            module.train()


def build_feature_vector(features: dict, bundle: TabularModelBundle) -> list[float]:
    """Assemble the model input in feature order, filling gaps with training medians."""
    return [float(features.get(name, bundle.defaults.get(name, 0.0))) for name in bundle.features]


@torch.no_grad()
def _mc_probs(model: torch.nn.Module, x: torch.Tensor, passes: int) -> torch.Tensor:
    return torch.stack([torch.sigmoid(model(x)) for _ in range(passes)], dim=0)


def predict_tabular_batch(rows: list[dict], mc_passes: int = 20):
    """Predict on many feature dicts in one batched forward pass. No persistence."""
    bundle = load_active_bundle()
    raws = [build_feature_vector(row, bundle) for row in rows]
    x_scaled = bundle.scaler.transform(np.array(raws, dtype=np.float64))
    x_tensor = torch.tensor(x_scaled, dtype=torch.float32)

    _enable_mc_dropout(bundle.model)
    probs = _mc_probs(bundle.model, x_tensor, mc_passes)  # (passes, N)
    bundle.model.eval()

    means = probs.mean(dim=0).numpy()
    stds = probs.std(dim=0).numpy()

    results = []
    for mean, std in zip(means, stds):
        mean_f = float(mean)
        label = "defect" if mean_f >= 0.5 else "ok"
        confidence = mean_f if label == "defect" else 1.0 - mean_f
        results.append(
            {
                "label": label,
                "defect_probability": mean_f,
                "confidence": float(confidence),
                "uncertainty": float(std),
            }
        )
    return results, bundle


def predict_tabular(features: dict, mc_passes: int = 20):
    """Predict on a feature dict. Returns prediction, scaled input, raw vector and bundle."""
    bundle = load_active_bundle()
    raw = build_feature_vector(features, bundle)
    x_scaled = bundle.scaler.transform(np.array([raw], dtype=np.float64))
    x_tensor = torch.tensor(x_scaled, dtype=torch.float32)

    _enable_mc_dropout(bundle.model)
    probs = _mc_probs(bundle.model, x_tensor, mc_passes)
    bundle.model.eval()

    mean = float(probs.mean())
    std = float(probs.std())
    label = "defect" if mean >= 0.5 else "ok"
    confidence = mean if label == "defect" else 1.0 - mean

    prediction = TabularPrediction(
        label=label,
        defect_probability=mean,
        confidence=confidence,
        uncertainty=std,
    )
    return prediction, x_scaled, raw, bundle
