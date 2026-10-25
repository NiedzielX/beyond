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
7. [`ml/ROBOTICKET_INGESTION_SAFETY_NET_2026-10-25.md`](ml/ROBOTICKET_INGESTION_SAFETY_NET_2026-10-25.md)
8. [`ml/MODEL_ACCURACY_DEVELOPMENT_INSTRUCTIONS_V2.md`](ml/MODEL_ACCURACY_DEVELOPMENT_INSTRUCTIONS_V2.md)

Do **not** restart from Roadmap v3. Roadmap v4 is canonical.

## North star

> **Minimize true out-of-sample attendance-forecast MAE at decision-relevant horizons with PIT-safe, reproducible evidence.**

Current mode: **representation-first, not tuning-first**.

Production remains unchanged:

`live_adjustment = 0`

## Current state — 2026-10-25

### Completed / live

- repository reconciliation is complete;
- RoboTicket ingestion safety net is live: hardened discovery, private pre-mapping buffer, verified promotion/backfill and dashboard coverage;
- dashboard CI passes with ingestion coverage visible on Overview and Data Quality;
- Long72 has **2 genuine prospective scored events**;
- P7 Long168 frozen tournament executed at genuine 10/9 readiness;
- P7 prospective follow-up is precommitted, fingerprint-pinned and now has **3 immutable genuine predictions across 3 independent future events**;
- P9a T-24/T-48 target-free freeze audit completed;
- first genuine P11a bookmaker capture completed and audited;
- P11a scheduled append-only capture is enabled every 6 hours;
- P11b PIT-safe price `as-known` contract is live;
- P11c/P11d target-free source audit is complete;
- Governance v2 business-threshold framework and P12 audit pre-plan exist.

### Immediate execution order

`preserve P7 prospective schedule -> expand/protect ticketing source coverage -> preserve P11a/P11b/P11d collection -> score P7/Long72 only after genuine outcomes -> accumulate P9 to 9/9 -> accumulate P4a labels -> derive business ΔMAE threshold`

No research result activates production automatically.

## RoboTicket ingestion safety net

Canonical incident/safety document:

[`ml/ROBOTICKET_INGESTION_SAFETY_NET_2026-10-25.md`](ml/ROBOTICKET_INGESTION_SAFETY_NET_2026-10-25.md)

The 2026-10-25 audit confirmed that the previous round was **not** fully lost: genuine pre-match booking curves were preserved for 5/9 fixtures hosted by onboarded ticketing sources. The four remaining fixtures were hosted by non-onboarded clubs; the onboarded clubs in those matches were away teams.

The real systemic problem was a missing robust path from newly discovered RoboTicket products to canonical `ticket_events`, plus loose eventId/label matching.

Now live:

- hardened same-element discovery: `roboticket-discovery-v7`;
- explicit fail-closed exclusions for parking/VIP/premium/reserve/non-football products;
- private raw candidate buffer before kickoff mapping;
- football-universe gate before buffering;
- verified schedule -> automatic ticket-event promotion + PIT-preserving backfill;
- hourly discovery;
- 10-minute candidate buffer cadence;
- dashboard ingestion coverage and historical completed-match visibility.

Fresh monitoring after recovery:

- **12 future matches tracked**;
- **11 already have genuine inventory snapshots**;
- **1 explicit `TRACKED_NO_SNAPSHOT`**: Wisła Kraków – Cracovia, already mapped but RoboTicket currently exposes zero readable sectors; normal collection continues to retry it;
- no genuine match is silently hanging as an unbuffered candidate;
- early false-positive buffer rows stayed private and were never promoted into model-facing `public.snapshots`.

This safety net changes data acquisition only. It does not change model parameters, validation or production forecasts.

## P7 Long168 — frozen result and prospective follow-up

Frozen historical/forward-fold result:

- 10 frozen events / 139 rows;
- 5 strict forward held-out events / folds;
- anchor MAE: **7,409.79**;
- selected candidate: `gbr-l1-depth2-n50-lr003`;
- challenger MAE: **6,339.99**;
- point improvement: **1,069.80 / 14.44%**;
- event/fold improvement rate: **80% / 80%**;
- paired event-block 95% CI: **[-2,566.13, +174.47]**;
- interpretation: `POINT_GAIN_UNCERTAINTY_LIMITED`;
- decision: `ADVANCE_RESEARCH`;
- production activation: not allowed.

Canonical result: [`ml/P7_LONG168_RESULT_2026-10-25.md`](ml/P7_LONG168_RESULT_2026-10-25.md).

The old tournament is exposed and must not be rerun or tuned.

Prospective continuation:

- precommit: `ml/P7_LONG168_PROSPECTIVE_PRECOMMIT_V1.md`;
- bootstrap rule: no prospective backfill of historical buckets;
- exact training set: events `[1,3,4,5,10,11,15,16,18,19]` / 139 rows;
- training manifest: `185a9fc90e646bd5fa1bbed3b50c625d65d127a2b2943501761bdfcb89f354ed`;
- pinned deterministic model fingerprint: `70fa929181531276c80a75c0b78a60fb821cf50e714e2bc001de8251cea1793f`;
- fingerprint run `40201818862`: SUCCESS; fingerprint mode persisted zero predictions;
- first true prospective run `40216860928`: SUCCESS;
- first immutable ledger: **3 predictions / 3 independent events / 0 scored outcomes**;
- persisted events: Lech Poznań–Wisła Kraków, GKS Katowice–Widzew Łódź, Wisła Płock–Piast Gliwice;
- target values used in prediction: false;
- production activation allowed: false;
- `live_adjustment=0`.

Pinned fingerprint evidence: [`ml/P7_LONG168_PROSPECTIVE_FINGERPRINT_V1.md`](ml/P7_LONG168_PROSPECTIVE_FINGERPRINT_V1.md).

First genuine prospective prediction evidence: [`ml/P7_LONG168_PROSPECTIVE_FIRST_PREDICTIONS_2026-10-25.md`](ml/P7_LONG168_PROSPECTIVE_FIRST_PREDICTIONS_2026-10-25.md).

The scheduled `predict -> immutable persist -> outcome-later score` workflow is now the active P7 lane. Do not interpret MAE until genuine outcomes exist.

## Long72 prospective evidence

Genuine post-match outcomes currently scored:

- event 10 — Pogoń Szczecin vs Radomiak Radom: **19,050**;
- event 16 — Wisła Kraków vs Raków Częstochowa: **33,000**.

Frozen package point evidence on n=2:

- anchor MAE: **9,069.52**;
- frozen package MAE: **7,641.71**;
- point improvement: **1,427.80 seats / 15.74%**.

Preserve and collect more. Do not retune/calibrate/promote from n=2.

## P9 / P9a Booking Curve

P9a target-free audit is complete:

- T-24 manifest: `738a42da33b46361f0ba29d3f90c72e2e0019c0057ef00b78ac7e6a073f0bd1c`;
- T-48 manifest: `ffa6dd178332bf328a24fc7ce15ef346214a0037325d7161426f9f96664babd4`;
- targets unopened;
- no model training;
- no future target trajectory use.

Fresh full P9 readiness:

- 168h: **5/9 events / 5 clubs**;
- 72h: **9 / 7**;
- 48h: **12 / 7**;
- 24h: **15 / 9**;
- full 168h status: `DATA_BOUND`;
- learner precommitted: false.

The newly recovered future events improve data collection going forward but cannot be dishonestly backfilled into T-168 history. Do not select/train the first full-168h learner before 9/9 plus a separate precommit.

## P4a fixture context

Fresh readiness:

- READY events: 5;
- genuine labeled READY events: **2**;
- distinct `previous_home_match_days` among READY events: **4**;
- distinct labeled values: **2**;
- required: `>=9 labeled AND >=3 distinct labeled values`;
- research trigger: false.

Gate remains closed.

## P11 context program

Canonical context audit: [`ml/P11_CONTEXT_AUDIT_2026-10-25.md`](ml/P11_CONTEXT_AUDIT_2026-10-25.md).

### P11a — bookmaker odds

Current fresh readiness:

- status: `GENUINE_PIT_DATA_ACCUMULATING`;
- events with any genuine PIT 1X2: **2**;
- clubs with any: **2**;
- events with >=3 bookmakers: **2**;
- current horizon coverage 24h / 72h / 168h: **1 / 1 / 0**;
- model precommitted: false;
- target values used: false;
- production change: false.

Scheduled GitHub capture is enabled at:

`17 */6 * * *`

Never backfill closing odds into earlier horizons.

### P11b — price / promotion

Live target-free function:

`public.p11_price_context_as_known_v1(ticket_event_id, as_of_at)`

Promotion remains intentionally unknown because no explicit promotion source exists:

`DO_NOT_INFER_PROMOTION_FROM_PRICE_CHANGE`

### P11c — verified absences

Current evidence remains data-bound. Missing records are not interpreted as confirmed availability.

### P11d — weather / attention

Existing weather mechanism: `research_only_no_uplift`. Do not reopen the same hypothesis.

Media attention remains prospective-only and collecting.

## Governance / P12

Governance framework:

`ml/GOVERNANCE_V2_BUSINESS_DMAE_THRESHOLD.md`

The numerical minimum meaningful `ΔMAE` remains intentionally unset until derived from real operational decisions.

P12 target-free pre-plan:

`ml/P12_DEMAND_REGIME_AUDIT_PLAN.md`

P12 remains lower priority than P7/P9/P11 evidence accumulation.

## Closed loops

Do not reopen without a materially new mechanism:

- original P7 tournament;
- P10/P10b fixed pooled-HGB path;
- P5a shrinkage;
- P6 historical Long72 signal;
- P8 simple calibration;
- existing weather mechanism;
- old estimator-only sweeps;
- post-hoc tuning on inspected evidence.

## Never do these

- do not backfill booking curves or closing odds and label them prospective;
- do not fuzzy-match ambiguous fixtures/products;
- do not promote parking/VIP/reserve/non-football products into model-facing snapshots;
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
