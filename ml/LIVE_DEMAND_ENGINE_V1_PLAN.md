# Beyond Ticketing — Live Demand Engine v1 Plan

Last updated: **2026-10-19**

## Current position

> **Phase A — Foundation: DONE**  
> **Phase B — Shadow Forecasting: DONE**  
> **Five-horizon Structural Prior materialization: DONE / LIVE**  
> **Phase C1-alpha — frozen v2+v8 prospective shadow validation: LIVE**  
> **Phase C1 promotion — EVIDENCE-GATED**  
> **Phase E0 — Sector / Price-area Decision Support MVP: IMPLEMENTED**  
> **Pre-Live v2 historical candidate: FROZEN + SEALED**  
> **d2 Stage 0 Frozen-v2 replay compatibility: DONE / GREEN**  
> **d2 Stage 1 live-residual + TSFM tournament: ACTIVE**

The immediate model-quality roadmap is defined in:

- `ml/MODEL_ACCURACY_DEVELOPMENT_INSTRUCTIONS_V2.md`;
- `ml/DEMAND_FORECAST_DEVELOPMENT_PLAN_V2.md`;
- `ml/CURRENT_MODEL.md`;
- `AI_BOOTSTRAP.md`.

Stage-1 implementation contract:

`ml/D2_STAGE1_MODEL_TOURNAMENT_V1.md`

## Critical architecture state

New live-model development must use the strongest frozen pre-live baseline.

### Frozen Pre-Live Model v2 historical candidate

Freeze ID:

`pre-live-v2-historical-candidate-2026-10-18-v1`

Canonical manifest:

`ml/artifacts/pre_live_v2_historical_candidate_v1/manifest.json`

Architecture:

`history + proven current-season regime -> frozen pre-live anchor`

Historical c2 context extension:

`NO_CONTEXT_ALL_HORIZONS`

Forward-only context such as rivalry, verified absences and media/hype remains prospective research/shadow because complete historical PIT truth does not exist.

### Continuous Live Updater v2

`frozen Pre-Live v2 + live trajectory + inventory state + time-to-kickoff + reliability -> delta / revised forecast`

The baseline is now frozen. New learned d2 development is therefore allowed and is the active model workstream.

Frozen C1 v8 remains a separate prospective comparator and continues running in parallel.

## Current runtime state

Production remains:

`live_adjustment = 0`

C1 v8 remains:

`EXPERIMENTAL_SHADOW`

It does not write production forecast values.

The frozen Pre-Live v2 historical candidate is also not an automatic production replacement.

## Structural Prior production incumbent

Current executable production model specs:

- T-30 `structural-prior-runtime-v1-t30-extra-full`;
- T-14 `structural-prior-runtime-v1-t14-hist-base`;
- T-7 `structural-prior-runtime-v1-t7-gbr-base`;
- T-3 `structural-prior-runtime-v1-t3-hist-full`;
- T-1 `structural-prior-runtime-v1-t1-hist-full`.

These remain the production incumbent until an explicit promotion step changes the production contract.

## Frozen Pre-Live v2 candidate state

Historical candidate contract:

| Horizon | Historical base | b2 regime | historical c2 |
|---|---|---|---|
| T-30 | `structural-prior-runtime-v1-t30-extra-full` | `NO_ADJUSTMENT` | `NO_CONTEXT` |
| T-14 | `structural-prior-runtime-v1-t14-hist-base` | `NO_ADJUSTMENT` | `NO_CONTEXT` |
| T-7 | `hist31-leaf20-l2-1` | `ewma50-resid-k6-cap05-min3` | `NO_CONTEXT` |
| T-3 | `structural-prior-runtime-v1-t3-hist-full` | `ewma50-resid-k2-cap05-min3` | `NO_CONTEXT` |
| T-1 | `structural-prior-runtime-v1-t1-hist-full` | `ewma50-resid-k6-cap05-min3` | `NO_CONTEXT` |

Historical reference mean MAE across exposed 2024/25 + 2025/26:

- T-30: `1867.82`;
- T-14: `1809.45`;
- T-7: `1691.40`;
- T-3: `1682.63`;
- T-1: `1661.52`.

Freeze gate includes exact 20/20 horizon-season reproduction at tolerance `1e-9` plus manifest/source hashes.

Do not mutate or silently refit this anchor during d2 experiments. Any material change requires a new explicit freeze version.

## Frozen C1-alpha package

Package:

`c1-shadow-v8-frozen-2026-10-16-n9`

Frozen expert:

`c1-v2-live-ridge-directocc-compact-generic-a10`

Frozen policy:

`c1-alpha-reliability-policy-v8-fixed-10pp-positive-slope-20pp-single`

Training events:

`[1, 3, 4, 8, 9, 12, 13, 14, 17]`

Rule:

- one observation: LIVE only if disagreement >= `0.20` capacity;
- >=2 observations: LIVE only if disagreement >= `0.10` and live slope to date > 0;
- otherwise PRIOR.

Scheduled inference must never fit this package.

Do not change these thresholds as part of d2 development.

## Current C1 evidence

Historical development/validation:

- raw Live LOEO: **2,929.3 MAE**;
- conservative train-only synthetic Live LOEO: **2,261.5 MAE**;
- stress train-only synthetic Live LOEO: **2,498.8 MAE**;
- four-event chronological Prior: **452.8 MAE**;
- four-event chronological raw Live: **2,103.7 MAE**;
- frozen v8 final policy: **452.8 MAE**, PRIOR selected in **16/16 rows**.

Interpretation:

- synthetic augmentation improves the raw live expert;
- raw Live is not safe as a universal replacement for Prior;
- frozen v8 was conservative and safe on the current retrospective forward events;
- this does not prove it can identify future cases where Live is genuinely better;
- prospective independent completed events remain necessary.

## d2 Stage 0 evidence

Stage 0 replays the exact existing 9-event / 30-row C1 live contract against the sealed Frozen Pre-Live v2 anchor.

Current state:

`FROZEN_V2_EXACT_COMPATIBILITY_READY`

Main-only replay passed after the freeze-lineage stabilization work.

Important diagnostic:

- legacy Structural Prior anchor MAE on these 9 specific events: about `3969`;
- Frozen Pre-Live v2 anchor MAE: about `4128`;
- Frozen-v2 anchor is about `159` seats worse on this very small live replay set.

This does not reopen b2: the b2 historical decision is supported by a much broader four-fold temporal audit. It does mean d2 must benchmark every live correction against the exact Frozen-v2 anchor and must not assume the anchor wins every live event.

## Existing live / decision infrastructure

Already implemented:

- live public inventory collection;
- PIT trajectory / velocity / acceleration;
- release / coverage-change handling;
- frozen C1 v8 prospective shadow;
- sector trajectories;
- price-area trajectories;
- Roboticket price observations;
- guarded sector / price-area recommendations;
- dashboard decision support;
- grouped event-level modelling/evaluation infrastructure;
- exact Frozen-v2 Stage-0 replay lineage.

This infrastructure should be reused by d2 rather than rebuilt from scratch.

## Parallel work allowed while d2 is active

Allowed in parallel:

- scraping / inventory reliability improvements;
- earlier sales-opening detection;
- additional prospective data collection;
- sector / price-area coverage quality;
- data-quality flags;
- outcome collection / scoring automation;
- observability;
- reproducibility fixes;
- frozen-v8 prospective scoring;
- forward-only rivalry / absence / media-hype data collection where valid.

These activities must not mutate the frozen Pre-Live v2 lineage or C1 v8 package silently.

## d2 — Continuous Live Updater

### 1. Continuous time

T-30/T-14/T-7/T-3/T-1 remain standard quality checkpoints.

The model itself should update at meaningful snapshots using continuous `time_to_kickoff`.

Examples may include:

- T-32;
- T-25;
- T-20;
- T-11.5;
- T-4.2;
- any other valid observation time.

### 2. Earliest usable sales evidence

Use inventory from the earliest reliable sales moment.

Do not wait for T-30 if the event has a valid earlier trajectory.

### 3. Target formulations to benchmark

#### A. Delta against frozen Pre-Live v2

Primary direction:

`live_delta = final_attendance - frozen_pre_live_v2_p50`

Final:

`forecast = clip(frozen_pre_live_v2_p50 + governed_live_delta, 0, capacity)`

Capacity-normalized delta should also be benchmarked.

#### B. Remaining demand

Estimate additional demand remaining between the current snapshot and kickoff.

This may be more stable than asking a small live model to relearn the full event attendance level.

#### C. Reliability-weighted blend

Blend frozen Pre-Live and live evidence continuously according to reliability rather than only a binary hard switch.

Frozen v8 remains the comparator; do not mutate it into this formulation.

### 4. Training unit and validation independence

Candidate training rows:

`event x as_of_timestamp`

Independent evaluation unit:

`event`

Rules:

- all snapshots from one event stay in one fold;
- LOEO is primary while independent completed-event N is small;
- event-balanced weights or equivalent are mandatory;
- no random snapshot-row train/test split;
- no future snapshots;
- source Pre-Live forecast must identify freeze ID `pre-live-v2-historical-candidate-2026-10-18-v1` or an explicitly documented fallback.

Do not count multiple timestamps from one held-out event as independent successes.

### 5. Initial d2 features

Reuse existing PIT-safe C1/live infrastructure before adding a feature zoo.

#### Anchor / time

- frozen Pre-Live v2 P50;
- expected occupancy;
- capacity;
- continuous hours/days to kickoff;
- checkpoint labels as diagnostics only.

#### Inventory / trajectory

- normalized availability/inventory;
- observed progress;
- expected progress;
- trajectory gap;
- 6h / 24h / 72h / 7d velocity where available;
- acceleration;
- latest change rate;
- signal readiness/confidence.

#### Sector aggregates

- underperforming/outperforming sector share;
- worst/median sector gap;
- sector-gap dispersion;
- sector velocity dispersion;
- remaining availability concentration;
- release/replenishment activity;
- coverage changes.

#### Price evidence

Use Roboticket price observations only when PIT-valid and coverage semantics are explicit.

Missing price coverage is not a zero-demand signal.

### 6. Reliability inputs

Candidate reliability signals include:

- observation count;
- observation span;
- time to kickoff;
- trajectory stability;
- velocity;
- acceleration;
- coverage completeness;
- material release events;
- sector consistency;
- price-area consistency;
- disagreement with frozen Pre-Live v2;
- scrape/data-quality state.

All reliability thresholds/weights must be explicit and versioned.

### 7. Inventory interpretation

Public availability is a demand proxy, not confirmed paid sales.

Live features must account for:

- ticket release;
- sector opening/closure;
- coverage expansion/contraction;
- scrape anomalies;
- true demand movement as far as it can be inferred safely.

### 8. First d2 tournament — active Stage 1

Canonical contract:

`ml/D2_STAGE1_MODEL_TOURNAMENT_V1.md`

Primary baselines:

1. frozen Pre-Live v2 / zero live correction;
2. training-fold bias-only correction;
3. inventory linear extrapolation.

Focused learned candidates:

- Ridge `alpha=10`;
- Huber robust linear;
- strongly regularized HistGradientBoosting;
- Ridge + Chronos-2 zero-shot trajectory features;
- Ridge + Chronos-Bolt-small zero-shot trajectory features.

#### Time-Series Foundation Model family

Stage 1 explicitly includes:

- `amazon/chronos-2`;
- `amazon/chronos-bolt-small`.

Both model-weight revisions are pinned in the canonical runner, and runtime dependencies are pinned in:

`ml/requirements-d2-tsfm-v1.txt`

Chronos does **not** receive final attendance as a historical time-series point.

TSFM target:

`available_share_of_capacity`

Chronos forecasts the causal public inventory-proxy trajectory toward kickoff. Terminal p50 / uncertainty / projected-removal outputs become additional live features for the supervised attendance-residual model.

Rules:

- zero-shot only in Stage 1;
- no fine-tuning with N=9;
- no cross-learning from held-out outcomes;
- final attendance labels never enter Chronos context;
- at least 2 real live context observations are required for a TSFM-ready row;
- missing historical 6h buckets may be filled only causally from an older observed value;
- a good trajectory forecast is not sufficient: the TSFM challenger must improve final attendance MAE vs the matching Ridge benchmark.

Why this ordering:

- Chronos-2 is the modern higher-capability TSFM challenger;
- Chronos-Bolt-small is the lighter same-family benchmark;
- NeuralProphet / Lag-Llama are not added to Stage 1 because the current evidence does not justify a larger TSFM model zoo.

If the Chronos family shows real attendance-MAE signal, a later Stage 2 may test one richer formulation such as covariate-informed Chronos-2 or fine-tuning after enough independent events exist.

### 9. Forecast refresh and audit trail

A new meaningful snapshot may trigger a new shadow forecast.

Every revision must preserve:

- as-of timestamp;
- input snapshot ID(s);
- frozen Pre-Live freeze/model lineage;
- live model ID;
- feature-contract ID;
- previous forecast;
- revised forecast;
- revision reason/reliability;
- audit trail.

## Accuracy evaluation for d2

Mandatory metrics:

- event-level MAE vs frozen Pre-Live v2;
- event-balanced window MAE;
- latest-row MAE;
- median AE;
- bias;
- occupancy error;
- tail/worst-event degradation;
- revision rate;
- maximum harmful revision;
- percent observations using non-zero live correction;
- event improvement rate;
- performance conditional on observation count/time-to-kickoff;
- model revision magnitude.

A live model is not promoted merely because it improves average MAE on a small development set.

Stage-1 research lead eligibility requires positive improvement on both latest-row MAE and event-balanced window MAE. With N=9, that is still research ranking only.

## CI/CD requirements

All new live challengers follow `ml/MODEL_ACCURACY_DEVELOPMENT_INSTRUCTIONS_V2.md`.

Do not skip:

- source code;
- CI workflow;
- pinned runtime;
- pinned external model revision for TSFM candidates;
- deterministic seeds;
- exact training events;
- exact feature definitions;
- input artifact versions;
- PIT assertions;
- event-independent evaluation;
- frozen-anchor lineage checks;
- machine-readable artifact;
- run/artifact IDs and hashes;
- committed result document;
- explicit decision;
- canonical docs update.

No local-only benchmark becomes canonical.

CI success is not automatic production activation.

## E0 sector / price-area decision support

Current implemented flow remains:

`sector state -> trajectory gap -> no-action projection -> real price-area mapping -> pricing scenario -> guarded recommendation`

Current pricing maturity:

`ASSUMPTION_BASED_SCENARIO`

No automatic price changes:

`auto_price_change_allowed = false`

No learned elasticity or causal uplift claim is allowed yet.

## Promotion boundary

Production learned live correction remains evidence-gated.

Promotion requires:

- enough genuinely prospective independent completed events;
- positive uplift vs the correct frozen incumbent/anchor contract;
- acceptable degradation/tail risk;
- frozen reproducible package;
- full CI evidence;
- explicit human-reviewed promotion.

No automatic production promotion exists.

## Immediate live-engine instruction

> **Run d2 Stage 1 against the exact Frozen Pre-Live v2 anchor using event-independent LOEO. Benchmark compact live-residual models plus zero-shot Chronos-2 / Chronos-Bolt-small trajectory features; final ranking is attendance MAE, not trajectory aesthetics. Keep Frozen C1 v8 and production unchanged, persist exact runtime/model revisions, and treat any N=9 winner as a research lead only.**
