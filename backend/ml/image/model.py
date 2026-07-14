"""CNN defect classifier: ResNet18 transfer learning with an MC-Dropout head.

Two output classes: index 0 = "good", index 1 = "defect".
"""

from __future__ import annotations

import torch
import torch.nn as nn
from torchvision.models import ResNet18_Weights, resnet18

CLASS_NAMES = ["good", "defect"]
DEFECT_INDEX = 1


class DefectCNN(nn.Module):
    """ResNet18 backbone with a dropout + linear classification head."""

    def __init__(
        self,
        num_classes: int = 2,
        dropout: float = 0.5,
        pretrained: bool = True,
    ) -> None:
        super().__init__()
        weights = ResNet18_Weights.IMAGENET1K_V1 if pretrained else None
        self.backbone = resnet18(weights=weights)
        in_features = self.backbone.fc.in_features
        self.backbone.fc = nn.Sequential(
            nn.Dropout(p=dropout),
            nn.Linear(in_features, num_classes),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.backbone(x)

    def freeze_backbone(self, unfreeze_last_block: bool = True) -> None:
        """Freeze the backbone, keeping the head (and optionally layer4) trainable."""
        for param in self.backbone.parameters():
            param.requires_grad = False
        for param in self.backbone.fc.parameters():
            param.requires_grad = True
        if unfreeze_last_block:
            for param in self.backbone.layer4.parameters():
                param.requires_grad = True

    @property
    def gradcam_target_layer(self) -> nn.Module:
        """The convolutional layer used as the Grad-CAM target."""
        return self.backbone.layer4[-1]
