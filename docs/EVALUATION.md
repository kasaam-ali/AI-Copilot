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
