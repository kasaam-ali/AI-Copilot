# Development Log

Short daily notes on what was built and why. Newest entries at the top.

## Phase 3 — Time-Series Modality + Fusion Health Score

- Time-series RUL model: 2-layer LSTM (hidden 64) with a Dropout head, Huber loss, split
  grouped by machine unit; MC-Dropout uncertainty. Test RMSE 8.34 on synthetic telemetry
  (cap 125). Self-contained Integrated Gradients (no captum dependency) attributes RUL back
  to each timestep-per-sensor, aggregated to per-sensor importance.
- Synthetic machine-telemetry generator (six named degrading sensors, transparent signal ->
  honest IG drivers); `prepare_cmapss.py` writes the same window format as a drop-in swap
  for NASA C-MAPSS FD001 (retrain only, no serving-code change).
- Fusion service (pure, unit-tested): weighted, uncertainty-discounted Health Score over
  present modalities with missing-modality renormalization; bands healthy/watch/at_risk/defect.
- Hero endpoint `POST /inspect/session` (multipart): runs every supplied modality under ONE
  inspection and fuses one score; a single modality failing is reported, not fatal (~2.5 s
  for all three on CPU). Also `POST /inspect/timeseries` and `GET /explain/timeseries/{id}`.
- Refactored image/tabular services to expose reusable `infer_and_persist_*` helpers so the
  session reuses them without duplicating persistence.
- Frontend: HealthScoreGauge (semicircular SVG), TimeSeriesChart (IG heat strip), SessionPanel
  (optional image + process defaults + sensor-history preset), and a fused Results view with a
  per-modality contribution breakdown. 17/17 backend tests pass; frontend builds clean.

## Phase 2 — Tabular Modality (ANN + SHAP)

- Tabular MLP (256-128-64, BatchNorm/Dropout) with binary focal loss for imbalance;
  MC-Dropout uncertainty; SHAP KernelExplainer over named features (lazy-imported to keep
  startup fast).
- Synthetic production-telemetry generator with named, interpretable features (a
  transparent risk rule -> honest SHAP drivers); `prepare_secom.py` for optional real data.
- Endpoints: `GET /inspect/tabular/schema`, `POST /inspect/tabular`, `GET /explain/shap/{id}`.
- Frontend: process-parameter form and a signed SHAP bar chart; Results page now renders
  image and/or tabular cards. Tabular v1 test AUROC 0.851.

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
