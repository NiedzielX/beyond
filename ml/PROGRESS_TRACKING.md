# Beyond Ticketing — ML Progress Tracking

Last updated: **2026-10-25**

Status: **CANONICAL PLAN / STATUS / TRACKING SNAPSHOT**

Canonical strategy: `ml/MAE_RESEARCH_ROADMAP_V4.md`

Operational handoff: `ml/NEXT_SESSION_HANDOFF.md`

Current execution order: `ml/EXECUTION_PLAN_CURRENT.md`

## North star

> **Minimize true out-of-sample attendance-forecast MAE at decision-relevant horizons with PIT-safe, reproducible evidence.**

Production: `live_adjustment = 0`.

## Current status

| Item | Status | Current decision |
|---|---|---|
| Branch reconciliation | ✅ DONE | do not repeat |
| Long72 prospective evidence | 🟢 **2 genuine scored events** | preserve, collect more, no retuning |
| P4a previous-home spacing | 🟡 **2/9 labels / 2 distinct** | gate closed |
| P7 Long168 | ✅ **EXECUTED** | 14.44% point gain; uncertainty-limited; next step only via new prospective precommit |
| P9 full-168h Booking Curve | 🟡 **5/9** | continue collection; learner blocked |
| P9a T-24/T-48 freeze | ✅ COMPLETE | target-free audit frozen; learner still closed |
| P10/P10b | ✅ CLOSED | do not reopen fixed pooled-HGB path |
| P11a PIT odds | 🟢 **34 genuine raw rows / 2 events** | scheduled accumulation every 6h; no model yet |
| P11b price context | 🟢 **AS-KNOWN CONTRACT LIVE** | representation ready; promotion evidence absent; no model yet |
| P11c verified absences | 🟡 **DATA_BOUND** | 1 active verified row / 1 team |
| P11d weather | ✅ EXISTING LOOP CLOSED | `research_only_no_uplift`; do not repeat same mechanism |
| P11d media attention | 🟡 PROSPECTIVE COLLECTING | >1k samples; insufficient useful variance for evaluation |
| Governance v2 | ✅ FRAMEWORK / threshold pending | robust state unavailable until business ΔMAE threshold exists |
| P12 regime audit | 🟡 PRE-PLAN | lower priority than P9/P11 evidence |
| Production | ⛔ UNCHANGED | `live_adjustment = 0` |

## Long72

Genuine outcomes currently scored:

- event 10 Pogoń Szczecin vs Radomiak Radom: **19,050**;
- event 16 Wisła Kraków vs Raków Częstochowa: **33,000**.

Frozen point evidence on n=2:

- anchor MAE: `9069.5168`;
- frozen package MAE: `7641.7132`;
- point improvement: `1427.8036 / 15.7429%`;
- event improvement rate: 1.0;
- production change: false.

Interpretation: first prospective observations only. Do not retune or promote.

## P7 Long168

Frozen executor run: `40197742930`.

- independent frozen events: 10;
- frozen rows: 139;
- forward held-out events/folds: 5/5;
- anchor MAE: `7409.7882`;
- best candidate: `gbr-l1-depth2-n50-lr003`;
- challenger MAE: `6339.9915`;
- delta MAE: `-1069.7967`;
- relative point improvement: `14.4376%`;
- event/fold improvement rate: `0.8 / 0.8`;
- 95% event-block bootstrap interval: `[-2566.13, +174.47]`;
- `P(delta_MAE < 0)=0.9322`;
- decision: `ADVANCE_RESEARCH`;
- evidence: `POINT_GAIN_UNCERTAINTY_LIMITED`.

Do not rerun/tune the inspected tournament. Any next P7 evidence lane must be separately precommitted and prospective.

Canonical result: `ml/P7_LONG168_RESULT_2026-10-25.md`.

## P9 / P9a

Full-window coverage:

- 168h: **5 events / 5 clubs**;
- 72h: **9 / 7**;
- 48h: **12 / 7**;
- 24h: **15 / 9**;
- full 168h status: `DATA_BOUND`;
- learner precommitted: false.

P9a target-free freeze is complete:

- T-24 manifest: `738a42da33b46361f0ba29d3f90c72e2e0019c0057ef00b78ac7e6a073f0bd1c`;
- T-48 manifest: `ffa6dd178332bf328a24fc7ce15ef346214a0037325d7161426f9f96664babd4`;
- target values unopened;
- no model training;
- no future target trajectory use.

Do not train/select full P9 before 9/9 plus a separate precommit.

## P4a

- READY events: 5;
- genuine labeled READY events: 2;
- distinct labeled previous-home-spacing values: 2;
- required: >=9 labeled AND >=3 distinct labeled values;
- trigger: false.

## P11a — genuine odds capture active

First genuine capture:

- run `40199626764`;
- captured at `2026-10-25T13:46:04.688Z`;
- local candidates: 3;
- provider events: 2;
- matched events: 2;
- raw append-only quotes inserted: **34**;
- event 22: 18 quotes, kickoff delta 0;
- event 6: 16 quotes, kickoff delta 0;
- event 23: `NO_PROVIDER_MATCH`, no insert;
- target values used: false;
- production change: false.

Readiness:

- `GENUINE_PIT_DATA_ACCUMULATING`;
- genuine PIT events: 2;
- events with >=3 bookmakers: 2;
- 24h / 72h / 168h coverage: 2 / 1 / 0;
- model precommitted: false.

Scheduled capture:

`17 */6 * * *`

Live Edge runtime: version 6; scheduled capture config is synchronized with `main`.

Canonical evidence: `ml/P11A_FIRST_GENUINE_CAPTURE_2026-10-25.md`.

## P11b — PIT-safe price context

Existing data at audit time:

- `ticket_price_observations_v1`: 118,156 rows / 7 events;
- `sector_price_area_observations_v1`: 241,525 rows / 13 events.

Live target-free function:

`public.p11_price_context_as_known_v1(ticket_event_id, as_of_at)`

Verified behavior:

- event 6: `PRICE_CONTEXT_READY`;
- event 22: `PRICE_AREA_ONLY`;
- historical cutoff replay returns only price/inventory observations known by that cutoff;
- no outcome table is referenced;
- promotion remains null because there is no explicit promotion source;
- price movement is not reinterpreted as promotion.

No P11b attendance model has been opened.

## P11c — verified absences

Existing source/refresh is healthy, but current evidence is only:

- active PIT-valid rows: 1;
- teams: 1.

Status: `DATA_BOUND`.

Missing rows are not interpreted as confirmed player availability.

## P11d — weather / attention

Weather:

- collector healthy;
- existing status: `research_only_no_uplift`;
- historical study: `weather-signal-v1-t7-ecmwf`;
- do not reopen the same mechanism.

Media attention:

- >1,000 prospective samples;
- 12 events;
- historical backfill forbidden;
- `hype.media_attention`: `prospective_collecting`;
- `hype.mention_acceleration`: `prospective_collecting_warmup`;
- current headline feature lacks adequate useful variance for evaluation.

Canonical audit: `ml/P11_CONTEXT_AUDIT_2026-10-25.md`.

## Governance / P12

Business threshold framework:

`ml/GOVERNANCE_V2_BUSINESS_DMAE_THRESHOLD.md`

Numeric minimum meaningful `ΔMAE` remains intentionally unset until business-derived.

P12 pre-plan:

`ml/P12_DEMAND_REGIME_AUDIT_PLAN.md`

P12 remains deferred behind current P9/P11 evidence priorities.

## Closed loops

Do not reopen without a materially new mechanism:

- P10/P10b;
- P5a shrinkage;
- P6 historical Long72 incremental signal;
- P8 simple calibration;
- existing weather mechanism;
- old estimator-only sweeps;
- post-hoc tuning on already inspected evidence.
