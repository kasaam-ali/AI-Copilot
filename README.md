# SentinelQ

An AI Co-Pilot for Manufacturing Quality Inspection.

SentinelQ inspects products across multiple data modalities, predicts defects and
machine remaining-useful-life with deep learning, explains every prediction, keeps a
human inspector in the loop, learns from their corrections, and generates downloadable
reports.

## Capabilities

- **Vision defect detection** — CNN classifier with Grad-CAM heatmaps.
- **Live camera inspection** — real-time detection, defect classification and unique
  product counting from a webcam feed.
- **Process risk** — ANN over tabular sensor data with SHAP feature attributions.
- **Predictive maintenance** — LSTM remaining-useful-life forecasting over sensor
  time-series with per-timestep attributions.
- **Fused Product Health Score** — a single 0-100 score combining every available
  modality, with named drivers.
- **Human-in-the-loop** — inspectors approve, reject or modify predictions; corrections
  retrain new model versions that a human then promotes.
- **Language layer** — a provider-agnostic LLM narrates root causes and summarizes
  maintenance logs (it never makes the predictions).
- **Reports** — downloadable PDF / DOCX inspection reports.

## Tech stack

FastAPI + PyTorch backend, React + Vite + TypeScript + Tailwind frontend, SQLite
(SQLModel). See `docs/` for the execution plan and development log.

## Getting started

Documented as the project is built out. See `docs/DEVLOG.md` for progress.
