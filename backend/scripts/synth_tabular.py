"""Generate a synthetic production-line telemetry dataset for defect prediction.

Unlike SECOM (whose 590 features are anonymized), these features are named and
interpretable, which makes the SHAP explanation genuinely readable. The defect
label is generated from a transparent rule so the SHAP drivers are honest. This is
disclosed in the report as simulated production telemetry.

Output:
    data/tabular/synthetic.csv        - features + label
    data/tabular/synthetic_meta.json  - feature names and label name
"""

from __future__ import annotations

import argparse
import json

import numpy as np
import pandas as pd

from ml.registry import REPO_ROOT

OUT_DIR = REPO_ROOT / "data" / "tabular"

FEATURES = [
    "machine_temp_c",
    "vibration_rms",
    "line_speed_mpm",
    "fill_pressure_bar",
    "ambient_humidity_pct",
    "tool_wear_hours",
    "material_purity_pct",
    "cycle_time_s",
    "operator_shift",
]
LABEL = "defect"


def generate(n_rows: int, seed: int) -> pd.DataFrame:
    rng = np.random.default_rng(seed)

    machine_temp = rng.normal(65, 4, n_rows)
    vibration = np.clip(rng.normal(2.0, 0.5, n_rows), 0.1, None)
    line_speed = rng.normal(40, 6, n_rows)
    fill_pressure = rng.normal(3.0, 0.3, n_rows)
    humidity = np.clip(rng.normal(45, 8, n_rows), 5, 95)
    tool_wear = rng.uniform(0, 500, n_rows)
    material_purity = np.clip(rng.normal(99.0, 0.6, n_rows), 95, 100)
    cycle_time = rng.normal(12, 1.5, n_rows)
    operator_shift = rng.integers(0, 3, n_rows)

    # Transparent risk model -> the SHAP story is honest.
    logit = (
        -2.0
        + 0.9 * ((machine_temp - 65) / 4)
        + 0.8 * ((vibration - 2.0) / 0.5)
        + 0.7 * ((line_speed - 40) / 6)
        + 0.9 * (np.abs(fill_pressure - 3.0) / 0.3)
        + 1.1 * ((tool_wear - 250) / 150)
        + 0.9 * (-(material_purity - 99.0) / 0.6)
        + 0.3 * ((humidity - 45) / 8)
        + rng.normal(0, 0.5, n_rows)
    )
    probability = 1.0 / (1.0 + np.exp(-logit))
    label = (rng.uniform(0, 1, n_rows) < probability).astype(int)

    return pd.DataFrame(
        {
            "machine_temp_c": machine_temp.round(2),
            "vibration_rms": vibration.round(3),
            "line_speed_mpm": line_speed.round(2),
            "fill_pressure_bar": fill_pressure.round(3),
            "ambient_humidity_pct": humidity.round(1),
            "tool_wear_hours": tool_wear.round(1),
            "material_purity_pct": material_purity.round(2),
            "cycle_time_s": cycle_time.round(2),
            "operator_shift": operator_shift,
            LABEL: label,
        }
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate synthetic tabular telemetry.")
    parser.add_argument("--rows", type=int, default=4000)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    frame = generate(args.rows, args.seed)

    csv_path = OUT_DIR / "synthetic.csv"
    meta_path = OUT_DIR / "synthetic_meta.json"
    frame.to_csv(csv_path, index=False)
    meta_path.write_text(
        json.dumps({"features": FEATURES, "label": LABEL}, indent=2), encoding="utf-8"
    )

    defect = int(frame[LABEL].sum())
    print(f"Wrote {csv_path} ({len(frame)} rows, {defect} defect, {len(frame) - defect} good)")
    print(f"Defect rate: {defect / len(frame):.1%}")
    print(f"Wrote {meta_path}")


if __name__ == "__main__":
    main()
