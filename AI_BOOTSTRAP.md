# Beyond — AI Bootstrap / Read This First

Last product-direction update: **2026-10-16**

This file exists so a new AI/chat session continues the actual Beyond plan instead of rediscovering or redefining it.

## Cold-start rule

Before doing Beyond forecasting, ML, dashboard, Growth or recommendation work, read in this order:

1. `ml/CURRENT_MODEL.md` — canonical current model/product state;
2. `ml/LIVE_DEMAND_ENGINE_V1_PLAN.md` — implementation roadmap;
3. `ml/C1_MODEL_TOURNAMENT_V1.md` — C1-alpha validation rules;
4. latest `ml/results/C1_ALPHA_*.md` evidence — current experiment state;
5. `ml/SECTOR_DECISION_PRICING_V1.md` — sector/no-action/pricing contract;
6. `ml/NORTH_STAR.md`;
7. `ml/LIVE_FORECAST_ORCHESTRATOR_V1.md`;
8. `ml/STRUCTURAL_PRIOR_MATERIALIZER_V1.md`;
9. `ml/MODEL_PROMOTION_GOVERNANCE_V1.md`;
10. `growth/GROWTH_EXECUTION_DATA_V2.md`.

## Critical product direction — DO NOT LOSE THIS

Beyond is **not** primarily a generic campaign recommendation tool.

Primary output:

`event -> sector -> trajectory -> expert reliability -> no-action projection -> pricing scenario -> recommendation`

For an active event the product should tell the club where the event is going, whether the live evidence is strong enough to revise the Structural Prior, which sector is behind/ahead, what happens if the trajectory continues, what price action is worth testing, and what happened after the club acted.

Public seat-map inventory is a **demand proxy, not confirmed paid sales**.

## Structural Prior state

All five current-event horizons are executable and frozen:

- T-30 `structural-prior-runtime-v1-t30-extra-full`;
- T-14 `structural-prior-runtime-v1-t14-hist-base`;
- T-7 `structural-prior-runtime-v1-t7-gbr-base`;
- T-3 `structural-prior-runtime-v1-t3-hist-full`;
- T-1 `structural-prior-runtime-v1-t1-hist-full`.

Frozen bundle:

`structural-prior-runtime-v1-frozen-2026-10-15-t1`

Scheduled Structural Prior inference is load + predict only.

## C1-alpha evidence base

The 20-independent-match rule is a **later promotion gate**, not a training-start gate.

Current-domain completed evidence:

- 9 Ekstraklasa events;
- 206 PIT-valid full-trajectory rows;
- 30 regularized PIT-valid final-24h rows;
- 8/9 events with PIT-safe T-24 `hybrid_v6`.

Never treat multiple snapshots from one event as independent matches.

## C1-alpha result ladder — canonical state

### v1 — mixed all-phase tournament

`ml/results/C1_ALPHA_MODEL_TOURNAMENT_V1_2026-10-16.md`

Result: no improvement. Mixed T-14/T-7/T-3/T-1 phase coverage is the wrong first formulation.

### v2 — final-24h live expert

`ml/results/C1_ALPHA_T1_TOURNAMENT_V2_2026-10-16.md`

Winner:

`ridge_directocc_compact_generic_a10`

- Structural Prior: **3,968.7 MAE**;
- live expert: **2,929.3 MAE**;
- improvement: **26.19%**;
- complementary but unstable.

### v3–v5 — gating / stacking attempts

- v3: **3,054.3 MAE**;
- v4: **3,106.8 MAE**;
- v5: **3,073.8 MAE**.

Conclusion: more stacking did not solve expert selection.

### v6 — T-24-only challenger

`ml/results/C1_ALPHA_T24_RESIDUAL_V6_2026-10-16.md`

- LOEO **3,873.2 MAE**;
- LOCO **3,989.8 MAE**.

Reject T-24-only as the primary direction.

### v7 — expert reliability diagnostic

`ml/results/C1_ALPHA_V2_EXPERT_RELIABILITY_V7_2026-10-16.md`

Exact v2 reproduction:

- Prior **3,968.7**;
- Live **2,929.3**;
- oracle **1,867.9**.

Useful PIT pattern:

- large prior/live disagreement is associated with LIVE wins;
- positive live-expert trajectory direction helps distinguish real disagreement from a decaying live estimate;
- generic `signal_ready`, feature quality and raw-vs-matched labels are not safe standalone gates.

### v8 — fixed PIT-safe reliability policy — **current prospective shadow candidate**

`ml/results/C1_ALPHA_RELIABILITY_POLICY_V8_2026-10-16.md`

Policy ID:

`c1-alpha-reliability-policy-v8-fixed-10pp-positive-slope-20pp-single`

Rule:

- 1 observation: LIVE only if disagreement >= **20 pp capacity**;
- >=2 observations: LIVE only if disagreement >= **10 pp** and live slope to date > 0;
- otherwise PRIOR.

No threshold grid or selector model was fitted in v8.

Development replay:

- Prior: **3,968.7 MAE**;
- v2 Live: **2,929.3 MAE**;
- **v8 window MAE: 2,713.3**;
- **v8 latest-row MAE: 1,998.1**;
- worst event degradation vs Prior: **203.3**;
- oracle: **1,867.9**.

This is the strongest current decision policy result, but it is **NOT fresh validation** because the v8 thresholds were designed after inspecting v7 labels on these same 9 events.

Do not retune v8 on the original 9 events.

## Production state

Production remains:

`live_adjustment = 0`

Do **not** write v8 decisions into production forecast values yet.

v8 status:

`EXPERIMENTAL_SHADOW`

## Immediate C1-alpha next action — prospective shadow package

Freeze one reproducible v2+v8 package for future events:

1. fit the exact v2 live expert on all currently completed in-domain training events;
2. freeze artifact + training event IDs + training/export hashes + feature contract + package version;
3. freeze the v8 thresholds exactly at **10 pp / positive slope / 20 pp single-observation**;
4. scheduled shadow inference must load the artifact and predict only — never fit;
5. persist pre-outcome shadow decisions with:
   - event ID;
   - timestamp;
   - Structural Prior;
   - v2 live estimate;
   - disagreement;
   - observation count;
   - live slope to date;
   - selected expert;
   - reason code;
   - model/package version;
6. score those frozen decisions only after outcomes arrive;
7. use future 2026/27 completed events as genuinely prospective validation.

## Dynamic pricing / E0 — continue in parallel

Pricing is a first-class intervention.

MVP sector output:

- `HOLD / INCREASE / DECREASE`;
- proposed price/scenario;
- projected sell-through/availability impact;
- projected revenue proxy;
- confidence;
- reason codes;
- assumption/model version.

Before learned elasticity exists, label the output as assumption-based scenario analysis.

Never change a club's production price automatically:

`auto_price_change_allowed = false`

## Historical governance

Canonical history:

- Ekstraklasa 2021/22–2025/26;
- 1,530 matches;
- 7,650 horizon rows;
- verified capacity coverage 100%.

2024/25 and 2025/26 are not pristine untouched T-30 holdouts for new R&D.

## Critical rules

- do not retrain/replay just to recover context;
- do not present oracle metrics as deployable;
- do not call public inventory paid sales;
- do not retune v8 thresholds on the original 9 events;
- do not report v8's 1,998 latest-row MAE as independently validated;
- scheduled inference loads frozen artifacts, never fits;
- keep `live_adjustment=0` until prospective evidence and promotion review justify otherwise.

## Immediate work order

1. freeze/version the **v2+v8 prospective shadow package**;
2. implement load+predict shadow inference and pre-outcome evidence persistence;
3. keep Structural Prior/orchestrator production output unchanged;
4. score each genuinely new completed event against frozen v8;
5. continue sector trajectory gap/status and no-action projection;
6. continue price-data and E0 pricing scenarios;
7. continue T-30 R&D in parallel.

## One-line cold-start instruction

> **The current C1-alpha candidate is v8: a frozen PIT-safe expert switch around the v2 live expert. Development replay is 2,713 MAE and 1,998 latest-row MAE, but it is not fresh validation. Do not tune it again — freeze a shadow-only v2+v8 package, persist decisions before outcomes, and validate prospectively while production stays `live_adjustment=0`.**
