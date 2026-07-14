"""Prepare the SECOM (UCI) semiconductor dataset for tabular defect training.

SECOM is real, imbalanced sensor data with 590 anonymized features and a pass/fail
label. This script fetches it, median-imputes missing values, drops constant columns
and writes it in the same format the tabular trainer expects:

    data/tabular/secom.csv
    data/tabular/secom_meta.json

Then: python -m ml.tabular.train --dataset secom
"""

from __future__ import annotations

import argparse
import json

import numpy as np
import pandas as pd

from ml.registry import REPO_ROOT

OUT_DIR = REPO_ROOT / "data" / "tabular"


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare the SECOM dataset.")
    parser.add_argument("--variance-threshold", type=float, default=0.0)
    args = parser.parse_args()

    try:
        from ucimlrepo import fetch_ucirepo
    except ImportError as exc:  # pragma: no cover
        raise SystemExit("ucimlrepo is required: pip install ucimlrepo") from exc

    print("Fetching SECOM (UCI id=179) ...")
    dataset = fetch_ucirepo(id=179)

    features = dataset.data.features.apply(pd.to_numeric, errors="coerce")
    features = features.fillna(features.median())

    variances = features.var()
    keep = variances[variances > args.variance_threshold].index.tolist()
    features = features[keep]
    features.columns = [f"feature_{i}" for i in range(features.shape[1])]

    target = dataset.data.targets.iloc[:, 0].to_numpy()
    label = (target == 1).astype(int)  # SECOM: 1 = fail (defect), -1 = pass

    frame = features.copy()
    frame["defect"] = label

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    csv_path = OUT_DIR / "secom.csv"
    meta_path = OUT_DIR / "secom_meta.json"
    frame.to_csv(csv_path, index=False)
    meta_path.write_text(
        json.dumps({"features": list(features.columns), "label": "defect"}, indent=2),
        encoding="utf-8",
    )

    defect = int(label.sum())
    print(f"Wrote {csv_path} ({len(frame)} rows, {features.shape[1]} features)")
    print(f"Defect (fail) rate: {defect / len(frame):.1%}")
    print(f"Wrote {meta_path}")


if __name__ == "__main__":
    main()
