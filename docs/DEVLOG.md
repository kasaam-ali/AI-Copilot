# Development Log

Short daily notes on what was built and why. Newest entries at the top.

## Phase 1 — Vision Modality (CNN + Grad-CAM)

- Added the model registry (versioned weights + SHA-256 + active resolution) and the
  `inspection` / `prediction` / `model_version` tables (with a partial unique index that
  enforces one active version per model type).
- Implemented the image model (ResNet18 transfer learning + MC-Dropout head), dataset,
  training script, Grad-CAM overlay generation and inference with uncertainty.
- Endpoints: `POST /inspect/image` and `GET /explain/gradcam/{id}`; frontend Inspect and
  Results pages with a Grad-CAM viewer and confidence meter.
- MVTec download mirror was stale, so added a synthetic image generator to validate the
  full pipeline now (test AUROC 0.998) and a Colab notebook to train the real MVTec model
  on GPU and export weights (`scripts/register_weights.py` registers them locally).

## Phase 0 — Foundation & Scaffolding

- Scaffolded the repository: backend (FastAPI) and frontend (React/Vite) skeletons,
  configuration, database bootstrap, and a health/readiness API.
