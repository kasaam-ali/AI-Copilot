"""Grad-CAM heatmap generation for the defect classifier."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import torch
from PIL import Image
from pytorch_grad_cam import GradCAM
from pytorch_grad_cam.utils.image import show_cam_on_image
from pytorch_grad_cam.utils.model_targets import ClassifierOutputTarget

from ml.image.dataset import IMAGE_SIZE, RESIZE_SIZE
from ml.image.model import DefectCNN


def _base_rgb(image: Image.Image) -> np.ndarray:
    """Resize + center-crop the original image to the model input, without normalizing."""
    resized = image.convert("RGB").resize((RESIZE_SIZE, RESIZE_SIZE))
    offset = (RESIZE_SIZE - IMAGE_SIZE) // 2
    cropped = resized.crop((offset, offset, offset + IMAGE_SIZE, offset + IMAGE_SIZE))
    return np.asarray(cropped, dtype=np.float32) / 255.0


def compute_gradcam_overlay(
    model: DefectCNN,
    input_tensor: torch.Tensor,
    base_image: Image.Image,
    target_class: int,
    out_path: str | Path,
) -> Path:
    """Render a Grad-CAM overlay for ``target_class`` and save it as a PNG.

    ``input_tensor`` is the normalized (1, 3, H, W) tensor fed to the model.
    ``base_image`` is the original PIL image (used as the overlay background).
    """
    rgb = _base_rgb(base_image)
    cam = GradCAM(model=model, target_layers=[model.gradcam_target_layer])
    grayscale = cam(
        input_tensor=input_tensor,
        targets=[ClassifierOutputTarget(target_class)],
    )[0]
    overlay = show_cam_on_image(rgb, grayscale, use_rgb=True)

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(overlay).save(out_path)
    return out_path
