"""Download and prepare one MVTec AD category for supervised good-vs-defect training.

Usage (from the backend directory):
    python -m scripts.prepare_mvtec --category bottle
    python -m scripts.prepare_mvtec --category bottle --source C:/path/to/bottle.tar.xz
    python -m scripts.prepare_mvtec --category bottle --source C:/path/to/bottle_dir

The script produces, under data/mvtec/:
    <category>_manifest.json  - every image with its good/defect label
    <category>_split.json     - stratified train/val/test index lists
"""

from __future__ import annotations

import argparse
import json
import shutil
import tarfile
from pathlib import Path

import requests
from sklearn.model_selection import train_test_split
from tqdm import tqdm

from ml.registry import REPO_ROOT

DATA_DIR = REPO_ROOT / "data" / "mvtec"
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp"}

# Known per-category download mirror for MVTec AD (bottle by default).
DEFAULT_SOURCES = {
    "bottle": "https://www.mydrive.ch/shares/38536/3830184030e49fe74747669442f0f282/download/420937370-1629951468/bottle.tar.xz",
}


def _download(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    print(f"Downloading {url}")
    with requests.get(url, stream=True, timeout=60) as response:
        response.raise_for_status()
        total = int(response.headers.get("content-length", 0))
        with open(dest, "wb") as handle, tqdm(total=total, unit="B", unit_scale=True) as bar:
            for chunk in response.iter_content(chunk_size=1 << 20):
                handle.write(chunk)
                bar.update(len(chunk))


def _extract(archive: Path, target_parent: Path) -> None:
    print(f"Extracting {archive.name}")
    with tarfile.open(archive, "r:xz") as tar:
        tar.extractall(target_parent, filter="data")


def _ensure_category_dir(category: str, source: str | None) -> Path:
    category_dir = DATA_DIR / category
    if category_dir.exists() and any(category_dir.rglob("*.png")):
        print(f"Using existing category directory: {category_dir}")
        return category_dir

    if source and Path(source).is_dir():
        return Path(source)

    archive = DATA_DIR / f"{category}.tar.xz"
    if source and Path(source).is_file():
        archive = Path(source)
    else:
        url = source or DEFAULT_SOURCES.get(category)
        if not url:
            raise SystemExit(
                f"No download source for category {category!r}. "
                f"Pass --source with a URL, a .tar.xz file, or an extracted directory."
            )
        if not archive.exists():
            _download(url, archive)

    _extract(archive, DATA_DIR)
    if not category_dir.exists():
        raise SystemExit(f"Extraction did not produce expected directory: {category_dir}")
    return category_dir


def _build_manifest(category_dir: Path) -> dict:
    samples: list[dict] = []
    for image_path in sorted(category_dir.rglob("*")):
        if image_path.suffix.lower() not in IMAGE_EXTENSIONS:
            continue
        parts = {p.lower() for p in image_path.parts}
        if "ground_truth" in parts:
            continue
        label = 0 if image_path.parent.name.lower() == "good" else 1
        samples.append(
            {
                "path": str(image_path.relative_to(category_dir)).replace("\\", "/"),
                "label": label,
                "source": image_path.parent.name,
            }
        )
    if not samples:
        raise SystemExit(f"No images found under {category_dir}")
    return {"root": str(category_dir), "samples": samples}


def _stratified_split(labels: list[int], seed: int) -> dict[str, list[int]]:
    indices = list(range(len(labels)))
    train_idx, temp_idx = train_test_split(
        indices, test_size=0.4, stratify=labels, random_state=seed
    )
    temp_labels = [labels[i] for i in temp_idx]
    val_idx, test_idx = train_test_split(
        temp_idx, test_size=0.5, stratify=temp_labels, random_state=seed
    )
    return {"train": sorted(train_idx), "val": sorted(val_idx), "test": sorted(test_idx)}


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare an MVTec AD category.")
    parser.add_argument("--category", default="bottle")
    parser.add_argument("--source", default=None, help="URL, .tar.xz file, or extracted directory")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    category_dir = _ensure_category_dir(args.category, args.source)

    manifest = _build_manifest(category_dir)
    labels = [s["label"] for s in manifest["samples"]]
    split = _stratified_split(labels, args.seed)

    manifest_path = DATA_DIR / f"{args.category}_manifest.json"
    split_path = DATA_DIR / f"{args.category}_split.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    split_path.write_text(json.dumps(split, indent=2), encoding="utf-8")

    good = sum(1 for label in labels if label == 0)
    defect = len(labels) - good
    print(f"Category '{args.category}': {len(labels)} images ({good} good, {defect} defect)")
    for name, idx in split.items():
        split_labels = [labels[i] for i in idx]
        print(
            f"  {name:5s}: {len(idx):4d}  "
            f"(good={split_labels.count(0)}, defect={split_labels.count(1)})"
        )
    print(f"Wrote {manifest_path}")
    print(f"Wrote {split_path}")


if __name__ == "__main__":
    main()
