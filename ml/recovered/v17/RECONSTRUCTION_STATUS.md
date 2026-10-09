# v1.7 inference reconstruction status

Status date: 2026-10-09

## What is now recovered

The original `lech_early_model_v17.zip` has been found and verified. Its
benchmark outputs, design report and exact T-30 correction semantics are no
longer inferred from later documents.

The immediately preceding `lech_model_hardening_v161.zip` also survives with
both fitted Ridge joblibs and feature contracts.

## T-30 feature and walk-forward pipeline recovery

Using the preserved v1.2 enriched history plus the v1.6.1 fitted pipeline and
feature contract, the T-30 as-of builder and walk-forward protocol have been
reconstructed with the following semantics:

- forecast cutoff = target kickoff minus 30 days;
- only Lech home attendances before that cutoff are available to target history
  features;
- capacity-constrained historical attendance rows are excluded;
- rolling 3/5/10 = latest available historical Lech home attendances;
- current-season average = mean of available home attendances in the target
  season, with previous global history as the cold-start fallback;
- recent trend = rolling-3 / rolling-10;
- opponent draw ratio = historical opponent mean / global historical mean,
  clipped to 0.50–1.80;
- recent opponent draw ratio uses the latest 3 historical home meetings;
- `history_n` and `season_home_matches_known` are as-of-cutoff counts;
- `target_matches_remaining` maps to the preserved `matches_remaining_after`
  field;
- opponent identity is frequency-gated from the training fold only; minimum
  historical observations = 3, otherwise `other`;
- **Ridge training is season-block walk-forward:** for a target season the model
  fit uses completed prior seasons only. Same-season completed matches can update
  the target's as-of attendance-history features, but do not enter that season's
  Ridge fit;
- T-30 recency weighting uses a 3-year half-life;
- recency weight reference = latest training match, whose weight is exactly 1;
- Ridge alpha in the v1.6.1 predecessor = 0.3.

### Reconstruction control result

Retraining the **v1.6.1 direct T-30 Ridge** with this protocol reproduces its
preserved 68 walk-forward predictions to approximately numerical solver
tolerance:

- mean absolute prediction difference: **0.9866 persons**;
- maximum absolute prediction difference: **6.1042 persons**.

This is strong evidence that the T-30 as-of feature state, season-block fold,
opponent gate and recency weighting are recovered correctly.

## Exact v1.7 T-30 online correction

The original v1.7 walk-forward output makes this formula directly verifiable:

`correction = mean(previous_raw_residuals_actual_minus_prediction) * n / (n + 3)`

where `n` is the number of earlier completed Lech home matches in the same
season. The correction is added to the raw residual-model forecast, then the
result is capped at stadium capacity 43,269.

Applying that formula to the **preserved original raw v1.7 predictions**
reproduces the original final v1.7 prediction column essentially exactly:

- mean absolute prediction difference: **~1.28e-12 persons**;
- maximum absolute prediction difference: **~7.28e-12 persons**.

So the correction layer is no longer a reconstruction uncertainty.

## Remaining blocker: raw residual Ridge specification

The current best-supported raw T-30 reconstruction uses:

- the recovered T-30 feature state;
- season-block prior-season training;
- frequency-gated opponent identity;
- Ridge alpha 0.3;
- 3-year recency sample weighting with latest training match weight 1;
- target = `attendance - season_avg_so_far`;
- point forecast = `season_avg_so_far + predicted_residual`.

That candidate still does **not** reproduce the original v1.7 raw prediction
column tightly enough:

- mean absolute raw-prediction difference: **652.1987 persons**;
- maximum absolute raw-prediction difference: **4,466.3459 persons**;
- candidate raw MAE: **5,221.6** vs original raw v1.7 MAE **5,147.0**;
- after applying the exact recovered correction, candidate final MAE: **4,936.8**
  vs original final v1.7 MAE **4,723.8**.

Because the v1.6.1 direct model reproduces almost exactly with the same recovered
features and training fold, and the v1.7 correction reproduces exactly, the
remaining discrepancy is now isolated to the **raw v1.7 residual Ridge
training/target specification**.

## Reproducible forensic harness

`reconstruct_t30_v17.py` codifies the recovered protocol and refuses to proceed
if the v1.6.1 control is outside a tight tolerance. It then reports, rather than
hides, the remaining v1.7 raw-model gap.

`v17_t30_reconstruction_report.json` records the current evidence numerically.

## Promotion rule

Do not call v1.7 runtime-reproducible and do not use a reconstructed v1.7 model
for live forecasts until its raw T-30 and T-7 walk-forward predictions reproduce
the original archive to a tight numerical tolerance.

The original v1.7 benchmark remains the frozen historical champion; current live
v0.3 lineage remains separate until executable inference recovery is complete.
