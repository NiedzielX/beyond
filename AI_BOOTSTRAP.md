# Beyond — AI Bootstrap / Read This First

Last product-direction update: **2026-10-18**

This file exists so a new AI/chat session continues the actual Beyond plan instead of rediscovering or redefining it.

## Cold-start rule

Before doing Beyond forecasting, ML, dashboard, Growth or recommendation work, read in this order:

1. `ml/CURRENT_MODEL.md` — canonical current model/product state;
2. `ml/DEMAND_FORECAST_DEVELOPMENT_PLAN_V2.md` — current forecasting-quality development order;
3. `ml/C1_V8_PROSPECTIVE_SHADOW_V1.md` — frozen C1 prospective runtime/governance;
4. `ml/LIVE_DEMAND_ENGINE_V1_PLAN.md` — live forecasting roadmap;
5. `ml/SECTOR_DECISION_PRICING_V1.md` — E0 sector/pricing product contract;
6. `ml/NORTH_STAR.md`;
7. `ml/LIVE_FORECAST_ORCHESTRATOR_V1.md`;
8. `ml/STRUCTURAL_PRIOR_MATERIALIZER_V1.md`;
9. `ml/MODEL_PROMOTION_GOVERNANCE_V1.md`.

## Critical product direction

Beyond is a **live demand decision system**, not primarily a campaign tool or a single attendance model.

Forecasting direction:

`Historical baseline -> Current-season adjustment -> Match context -> Live demand trajectory -> Forecast revision`

Decision-support direction:

`Event forecast -> Sector trajectory -> No-action projection -> Price-area scenario -> Recommendation`

Public seat-map inventory is a **demand proxy, not confirmed paid sales**.

## Structural Prior — production incumbent

All five horizons T-30/T-14/T-7/T-3/T-1 are executable and frozen.

Production remains:

`live_adjustment = 0`

Historical benchmark reference:

| Horizon | 2024/25 MAE | 2025/26 MAE |
|---|---:|---:|
| T-30 | 1,889.4 | 1,846.3 |
| T-14 | 1,748.5 | 1,870.4 |
| T-7 | 1,777.7 | 1,802.3 |
| T-3 | 1,661.7 | 1,775.1 |
| T-1 | 1,651.7 | 1,742.8 |

These are historical reference results, not prospective 2026/27 accuracy.

## C1 v8 — frozen prospective shadow

Package:

`c1-shadow-v8-frozen-2026-10-16-n9`

Status:

`EXPERIMENTAL_SHADOW`

Frozen live expert:

`c1-v2-live-ridge-directocc-compact-generic-a10`

Frozen policy:

`c1-alpha-reliability-policy-v8-fixed-10pp-positive-slope-20pp-single`

Training events:

`[1, 3, 4, 8, 9, 12, 13, 14, 17]`

Do not retune or silently retrain this package during prospective validation.

### Development evidence

- v2 live expert: **2,929.3 MAE** vs Prior **3,968.7** on the development set;
- non-deployable Prior/Live oracle: **1,867.9 MAE**;
- v8: **2,713.3 window MAE** and **1,998.1 latest-row MAE** in development replay.

These values are **development evidence only** because model/policy design used the same small event set.

### Current prospective evidence — 2026-10-18

Runtime state verified in production:

- prediction rows: **31**;
- prospective events: **5**;
- scored prospective events: **0**;
- validation state: `AWAITING_FIRST_PROSPECTIVE_SCORE`;
- production live adjustment: **0**.

Therefore there is **no confirmed prospective live MAE yet**.

The next fresh evidence milestone is the first completed event for which the pre-outcome C1 decision already exists.

## E0 sector / price-area decision support — implemented

The previous docs described E0 as the next build. That is no longer the current state.

Implemented capabilities include:

- sector trajectory / relative status;
- release-aware public-inventory interpretation;
- bounded no-action sector projection;
- real Roboticket price capture where available;
- sector -> price-area mapping;
- assumption-based `-10% / -5% / HOLD / +5% / +10%` scenario logic;
- guarded `DECREASE / HOLD / INCREASE / MONITOR` recommendation;
- mixed-price sectors split into real price areas rather than a fake weighted sector price;
- RLS-safe dashboard caches and UI;
- `auto_price_change_allowed = false`.

Do not claim learned elasticity or causal pricing uplift. E0 remains assumption-based decision support.

Club decision/execution workflow is intentionally deferred for now. If product demos simulate an intervention, label it explicitly as **simulated**, never as observed club uplift.

## Active forecasting development plan

Canonical plan:

`ml/DEMAND_FORECAST_DEVELOPMENT_PLAN_V2.md`

Development order:

1. **Validate the current model honestly**
   - Leave-One-Event-Out;
   - chronological walk-forward;
   - held-out event must not participate in fitting/tuning;
   - compare Structural Prior vs Live/C1 vs final policy on identical PIT evidence.
2. **Strengthen current-season adjustment**
   - recent home matches;
   - above/below historical club baseline;
   - recency weighting.
3. **Expand match context**
   - opponent attractiveness;
   - future-fixture attractiveness;
   - fixture cannibalization/congestion;
   - form/position;
   - reliable PIT squad context where available.
4. **Develop continuous live demand correction**
   - inventory from earliest sales moment;
   - velocity/acceleration/sector/price-area movement;
   - forecast revision after meaningful snapshots;
   - T-30/T-14/T-7/T-3/T-1 remain evaluation checkpoints, not the only reasoning times.
5. **Tune historical Structural Prior last**
   - feature contribution;
   - remove noisy features;
   - stronger recency weighting;
   - no unnecessary architecture rewrite.

## Why validation is first

We currently know that historical Structural Prior benchmarks are strong and that C1 development replay is promising. We do **not** yet know the true unseen-event live MAE.

The immediate objective is to produce the strongest leakage-safe historical approximation of deployment quality:

`LOEO + chronological walk-forward + strict point-in-time replay`

This does not replace prospective validation, but it tells us whether the current model is actually closer to ~2k, ~3k or worse before more feature development.

## Non-negotiable forecasting rules

- no future leakage;
- event is the independent evaluation unit;
- multiple snapshots from one event do not count as multiple matches;
- no random snapshot-row train/test split across the same events;
- every feature must exist as-of the forecast timestamp;
- never present the oracle as deployable;
- never call development replay prospective evidence;
- C1 v8 stays frozen during its prospective evidence collection;
- production remains `live_adjustment = 0` until explicit promotion.

## One-line cold-start instruction

> **Start with `ml/DEMAND_FORECAST_DEVELOPMENT_PLAN_V2.md`: first run strict LOEO + chronological walk-forward on the current model, then strengthen current-season adjustment, match context and continuous live demand. Do not restart the C1 tournament, do not retune frozen v8, and do not treat E0 pricing as still unimplemented.**
