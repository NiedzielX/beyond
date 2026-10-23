# Beyond Ticketing — d2 Long-Horizon Live v1 Plan

Last updated: **2026-10-23**

Status: **P7 HARNESS READY / DATA GATE 8 OF 9 / NO PRODUCTION CHANGE**

Canonical harness:

- `ml/p7_long168_harness_v1.py`;
- `ml/test_p7_long168_harness_v1.py`;
- `.github/workflows/p7-long168-harness-v1.yml`;
- `ml/results/P7_LONG168_HARNESS_V1_2026-10-23.md`.

## Research question

> **Can PIT live ticket trajectory between 72h and 168h before kickoff reduce event-balanced attendance MAE beyond the Structural Prior T-7 forecast?**

This is a separate Track-B challenger family. It does not mutate final24, frozen Long72 P2 or Structural Prior runtimes.

## Current readiness

Current Supabase long-horizon export:

`public.export_d2_long_horizon_168_rows_v1()`

Sampling contract:

- maximum window: 168h;
- cadence: 6h;
- latest source snapshot in each event x 6h bucket;
- PIT feature function: `get_live_trajectory_features_v1_1_asof`;
- no target in live features.

Latest checkpoint on 2026-10-23:

- independent events with valid rows `>72h`: **8**;
- valid rows `>72h`: **110**;
- research-start threshold: **9 independent events**.

Therefore:

**P7 model fitting remains prohibited.**

`N=9` is a research-start threshold inherited from the existing frozen d2 development scale. It is not proof of adequacy and never implies production readiness.

## Data integrity

Every P7 row must be genuinely point-in-time:

- source snapshot identity is frozen;
- `requested_as_of_at` equals the feature as-of;
- feature snapshot id equals requested snapshot id;
- `point_in_time_validated = true`;
- as-of precedes kickoff;
- reported hours-to-kickoff agrees with timestamps;
- no future observation may be forward-filled;
- no attendance target/outcome may exist in the freeze payload.

Missing history is missing evidence, not zero demand.

## P7 window

P7 v1 is intentionally scoped to:

`72 < hours_to_kickoff <= 168`

This avoids silently mixing the already-developed Long72 problem with the new earlier-horizon problem.

Rows at `<=72h` remain governed by the existing Long72 research/package contracts.

## Pre-result freeze sequence

When the ninth independent event becomes eligible:

1. export the current Long168 payload;
2. filter exact eligible rows in `72 < h <= 168`;
3. validate PIT lineage and reject target/outcome fields;
4. freeze exact identities:
   - `ticket_event_id`;
   - `requested_as_of_at`;
   - `requested_snapshot_id`;
   - `bucket_6h`;
   - kickoff / coverage metadata;
5. persist deterministic manifest SHA256;
6. only after the manifest exists, join actual attendance for supervised evaluation;
7. only then open model comparisons.

At `N<9`, the harness must fail with:

`P7_NOT_READY`

The first output at 9/9 is a **freeze manifest**, not a model leaderboard.

## Anchor rule — frozen before model results

For the entire P7 v1 72–168h band, use:

**Structural Prior T-7 / zero live correction**

as the incumbent control.

Rules:

- T-7 must be PIT-safe and available at or before the live row as-of;
- do not use T-3/T-1 before those checkpoints exist;
- do not interpolate using future structural checkpoints;
- do not extrapolate frozen Long72 P2 backward beyond 72h.

P7 challengers predict a residual over the T-7 structural anchor.

## Fixed P7 v1 challenger family

The family is deliberately small because independent-event N is small.

### A. `anchor-only-t7`

No fitted live correction.

### B. `q50-linear-residual-a002`

MAE-native linear residual challenger:

- `QuantileRegressor`;
- quantile `0.50`;
- alpha `0.002`;
- solver `highs`;
- training-fold median imputation;
- training-fold `RobustScaler`;
- no hyperparameter search.

### C. `gbr-l1-depth2-n50-lr003`

Small nonlinear absolute-error residual challenger:

- `GradientBoostingRegressor`;
- loss `absolute_error`;
- `n_estimators=50`;
- `learning_rate=0.03`;
- `max_depth=2`;
- `min_samples_leaf=4`;
- `random_state=42`;
- no hyperparameter search.

No broad tuning is allowed under P7 v1. A materially different feature/model family requires a new version.

## Feature contract

Only the frozen allowlist in `ml/p7_long168_harness_v1.py` is allowed.

The allowlist is limited to PIT live inventory/trajectory features already available in the current export, including:

- hours-to-kickoff;
- current / first available inventory;
- available share of capacity;
- net removed inventory;
- velocity and acceleration measures;
- observation-window / snapshot-age / gap quality measures;
- release/data-gap flags.

P4 schedule/context features are **not silently added** to P7 v1. If context is later combined with Long168, that is a new experiment/version.

## Event weighting

Trajectory rows are not independent units.

During fitting:

`row_weight = 1 / number_of_training_rows_for_that_event`

so every training event contributes total weight `1` regardless of snapshot coverage.

Independent evidence unit remains:

`ticket_event`

## Validation contract

Use:

`ml/temporal_validation_v1.py::build_forward_event_folds`

with:

- strict forward-event ordering by kickoff;
- minimum training events: `5`;
- `train_end < test_start`;
- tied kickoffs cannot train one another;
- no random snapshot split;
- exact fold identities + SHA persisted.

LOEO may be diagnostic but cannot replace strict forward-event evidence.

## Metrics

Primary:

**event-balanced MAE**.

For each held-out event, first average AE across its eligible trajectory rows, then average event MAEs equally.

Required secondary diagnostics:

- median AE;
- signed bias;
- P90 AE;
- worst-event degradation;
- event-improvement rate;
- forward-fold MAE delta;
- MAE by 24h band:
  - 72–96h;
  - 96–120h;
  - 120–144h;
  - 144–168h;
- coverage / missingness.

## Uncertainty

Use canonical:

`ml/mae_delta_uncertainty_v1.py`

with paired event-block bootstrap:

- 5,000 draws;
- seed `42`.

Interpretation:

- `ΔMAE >= 0` → `NO_MAE_GAIN`;
- `ΔMAE < 0` and CI crosses zero → `POINT_GAIN_UNCERTAINTY_LIMITED`;
- CI upper bound `<0` → `SUPPORTED_HISTORICAL_FORWARD_GAIN`.

At N=9, uncertainty is expected to be wide. Report it honestly.

## Research advancement

A candidate may advance only as a **research challenger** when:

1. strict-forward event-balanced MAE beats the T-7 anchor;
2. a majority of independently held-out events improve;
3. a majority of usable forward folds improve;
4. PIT/lineage/reproducibility gates pass.

Bias/tail metrics and paired bootstrap must accompany the decision.

No P7 v1 result can activate production directly.

## Evidence boundary

Previously inspected historical events remain exposed historical evidence. Do not relabel them as unseen.

The original final24 frozen development events and subsequent diagnostic events remain part of research history. Genuine future fixtures must remain separately labeled as prospective evidence after any P7 challenger is frozen.

## Immediate work order

### While current state remains 8/9

1. keep Long168 data collection unchanged;
2. keep the P7 harness/contract fixed;
3. do not fit challengers;
4. keep the readiness watch active.

### Immediately at 9/9

1. freeze exact identities + manifest SHA;
2. verify anchor availability and feature contract;
3. attach labels only after freeze;
4. build strict forward-event fold manifest;
5. run the fixed three-candidate P7 v1 tournament;
6. calculate event-balanced MAE + guardrails;
7. run paired event-block uncertainty;
8. persist machine-readable artifacts and human result doc;
9. make an explicit `ADVANCE_RESEARCH / RETAIN_ANCHOR / INSUFFICIENT` decision;
10. keep production unchanged.

## What not to do

- do not lower the 9-event gate;
- do not inspect model results before identity freeze;
- do not random-split snapshots;
- do not let high-coverage events dominate training;
- do not forward-fill future observations;
- do not join attendance before freeze;
- do not use future T-3/T-1 anchors;
- do not extrapolate Long72 P2 backward;
- do not broaden the hyperparameter search after seeing results;
- do not mutate frozen final24/Long72 packages;
- do not activate production.

## Production boundary

Always:

`live_adjustment = 0`

until explicit reviewed production promotion based on separate genuine future evidence.
