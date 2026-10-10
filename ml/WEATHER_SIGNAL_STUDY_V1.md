# Beyond Weather Signal Study v1 — final

## Purpose

Test whether weather forecast information available **before** the canonical T-7 checkpoint improves the frozen Lech v1.7 T-7 attendance forecast.

This study does not use observed post-match weather and does not modify the production or shadow forecasting model.

## Source forecast baseline

Frozen benchmark:

`ml/recovered/v17/evidence/t7_walkforward_v17_original.csv`

The exact v1.7 reconstruction harness parses `match_date` as UTC via:

`pd.to_datetime(df["match_date"], utc=True)`

Therefore Weather Signal Study v1 uses the same UTC semantics. An initial exploratory backfill that interpreted these timestamps as Europe/Warsaw local time was rejected and recomputed before the final study result was accepted.

## Weather source

Open-Meteo Single Runs API.

Fixed model:

`ecmwf_ifs`

The Single Runs archive preserves individual forecast runs and is used here because the objective is to reconstruct information that was actually forecast before the decision checkpoint rather than use reanalysis or stitched near-observation weather.

## Strict anti-leakage protocol

For every preserved v1.7 T-7 OOS row:

1. `kickoff_at` = preserved `match_date` interpreted as UTC, matching the exact v1.7 reconstruction harness.
2. `checkpoint_at` = kickoff − 168 hours.
3. Only ECMWF IFS 00Z and 12Z cycles are used across the whole historical sample for consistency.
4. A conservative model-publication lag of 6 hours is assumed.
5. Selected run = latest 00Z/12Z run whose `run_initialized_at + 6h <= checkpoint_at`.
6. Weather features are taken for the forecast hour nearest kickoff.
7. No run initialised or assumed available after the T-7 checkpoint is allowed.

Validation after backfill:

- 38 / 38 rows pass the availability check;
- minimum safety margin between assumed model availability and checkpoint: 2.25 h;
- forecast lead time range: 176.25–185.5 h;
- all run cycles are 00Z or 12Z.

## Historical coverage

The ECMWF IFS Single Runs archive permits a strict T-7 reconstruction for 38 frozen v1.7 OOS matches spanning 3 seasons:

- 2023/2024
- 2024/2025
- 2025/2026

One archived row (Lech–Korona, 2025-08-16) lacks wind fields in the source run. It is retained in pairwise descriptive statistics but excluded from the multivariate Ridge correction, leaving 37 usable model rows.

## Candidate features

Fixed before final evaluation:

- temperature at 2 m;
- precipitation amount;
- wind speed at 10 m;
- cloud cover.

Target:

`actual_attendance - v17_pred_final`

Candidate model:

- Ridge residual correction;
- fixed `alpha = 10`;
- features standardized inside each training fold;
- no hyperparameter tuning after seeing results.

Evaluation:

1. leave-one-match-out cross-validation;
2. leave-one-season-out cross-validation.

The candidate correction is added to the frozen v1.7 T-7 P50 and compared against the original v1.7 absolute error.

## Final result

Usable sample: **37 matches** across **3 seasons**.

Frozen v1.7 baseline MAE on the usable sample:

**3,896.93**

Weather Ridge — leave-one-match-out:

- MAE: **4,198.98**
- change vs baseline: **+302.06 people error**
- relative error change: **+7.75% worse**

Weather Ridge — leave-one-season-out:

- MAE: **4,165.69**
- change vs baseline: **+268.76 people error**
- relative error change: **+6.90% worse**

### Leave-one-season-out folds

| Held-out season | n | v1.7 baseline MAE | weather-corrected MAE | result |
| --- | ---: | ---: | ---: | --- |
| 2023/2024 | 4 | 4,793.60 | 4,304.93 | improved, very small fold |
| 2024/2025 | 17 | 4,715.28 | 4,874.23 | worse |
| 2025/2026 | 16 | 2,803.26 | 3,378.05 | materially worse |

## Descriptive associations

Across all 38 reconstructed rows, pairwise correlations with the frozen baseline residual are weak:

- temperature: `+0.1140`
- precipitation: `-0.1063`
- wind speed: `+0.0051`
- wind gusts: `+0.0369`
- cloud cover: `-0.1717`

Correlations with absolute error are also near zero for the tested variables.

These correlations are descriptive only; the cross-validated correction result is the decision criterion.

## Decision

**Reject Weather Linear Correction v1.**

Weather does not improve the frozen v1.7 T-7 benchmark under either event-level or season-level out-of-sample evaluation. It should not be added to v1.7 T-7 or to the first live-correction model based on this evidence.

## What remains active

Prospective weather telemetry remains enabled as a low-cost research stream because:

- cross-club effects may differ from Lech-only historical effects;
- interactions with live inventory trajectory may be different from a standalone linear residual correction;
- the telemetry is collected prospectively and therefore remains leakage-safe for future studies.

However, weather is now **lower priority** than inventory trajectory and independent outcome accumulation.

## Database artifacts

- `v17_t7_weather_backfill`
- `weather_signal_study_reports`
- `get_weather_signal_study_v1_summary()`

Final stored decision:

`reject_weather_linear_correction_v1`
