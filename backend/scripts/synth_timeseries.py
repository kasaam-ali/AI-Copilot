"""Generate a synthetic multivariate machine-degradation dataset for RUL prediction.

Each "unit" runs from healthy to failure. Named, interpretable sensors drift with a
transparent degradation signal, so the Integrated-Gradients attributions are honest and
readable. The remaining-useful-life (RUL) target is the cycles left until failure, capped.
This is disclosed in the report as simulated machine telemetry.

It writes pre-built sliding windows so the trainer is dataset-agnostic; NASA C-MAPSS FD001
(see ``scripts/prepare_cmapss.py``) writes the same format and swaps in with no code change.

Output:
    data/timeseries/synthetic.npz        - X (N, W, S) float32, y (N,) RUL, unit (N,)
    data/timeseries/synthetic_meta.json  - sensors, window, rul_cap
"""

from __future__ import annotations

import argparse
import json

import numpy as np

from ml.registry import REPO_ROOT

OUT_DIR = REPO_ROOT / "data" / "timeseries"

SENSORS = [
    "temperature_c",
    "vibration_rms",
    "spindle_load_pct",
    "acoustic_db",
    "current_a",
    "oil_pressure_bar",
]


def _unit_series(rng: np.random.Generator, life: int) -> np.ndarray:
    """Return a (life, n_sensors) array of readings from new (t=0) to failure (t=life-1)."""
    health = np.linspace(0.0, 1.0, life)  # 0 = new, 1 = failed
    temperature = 60 + 15 * health + rng.normal(0, 1.2, life)
    vibration = 1.5 + 2.2 * health**1.5 + rng.normal(0, 0.15, life)
    spindle_load = 40 + 30 * health + rng.normal(0, 2.0, life)
    acoustic = 65 + 12 * health + rng.normal(0, 1.0, life)
    current = 10 + 4 * health + rng.normal(0, 0.4, life)
    oil_pressure = 3.0 - 0.6 * health + rng.normal(0, 0.05, life)
    return np.stack(
        [temperature, vibration, spindle_load, acoustic, current, oil_pressure], axis=1
    ).astype(np.float32)


def generate(units: int, window: int, rul_cap: int, seed: int):
    rng = np.random.default_rng(seed)
    x_list, y_list, unit_list = [], [], []
    for unit in range(units):
        life = int(rng.integers(window + 40, 320))
        series = _unit_series(rng, life)
        for end in range(window, life + 1):
            x_list.append(series[end - window : end])
            rul = min(life - end, rul_cap)
            y_list.append(rul)
            unit_list.append(unit)
    x = np.stack(x_list).astype(np.float32)
    y = np.asarray(y_list, dtype=np.float32)
    unit = np.asarray(unit_list, dtype=np.int64)
    return x, y, unit


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate synthetic time-series RUL data.")
    parser.add_argument("--units", type=int, default=120)
    parser.add_argument("--window", type=int, default=30)
    parser.add_argument("--rul-cap", type=int, default=125)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    x, y, unit = generate(args.units, args.window, args.rul_cap, args.seed)

    npz_path = OUT_DIR / "synthetic.npz"
    meta_path = OUT_DIR / "synthetic_meta.json"
    np.savez_compressed(npz_path, X=x, y=y, unit=unit)
    meta_path.write_text(
        json.dumps(
            {"sensors": SENSORS, "window": args.window, "rul_cap": args.rul_cap}, indent=2
        ),
        encoding="utf-8",
    )

    print(f"Wrote {npz_path} ({x.shape[0]} windows, {args.units} units, {len(SENSORS)} sensors)")
    print(f"Window {args.window}, RUL cap {args.rul_cap}, RUL range [{y.min():.0f}, {y.max():.0f}]")
    print(f"Wrote {meta_path}")


if __name__ == "__main__":
    main()
