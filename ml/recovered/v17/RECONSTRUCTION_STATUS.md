# v1.7 inference reconstruction status

Status date: 2026-10-09

## Current status

The original `lech_early_model_v17.zip` and the immediately preceding
`lech_model_hardening_v161.zip` survive with benchmark outputs and the fitted
v1.6.1 Ridge pipelines.

The reconstruction is now asymmetric by horizon:

- **T-7: executable inference semantics recovered exactly**;
- **T-30: feature/control/correction layers recovered, raw residual Ridge still unresolved**.

## T-7 — recovered exactly

The decisive missing table-feature semantics were recovered by using the fitted
v1.4/v1.6.1 preprocessor statistics as a forensic control.

### Exact T-7 feature semantics

Attendance-history state:

- cutoff = target kickoff timestamp minus 7 days;
- only Lech home attendances before that exact timestamp are visible;
- capacity-constrained historical rows are excluded;
- rolling 3/5/10, current-season average, opponent ratios, history counts and
  season-home-match counts are computed from that as-of history.

Sporting/table state:

- forecast table state is built from completed league matches **strictly before
  the local calendar T-7 date**; matches played later on the same calendar day
  are not included;
- table signal activates only when both Lech and the opponent have played at
  least 10 league matches;
- raw position is transformed relative to league mid-table:
  `((league_team_count + 1) / 2) - raw_position`;
- `pos_gap_gate_10 = opponent_raw_position - lech_raw_position` when active;
- inactive gated table features are zero.

Model protocol:

- season-block walk-forward: target-season fit uses completed prior seasons only;
- frequency-gated opponent category, minimum 3 observations in the training fold;
- Ridge alpha = 0.3;
- no recency weighting;
- v1.7 target = `attendance - season_avg_so_far`;
- prediction = `season_avg_so_far + predicted_residual`;
- hard stadium capacity cap = 43,269;
- no T-7 online correction was promoted in v1.7.

### Exact controls

The reconstructed numeric feature matrix reproduces all fitted v1.6.1 numeric
imputer medians, RobustScaler centers and RobustScaler scales.

Preserved 68-row OOS controls:

- v1.6.1 mean absolute prediction difference: **~1.35e-11 persons**;
- v1.6.1 maximum absolute prediction difference: **~6.91e-11 persons**;
- v1.7 raw mean absolute prediction difference: **~9.98e-12 persons**;
- v1.7 raw maximum absolute prediction difference: **~2.55e-11 persons**;
- v1.7 final mean absolute prediction difference: **~9.87e-12 persons**;
- reconstructed v1.7 T-7 final MAE: **4151.0819**, matching the preserved benchmark.

This is floating-point-level reproduction, so T-7 may now be implemented as a
shadow historical forecaster with explicit recovered-v1.7 lineage.

Evidence:

- `reconstruct_t7_v17.py`
- `v17_t7_reconstruction_report.json`
- original preserved T-7 OOS predictions in this recovery bundle.

## T-30 — remaining blocker

Recovered:

- T-30 as-of attendance/history feature builder;
- `target_matches_remaining` mapping;
- season-block prior-season training fold;
- frequency-gated opponent categories;
- three-year recency weighting with latest training match weight 1;
- v1.6.1 direct-model control to near numerical tolerance:
  - mean absolute prediction difference **0.9866 persons**;
  - maximum absolute prediction difference **6.1042 persons**;
- exact v1.7 same-season online correction:
  `mean(previous raw residuals actual-pred) * n/(n+3)`;
- correction output reproduces the preserved final prediction column to
  floating-point tolerance when applied to preserved original raw predictions.

Still unresolved:

- exact raw T-30 v1.7 residual-Ridge training specification.

Current best-supported candidate:

- target = `attendance - season_avg_so_far`;
- same recovered T-30 feature state;
- Ridge alpha 0.3;
- three-year recency weighting;
- mean absolute difference from original raw v1.7 predictions: **652.1987**;
- maximum difference: **4466.3459**;
- candidate final MAE: **4936.8** vs preserved original **4723.8**.

The calendar-date discovery that solved the T-7 table state does not explain the
T-30 gap. The T-30 blocker remains isolated to the raw residual-model fit/target
semantics.

## Promotion rule

- T-7: allowed for **shadow historical forecasting** with explicit
  `lech-v17-t7-recovered` lineage; not an automatic production promotion.
- T-30: do not use reconstructed output for new forecasts until raw OOS
  predictions reproduce to numerical tolerance.
- Production v0.3 remains separate while the full horizon migration is incomplete.
