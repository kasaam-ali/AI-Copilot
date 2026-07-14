"""Generate a synthetic good-vs-defect product image dataset.

This is a fallback so the full vision pipeline (train -> registry -> inference ->
Grad-CAM -> API -> UI) can be validated without the real MVTec AD download. Images
are procedural manufactured-part renders; defect images carry an injected anomaly
(scratch, blob or crack). Output mirrors an MVTec category folder layout:

    data/mvtec/synthetic/good/*.png
    data/mvtec/synthetic/defect/*.png

Then run: python -m scripts.prepare_mvtec --category synthetic --source data/mvtec/synthetic
"""

from __future__ import annotations

import argparse

import numpy as np
from PIL import Image, ImageDraw

from ml.registry import REPO_ROOT

OUT_DIR = REPO_ROOT / "data" / "mvtec" / "synthetic"


def _background(rng: np.random.Generator) -> Image.Image:
    base = int(rng.integers(200, 230))
    arr = np.full((256, 256, 3), base, dtype=np.int16)
    arr = arr + rng.normal(0, 6, (256, 256, 3)).astype(np.int16)
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))


def _draw_product(img: Image.Image, rng: np.random.Generator) -> tuple[int, int, int]:
    draw = ImageDraw.Draw(img)
    cx = 128 + int(rng.integers(-12, 12))
    cy = 128 + int(rng.integers(-12, 12))
    radius = int(rng.integers(70, 86))
    color = tuple(int(c) for c in rng.integers(90, 150, 3))
    draw.ellipse(
        [cx - radius, cy - radius, cx + radius, cy + radius],
        fill=color,
        outline=(60, 60, 60),
        width=3,
    )
    for ring in range(20, radius, 18):
        draw.ellipse(
            [cx - ring, cy - ring, cx + ring, cy + ring],
            outline=tuple(min(255, c + 20) for c in color),
            width=2,
        )
    return cx, cy, radius


def _add_defect(img: Image.Image, center: tuple[int, int, int], rng: np.random.Generator) -> None:
    cx, cy, radius = center
    draw = ImageDraw.Draw(img)
    kind = int(rng.integers(0, 3))
    angle = float(rng.uniform(0, 2 * np.pi))
    dist = float(rng.uniform(0, radius * 0.6))
    px = int(cx + dist * np.cos(angle))
    py = int(cy + dist * np.sin(angle))

    if kind == 0:  # scratch
        dx, dy = int(rng.integers(15, 40)), int(rng.integers(-10, 10))
        draw.line([px - dx, py - dy, px + dx, py + dy], fill=(30, 30, 30), width=int(rng.integers(2, 4)))
    elif kind == 1:  # contamination blob
        br = int(rng.integers(6, 14))
        draw.ellipse([px - br, py - br, px + br, py + br], fill=(200, 40, 40))
    else:  # crack
        points = [(px, py)]
        for _ in range(5):
            px += int(rng.integers(-8, 8))
            py += int(rng.integers(4, 10))
            points.append((px, py))
        draw.line(points, fill=(20, 20, 20), width=2)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate synthetic defect images.")
    parser.add_argument("--per-class", type=int, default=180)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    rng = np.random.default_rng(args.seed)
    for cls in ("good", "defect"):
        (OUT_DIR / cls).mkdir(parents=True, exist_ok=True)

    for i in range(args.per_class):
        for cls in ("good", "defect"):
            img = _background(rng)
            center = _draw_product(img, rng)
            if cls == "defect":
                _add_defect(img, center, rng)
            img.save(OUT_DIR / cls / f"{cls}_{i:04d}.png")

    print(f"Generated {args.per_class} good + {args.per_class} defect images at {OUT_DIR}")


if __name__ == "__main__":
    main()
