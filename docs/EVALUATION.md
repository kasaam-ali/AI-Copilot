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
| Synthetic (pipeline validation) | 216 / 72 / 72 | 0.998 | 0.90 |
| MVTec AD `bottle` | pending (train on Colab) | pending | pending |

> The synthetic dataset is a procedural good-vs-defect generator used only to validate
> the end-to-end pipeline while the real MVTec AD weights are trained on Colab. The
> MVTec-trained `image/v1` weights replace the synthetic ones with zero code change; this
> table is updated with the real numbers once available.

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
