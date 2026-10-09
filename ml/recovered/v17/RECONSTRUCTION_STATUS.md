# v1.7 inference reconstruction status

Status date: 2026-10-09

## What is now recovered

The original `lech_early_model_v17.zip` has been found and verified. Its
benchmark outputs, design report and exact T-30 correction semantics are no
longer inferred from later documents.

The immediately preceding `lech_model_hardening_v161.zip` also survives with
both fitted Ridge joblibs and feature contracts.

## T-30 feature pipeline recovery

Using the preserved v1.2 enriched history plus the v1.6.1 feature contract, the
T-30 as-of feature builder has been reconstructed with the following semantics:

- forecast cutoff = target kickoff minus 30 days;
- only Lech home attendances before that cutoff are available to history
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
- opponent identity is frequency-gated from the training fold only; minimum
  historical observations = 3, otherwise `other`;
- T-30 recency weighting uses a 3-year half-life;
- Ridge alpha in the v1.6.1 predecessor = 0.3.

### Reconstruction control result

Retraining the **v1.6.1 direct T-30 Ridge** with the reconstructed features
reproduces its preserved 68 walk-forward predictions to approximately numerical
solver tolerance:

- mean absolute prediction difference: **~0.99 persons**;
- maximum prediction difference: **~6.1 persons**.

This is strong evidence that the T-30 as-of feature state, fold protocol,
opponent gate and recency weighting have been recovered correctly.

## Exact v1.7 T-30 online correction

The original v1.7 walk-forward output makes this formula directly verifiable:

`correction = mean(previous_raw_residuals_actual_minus_prediction) * n / (n + 3)`

where `n` is the number of earlier completed Lech home matches in the same
season. The correction is added to the raw residual-model forecast, then the
result is capped at stadium capacity 43,269.

## Remaining blocker: raw residual model

A first controlled reconstruction of the raw T-30 v1.7 model used:

- the recovered T-30 feature state;
- frequency-gated opponent identity;
- Ridge alpha 0.3;
- 3-year recency sample weighting;
- target = `attendance - season_avg_so_far`;
- point forecast = `season_avg_so_far + predicted_residual`.

That candidate does **not** yet reproduce the original v1.7 raw prediction
column tightly enough:

- mean absolute raw-prediction difference: **~652 persons**;
- maximum difference: **~4,466 persons**.

Because the v1.6.1 direct model reproduces almost exactly with the same recovered
features, the remaining discrepancy is isolated to the v1.7 residual-model
training/target specification rather than the T-30 feature builder.

## Promotion rule

Do not call v1.7 runtime-reproducible and do not use a reconstructed v1.7 model
for live forecasts until its raw T-30 and T-7 walk-forward predictions reproduce
the original archive to a tight numerical tolerance.

The original v1.7 benchmark remains the frozen historical champion; current live
v0.3 lineage remains separate until executable inference recovery is complete.
