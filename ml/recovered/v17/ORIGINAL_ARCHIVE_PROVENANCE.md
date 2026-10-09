# Original v1.7 archive provenance

## Discovery

The original Library archive **`lech_early_model_v17.zip`** was recovered on
2026-10-09. This supersedes the earlier assumption that only the later recovered
strict-tournament bundle survived.

Original archive SHA-256:

`187e2af23f9f56e824b566fed8f61f06b0dae305610f40695571dc81eacd0347`

## Original archive contents

| File | SHA-256 |
|---|---|
| `README.md` | `778ed154b3a950cdd2e1492dd7706d7bd6e61f89ceb67523bd3e5774ee729d4c` |
| `early_model_report_v17.json` | `6ef455d6cd244d04e0e4ef2442c9255ce7f34eb4b83b624c8b1c1d79d9640c4f` |
| `fresh_2026_27_validation_v17.csv` | `96f413e5760c86e689a425e9c51840835f71a28ed4a80672e91a9a2da1e98a8c` |
| `t30_walkforward_v17.csv` | `166f92489713be76356ffd306fa0f0d56e7202dcb20472c1354fd0a9cc4e2307` |
| `t7_walkforward_v17.csv` | `eb5615a19b4f53f32806e67712920296278e685ca2722b2cf374cbd5f8b7a602` |
| `v17_vs_v161.csv` | `88d47a8d40f1a31a6e4a56a953caeadebccb08dcbb4c0a18c1b23c5a4a3af4bc` |

## What the original archive proves

The original report confirms:

- stadium capacity cap = **43,269**;
- T-30 strict/OOS MAE = **4,723.8**;
- T-7 strict/OOS MAE = **4,151.1**;
- T-30 design = Ridge residual model around current-season average +
  frequency-gated opponent categories + online same-season bias correction +
  capacity cap;
- T-30 online correction uses residuals from already completed Lech home
  matches in the same season with shrinkage **k=3**;
- T-7 design = Ridge residual model around current-season average +
  frequency-gated opponent categories + gated table context + capacity cap;
- T-7 online correction was not promoted.

The original T-30 walk-forward CSV also makes the online correction formula
recoverable exactly:

`correction = mean(previous_raw_residuals_actual_minus_prediction) * n / (n + 3)`

where `n` is the number of earlier completed Lech home matches in that season.
The correction is applied to the raw T-30 prediction before the hard capacity cap.

## What the original archive does NOT contain

The ZIP contains benchmark outputs and decision evidence, but **no training
source code and no v1.7 joblib/model binary**. Therefore recovery of the original
archive does not by itself make v1.7 executable for new fixtures.

The immediately preceding `lech_model_hardening_v161.zip` does contain fitted
T-30/T-7 joblib pipelines and feature contracts. Those artifacts are being used
as the controlled starting point for v1.7 inference reconstruction.
