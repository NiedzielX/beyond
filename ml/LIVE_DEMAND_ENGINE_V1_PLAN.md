# Beyond Ticketing — Live Demand Engine v1 Plan

Last updated: **2026-10-18**

## Current position

> **Phase A — Foundation: DONE**  
> **Phase B — Shadow Forecasting: DONE**  
> **Five-horizon Structural Prior materialization: DONE / LIVE**  
> **Phase C1-alpha — frozen v2+v8 prospective shadow validation: LIVE**  
> **Phase C1 promotion — EVIDENCE-GATED**  
> **Phase E0 — Sector / Price-area Decision Support MVP: IMPLEMENTED**  
> **New learned live development: WAIT FOR PRE-LIVE v2 FREEZE**

The immediate model-quality roadmap is defined in:

- `ml/MODEL_ACCURACY_DEVELOPMENT_INSTRUCTIONS_V2.md`;
- `ml/DEMAND_FORECAST_DEVELOPMENT_PLAN_V2.md`;
- `ml/CURRENT_MODEL.md`.

## Critical architecture change

New live-model development must use the strongest frozen pre-live baseline.

Target architecture:

### Pre-Live Model v2

`history + current-season regime + match context -> pre-live forecast`

### Continuous Live Updater v2

`Pre-Live v2 + live trajectory + inventory state + time-to-kickoff + reliability -> delta / revised forecast`

Therefore new learned live correction should not be trained while the baseline is still being materially changed by a2/b2/c2 optimization.

Frozen C1 v8 remains a separate prospective comparator and continues running in parallel.

## Current runtime state

Production remains:

`live_adjustment = 0`

C1 v8 remains:

`EXPERIMENTAL_SHADOW`

It does not write production forecast values.

## Structural Prior incumbent

Current executable model specs:

- T-30 `structural-prior-runtime-v1-t30-extra-full`;
- T-14 `structural-prior-runtime-v1-t14-hist-base`;
- T-7 `structural-prior-runtime-v1-t7-gbr-base`;
- T-3 `structural-prior-runtime-v1-t3-hist-full`;
- T-1 `structural-prior-runtime-v1-t1-hist-full`.

These remain the production incumbent while Pre-Live v2 challengers are evaluated.

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

Do not change these thresholds as part of the new accuracy roadmap.

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
- dashboard decision support.

This infrastructure remains useful and should continue collecting prospective evidence during Pre-Live v2 development.

## What may continue before Pre-Live v2 freeze

Allowed in parallel:

- scraping / inventory reliability improvements;
- earlier sales-opening detection;
- additional prospective data collection;
- sector / price-area coverage quality;
- data-quality flags;
- outcome collection / scoring automation;
- observability;
- reproducibility fixes;
- frozen-v8 prospective scoring.

Do not treat these as permission to train/promote a new learned d2 correction against a moving baseline.

## d2 — Continuous Live Updater after Pre-Live v2 freeze

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

#### A. Delta against Pre-Live v2

`live_delta = final_attendance - pre_live_prediction`

Final:

`forecast = pre_live_prediction + governed_live_delta`

#### B. Remaining demand

Estimate additional demand remaining between current snapshot and kickoff.

This may be more stable than asking a small live model to relearn the full event attendance level.

#### C. Reliability-weighted blend

Blend Pre-Live and live evidence continuously according to reliability rather than only a binary hard switch.

Frozen v8 remains the comparator; do not mutate it into this formulation.

### 4. Reliability inputs

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
- disagreement with Pre-Live;
- scrape/data-quality state.

All reliability thresholds/weights must be explicit and versioned.

### 5. Inventory interpretation

Public availability is a demand proxy, not confirmed paid sales.

Live features must account for:

- ticket release;
- sector opening/closure;
- coverage expansion/contraction;
- scrape anomalies;
- true demand movement as far as it can be inferred safely.

### 6. Forecast refresh

A new meaningful snapshot may trigger a new shadow forecast.

Every revision must preserve:

- as-of timestamp;
- input snapshot ID(s);
- Pre-Live model ID;
- live model ID;
- feature-contract ID;
- previous forecast;
- revised forecast;
- revision reason/reliability;
- audit trail.

## Accuracy evaluation for d2

Mandatory metrics:

- event-level MAE;
- window MAE;
- latest-row MAE;
- median AE;
- bias;
- tail/worst-event degradation;
- revision rate;
- maximum harmful revision;
- percent observations using non-zero live correction;
- performance conditional on observation count/time-to-kickoff where possible.

A live model is not promoted merely because it improves average MAE on a small development set.

## CI/CD requirements

All new live challengers follow `ml/MODEL_ACCURACY_DEVELOPMENT_INSTRUCTIONS_V2.md`.

Do not skip:

- source code;
- CI workflow;
- pinned runtime;
- deterministic seeds;
- exact training events;
- exact feature definitions;
- input artifact versions;
- PIT assertions;
- event-independent evaluation;
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
- positive uplift vs the correct frozen incumbent;
- acceptable degradation/tail risk;
- frozen reproducible package;
- full CI evidence;
- explicit human-reviewed promotion.

No automatic production promotion exists.

## Immediate live-engine instruction

> **Keep frozen C1 v8 and data collection running, improve live-data infrastructure where useful, but do not train/promote the next learned live correction until Pre-Live v2 is frozen. Then build d2 as a continuous correction/remaining-demand/reliability layer against that stronger baseline.**
