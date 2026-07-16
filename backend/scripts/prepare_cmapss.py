"""Prepare NASA C-MAPSS FD001 as a drop-in replacement for the synthetic RUL data.

C-MAPSS FD001 is real turbofan run-to-failure data: per-unit cycles with 3 operating
settings and 21 sensors. This writes the SAME pre-windowed format as
``scripts/synth_timeseries.py`` (X, y, unit + meta), so ``ml/timeseries/train.py`` and the
serving code work unchanged — only a retrain is needed.

Place the dataset file first (from the NASA C-MAPSS turbofan set):
    data/timeseries/cmapss/train_FD001.txt

Then:
    python -m scripts.prepare_cmapss
    python -m ml.timeseries.train --dataset cmapss
"""

from __future__ import annotations

import argparse
import json

import numpy as np
import pandas as pd

from ml.registry import REPO_ROOT

OUT_DIR = REPO_ROOT / "data" / "timeseries"
DEFAULT_SOURCE = OUT_DIR / "cmapss" / "train_FD001.txt"

COLUMNS = (
    ["unit", "cycle", "op_1", "op_2", "op_3"]
    + [f"sensor_{i}" for i in range(1, 22)]
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare NASA C-MAPSS FD001 for RUL training.")
    parser.add_argument("--source", default=str(DEFAULT_SOURCE))
    parser.add_argument("--window", type=int, default=30)
    parser.add_argument("--rul-cap", type=int, default=125)
    args = parser.parse_args()

    from pathlib import Path

    source = Path(args.source)
    if not source.exists():
        raise SystemExit(
            f"Missing {source}. Download NASA C-MAPSS and place train_FD001.txt there."
        )

    frame = pd.read_csv(source, sep=r"\s+", header=None).dropna(axis=1, how="all")
    frame.columns = COLUMNS[: frame.shape[1]]

    # Per-unit RUL = cycles remaining until the unit's last cycle, capped.
    max_cycle = frame.groupby("unit")["cycle"].transform("max")
    frame["rul"] = (max_cycle - frame["cycle"]).clip(upper=args.rul_cap)

    sensor_cols = [c for c in frame.columns if c.startswith("sensor_")]
    # Drop constant sensors (no information for degradation).
    sensor_cols = [c for c in sensor_cols if frame[c].std() > 1e-6]

    x_list, y_list, unit_list = [], [], []
    for unit, group in frame.groupby("unit"):
        group = group.sort_values("cycle")
        values = group[sensor_cols].to_numpy(dtype=np.float32)
        ruls = group["rul"].to_numpy(dtype=np.float32)
        for end in range(args.window, len(group) + 1):
            x_list.append(values[end - args.window : end])
            y_list.append(ruls[end - 1])
            unit_list.append(int(unit))

    x = np.stack(x_list).astype(np.float32)
    y = np.asarray(y_list, dtype=np.float32)
    unit = np.asarray(unit_list, dtype=np.int64)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    npz_path = OUT_DIR / "cmapss.npz"
    meta_path = OUT_DIR / "cmapss_meta.json"
    np.savez_compressed(npz_path, X=x, y=y, unit=unit)
    meta_path.write_text(
        json.dumps(
            {"sensors": sensor_cols, "window": args.window, "rul_cap": args.rul_cap}, indent=2
        ),
        encoding="utf-8",
    )

    print(f"Wrote {npz_path} ({x.shape[0]} windows, {len(np.unique(unit))} units, {len(sensor_cols)} sensors)")
    print(f"Window {args.window}, RUL cap {args.rul_cap}")
    print(f"Wrote {meta_path}")


if __name__ == "__main__":
    main()
