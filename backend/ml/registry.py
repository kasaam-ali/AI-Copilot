"""Filesystem-backed model registry.

This module is intentionally free of any ``app`` imports so that training scripts,
inference services and tests can all share it. It manages versioned weight
directories under ``<repo>/models`` and a JSON index (``models_registry.json``)
that records, per model type, the available versions and which one is active.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_THIS = Path(__file__).resolve()
BACKEND_DIR = _THIS.parents[1]
REPO_ROOT = BACKEND_DIR.parent
MODELS_ROOT = REPO_ROOT / "models"
REGISTRY_FILE = MODELS_ROOT / "models_registry.json"


def sha256_file(path: str | Path) -> str:
    """Return the SHA-256 hex digest of a file."""
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def version_dir(model_type: str, version: str) -> Path:
    """Return the directory that holds the weights for a model version."""
    return MODELS_ROOT / model_type / version


def resolve(relative_path: str) -> Path:
    """Resolve a repo-relative path stored in the registry to an absolute path."""
    return (REPO_ROOT / relative_path).resolve()


def _relative(path: str | Path) -> str:
    """Store paths relative to the repo root for portability."""
    return str(Path(path).resolve().relative_to(REPO_ROOT)).replace("\\", "/")


def _load() -> dict[str, Any]:
    if REGISTRY_FILE.exists():
        return json.loads(REGISTRY_FILE.read_text(encoding="utf-8"))
    return {"models": {}}


def _save(data: dict[str, Any]) -> None:
    MODELS_ROOT.mkdir(parents=True, exist_ok=True)
    REGISTRY_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


def register_version(
    model_type: str,
    version: str,
    weights_path: str | Path,
    *,
    metrics: dict[str, Any] | None = None,
    train_config: dict[str, Any] | None = None,
    make_active: bool | None = None,
) -> dict[str, Any]:
    """Register (or overwrite) a model version and optionally make it active.

    If no version is active yet for this model type, the new one becomes active
    unless ``make_active`` is explicitly ``False``.
    """
    data = _load()
    models = data.setdefault("models", {})
    entry = models.setdefault(model_type, {"active": None, "versions": {}})

    record = {
        "version": version,
        "weights_path": _relative(weights_path),
        "weights_sha256": sha256_file(weights_path),
        "metrics": metrics or {},
        "train_config": train_config or {},
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    entry["versions"][version] = record

    should_activate = make_active if make_active is not None else entry["active"] is None
    if should_activate:
        entry["active"] = version

    _save(data)
    return record


def get_version(model_type: str, version: str) -> dict[str, Any] | None:
    entry = _load().get("models", {}).get(model_type)
    if not entry:
        return None
    return entry["versions"].get(version)


def get_active(model_type: str) -> dict[str, Any] | None:
    """Return the active version record for a model type, or ``None``."""
    entry = _load().get("models", {}).get(model_type)
    if not entry or not entry.get("active"):
        return None
    return entry["versions"].get(entry["active"])


def set_active(model_type: str, version: str) -> None:
    """Promote a specific version to active."""
    data = _load()
    entry = data.get("models", {}).get(model_type)
    if not entry or version not in entry["versions"]:
        raise ValueError(f"Unknown version {version!r} for model type {model_type!r}")
    entry["active"] = version
    _save(data)


def list_versions(model_type: str) -> list[dict[str, Any]]:
    entry = _load().get("models", {}).get(model_type)
    if not entry:
        return []
    return list(entry["versions"].values())
