"""Inference for the time-series RUL model, with MC-Dropout uncertainty."""

from __future__ import annotations

import json
from dataclasses import dataclass

import joblib
import numpy as np
import torch

from ml import registry
from ml.timeseries.model import RULLSTM


@dataclass
class TimeSeriesPrediction:
    label: str
    rul: float
    risk: float
    confidence: float
    uncertainty: float
    rul_std: float


def _band(rul: float, rul_cap: float) -> str:
    ratio = rul / rul_cap
    if ratio >= 0.8:
        return "healthy"
    if ratio >= 0.4:
        return "monitor"
    if ratio >= 0.16:
        return "degrading"
    return "critical"


class TimeSeriesModelBundle:
    def __init__(self, model, scaler, sensors, window, rul_cap, defaults, version, weights_sha256):  # noqa: ANN001
        self.model = model
        self.scaler = scaler
        self.sensors = sensors
        self.window = window
        self.rul_cap = rul_cap
        self.defaults = defaults
        self.version = version
        self.weights_sha256 = weights_sha256


_bundle_cache: dict[str, TimeSeriesModelBundle] = {}


def load_active_bundle(force_reload: bool = False) -> TimeSeriesModelBundle:
    active = registry.get_active("timeseries")
    if active is None:
        raise RuntimeError(
            "No active timeseries model. Train one with: python -m ml.timeseries.train"
        )
    key = f"{active['version']}:{active['weights_sha256']}"
    if not force_reload and key in _bundle_cache:
        return _bundle_cache[key]

    vdir = registry.version_dir("timeseries", active["version"])
    meta = json.loads((vdir / "meta.json").read_text(encoding="utf-8"))
    sensors = meta["sensors"]
    scaler = joblib.load(vdir / "scaler.joblib")

    model = RULLSTM(len(sensors))
    model.load_state_dict(torch.load(registry.resolve(active["weights_path"]), map_location="cpu"))
    model.eval()

    bundle = TimeSeriesModelBundle(
        model,
        scaler,
        sensors,
        int(meta["window"]),
        float(meta["rul_cap"]),
        meta.get("defaults", {}),
        active["version"],
        active["weights_sha256"],
    )
    _bundle_cache.clear()
    _bundle_cache[key] = bundle
    return bundle


def build_window(series: list[list[float]], bundle: TimeSeriesModelBundle) -> np.ndarray:
    """Take the most recent `window` timesteps (front-padding a short series), scaled."""
    n_sensors = len(bundle.sensors)
    rows = [list(map(float, row))[:n_sensors] for row in series if row]
    if not rows:
        raise ValueError("Empty time-series input.")
    for row in rows:
        if len(row) != n_sensors:
            raise ValueError(f"Each timestep must have {n_sensors} sensor values.")

    if len(rows) >= bundle.window:
        rows = rows[-bundle.window :]
    else:
        rows = [rows[0]] * (bundle.window - len(rows)) + rows

    raw = np.asarray(rows, dtype=np.float64)
    scaled = bundle.scaler.transform(raw).astype(np.float32)
    return scaled  # (window, n_sensors)


def _enable_mc_dropout(model: torch.nn.Module) -> None:
    for module in model.modules():
        if isinstance(module, torch.nn.Dropout):
            module.train()


@torch.no_grad()
def _mc_rul(model: torch.nn.Module, x: torch.Tensor, passes: int) -> torch.Tensor:
    return torch.stack([model(x) for _ in range(passes)], dim=0)


def predict_timeseries(series: list[list[float]], mc_passes: int = 20):
    """Predict RUL + risk from a sensor time-series. Returns prediction, window, bundle."""
    bundle = load_active_bundle()
    window = build_window(series, bundle)
    x_tensor = torch.tensor(window[None, :, :], dtype=torch.float32)

    _enable_mc_dropout(bundle.model)
    ruls = _mc_rul(bundle.model, x_tensor, mc_passes)
    bundle.model.eval()

    mean_rul = float(np.clip(ruls.mean().item(), 0.0, bundle.rul_cap))
    rul_std = float(ruls.std().item())
    risk = float(np.clip(1.0 - mean_rul / bundle.rul_cap, 0.0, 1.0))
    uncertainty = float(np.clip(rul_std / bundle.rul_cap, 0.0, 1.0))
    confidence = float(np.clip(1.0 - uncertainty, 0.0, 1.0))

    prediction = TimeSeriesPrediction(
        label=_band(mean_rul, bundle.rul_cap),
        rul=mean_rul,
        risk=risk,
        confidence=confidence,
        uncertainty=uncertainty,
        rul_std=rul_std,
    )
    return prediction, window, bundle
