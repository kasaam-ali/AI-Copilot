"""SHAP explanations for the tabular defect model.

Uses a model-agnostic KernelExplainer over the (few) named features, which is robust
and produces signed per-feature contributions for a readable bar chart.
"""

from __future__ import annotations

import numpy as np
import torch


def _predict_proba(model: torch.nn.Module):
    def forward(x: np.ndarray) -> np.ndarray:
        model.eval()
        with torch.no_grad():
            tensor = torch.tensor(np.asarray(x), dtype=torch.float32)
            return torch.sigmoid(model(tensor)).numpy()

    return forward


def compute_shap(
    model: torch.nn.Module,
    background: np.ndarray,
    x_scaled: np.ndarray,
    feature_names: list[str],
    raw_values: list[float],
    top_k: int = 8,
    nsamples: int = 100,
) -> tuple[float, list[dict], list[dict]]:
    """Return (base_value, top_k contributions, all contributions), signed and sorted."""
    import shap  # imported lazily to keep app startup fast

    explainer = shap.KernelExplainer(_predict_proba(model), background)
    values = np.array(explainer.shap_values(x_scaled, nsamples=nsamples, silent=True)).reshape(-1)
    base = float(np.reshape(explainer.expected_value, -1)[0])

    contributions = [
        {
            "feature": feature_names[i],
            "value": float(raw_values[i]),
            "contribution": float(values[i]),
        }
        for i in range(len(feature_names))
    ]
    contributions.sort(key=lambda item: abs(item["contribution"]), reverse=True)
    return base, contributions[:top_k], contributions
