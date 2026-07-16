# Evaluation Protocol

All quoted metrics come from this document. The protocol is frozen before training:
fixed seed (42), stratified train/val/test split persisted by index, and the test split
is never used for training or model selection.

## Image model (defect classification)

- **Architecture:** ResNet18 (ImageNet weights), backbone frozen except `layer4` + a
  dropout(0.5) + linear head. Two classes: good (0), defect (1).
- **Selection:** best validation AUROC with early stopping (patience 5).
- **Metric:** AUROC on the held-out test split (threshold-independent), plus accuracy.
- **Uncertainty:** MC-Dropout (N=20) at inference time.

### v1 results

| Dataset | Split sizes (train/val/test) | Test AUROC | Test accuracy |
|---|---|---|---|
| **MVTec AD `bottle` (active)** | 175 / 59 / 58 | **1.000** | 0.847 |
| Synthetic (pipeline validation) | 216 / 72 / 72 | 0.998 | 0.90 |

> **Active model:** the MVTec AD `bottle` weights, trained on GPU (Colab) and loaded via
> `scripts/register_weights.py`. Test AUROC is 1.000 on a small test set (58 images);
> `bottle` is a visually clear category, so perfect ranking is expected and is reported
> with the test size for honesty. The 0.847 accuracy is at the default 0.5 threshold — a
> calibration artifact, not a generalization gap (AUROC 1.0 means a threshold exists that
> separates the classes perfectly). MC-Dropout uncertainty plus the human-in-the-loop
> review handle borderline cases.
>
> The synthetic generator remains for offline pipeline validation; swapping datasets needs
> no code change.

## Tabular model (defect probability)

- **Architecture:** MLP 256-128-64 with BatchNorm + ReLU + Dropout(0.3), single logit.
- **Loss:** binary focal loss (gamma 2.0, alpha 0.25) for class imbalance.
- **Metrics:** test AUROC, accuracy, and recall at 90% precision.
- **Uncertainty:** MC-Dropout (N=20). **Explanation:** SHAP KernelExplainer over the
  named features.

### v1 results

| Dataset | Split (train/val/test) | Test AUROC | Accuracy | Recall @ P0.90 |
|---|---|---|---|---|
| Synthetic production telemetry | 2800 / 600 / 600 | 0.851 | 0.777 | 0.198 |
| SECOM (UCI) | optional (`scripts/prepare_secom.py`) | pending | pending | pending |

> The synthetic telemetry uses named, interpretable features (machine temperature,
> vibration, tool wear, material purity, ...) generated from a transparent rule, so the
> SHAP drivers are honest and readable. It is disclosed as simulated production data.
> SECOM (real, anonymized 590 features) can be swapped in via `prepare_secom.py`.

## Time-series model (remaining-useful-life)

- **Architecture:** 2-layer LSTM (hidden 64) with a Dropout head, single RUL output.
- **Loss:** Huber (SmoothL1). **Target:** RMSE ≤ 20 RUL units (cap 125).
- **Split:** grouped by machine unit (windows from one unit never cross splits).
- **Uncertainty:** MC-Dropout (N=20). **Explanation:** self-contained Integrated Gradients
  over each timestep-per-sensor, aggregated to per-sensor importance.

### v1 results

| Dataset | Windows / units | Window | Test RMSE (RUL units) |
|---|---|---|---|
| Synthetic machine telemetry | 20,865 / 120 | 30 | **8.34** |
| NASA C-MAPSS FD001 | optional (`scripts/prepare_cmapss.py`) | 30 | pending |

> Six named degrading sensors (temperature, vibration, spindle load, acoustic, current, oil
> pressure) drift with a transparent degradation signal, so the Integrated-Gradients drivers
> are honest — vibration and temperature dominate near failure, as designed. Disclosed as
> simulated machine telemetry. NASA C-MAPSS FD001 writes the same window format and swaps in
> with no serving-code change (retrain only).

## Fusion Health Score

Present modalities are fused as `health = 100·(1 − Σ wᵢcᵢrᵢ / Σ wᵢcᵢ)` with weights
image 0.45 / tabular 0.30 / timeseries 0.25 and `cᵢ = 1/(1+σᵢ)`; a missing or failed
modality drops out and the score renormalizes over the rest. Bands: healthy ≥ 80,
watch 60–79, at_risk 40–59, defect < 40. Verified by `tests/test_fusion.py`. The
`/inspect/session` hero endpoint runs all supplied modalities under one inspection
(measured ~2.5 s for all three on CPU, well under the 6 s p95 target).
