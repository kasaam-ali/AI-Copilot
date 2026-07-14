"""Train the image defect classifier on a prepared MVTec category.

Run from the backend directory:
    python -m ml.image.train
    python -m ml.image.train --config configs/image_v1.yaml --epochs 25
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
import yaml
from sklearn.metrics import accuracy_score, roc_auc_score
from torch.utils.data import DataLoader

from ml import registry
from ml.common.device import get_device
from ml.common.seeds import set_seed
from ml.image.dataset import MVTecBinaryDataset
from ml.image.model import DEFECT_INDEX, DefectCNN

DATA_DIR = registry.REPO_ROOT / "data" / "mvtec"
CONFIG_DEFAULT = registry.BACKEND_DIR / "configs" / "image_v1.yaml"


def _loaders(category: str, batch_size: int, num_workers: int):
    manifest = DATA_DIR / f"{category}_manifest.json"
    split = DATA_DIR / f"{category}_split.json"
    if not manifest.exists():
        raise SystemExit(
            f"Missing {manifest}. Run: python -m scripts.prepare_mvtec --category {category}"
        )
    train_ds = MVTecBinaryDataset(manifest, split, "train", train=True)
    val_ds = MVTecBinaryDataset(manifest, split, "val", train=False)
    test_ds = MVTecBinaryDataset(manifest, split, "test", train=False)
    return (
        train_ds,
        DataLoader(train_ds, batch_size=batch_size, shuffle=True, num_workers=num_workers),
        DataLoader(val_ds, batch_size=batch_size, shuffle=False, num_workers=num_workers),
        DataLoader(test_ds, batch_size=batch_size, shuffle=False, num_workers=num_workers),
    )


def _class_weights(labels: list[int]) -> torch.Tensor:
    counts = np.bincount(labels, minlength=2).astype(np.float64)
    counts[counts == 0] = 1.0
    weights = counts.sum() / (2.0 * counts)
    return torch.tensor(weights, dtype=torch.float32)


@torch.no_grad()
def _evaluate(model: nn.Module, loader: DataLoader, device: torch.device) -> dict:
    model.eval()
    probs: list[float] = []
    targets: list[int] = []
    for x, y in loader:
        p = torch.softmax(model(x.to(device)), dim=1)[:, DEFECT_INDEX]
        probs.extend(p.cpu().tolist())
        targets.extend(y.tolist())
    prob_arr = np.array(probs)
    target_arr = np.array(targets)
    preds = (prob_arr >= 0.5).astype(int)
    metrics = {"accuracy": float(accuracy_score(target_arr, preds))}
    metrics["auroc"] = (
        float(roc_auc_score(target_arr, prob_arr))
        if len(set(target_arr.tolist())) > 1
        else float("nan")
    )
    return metrics


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default=str(CONFIG_DEFAULT))
    parser.add_argument("--epochs", type=int, default=None)
    parser.add_argument("--category", default=None, help="Override the dataset category")
    args = parser.parse_args()

    config = yaml.safe_load(Path(args.config).read_text(encoding="utf-8"))
    if args.epochs is not None:
        config["epochs"] = args.epochs
    if args.category is not None:
        config["category"] = args.category

    set_seed(config["seed"])
    device = get_device()
    category = config["category"]
    print(f"Training image model on '{category}' (device={device})")

    train_ds, train_loader, val_loader, test_loader = _loaders(
        category, config["batch_size"], config["num_workers"]
    )

    model = DefectCNN(dropout=config["dropout"], pretrained=True).to(device)
    model.freeze_backbone(unfreeze_last_block=config["unfreeze_last_block"])

    criterion = nn.CrossEntropyLoss(weight=_class_weights(train_ds.labels()).to(device))
    trainable = [p for p in model.parameters() if p.requires_grad]
    optimizer = torch.optim.Adam(trainable, lr=config["lr"], weight_decay=config["weight_decay"])

    best_score = -1.0
    best_state: dict | None = None
    since_improve = 0

    for epoch in range(1, config["epochs"] + 1):
        model.train()
        running = 0.0
        for x, y in train_loader:
            x, y = x.to(device), y.to(device)
            optimizer.zero_grad()
            loss = criterion(model(x), y)
            loss.backward()
            optimizer.step()
            running += loss.item() * x.size(0)

        train_loss = running / len(train_loader.dataset)
        val = _evaluate(model, val_loader, device)
        score = val["auroc"] if not np.isnan(val["auroc"]) else val["accuracy"]
        print(
            f"epoch {epoch:2d} | train_loss {train_loss:.4f} "
            f"| val_auroc {val['auroc']:.4f} | val_acc {val['accuracy']:.4f}"
        )

        if score > best_score:
            best_score = score
            best_state = {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}
            since_improve = 0
        else:
            since_improve += 1
            if since_improve >= config["early_stopping_patience"]:
                print(f"Early stopping at epoch {epoch}")
                break

    assert best_state is not None
    model.load_state_dict(best_state)
    test = _evaluate(model, test_loader, device)
    print(f"TEST | auroc {test['auroc']:.4f} | acc {test['accuracy']:.4f}")

    version = config["version"]
    vdir = registry.version_dir("image", version)
    vdir.mkdir(parents=True, exist_ok=True)
    weights_path = vdir / "weights.pt"
    torch.save(model.state_dict(), weights_path)
    (vdir / "config.json").write_text(json.dumps(config, indent=2), encoding="utf-8")

    metrics = {"val_best_score": float(best_score), "test": test, "num_train": len(train_ds)}
    (vdir / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")

    registry.register_version(
        "image", version, weights_path, metrics=metrics, train_config=config, make_active=True
    )
    print(f"Saved and registered image/{version} -> {weights_path}")


if __name__ == "__main__":
    main()
