"""Train the time-series RUL LSTM.

Run from the backend directory:
    python -m ml.timeseries.train
    python -m ml.timeseries.train --config configs/timeseries_v1.yaml --dataset synthetic
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import joblib
import numpy as np
import torch
import yaml
from sklearn.model_selection import GroupShuffleSplit
from sklearn.preprocessing import StandardScaler
from torch.utils.data import DataLoader, TensorDataset

from ml import registry
from ml.common.device import get_device
from ml.common.seeds import set_seed
from ml.timeseries.model import RULLSTM

DATA_DIR = registry.REPO_ROOT / "data" / "timeseries"
CONFIG_DEFAULT = registry.BACKEND_DIR / "configs" / "timeseries_v1.yaml"


def _scale_windows(scaler: StandardScaler, x: np.ndarray) -> np.ndarray:
    """Apply a per-sensor scaler to a batch of windows (N, W, S)."""
    n, w, s = x.shape
    return scaler.transform(x.reshape(-1, s)).reshape(n, w, s).astype(np.float32)


@torch.no_grad()
def _rmse(model: torch.nn.Module, x: np.ndarray, y: np.ndarray, device: torch.device) -> float:
    model.eval()
    preds = model(torch.tensor(x, dtype=torch.float32, device=device)).cpu().numpy()
    return float(np.sqrt(np.mean((preds - y) ** 2)))


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

    npz_path = DATA_DIR / f"{dataset}.npz"
    meta_path = DATA_DIR / f"{dataset}_meta.json"
    if not npz_path.exists():
        raise SystemExit(
            f"Missing {npz_path}. Run: python -m scripts.synth_timeseries  (or prepare_cmapss)"
        )
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    sensors, window, rul_cap = meta["sensors"], meta["window"], meta["rul_cap"]

    archive = np.load(npz_path)
    x, y, unit = archive["X"], archive["y"], archive["unit"]
    print(f"Training RUL LSTM on '{dataset}' ({x.shape[0]} windows, {len(np.unique(unit))} units)")

    # Split by unit so windows from one machine never leak across splits.
    train_idx, tmp_idx = next(
        GroupShuffleSplit(n_splits=1, test_size=0.3, random_state=config["seed"]).split(x, y, unit)
    )
    val_rel, test_rel = next(
        GroupShuffleSplit(n_splits=1, test_size=0.5, random_state=config["seed"]).split(
            x[tmp_idx], y[tmp_idx], unit[tmp_idx]
        )
    )
    val_idx, test_idx = tmp_idx[val_rel], tmp_idx[test_rel]

    scaler = StandardScaler().fit(x[train_idx].reshape(-1, len(sensors)))
    x_train = _scale_windows(scaler, x[train_idx])
    x_val = _scale_windows(scaler, x[val_idx])
    x_test = _scale_windows(scaler, x[test_idx])
    y_train, y_val, y_test = y[train_idx], y[val_idx], y[test_idx]

    loader = DataLoader(
        TensorDataset(torch.tensor(x_train), torch.tensor(y_train, dtype=torch.float32)),
        batch_size=config["batch_size"],
        shuffle=True,
    )

    model = RULLSTM(
        len(sensors), hidden=config["hidden"], num_layers=config["num_layers"], dropout=config["dropout"]
    ).to(device)
    criterion = torch.nn.SmoothL1Loss()
    optimizer = torch.optim.Adam(model.parameters(), lr=config["lr"], weight_decay=config["weight_decay"])

    best_rmse, best_state, since_improve = float("inf"), None, 0
    for epoch in range(1, config["epochs"] + 1):
        model.train()
        for xb, yb in loader:
            xb, yb = xb.to(device), yb.to(device)
            optimizer.zero_grad()
            loss = criterion(model(xb), yb)
            loss.backward()
            optimizer.step()

        val_rmse = _rmse(model, x_val, y_val, device)
        if epoch % 5 == 0 or epoch == 1:
            print(f"epoch {epoch:2d} | val_rmse {val_rmse:.3f}")
        if val_rmse < best_rmse:
            best_rmse, since_improve = val_rmse, 0
            best_state = {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}
        else:
            since_improve += 1
            if since_improve >= config["early_stopping_patience"]:
                print(f"Early stopping at epoch {epoch}")
                break

    assert best_state is not None
    model.load_state_dict(best_state)
    test_rmse = _rmse(model, x_test, y_test, device)
    print(f"TEST | rmse {test_rmse:.3f} (RUL units, cap {rul_cap})")

    version = config["version"]
    vdir = registry.version_dir("timeseries", version)
    vdir.mkdir(parents=True, exist_ok=True)

    weights_path = vdir / "weights.pt"
    torch.save(model.state_dict(), weights_path)
    joblib.dump(scaler, vdir / "scaler.joblib")

    defaults = {
        sensor: float(np.median(x[train_idx][:, :, i]))
        for i, sensor in enumerate(sensors)
    }
    (vdir / "meta.json").write_text(
        json.dumps(
            {"sensors": sensors, "window": window, "rul_cap": rul_cap, "defaults": defaults},
            indent=2,
        ),
        encoding="utf-8",
    )
    (vdir / "config.json").write_text(json.dumps(config, indent=2), encoding="utf-8")
    metrics = {"val_best_rmse": float(best_rmse), "test": {"rmse": float(test_rmse)}, "num_train": int(len(train_idx))}
    (vdir / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")

    registry.register_version(
        "timeseries", version, weights_path, metrics=metrics, train_config=config, make_active=True
    )
    print(f"Saved and registered timeseries/{version} -> {weights_path}")


if __name__ == "__main__":
    main()
