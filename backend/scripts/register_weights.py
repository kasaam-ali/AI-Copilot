"""Register externally-trained weights (e.g. from Google Colab) into the registry.

Place the downloaded files under models/<type>/<version>/ so the folder contains
weights.pt (and optionally metrics.json and config.json), then run from backend/:

    python -m scripts.register_weights --model-type image --version v1 --activate
"""

from __future__ import annotations

import argparse
import json

from ml import registry


def main() -> None:
    parser = argparse.ArgumentParser(description="Register trained weights into the registry.")
    parser.add_argument("--model-type", required=True)
    parser.add_argument("--version", default="v1")
    parser.add_argument("--activate", action="store_true", help="Make this version active")
    args = parser.parse_args()

    vdir = registry.version_dir(args.model_type, args.version)
    weights_path = vdir / "weights.pt"
    if not weights_path.exists():
        raise SystemExit(
            f"Weights not found: {weights_path}\n"
            f"Download the trained weights.pt into that folder first."
        )

    metrics = {}
    metrics_file = vdir / "metrics.json"
    if metrics_file.exists():
        metrics = json.loads(metrics_file.read_text(encoding="utf-8"))

    train_config = {}
    config_file = vdir / "config.json"
    if config_file.exists():
        train_config = json.loads(config_file.read_text(encoding="utf-8"))

    record = registry.register_version(
        args.model_type,
        args.version,
        weights_path,
        metrics=metrics,
        train_config=train_config,
        make_active=True if args.activate else None,
    )
    print(f"Registered {args.model_type}/{args.version}")
    print(f"  weights_sha256: {record['weights_sha256']}")
    print(f"  active: {registry.get_active(args.model_type)['version']}")


if __name__ == "__main__":
    main()
