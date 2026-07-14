"""Train the tabular defect-probability MLP.

Run from the backend directory:
    python -m ml.tabular.train
    python -m ml.tabular.train --config configs/tabular_v1.yaml --dataset synthetic
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import torch
import yaml
from sklearn.metrics import accuracy_score, precision_recall_curve, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from torch.utils.data import DataLoader, TensorDataset

from ml import registry
from ml.common.device import get_device
from ml.common.seeds import set_seed
from ml.tabular.model import BinaryFocalLoss, DefectMLP

DATA_DIR = registry.REPO_ROOT / "data" / "tabular"
CONFIG_DEFAULT = registry.BACKEND_DIR / "configs" / "tabular_v1.yaml"


def _recall_at_precision(y_true: np.ndarray, probs: np.ndarray, target: float = 0.9) -> float:
    precision, recall, _ = precision_recall_curve(y_true, probs)
    feasible = recall[precision >= target]
    return float(feasible.max()) if feasible.size else 0.0


@torch.no_grad()
def _probs(model: torch.nn.Module, x: np.ndarray, device: torch.device) -> np.ndarray:
    model.eval()
    logits = model(torch.tensor(x, dtype=torch.float32, device=device))
    return torch.sigmoid(logits).cpu().numpy()


def _metrics(y_true: np.ndarray, probs: np.ndarray) -> dict:
    return {
        "auroc": float(roc_auc_score(y_true, probs)),
        "accuracy": float(accuracy_score(y_true, (probs >= 0.5).astype(int))),
        "recall_at_precision_90": _recall_at_precision(y_true, probs),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default=str(CONFIG_DEFAULT))
    parser.add_argument("--dataset", default=None)
    parser.add_argument("--epochs", type=int, default=None)
    args = parser.parse_args()

    config = yaml.safe_load(Path(args.config).read_text(encoding="utf-8"))
    if args.dataset:
        config["dataset"] = args.dataset
    if args.epochs is not None:
        config["epochs"] = args.epochs

    set_seed(config["seed"])
    device = get_device()
    dataset = config["dataset"]

    csv_path = DATA_DIR / f"{dataset}.csv"
    meta_path = DATA_DIR / f"{dataset}_meta.json"
    if not csv_path.exists():
        raise SystemExit(
            f"Missing {csv_path}. Run: python -m scripts.synth_tabular  (or prepare_secom)"
        )
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    features, label = meta["features"], meta["label"]

    frame = pd.read_csv(csv_path)
    x = frame[features].to_numpy(dtype=np.float64)
    y = frame[label].to_numpy(dtype=np.float64)
    print(f"Training tabular model on '{dataset}' ({len(frame)} rows, {int(y.sum())} defect)")

    x_train, x_tmp, y_train, y_tmp = train_test_split(
        x, y, test_size=0.3, stratify=y, random_state=config["seed"]
    )
    x_val, x_test, y_val, y_test = train_test_split(
        x_tmp, y_tmp, test_size=0.5, stratify=y_tmp, random_state=config["seed"]
    )

    scaler = StandardScaler().fit(x_train)
    x_train_s = scaler.transform(x_train)
    x_val_s = scaler.transform(x_val)
    x_test_s = scaler.transform(x_test)

    loader = DataLoader(
        TensorDataset(
            torch.tensor(x_train_s, dtype=torch.float32),
            torch.tensor(y_train, dtype=torch.float32),
        ),
        batch_size=config["batch_size"],
        shuffle=True,
    )

    model = DefectMLP(len(features), tuple(config["hidden"]), dropout=config["dropout"]).to(device)
    criterion = BinaryFocalLoss(gamma=config["focal_gamma"], alpha=config["focal_alpha"])
    optimizer = torch.optim.Adam(model.parameters(), lr=config["lr"], weight_decay=config["weight_decay"])

    best_auroc, best_state, since_improve = -1.0, None, 0
    for epoch in range(1, config["epochs"] + 1):
        model.train()
        for xb, yb in loader:
            xb, yb = xb.to(device), yb.to(device)
            optimizer.zero_grad()
            loss = criterion(model(xb), yb)
            loss.backward()
            optimizer.step()

        val_auroc = float(roc_auc_score(y_val, _probs(model, x_val_s, device)))
        if epoch % 5 == 0 or epoch == 1:
            print(f"epoch {epoch:2d} | val_auroc {val_auroc:.4f}")
        if val_auroc > best_auroc:
            best_auroc, since_improve = val_auroc, 0
            best_state = {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}
        else:
            since_improve += 1
            if since_improve >= config["early_stopping_patience"]:
                print(f"Early stopping at epoch {epoch}")
                break

    assert best_state is not None
    model.load_state_dict(best_state)
    test = _metrics(y_test, _probs(model, x_test_s, device))
    print(
        f"TEST | auroc {test['auroc']:.4f} | acc {test['accuracy']:.4f} "
        f"| recall@P0.9 {test['recall_at_precision_90']:.4f}"
    )

    version = config["version"]
    vdir = registry.version_dir("tabular", version)
    vdir.mkdir(parents=True, exist_ok=True)

    weights_path = vdir / "weights.pt"
    torch.save(model.state_dict(), weights_path)
    joblib.dump(scaler, vdir / "scaler.joblib")

    rng = np.random.default_rng(config["seed"])
    background = x_train_s[rng.choice(len(x_train_s), min(config["shap_background"], len(x_train_s)), replace=False)]
    np.save(vdir / "background.npy", background)

    defaults = {feature: float(np.median(frame[feature])) for feature in features}
    (vdir / "meta.json").write_text(
        json.dumps({"features": features, "label": label, "defaults": defaults}, indent=2),
        encoding="utf-8",
    )
    (vdir / "config.json").write_text(json.dumps(config, indent=2), encoding="utf-8")
    metrics = {"val_best_auroc": float(best_auroc), "test": test, "num_train": int(len(x_train))}
    (vdir / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")

    registry.register_version(
        "tabular", version, weights_path, metrics=metrics, train_config=config, make_active=True
    )
    print(f"Saved and registered tabular/{version} -> {weights_path}")


if __name__ == "__main__":
    main()
