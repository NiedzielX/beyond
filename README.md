# Beyond

Beyond Ticketing engineering workspace.

## Start here

For every new AI / engineering session, read in this order:

1. [`AI_BOOTSTRAP.md`](AI_BOOTSTRAP.md)
2. [`ml/NEXT_SESSION_HANDOFF.md`](ml/NEXT_SESSION_HANDOFF.md)
3. [`ml/EXECUTION_PLAN_CURRENT.md`](ml/EXECUTION_PLAN_CURRENT.md)
4. [`ml/PROGRESS_TRACKING.md`](ml/PROGRESS_TRACKING.md)
5. [`ml/MAE_RESEARCH_ROADMAP_V4.md`](ml/MAE_RESEARCH_ROADMAP_V4.md)
6. [`ml/CURRENT_MODEL.md`](ml/CURRENT_MODEL.md)
7. [`ml/MODEL_ACCURACY_DEVELOPMENT_INSTRUCTIONS_V2.md`](ml/MODEL_ACCURACY_DEVELOPMENT_INSTRUCTIONS_V2.md)

Do **not** restart from Roadmap v3. Roadmap v4 is canonical.

## North star

> **Minimize true out-of-sample attendance-forecast MAE at decision-relevant horizons with PIT-safe, reproducible evidence.**

Current mode: **representation-first, not tuning-first**.

Production remains unchanged:

`live_adjustment = 0`

## Current state — 2026-10-25

### Completed

- repository reconciliation is complete;
- Long72 has **2 genuine prospective scored events**;
- P7 Long168 frozen tournament executed at genuine 10/9 readiness;
- P9a T-24/T-48 target-free freeze audit completed;
- first genuine P11a bookmaker capture completed and audited;
- P11a scheduled append-only capture is enabled every 6 hours;
- P11b PIT-safe price `as-known` contract is live;
- P11c/P11d target-free source audit is complete;
- Governance v2 business-threshold framework and P12 audit pre-plan exist.

### Immediate execution order

`preserve scheduled P11a accumulation -> preserve P11b/P11d collection -> precommit P7 prospective follow-up without retuning -> continue Long72 prospective evidence -> accumulate P9 to 9/9 -> accumulate P4a labels -> derive business ΔMAE threshold`

No research result activates production automatically.

## Long72 prospective evidence

Genuine post-match outcomes currently scored:

- event 10 — Pogoń Szczecin vs Radomiak Radom: **19,050**;
- event 16 — Wisła Kraków vs Raków Częstochowa: **33,000**.

Frozen package point evidence on n=2:

- anchor MAE: **9,069.52**;
- frozen package MAE: **7,641.71**;
- point improvement: **1,427.80 seats / 15.74%**.

Preserve and collect more. Do not retune/calibrate/promote from n=2.

## P7 Long168 — EXECUTED

Frozen result:

- 10 frozen events / 139 rows;
- 5 strict forward held-out events / folds;
- anchor MAE: **7,409.79**;
- best candidate: `gbr-l1-depth2-n50-lr003`;
- challenger MAE: **6,339.99**;
- point improvement: **1,069.80 / 14.44%**;
- event/fold improvement rate: **80% / 80%**;
- paired event-block 95% CI for challenger-minus-anchor MAE: **[-2,566.13, +174.47]**;
- interpretation: `POINT_GAIN_UNCERTAINTY_LIMITED`;
- research decision: `ADVANCE_RESEARCH`;
- production activation: not allowed.

Canonical result: [`ml/P7_LONG168_RESULT_2026-10-25.md`](ml/P7_LONG168_RESULT_2026-10-25.md).

Do not rerun or tune the inspected P7 tournament. Any continuation must be a separately precommitted prospective lane.

## P9 / P9a Booking Curve

P9a target-free audit is complete:

- T-24 manifest: `738a42da33b46361f0ba29d3f90c72e2e0019c0057ef00b78ac7e6a073f0bd1c`;
- T-48 manifest: `ffa6dd178332bf328a24fc7ce15ef346214a0037325d7161426f9f96664babd4`;
- targets unopened;
- no model training;
- no future target trajectory use.

Full P9 remains data-bound:

- 168h: **5/9 events / 5 clubs**;
- 72h: 9 / 7;
- 48h: 12 / 7;
- 24h: 15 / 9.

Do not select/train the first full-168h learner before 9/9 plus a separate precommit.

## P4a fixture context

- READY events: 5;
- genuine labeled READY events: **2**;
- distinct labeled `previous_home_match_days`: **2**;
- required: `>=9 labeled AND >=3 distinct labeled values`.

Gate remains closed.

## P11 context program

Canonical context audit: [`ml/P11_CONTEXT_AUDIT_2026-10-25.md`](ml/P11_CONTEXT_AUDIT_2026-10-25.md).

### P11a — bookmaker odds

First genuine capture is complete and audited:

- raw append-only rows: **34**;
- matched events: **2**;
- both matched with kickoff delta 0;
- event 23 correctly failed closed as `NO_PROVIDER_MATCH`;
- target values used: false;
- production change: false.

Readiness:

- status: `GENUINE_PIT_DATA_ACCUMULATING`;
- genuine PIT events: 2;
- events with >=3 bookmakers: 2;
- events reaching 24h / 72h / 168h: **2 / 1 / 0**;
- model precommitted: false.

Canonical evidence: [`ml/P11A_FIRST_GENUINE_CAPTURE_2026-10-25.md`](ml/P11A_FIRST_GENUINE_CAPTURE_2026-10-25.md).

Scheduled GitHub capture is enabled at:

`17 */6 * * *`

Pushes run contract/tests only; provider capture runs only on schedule or explicit manual dispatch.

Live Edge runtime is version 6 and its config contract reports scheduled capture enabled.

### P11b — price / promotion

Existing price collectors are healthy. New target-free function is live:

`public.p11_price_context_as_known_v1(ticket_event_id, as_of_at)`

It exposes PIT-safe price levels, prior-capture price delta and visible price-area inventory mix.

Promotion remains intentionally unknown because no explicit promotion source exists:

`DO_NOT_INFER_PROMOTION_FROM_PRICE_CHANGE`

No P11b attendance model is fitted yet.

### P11c — verified absences

Collector/refresh exists and is healthy, but current genuine coverage is only **1 active verified absence / 1 team**.

Status: **DATA_BOUND**. Do not fit a lineup/absence model.

### P11d — weather / attention

Weather collection is healthy, but the existing weather mechanism is already classified:

`research_only_no_uplift`

Do not reopen the same weather hypothesis under a new name.

Media attention remains prospective-only:

- >1,000 samples;
- 12 events;
- historical backfill forbidden;
- headline attention feature still lacks adequate useful variance.

Continue collection; do not force an ablation yet.

## Governance / P12

Governance framework:

`ml/GOVERNANCE_V2_BUSINESS_DMAE_THRESHOLD.md`

The numerical minimum meaningful `ΔMAE` remains intentionally unset until derived from real operational decisions.

P12 target-free pre-plan:

`ml/P12_DEMAND_REGIME_AUDIT_PLAN.md`

P12 remains lower priority than P9/P11 evidence accumulation.

## Closed loops

Do not reopen without a materially new mechanism:

- P10/P10b fixed pooled-HGB path;
- P5a shrinkage;
- P6 historical Long72 signal;
- P8 simple calibration;
- existing weather mechanism;
- old estimator-only sweeps;
- post-hoc tuning on inspected evidence.

## Never do these

- do not backfill closing odds into earlier PIT horizons;
- do not fuzzy-match ambiguous provider fixtures;
- do not infer promotion from price movement;
- do not interpret missing absence records as confirmed availability;
- do not use future target trajectory points in P9/P9a;
- do not lower P9/P4 gates;
- do not retune frozen Long72 from early prospective scores;
- do not retune frozen P7 after seeing its scorecard;
- do not change `live_adjustment` from zero without reviewed promotion.

## Engineering rule

`hypothesis -> PIT contract -> code -> tests -> forward/event-safe evaluation -> artifact -> hashes -> result doc -> decision -> canonical docs`

> **Frozen validation protects truth. It does not pause model development.**
