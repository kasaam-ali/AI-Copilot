"""Tabular ANN (MLP) for defect probability, with a binary focal loss."""

from __future__ import annotations

import torch
import torch.nn as nn
import torch.nn.functional as F


class DefectMLP(nn.Module):
    """Multi-layer perceptron producing a single defect logit."""

    def __init__(
        self,
        in_features: int,
        hidden: tuple[int, ...] = (256, 128, 64),
        dropout: float = 0.3,
    ) -> None:
        super().__init__()
        layers: list[nn.Module] = []
        prev = in_features
        for width in hidden:
            layers += [nn.Linear(prev, width), nn.BatchNorm1d(width), nn.ReLU(), nn.Dropout(dropout)]
            prev = width
        layers.append(nn.Linear(prev, 1))
        self.net = nn.Sequential(*layers)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x).squeeze(-1)


class BinaryFocalLoss(nn.Module):
    """Focal loss for imbalanced binary classification (Lin et al., 2017)."""

    def __init__(self, gamma: float = 2.0, alpha: float = 0.25) -> None:
        super().__init__()
        self.gamma = gamma
        self.alpha = alpha

    def forward(self, logits: torch.Tensor, targets: torch.Tensor) -> torch.Tensor:
        ce = F.binary_cross_entropy_with_logits(logits, targets, reduction="none")
        p = torch.sigmoid(logits)
        p_t = p * targets + (1 - p) * (1 - targets)
        loss = ce * (1 - p_t) ** self.gamma
        if self.alpha is not None:
            alpha_t = self.alpha * targets + (1 - self.alpha) * (1 - targets)
            loss = alpha_t * loss
        return loss.mean()
