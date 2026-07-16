# Development Log

Short daily notes on what was built and why. Newest entries at the top.

## Phase 7R.2 — Video defect detection

- `POST /inspect/detect/video`: sample up to 24 frames evenly across an uploaded clip
  (`cv2.VideoCapture`), run YOLO detection on each, aggregate per-class counts + total
  detections, and keep the frames with the most detections as annotated samples served via
  `GET /explain/detection-frame/{prediction_id}/{index}`.
- Frontend `VideoDetectionPanel`: upload a clip → frames-scanned / total-detections / time
  stats, per-class count chips, and a strip of annotated sample frames. Added under the image
  detector on Inspect.

## Phase 7R.1 — Visual defect detection (labeled bounding boxes)

- Benchmarked against commercial inspection copilots (Akridata, Google Visual Inspection AI,
  Siemens Inspekto): the product needed real localized detection (labeled boxes + confidence),
  not just a Grad-CAM heatmap. Added a YOLOv8 detection path.
- `ml/detection/` (infer + annotate): `load_active_detector()` loads the active `detection`
  weights from the registry and falls back to pretrained `yolov8n.pt` so the pipeline works
  before the domain model is trained; `detect()` returns labeled boxes; `annotate()` draws
  per-class colored boxes + labels onto the image.
- `detection_service.py` + `POST /inspect/detect` (image) + `GET /explain/detection/{id}`
  (annotated PNG). New `detection` ModelType; results persist like any other inspection.
- Frontend `DetectionPanel`: drag-drop a photo → annotated image with boxes + a per-class
  count/legend + detection list. Made the primary vision path on Inspect; the CNN + Grad-CAM
  is kept as a secondary anomaly heatmap.
- NEU-DET (steel surface defects, 6 classes) will be trained on Colab and registered as the
  active detector to replace the generic labels with defect classes.

## Phase 6 — Active-Learning Flywheel

- New `retrain_job` table and `active_learning.py`: inspector corrections (from
  `data/feedback/`) are assembled with a subset of the original data (corrections
  oversampled x3), a fresh version is trained (small subset, few epochs, seconds) and
  registered INACTIVE with a held-out AUROC comparison against the current active model.
- Runs as a FastAPI BackgroundTask; the job row carries live progress. Endpoints:
  `POST /retrain/{model_type}`, `GET /retrain/jobs`, `GET /retrain/jobs/{id}`,
  `GET /models/{model_type}`, `POST /models/{model_type}/{version}/activate` (human-gated
  promotion with a hot-swap of the served bundle; rollback = activate the previous version).
- Implemented for the tabular model (its corrections carry a corrected label + named
  features). Frontend: a Models page with a retrain trigger, polled progress bar, an
  old-vs-new metrics diff, and per-version Activate buttons.

## Phase 5 — LLM Layer + Report

- Provider-agnostic LLM layer: one OpenAI-compatible client covers Groq, OpenRouter, z.AI
  and Gemini; a `FallbackLLMService` tries providers in `LLM_PROVIDER_ORDER` and cascades on
  missing-key / transport / HTTP / timeout / schema-invalid (one repair retry each), with a
  per-provider circuit breaker and a deterministic `mock` terminal so the app never fails
  offline. Every response carries `provider_used` + `attempts[]`.
- `POST /llm/analyze` narrates the root cause grounded in the fused score + per-modality
  outputs + SHAP drivers + RUL; the narrative is stored on the inspection. The LLM only
  explains — it never predicts.
- `POST /llm/summarize-doc` extracts key points / entities / risks from an uploaded PDF
  (pypdf) — the fourth data modality (text).
- `report_service.py`: server-side matplotlib charts + ReportLab PDF and python-docx DOCX
  reports (health gauge, Grad-CAM, SHAP, IG, narrative, recommendations, inspector decisions).
  `POST /reports/{id}`, `GET /reports/{id}/download`, `GET /reports`.
- Frontend: an AI analysis panel with the provider cascade and PDF/DOCX download, a document
  summary card, and a Reports page.
- Live check: Groq, OpenRouter and z.AI all respond with the supplied keys; Gemini returns
  429 (quota) and cascades. Real Groq narrative in ~1.3 s; full offline path via mock.

## Phase 4 — Human-in-the-Loop

- Added the `hitl_decision` table and a `DecisionType` enum (approve/reject/modify).
- `hitl_service.py`: an uncertainty-first review queue (least-confident predictions surface
  first), inspection detail assembly (predictions + XAI links + decision history), and
  feedback capture that updates inspection status and writes the corrected sample to
  `data/feedback/` for the Phase 6 flywheel.
- Endpoints: `GET /inspections?sort=uncertainty|recent`, `GET /inspections/{id}`,
  `POST /feedback`.
- Frontend: a Review Queue page (uncertainty-sorted table), an inspection detail view that
  re-renders every modality's XAI evidence (Grad-CAM / SHAP / IG heat strip) with confidence,
  and approve/reject/modify decision buttons with a correction form and decision history.

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
