# Beyond — AI Bootstrap / Read This First

Last updated: **2026-10-25**

## Cold-start order

Read in this order:

1. `ml/NEXT_SESSION_HANDOFF.md`;
2. `ml/EXECUTION_PLAN_CURRENT.md`;
3. `ml/PROGRESS_TRACKING.md`;
4. `ml/MAE_RESEARCH_ROADMAP_V4.md`;
5. `ml/P9_BOOKING_CURVE_LEARNER_PRECOMMIT_V1.md`;
6. `ml/ROBOTICKET_INGESTION_SAFETY_NET_2026-10-25.md`;
7. `ml/TICKETING_SOURCE_COVERAGE_EXPANSION_2026-10-25.md`;
8. `ml/TICKETING_SCHEDULE_WATCHDOG_2026-10-25.md`;
9. `ml/P7_LONG168_RESULT_2026-10-25.md`;
10. `ml/P7_LONG168_PROSPECTIVE_PRECOMMIT_V1.md`;
11. `ml/P7_LONG168_PROSPECTIVE_FINGERPRINT_V1.md`;
12. `ml/P9A_FREEZE_AUDIT_2026-10-25.md`;
13. `ml/P11A_FIRST_GENUINE_CAPTURE_2026-10-25.md`;
14. `ml/P11_CONTEXT_AUDIT_2026-10-25.md`.

Do not restart from Roadmap v3. Do not reconstruct frozen experiments from memory.

## North star

> **Minimize true out-of-sample attendance-forecast MAE at decision-relevant horizons using honest PIT-safe, reproducible evidence.**

Current mode: **representation-first + prospective evidence accumulation, not tuning-first**.

Production remains:

`live_adjustment = 0`

## Immediate order

`preserve ticketing safety + P7/P11 schedules -> P9 8/9: obtain only genuine 9th label -> execute already-frozen target-free P9 chain -> continue Long72/P4 genuine scoring -> business ΔMAE threshold -> P12 later`

## Current canonical state

### Multi-source ticketing ingestion

Protection layers:

`fixture watchdog -> source discovery/private raw buffer -> verified mapping/promotion -> canonical model-facing snapshots`

League source coverage:

- current Ekstraklasa home clubs: **18**;
- covered by at least one active source: **18**;
- uncovered: **0**.

RoboTicket:

- hardened same-element product identity;
- fail-closed parking/VIP/premium/reserve/non-football exclusions;
- private unmapped-match buffer every 10 minutes;
- discovery hourly;
- football-universe gate;
- exact verified kickoff -> promotion + PIT-preserving backfill.

Stellis:

- canonical collector `stellis_collect_v3`;
- Widzew, Radomiak, Piast, Motor, Korona;
- cadence `3,13,23,33,43,53 * * * *`;
- hidden inventory never becomes fake zero.

Panel:

- shared status `public.dashboard_ticketing_ingestion_status_v1`;
- TRACKED / BUFFERING / SCHEDULE_GAP / recent completed states visible;
- Events screen exposes `Nadchodzące / Zakończone / Wszystkie`;
- schedule-gap UI CI is green on main.

### Genuine outcomes added/recovered on 2026-10-25

- event 21 Jagiellonia–Wisła Płock: **17,021**;
- event 23 Śląsk–Wieczysta: **12,391**;
- event 20 Wisła Płock–Radomiak: **5,014**.

No inventory-derived attendance estimate was used.

Event 22 Legia–Lech is completed but has no trusted attendance label yet. Do not estimate it.

### P9 — 8/9 and learner design already frozen

Fresh readiness:

- 168h: **8 events / 8 clubs**;
- 72h: **12 / 10**;
- 48h: **15 / 10**;
- 24h: **18 / 11**.

Full-window event IDs:

`[5,10,15,18,19,20,21,23]`

Event 22 is technically full-window ready once genuine attendance exists. Its 6–168h curve has ~648 observations and max gap ~0.25h.

Do not lower the frozen 12h quality gate. Events 3 and 4 remain excluded because their gaps exceed it.

P9 learner precommit:

`ml/P9_BOOKING_CURVE_LEARNER_PRECOMMIT_V1.md`

Precommit ID:

`p9-knn-median-residual-k5-v1`

Frozen mechanism:

`PIT booking-curve similarity -> fixed k=5 prior curves -> same-incumbent-family historical residuals -> median residual -> incumbent correction`

No coefficient fit, no regression, no candidate sweep.

Machine status:

`public.p9_learner_gate_status_v1()`

Current:

- `design_precommitted=true`;
- `readiness_168_events=8`;
- `readiness_168_clubs=8`;
- `full_window_gate_open=false`;
- `registered_target_free_manifests=0`;
- `labels_export_allowed=false`;
- model results opened false;
- production activation false.

Hard 9/9 execution order:

1. target-free P9a T-48/T-24 input export;
2. P9a representation/reference freeze;
3. immutable P9a manifest registration;
4. target-free incumbent catalog export;
5. `ml/p9_learner_support_freeze_v1.py` exact target/reference incumbent identity freeze;
6. immutable support manifest registration;
7. `public.export_p9_learner_labels_v2(...)`;
8. fixed `ml/p9_booking_curve_learner_v1.py` evaluation;
9. no post-result tuning.

At 8/9 all live gates were negative-tested and correctly rejected. Both target/support freeze registries remain empty.

P9 evaluator CI:

`P9 Booking Curve Learner Precommit v1` run `40225788533` — **SUCCESS**.

### P7 Long168 historical result

- 10 frozen events / 139 rows;
- 5 strict forward held-out events/folds;
- anchor MAE 7409.79;
- selected candidate `gbr-l1-depth2-n50-lr003`;
- challenger MAE 6339.99;
- point gain 1069.80 / 14.44%;
- 95% event-block CI `[-2566.13,+174.47]`;
- evidence `POINT_GAIN_UNCERTAINTY_LIMITED`.

Never retune/rerun the exposed tournament.

### P7 prospective validation

- pinned fingerprint `70fa929181531276c80a75c0b78a60fb821cf50e714e2bc001de8251cea1793f`;
- current ledger: **6 immutable rows / 3 events / 0 scores**;
- schedule `37 */6 * * *`;
- production activation false.

Next P7 work is collection/scoring only.

### Long72

Genuine scored events:

`[10,16,21,23]`

Current n=4 evidence:

- anchor event-balanced MAE **6942.59**;
- package MAE **6824.16**;
- point gain **118.43 / 1.71%**;
- event improvement rate **75%**;
- worst event degradation **3633.23**.

24–48h is slightly worse; 48–72h remains better. Do not retune from n=4.

### P4a

- READY 5;
- labeled READY **4/9**;
- distinct labeled previous-home-spacing values **3**;
- variance gate PASS;
- event-count gate FAIL.

### P11a odds

Latest audited genuine state:

- raw rows **81**;
- events / clubs **4 / 4**;
- capture batches **5**;
- 24h / 72h / 168h coverage **3 / 3 / 0**;
- latest audited capture `2026-10-25T18:56:51.448Z`;
- model precommitted false;
- production false.

Schedules:

- primary `17 */6 * * *`;
- fallback `47 0,6,12,18 * * *`;
- health threshold 270 minutes.

Never backfill closing odds.

### P11b/c/d

- P11b price as-known live; no inferred promotion;
- P11c data-bound;
- P11d weather closed/no-uplift;
- P11d media attention prospective collecting.

### Governance / P12

Business minimum meaningful ΔMAE remains intentionally unset until independently business-derived.

P12 remains lower priority.

## Closed research loops

Do not reopen without materially new information/mechanism:

- original P7 tournament;
- P10/P10b;
- P5a;
- P6 historical Long72 incremental signal;
- P8 calibration;
- existing weather mechanism;
- old estimator sweeps;
- post-hoc tuning.

The old ChatGPT Beyond readiness automations remain intentionally disabled.
