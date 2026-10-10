# Beyond Live Signal Study v1

## Purpose

Measure whether timestamped public inventory trajectory contains predictive information beyond the historical attendance baseline.

This is an **exploratory research benchmark**, not a production model and not a promotion mechanism.

## Inputs

The study intentionally reuses existing strict contracts:

- forecast baseline and actual outcome: `get_model_lab_rows_v1()`;
- live state: `multiclub_feature_store_v3`.

Join key:

`ticket_event_id + canonical horizon`

No separate horizon-selection logic is introduced in the study.

## Canonical horizons

- T-30
- T-14
- T-7
- T-3
- T-24h

Model Lab remains the source of truth for strict forecast selection:

- only forecasts available before the target checkpoint;
- one closest eligible forecast per event/model/version/horizon/mode;
- no post-checkpoint fallback.

The feature store independently follows the same one-sided checkpoint rule for the inventory snapshot.

## Study target

For a valid row, `historical_p50` must exist.

Primary correction target:

`baseline_signed_residual = actual_attendance - historical_p50`

Primary baseline error:

`baseline_absolute_error = abs(actual_attendance - historical_p50)`

Observed final error:

`final_absolute_error = abs(actual_attendance - final_p50)`

Observed current uplift:

`baseline_absolute_error - final_absolute_error`

This field describes already-stored final forecasts. It is not evidence that any candidate signal caused the difference.

## Live features examined

### Inventory state

- `available_index`
- `available_pct_of_first`
- `available_pct_of_public_seat_map` where verified

### Raw-total trajectory

- raw 6h velocity
- raw 24h velocity
- raw 6h-vs-24h acceleration

Normalized both to first observed inventory and, where available, public seat-map size.

### Sector-matched trajectory

- matched 6h velocity
- matched 24h velocity
- matched acceleration
- release activity
- sector coverage change
- coverage inventory effect

## Sample independence

A snapshot is **not** an independent sample.

Independence unit = `ticket_event_id`.

The row contract allows at most one row per:

`event x model_version x forecast_mode x canonical_horizon`.

Any future learned benchmark must use event-grouped splits.

## Evidence gates

### Gate A — exploratory cross-club study

Required before interpreting cross-club patterns:

- at least 8 independent events with verified outcomes;
- at least 3 clubs represented among verified outcomes.

Before this gate the benchmark returns:

- `insufficient_independent_events`, or
- `insufficient_club_diversity`.

Correlations may still be numerically returned for diagnostics but must not be interpreted as evidence.

### Gate B — learned live correction challenger

Minimum:

- 20 independent completed matches.

Passing Gate A does **not** permit production promotion.

## Current result — 2026-10-10

Readiness:

- independent outcome events: 4;
- clubs with outcome: 1;
- strict study rows: 6;
- models represented in strict rows: 1;
- cross-club gate: NOT MET;
- learned-correction gate: NOT MET.

Current strict evidence comes from historical Lech events only.

For `beyond-forecast-v0.1`:

- T-14: n=2, baseline MAE 9,605.5, final MAE 9,605.5;
- T-7: n=1, baseline MAE 13,405, final MAE 13,405;
- T-3: n=1, baseline MAE 18,490, final MAE 18,490;
- T-24h: n=2, baseline MAE 12,058.5, final MAE 12,058.5.

Observed live uplift is zero because these stored v0.1 rows have `live_adjustment = 0`.

With n=2, Pearson correlations can mechanically equal +1 or -1. They are diagnostic output only and have no inferential value.

## Backend surfaces

- `live_signal_study_rows_v1`
- `get_live_signal_study_summary_v1()`
- `get_live_signal_study_readiness_v1()`

All are backend/service-role only.

## Next execution rule

Do not change the study protocol after seeing future outcomes unless the change is explicitly versioned as v2.

When Gate A is reached, rerun the same v1 summary and examine:

1. sample/missingness by horizon and feature family;
2. sign and stability of association with baseline signed residual;
3. stability across clubs, not just pooled correlation;
4. whether public-seat-map normalization behaves more consistently than first-observed normalization;
5. whether evidence justifies building the first event-grouped live residual challenger.
