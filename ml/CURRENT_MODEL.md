# Beyond Ticketing — Current Model & Product State

Last product-direction update: **2026-10-18**

This is the canonical short-form state. Read `AI_BOOTSTRAP.md` first in a cold session.

## Current north star

Beyond is a **live demand decision system**, not only an attendance model.

Forecasting stack:

`Historical Structural Prior -> Current-season adjustment -> Match context -> Live demand trajectory -> Forecast revision`

Decision-support stack:

`Event forecast -> Sector trajectory -> No-action projection -> Price-area scenario -> Recommendation`

Public seat-map inventory is a **demand proxy, not confirmed paid sales**.

## Structural Prior runtime

All five horizons are executable and frozen:

| Horizon | Model spec | 2023/24 dev MAE | 2024/25 historical MAE | 2025/26 historical MAE |
|---|---|---:|---:|---:|
| T-30 | `structural-prior-runtime-v1-t30-extra-full` | 2,559.7 | 1,889.4 | 1,846.3 |
| T-14 | `structural-prior-runtime-v1-t14-hist-base` | 2,340.0 | 1,748.5 | 1,870.4 |
| T-7 | `structural-prior-runtime-v1-t7-gbr-base` | 2,476.8 | 1,777.7 | 1,802.3 |
| T-3 | `structural-prior-runtime-v1-t3-hist-full` | 2,311.6 | 1,661.7 | 1,775.1 |
| T-1 | `structural-prior-runtime-v1-t1-hist-full` | 2,348.0 | 1,651.7 | 1,742.8 |

Frozen bundle:

`structural-prior-runtime-v1-frozen-2026-10-15-t1`

Scheduled Structural Prior inference is load + predict only.

Production remains:

`live_adjustment = 0`

## Historical evidence base

Canonical historical benchmark:

- Ekstraklasa 2021/22–2025/26;
- 1,530 matches;
- 7,650 horizon rows;
- verified historical capacity coverage 100%.

2024/25 and 2025/26 are exposed historical reference seasons, not pristine fresh holdouts for new R&D.

## Current forecasting capability

### a) Historical data

**Implemented / mature.**

Structural Prior is the incumbent baseline. It should be tuned, not rebuilt without evidence.

### b) Current season

**Implemented partially.**

Current-season / recent host evidence exists, but the next model-quality step is a stronger explicit current-season adjustment and recency weighting.

### c) Match context

**Implemented partially.**

Existing context includes football / schedule / host-opponent information. Future-fixture attractiveness, fixture cannibalization and governed PIT squad context are not yet first-class features.

### d) Live demand

**Implemented and running, but not yet maximized.**

Live inventory, trajectory, velocity and C1 shadow inference exist. The next direction is continuous revision from meaningful snapshots while keeping the official horizons as evaluation checkpoints.

Canonical development plan:

`ml/DEMAND_FORECAST_DEVELOPMENT_PLAN_V2.md`

## C1-alpha development evidence

Development evidence contains:

- 9 completed in-domain Ekstraklasa events;
- 206 PIT-valid full-trajectory rows;
- 30 regularized PIT-valid final-24h rows.

Key results:

- Structural Prior T-1 on this difficult development subset: **3,968.7 MAE**;
- v2 live expert: **2,929.3 MAE**;
- non-deployable Prior/Live oracle: **1,867.9 MAE**;
- v8 development replay: **2,713.3 window MAE**;
- v8 latest-row replay: **1,998.1 MAE**.

These are **development results only**. The v8 policy was designed using the same small event set and is not independently validated.

## Frozen C1 v8 prospective package — LIVE

Package:

`c1-shadow-v8-frozen-2026-10-16-n9`

Status:

`EXPERIMENTAL_SHADOW`

Frozen live expert:

`c1-v2-live-ridge-directocc-compact-generic-a10`

Policy:

`c1-alpha-reliability-policy-v8-fixed-10pp-positive-slope-20pp-single`

Frozen training events:

`[1, 3, 4, 8, 9, 12, 13, 14, 17]`

The scheduled runtime loads the artifact and predicts only. It contains no fitting path.

## Current prospective evidence — verified 2026-10-18

Production status surface reports:

- prediction rows: **31**;
- prospective events: **5**;
- scored prospective events: **0**;
- validation state: `AWAITING_FIRST_PROSPECTIVE_SCORE`;
- production live adjustment: **0**.

Therefore there is **no confirmed prospective live MAE yet**.

Do not describe the 2.0k–2.7k replay range as current production accuracy.

## Immediate model-quality validation — NEW PRIORITY 1

Before adding more forecasting features, run the strongest historical approximation of an unseen-event deployment test:

1. **Leave-One-Event-Out** — remove the tested event from fitting/tuning entirely;
2. reconstruct PIT-safe T-7 / T-3 / T-1 evidence for the held-out event;
3. compare Structural Prior, Live expert/C1 and final policy on the same rows;
4. calculate MAE, bias and worst-event degradation;
5. repeat using **chronological walk-forward**.

This does not replace prospective validation, but it should answer whether the current live model is actually closer to ~2k, ~3k or worse on unseen historical events.

## Model-quality development order

Canonical plan:

`ml/DEMAND_FORECAST_DEVELOPMENT_PLAN_V2.md`

Order:

1. strict LOEO + chronological walk-forward validation;
2. stronger current-season adjustment;
3. richer match context — especially future-fixture cannibalization and reliable squad context;
4. continuous live demand correction;
5. historical Structural Prior tuning.

## E0 — Sector & Price-area Decision Support — IMPLEMENTED

The former E0 implementation path is no longer the primary next build.

Implemented capabilities include:

- real sector inventory trajectories;
- `UNDERPERFORMING / ON_TRACK / OUTPERFORMING / INSUFFICIENT_SIGNAL` status;
- bounded no-action sector projection;
- Roboticket price-area inventory and price capture where available;
- assumption-based pricing scenarios;
- guarded product recommendation;
- mixed-price sectors split by real price areas;
- RLS-safe dashboard caches and Event Detail UI.

Current pricing semantics:

`ASSUMPTION_BASED_SCENARIO`

`auto_price_change_allowed = false`

No learned elasticity or causal uplift is claimed.

Club decision/execution workflow is intentionally deferred. Any demo of a club taking an action and improving sales must be explicitly labeled **simulated scenario**, not measured causal uplift.

## Evaluation governance

- no future leakage;
- event is the independent evaluation unit;
- multiple snapshots from one event are correlated rows, not independent matches;
- no random row split across the same event trajectories;
- every feature must be reconstructable as-of the forecast timestamp;
- compare challengers against the exact incumbent on identical event/horizon pairs;
- replay is not prospective evidence;
- do not present the oracle as deployable;
- C1 v8 stays frozen during prospective validation;
- production remains `live_adjustment = 0` until explicit promotion.
