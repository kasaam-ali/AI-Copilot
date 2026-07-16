"""Active-learning flywheel: inspector corrections retrain a new model version.

The new version is registered INACTIVE with comparative metrics; a human activates it.
This build implements the tabular model (corrections carry a corrected label and the named
features), which is where the human feedback is richest.

Retraining is deliberately small (a subset + few epochs) so it finishes in seconds for the
demo, while exercising the full assemble -> train -> evaluate -> register -> activate loop.
"""

from __future__ import annotations

import json

import joblib
import numpy as np
import torch
from loguru import logger
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sqlmodel import Session, select
from torch.utils.data import DataLoader, TensorDataset

from app.database import engine
from app.models_db.models import JobStatus, RetrainJob, utcnow
from ml import registry
from ml.tabular import infer as tabular_infer
from ml.tabular.infer import build_feature_vector, load_active_bundle
from ml.tabular.model import BinaryFocalLoss, DefectMLP

FEEDBACK_DIR = registry.REPO_ROOT / "data" / "feedback"
DATA_DIR = registry.REPO_ROOT / "data" / "tabular"
AUTO_THRESHOLD = 10

SUPPORTED = {"tabular"}


def collect_corrections(model_type: str) -> list[tuple[dict, int]]:
    """Read persisted feedback samples with a corrected label into (features, label) pairs."""
    if model_type != "tabular" or not FEEDBACK_DIR.exists():
        return []
    items: list[tuple[dict, int]] = []
    for path in FEEDBACK_DIR.glob("*.json"):
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        if record.get("corrected_label") is None:
            continue
        features = (record.get("meta") or {}).get("features")
        if not features:
            continue
        label = 1 if record["corrected_label"] == "defect" else 0
        items.append((features, label))
    return items


def _assemble_batch(
    corrections: list[tuple[dict, int]],
    original_subset: int = 200,
    oversample: int = 3,
    seed: int = 42,
):
    import pandas as pd

    bundle = load_active_bundle()
    order = bundle.features

    corr_x = [build_feature_vector(f, bundle) for f, _ in corrections]
    corr_y = [y for _, y in corrections]

    meta = json.loads((DATA_DIR / "synthetic_meta.json").read_text(encoding="utf-8"))
    frame = pd.read_csv(DATA_DIR / "synthetic.csv")
    sample = frame.sample(min(original_subset, len(frame)), random_state=seed)
    orig_x = sample[order].to_numpy(dtype=float).tolist()
    orig_y = sample[meta["label"]].astype(int).tolist()

    x = np.array(orig_x + corr_x * oversample, dtype=float)
    y = np.array(orig_y + corr_y * oversample, dtype=int)
    return x, y, bundle, order


def _auroc(model: torch.nn.Module, scaler, x_raw: np.ndarray, y: np.ndarray) -> float:
    if len(set(y.tolist())) < 2:
        return float("nan")
    model.eval()
    with torch.no_grad():
        probs = torch.sigmoid(
            model(torch.tensor(scaler.transform(x_raw), dtype=torch.float32))
        ).numpy()
    return float(roc_auc_score(y, probs))


def _train_new_version(x, y, bundle, order, epochs: int = 3, seed: int = 42):
    stratify = y if len(set(y.tolist())) > 1 else None
    x_tr, x_ev, y_tr, y_ev = train_test_split(x, y, test_size=0.3, stratify=stratify, random_state=seed)

    scaler = StandardScaler().fit(x_tr)
    x_tr_s = scaler.transform(x_tr)

    model = DefectMLP(len(order))
    criterion = BinaryFocalLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-3, weight_decay=1e-4)
    loader = DataLoader(
        TensorDataset(torch.tensor(x_tr_s, dtype=torch.float32), torch.tensor(y_tr, dtype=torch.float32)),
        batch_size=64,
        shuffle=True,
        drop_last=True,
    )
    for _ in range(epochs):
        model.train()
        for xb, yb in loader:
            optimizer.zero_grad()
            criterion(model(xb), yb).backward()
            optimizer.step()

    new_auroc = _auroc(model, scaler, x_ev, y_ev)
    old_auroc = _auroc(bundle.model, bundle.scaler, x_ev, y_ev)

    existing = {v["version"] for v in registry.list_versions("tabular")}
    n = 2
    while f"v{n}" in existing:
        n += 1
    version = f"v{n}"

    vdir = registry.version_dir("tabular", version)
    vdir.mkdir(parents=True, exist_ok=True)
    weights_path = vdir / "weights.pt"
    torch.save(model.state_dict(), weights_path)
    joblib.dump(scaler, vdir / "scaler.joblib")

    rng = np.random.default_rng(seed)
    background = x_tr_s[rng.choice(len(x_tr_s), min(50, len(x_tr_s)), replace=False)]
    np.save(vdir / "background.npy", background)
    defaults = {feature: float(np.median(x[:, i])) for i, feature in enumerate(order)}
    (vdir / "meta.json").write_text(
        json.dumps({"features": order, "label": "defect", "defaults": defaults}, indent=2),
        encoding="utf-8",
    )

    metrics = {
        "auroc_new": new_auroc,
        "auroc_old": old_auroc,
        "eval_size": int(len(y_ev)),
        "delta": None if np.isnan(new_auroc) or np.isnan(old_auroc) else round(new_auroc - old_auroc, 4),
    }
    (vdir / "metrics.json").write_text(json.dumps({"retrain": metrics}, indent=2), encoding="utf-8")
    registry.register_version(
        "tabular", version, weights_path,
        metrics={"retrain": metrics}, train_config={"retrain": True, "epochs": epochs}, make_active=False,
    )
    return version, metrics


def run_retrain_job(job_id: int, model_type: str) -> None:
    """Background worker: assemble -> train -> evaluate -> register (inactive)."""
    with Session(engine) as session:
        job = session.get(RetrainJob, job_id)
        if job is None:
            return
        try:
            job.status = JobStatus.running
            job.progress = 10
            session.add(job)
            session.commit()

            corrections = collect_corrections(model_type)
            x, y, bundle, order = _assemble_batch(corrections)
            job.num_corrections = len(corrections)
            job.num_samples = int(len(y))
            job.base_version = bundle.version
            job.progress = 45
            session.add(job)
            session.commit()

            version, metrics = _train_new_version(x, y, bundle, order)
            job.new_version = version
            job.metrics = metrics
            job.progress = 100
            job.status = JobStatus.succeeded
            job.finished_at = utcnow()
            session.add(job)
            session.commit()
            logger.info("Retrain job {} produced tabular/{} (delta {})", job_id, version, metrics.get("delta"))
        except Exception as exc:  # noqa: BLE001 - surface failure on the job, never crash
            job.status = JobStatus.failed
            job.message = str(exc)
            job.finished_at = utcnow()
            session.add(job)
            session.commit()
            logger.exception("Retrain job {} failed", job_id)


def start_retrain(session: Session, model_type: str) -> RetrainJob:
    """Create a queued retrain job (the router schedules the background worker)."""
    if model_type not in SUPPORTED:
        raise ValueError(f"Retraining is supported for {sorted(SUPPORTED)} in this build.")
    corrections = collect_corrections(model_type)
    if not corrections:
        raise ValueError("Collect at least one correction (reject or modify) before retraining.")

    job = RetrainJob(model_type=model_type, status=JobStatus.queued, num_corrections=len(corrections))
    session.add(job)
    session.commit()
    session.refresh(job)
    return job


def list_jobs(session: Session, model_type: str | None = None, limit: int = 20) -> list[RetrainJob]:
    query = select(RetrainJob)
    if model_type:
        query = query.where(RetrainJob.model_type == model_type)
    jobs = session.exec(query).all()
    return sorted(jobs, key=lambda j: j.created_at, reverse=True)[:limit]


def list_versions(model_type: str) -> dict:
    active = registry.get_active(model_type)
    active_version = active["version"] if active else None
    versions = [
        {
            "version": v["version"],
            "created_at": v.get("created_at"),
            "is_active": v["version"] == active_version,
            "metrics": v.get("metrics", {}),
        }
        for v in registry.list_versions(model_type)
    ]
    versions.sort(key=lambda v: v["version"])
    return {"model_type": model_type, "active": active_version, "versions": versions}


def activate_version(model_type: str, version: str) -> dict:
    """Promote a version to active and hot-swap the served model."""
    registry.set_active(model_type, version)
    if model_type == "tabular":
        tabular_infer._bundle_cache.clear()
        load_active_bundle(force_reload=True)
    return list_versions(model_type)
