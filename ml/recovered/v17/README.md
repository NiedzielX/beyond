# Beyond Historical Demand v1.7 — recovered benchmark bundle

This bundle is a recovery artifact created from the strict, leakage-safe
Beyond Historical Model Tournament v1.3 package.

## What it contains
- v17_t30_oos_predictions.csv — v1.7 OOS predictions for T-30, 68 matches
- v17_t7_oos_predictions.csv — v1.7 OOS predictions for T-7, 68 matches
- v17_metrics_strict.json — exact strict metrics and leakage policy
- strict_decision_report.json — original tournament decision report
- historical_model_tournament_v13_README.md — original tournament README

## Status
v1.7 remains the frozen historical champion in the strict evaluation.
Strict OOS MAE:
- T-30: 4723.8
- T-7: 4151.1

## Important provenance note
The original temporary archive generated earlier was named:
  lech_early_model_v17.zip
That exact sandbox archive was not persisted to the Library and is no longer
available in the active runtime. This recovered bundle therefore preserves the
validated v1.7 benchmark outputs and decision evidence, but it is NOT claimed
to be byte-for-byte identical to the original archive and does not reconstruct
missing source code that was not preserved.
