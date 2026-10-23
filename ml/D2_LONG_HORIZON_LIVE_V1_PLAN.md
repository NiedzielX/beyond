# Beyond Ticketing — d2 Long-Horizon Live v1 Plan

Last updated: **2026-10-23**

Status: **P7 HARNESS + EXECUTOR READY / DATA GATE 8 OF 9 / NO REAL TOURNAMENT YET / NO PRODUCTION CHANGE**

Canonical P7 files:

- `ml/p7_long168_harness_v1.py`;
- `ml/test_p7_long168_harness_v1.py`;
- `ml/p7_long168_anchor_replay_v1.py`;
- `ml/p7_long168_tournament_v1.py`;
- `ml/test_p7_long168_executor_v1.py`;
- `.github/workflows/p7-long168-harness-v1.yml`;
- `.github/workflows/p7-long168-executor-v1.yml`;
- `ml/results/P7_LONG168_HARNESS_V1_2026-10-23.md`;
- `ml/results/P7_LONG168_EXECUTOR_V1_2026-10-23.md`.

## Research question

> **Can PIT live ticket trajectory between 72h and 168h before kickoff reduce event-balanced attendance MAE beyond the Structural Prior T-7 forecast?**

This is a separate Track-B challenger family. It does not mutate final24, frozen Long72 P2 or Structural Prior runtimes.

## Current readiness

Current Supabase export:

`public.export_d2_long_horizon_168_rows_v1()`

Latest checkpoint on 2026-10-23:

- independent events with valid rows `>72h`: **8**;
- valid rows `>72h`: **110**;
- research-start threshold: **9 independent events**.

Therefore:

**real P7 model fitting remains prohibited.**

`N=9` is a research-start threshold only. It is not evidence of production adequacy.

## Window and sampling

P7 v1 is scoped to:

`72 < hours_to_kickoff <= 168`

Long168 export sampling:

- maximum window: 168h;
- cadence: 6h;
- latest source snapshot in each event x 6h bucket;
- PIT feature function: `get_live_trajectory_features_v1_1_asof`;
- no attendance target inside live features.

Rows at `<=72h` remain governed by the existing Long72 contracts.

## Data integrity

Every frozen P7 row must satisfy:

- source snapshot identity is fixed;
- `requested_as_of_at` equals feature as-of;
- feature snapshot id equals requested snapshot id;
- `point_in_time_validated = true`;
- as-of precedes kickoff;
- reported hours-to-kickoff agrees with timestamps;
- no future observation is forward-filled;
- no target/outcome field exists in the freeze payload.

Missing evidence remains missing. It is never converted into zero demand.

## Hard research-start gate

At `N<9`:

- freeze fails with `P7_NOT_READY`;
- real tournament execution is blocked;
- only non-model anchor audit is allowed.

At `N>=9`:

1. export current Long168 payload;
2. freeze exact eligible identities;
3. persist deterministic freeze manifest SHA256;
4. verify target/outcome absence;
5. verify T-7 anchor package;
6. only then attach attendance labels;
7. build strict forward-event folds;
8. run the fixed candidate family;
9. run paired event-block uncertainty;
10. issue a research-only decision.

The first P7 artifact after the gate opens must still be the **identity freeze**, not a leaderboard.

## Anchor contract

For all rows in `72 < h <= 168`, control forecast is:

**Structural Prior T-7 / zero live correction**

Forbidden:

- future T-3/T-1 forecasts;
- interpolation from future checkpoints;
- extrapolation of frozen Long72 P2 backward beyond 72h.

P7 challengers model only the residual over the T-7 structural anchor.

## Historical T-7 replay boundary

The current historical Long168 events have **no persisted T-7 rows** in `private.structural_prior_forecasts_v1`.

Therefore P7 uses an explicit replay path:

`ml/p7_long168_anchor_replay_v1.py`

The replay:

- uses frozen Structural Prior Runtime v1 artifacts;
- reconstructs the checkpoint at exactly `kickoff - 7 days`;
- uses attendance only from matches with kickoff before that cutoff;
- uses sporting fixtures strictly before the cutoff date;
- strips the target event's `actual_attendance` from event metadata before replay;
- requires the replay cutoff to be no later than every Long168 row as-of;
- keeps verified capacity bounds.

This evidence is classified exactly as:

`historical_pit_replay`

and:

`persisted_forecast = false`

It must never be presented as a forecast that was actually persisted seven days before the match.

### Frozen artifact lineage

Expected T-7 artifact SHA256:

`97e712245d6539396030e88ea450809f4265bd7538aa90b29e234420231ac927`

Expected historical runtime SHA256:

`3c6b35142c6bd20a484f2aa758cd41284fd6f4c6db1353b138f81cf321161569`

The execution workflow checks the actual repository file bytes before any replay.

### Target-attendance invariance

For every P7 event, the anchor audit mutates the event's exact-kickoff attendance row to an impossible sentinel and replays T-7.

The T-7 P50 must remain unchanged within `1e-9`.

Every eligible event must have and pass this check; none may be silently skipped.

## Fixed P7 v1 challenger family

### A. `anchor-only-t7`

Control. No fitted live correction.

### B. `q50-linear-residual-a002`

- `QuantileRegressor`;
- quantile `0.50`;
- alpha `0.002`;
- solver `highs`;
- training-fold median imputation;
- training-fold `RobustScaler`;
- no hyperparameter search.

### C. `gbr-l1-depth2-n50-lr003`

- `GradientBoostingRegressor`;
- loss `absolute_error`;
- `n_estimators=50`;
- `learning_rate=0.03`;
- `max_depth=2`;
- `min_samples_leaf=4`;
- `random_state=42`;
- no hyperparameter search.

A materially different feature/model family requires a new experiment version.

## Feature contract

Only the frozen allowlist in `ml/p7_long168_harness_v1.py` may enter P7 v1.

The list is limited to PIT live inventory / trajectory features already available in the current export, including:

- hours-to-kickoff;
- current / first available inventory;
- available share of capacity;
- net removed inventory;
- velocity / acceleration measures;
- observation-window / snapshot-age / gap-quality measures;
- release/data-gap flags.

P4 schedule/context features are not silently added to P7 v1.

## Event weighting

Trajectory rows are not independent evidence.

During learned-model fitting:

`row_weight = 1 / number_of_training_rows_for_that_event`

so each training event contributes equal total weight.

Independent evidence unit remains:

`ticket_event`

## Validation contract

Use:

`ml/temporal_validation_v1.py::build_forward_event_folds`

with:

- strict chronological forward-event ordering;
- minimum training events: `5`;
- `train_end < test_start`;
- tied kickoffs cannot train one another;
- no random snapshot split;
- exact fold identities + SHA persisted.

At exactly nine chronological events this normally yields four held-out forward events, subject to tied kickoffs.

LOEO may be diagnostic but cannot replace the forward view.

## Primary metric

**Strict-forward event-balanced MAE**

For each held-out event:

1. average absolute error across its eligible 72–168h rows;
2. average those event MAEs equally.

Required diagnostics:

- event median AE;
- event P90 AE;
- event-balanced signed bias;
- worst-event degradation;
- event-improvement rate;
- forward-fold improvement rate;
- MAE by 72–96 / 96–120 / 120–144 / 144–168h band;
- coverage / missingness.

## Uncertainty

Use:

`ml/mae_delta_uncertainty_v1.py`

with:

- paired event-block percentile bootstrap;
- 5,000 draws;
- seed `42`.

Interpretation:

- `ΔMAE >= 0` → `NO_MAE_GAIN`;
- `ΔMAE < 0` and CI crosses zero → `POINT_GAIN_UNCERTAINTY_LIMITED`;
- CI upper bound `<0` → `SUPPORTED_HISTORICAL_FORWARD_GAIN`.

## Research advancement

A learned candidate may advance only when all precommitted gates pass and:

1. strict-forward event-balanced MAE beats the T-7 anchor;
2. event improvement rate is `>50%`;
3. forward-fold improvement rate is `>50%`.

Bootstrap evidence and bias/tail diagnostics must always accompany the decision.

If the majority-event or majority-fold rule fails, decision is:

`RETAIN_ANCHOR`

No P7 v1 result can directly activate production.

## Execution workflow

Workflow:

`.github/workflows/p7-long168-executor-v1.yml`

### Automatic `main` push behavior

Only:

1. validate code;
2. verify frozen artifact bytes;
3. fetch Long168 + C1 support data through main-only OIDC;
4. run T-7 anchor audit;
5. upload audit evidence.

**No real P7 challenger is fitted automatically.**

### Real tournament behavior

Requires explicit:

`workflow_dispatch -> mode=execute`

The execute path itself starts with `freeze`, so it still fails closed below `N=9`.

Execution artifacts:

- frozen identity manifest;
- T-7 anchor package;
- strict-forward fold manifest;
- prediction CSV;
- machine-readable scorecard.

## Evidence boundary

Previously inspected historical events remain exposed historical evidence.

Historical T-7 replay is not a persisted forecast and not genuine prospective evidence.

Any P7 challenger frozen after this research must collect separate genuine future evidence before production consideration.

## Immediate work order

### While current state remains 8/9

1. keep Long168 evidence collection unchanged;
2. keep harness/candidate contract fixed;
3. run only anchor audit, never the real tournament;
4. keep readiness watch active;
5. do not lower the gate.

### Immediately at 9/9

1. re-read `public.ml_research_readiness_v1()`;
2. explicitly dispatch P7 executor with `mode=execute`;
3. freeze exact identities + SHA;
4. verify frozen T-7 replay;
5. attach labels only after freeze validation;
6. build strict forward-event fold manifest;
7. run the fixed tournament;
8. calculate event-balanced metrics + guardrails;
9. run paired event-block uncertainty;
10. persist a human-readable result and explicit `ADVANCE_RESEARCH / RETAIN_ANCHOR / INSUFFICIENT` decision;
11. keep production unchanged.

## What not to do

- do not lower the 9-event gate;
- do not inspect real model results before identity freeze;
- do not claim replayed T-7 anchors were persisted forecasts;
- do not random-split snapshots;
- do not let high-coverage events dominate training;
- do not forward-fill future observations;
- do not use future T-3/T-1 anchors;
- do not extrapolate Long72 P2 backward;
- do not broaden the hyperparameter search after seeing results;
- do not mutate frozen final24/Long72 packages;
- do not auto-activate production.

## Production boundary

Always:

`live_adjustment = 0`

until explicit reviewed production promotion based on separate genuine future evidence.
