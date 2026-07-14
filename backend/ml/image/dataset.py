"""Image transforms and dataset for MVTec-style good-vs-defect classification.

MVTec AD ships only "good" images in each category's train split, with defects in
the test split. For a supervised binary classifier we pool every image, label it
good vs defect from its folder name, and use a persisted stratified split. This is
disclosed in the report as a supervised re-split of MVTec AD.
"""

from __future__ import annotations

import json
from pathlib import Path

import torch
from PIL import Image
from torch.utils.data import Dataset
from torchvision import transforms

IMAGE_SIZE = 224
RESIZE_SIZE = 256
IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]

GOOD_LABEL = 0
DEFECT_LABEL = 1


def build_transforms(train: bool) -> transforms.Compose:
    """Return the preprocessing pipeline. Heavy augmentation for training."""
    if train:
        return transforms.Compose(
            [
                transforms.Resize((RESIZE_SIZE, RESIZE_SIZE)),
                transforms.RandomCrop(IMAGE_SIZE),
                transforms.RandomHorizontalFlip(),
                transforms.RandomVerticalFlip(),
                transforms.RandomRotation(20),
                transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.1),
                transforms.ToTensor(),
                transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD),
            ]
        )
    return transforms.Compose(
        [
            transforms.Resize((RESIZE_SIZE, RESIZE_SIZE)),
            transforms.CenterCrop(IMAGE_SIZE),
            transforms.ToTensor(),
            transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD),
        ]
    )


def inference_transform() -> transforms.Compose:
    """Deterministic transform used at serving time (matches the eval transform)."""
    return build_transforms(train=False)


class MVTecBinaryDataset(Dataset):
    """Dataset backed by a manifest file and a split index file."""

    def __init__(self, manifest_path: str | Path, split_path: str | Path, split: str, train: bool):
        manifest = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
        split_indices = json.loads(Path(split_path).read_text(encoding="utf-8"))[split]
        self.samples = [manifest["samples"][i] for i in split_indices]
        self.root = Path(manifest["root"])
        self.transform = build_transforms(train=train)

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, index: int) -> tuple[torch.Tensor, int]:
        sample = self.samples[index]
        image = Image.open(self.root / sample["path"]).convert("RGB")
        return self.transform(image), int(sample["label"])

    def labels(self) -> list[int]:
        return [int(s["label"]) for s in self.samples]
