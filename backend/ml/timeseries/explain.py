"""Integrated Gradients for the time-series RUL model.

Self-contained (no captum dependency): attributes the RUL estimate back to each
timestep-per-sensor, then aggregates to a per-sensor importance for a readable summary.
The baseline is the per-sensor mean (zero in standardized space).
"""

from __future__ import annotations

import numpy as np
import torch


def integrated_gradients(
    model: torch.nn.Module,
    window: np.ndarray,
    steps: int = 32,
) -> np.ndarray:
    """Return an attribution matrix of shape (window, n_sensors) for a single window."""
    model.eval()
    x = torch.tensor(window[None, :, :], dtype=torch.float32)
    baseline = torch.zeros_like(x)

    total_grad = torch.zeros_like(x)
    for step in range(1, steps + 1):
        alpha = step / steps
        point = (baseline + alpha * (x - baseline)).clone().requires_grad_(True)
        model.zero_grad(set_to_none=True)
        model(point).sum().backward()
        total_grad += point.grad.detach()

    avg_grad = total_grad / steps
    attributions = ((x - baseline) * avg_grad).squeeze(0).numpy()
    return attributions  # (window, n_sensors)


def sensor_importance(
    attributions: np.ndarray,
    sensors: list[str],
    top_k: int = 6,
) -> list[dict]:
    """Aggregate per-timestep attributions into signed per-sensor importance, sorted."""
    signed = attributions.sum(axis=0)
    magnitude = np.abs(attributions).sum(axis=0)
    items = [
        {"sensor": sensors[i], "importance": float(signed[i]), "magnitude": float(magnitude[i])}
        for i in range(len(sensors))
    ]
    items.sort(key=lambda item: item["magnitude"], reverse=True)
    return items[:top_k]
