# Beyond Ticketing — Next Session Handoff

Last updated: **2026-10-25**

Status: **READ THIS FIRST AFTER `AI_BOOTSTRAP.md`**

## 1. North star

> **Minimize true out-of-sample attendance-forecast MAE at decision-relevant horizons using PIT-safe, reproducible evidence.**

Current phase: **representation-first + prospective evidence accumulation, not tuning-first**.

Production remains unchanged:

`live_adjustment = 0`

## 2. Immediate execution order

`preserve ingestion safety -> preserve P7/P11 scheduled evidence -> P9 8/9: obtain only genuine 9th label -> execute already-frozen P9 freeze/support/label/evaluator chain -> continue Long72/P4a genuine scoring -> define business ΔMAE threshold -> P12 later`

Do not restart the P7 tournament, P9a representation design, P10 or weather loops.

## 3. Ticketing ingestion — MULTI-SOURCE / LIVE

Read:

- `ml/ROBOTICKET_INGESTION_SAFETY_NET_2026-10-25.md`
- `ml/TICKETING_SOURCE_COVERAGE_EXPANSION_2026-10-25.md`
- `ml/TICKETING_SCHEDULE_WATCHDOG_2026-10-25.md`

The previous round was **not** fully lost. Genuine curves were preserved for 5/9 round-12 fixtures; the other four were hosted by non-onboarded sources at that time.

Current source coverage:

- current Ekstraklasa home clubs: **18**;
- covered by at least one active ticketing source: **18**;
- uncovered: **0**.

### RoboTicket safety net

- hardened same-element product identity;
- parking/VIP/premium/reserve/non-football fail closed;
- private pre-mapping inventory buffer;
- football-universe gate;
- exact verified kickoff -> automatic promotion/backfill;
- original `captured_at` retained during backfill;
- discovery hourly;
- candidate buffer every 10 minutes.

### Stellis

Canonical collector:

`stellis_collect_v3`

Active sources:

- Widzew Łódź;
- Radomiak Radom;
- Piast Gliwice;
- Motor Lublin;
- Korona Kielce.

Cadence:

`3,13,23,33,43,53 * * * *`

Hidden inventory remains unknown, never fake zero.

### Panel

Repo: `NiedzielX/BeyondTicketingPanel`.

Shared panel contract:

`public.dashboard_ticketing_ingestion_status_v1`

Panel now surfaces:

- TRACKED;
- protected BUFFERING states;
- SCHEDULE_GAP;
- recent completed matches;
- source family and actionable reason.

Events screen has `Nadchodzące / Zakończone / Wszystkie` and recent completed matches so completed games no longer appear to vanish.

Dashboard CI for the ingestion/schedule-gap update is green on main.

## 4. Genuine outcomes added/recovered on 2026-10-25

Genuine reported attendance now includes:

- event 21 — Jagiellonia Białystok vs Wisła Płock: **17,021**;
- event 23 — Śląsk Wrocław vs Wieczysta Kraków: **12,391**;
- event 20 — Wisła Płock vs Radomiak Radom: **5,014**.

Event 20 was a missing genuine label for an already-existing booking curve, not a reconstructed estimate.

Event 22 — Legia Warszawa vs Lech Poznań — has completed 1:2, but attendance is still not stored because no sufficiently reliable published attendance value has been confirmed. Do not estimate it.

## 5. P9 — HIGHEST IMMEDIATE RESEARCH PRIORITY / 8 OF 9

Fresh readiness:

- 168h: **8 events / 8 clubs**;
- 72h: **12 / 10**;
- 48h: **15 / 10**;
- 24h: **18 / 11**;
- full status: `DATA_BOUND`.

Full-window event IDs:

`[5,10,15,18,19,20,21,23]`

Event 22 is technically eligible once a genuine attendance label exists:

- ~648 snapshots in the 6–168h window;
- maximum gap ~0.25h;
- frozen P9 quality rule passes.

Events 3 and 4 remain correctly excluded because their maximum trajectory gaps exceed the frozen 12h ceiling (~13.26h and ~19.02h). Do not lower the gate.

### P9 learner precommit is already frozen

Canonical design:

`ml/P9_BOOKING_CURVE_LEARNER_PRECOMMIT_V1.md`

Precommit ID:

`p9-knn-median-residual-k5-v1`

Frozen learner:

`target incumbent + median residual of same-family incumbents among fixed 5 nearest PIT-safe booking curves`

Fixed rules:

- cutoffs: T-48 and T-24 only;
- canonical P9 curve representation;
- max interpolation gap 12h;
- min overlap 3 canonical points;
- weighted-L1 distance;
- fixed `k=5`;
- minimum 3 residual-bearing neighbors;
- no fitted coefficient;
- no regression;
- no candidate sweep;
- final capacity clipping only;
- primary metric = event-balanced MAE across T-48/T-24.

Machine-readable status:

`public.p9_learner_gate_status_v1()`

Current state:

- `design_precommitted=true`;
- `readiness_168_events=8`;
- `readiness_168_clubs=8`;
- `full_window_gate_open=false`;
- `registered_target_free_manifests=0`;
- `labels_export_allowed=false`;
- `model_results_opened=false`;
- `production_activation_allowed=false`.

### Hard execution order at 9/9

1. export target-free T-48/T-24 P9a inputs;
2. run `ml/p9a_booking_curve_freeze_v1.py`;
3. register immutable P9a target-free manifest;
4. export `public.export_p9_learner_incumbent_catalog_v1(...)` — target-free;
5. run `ml/p9_learner_support_freeze_v1.py` to freeze exact target/reference incumbent row IDs;
6. register immutable support-freeze manifest;
7. only then call `public.export_p9_learner_labels_v2(...)`;
8. run `ml/p9_booking_curve_learner_v1.py`;
9. report all frozen metrics; do not tune after result.

At 8/9 the following negative tests passed:

- target-free P9a freeze registration rejected;
- target-free incumbent catalog export rejected;
- label export v1 disabled;
- label export v2 rejected;
- base/support freeze registries remain empty.

P9 evaluator code and deterministic synthetic tests are already committed. CI workflow:

`.github/workflows/p9-booking-curve-learner-precommit-v1.yml`

## 6. P7 Long168 — exposed historical result

Historical frozen run `40197742930`:

- 10 events / 139 rows;
- 5 forward held-out folds;
- anchor MAE 7409.79;
- selected `gbr-l1-depth2-n50-lr003`;
- challenger MAE 6339.99;
- gain 1069.80 / 14.44%;
- 95% event-block CI `[-2566.13,+174.47]`;
- evidence `POINT_GAIN_UNCERTAINTY_LIMITED`.

Never rerun/tune this tournament.

### P7 prospective lane

- frozen training set `[1,3,4,5,10,11,15,16,18,19]` / 139 rows;
- pinned fingerprint `70fa929181531276c80a75c0b78a60fb821cf50e714e2bc001de8251cea1793f`;
- current ledger: **6 immutable prediction rows / 3 independent events / 0 scores**;
- schedule: `37 */6 * * *`;
- production activation false.

Next P7 work is scoring/collection only.

## 7. Long72 — genuine n=4

Scored events:

`[10,16,21,23]`

Current frozen evidence:

- anchor event-balanced MAE: **6942.59**;
- package event-balanced MAE: **6824.16**;
- point improvement: **118.43 / 1.71%**;
- event improvement rate: **75%**;
- worst event degradation: **3633.23**.

By band:

- 24–48h: challenger ~5 MAE worse;
- 48–72h: challenger ~241.85 MAE better.

This is much weaker than the earlier n=2 point result. Do not retune/calibrate/promote.

## 8. P4a

Current gate:

- READY events: 5;
- labeled READY events: **4/9**;
- distinct labeled previous-home-spacing values: **3**;
- variance requirement: PASS;
- event-count requirement: FAIL;
- trigger false.

Only genuine future labels should move this gate.

## 9. P11 — ACTIVE / RESILIENT CAPTURE

P11a latest audited genuine state:

- raw rows: **81**;
- genuine PIT events / clubs: **4 / 4**;
- capture batches: **5**;
- >=3 bookmaker events: **4**;
- 24h / 72h / 168h coverage: **3 / 3 / 0**;
- latest audited capture: `2026-10-25T18:56:51.448Z`;
- model precommitted: false;
- production change: false.

Schedules:

- primary: `17 */6 * * *`;
- fallback: `47 0,6,12,18 * * *`;
- health threshold: 270 minutes.

Never backfill closing odds.

P11b price as-known remains live. P11c remains data-bound. P11d weather is closed/no-uplift; attention keeps collecting.

## 10. Governance / P12

Business minimum meaningful ΔMAE remains intentionally unset until independently business-derived.

P12 remains lower priority than current prospective/data-coverage lanes.

## 11. Closed loops

Do not reopen without a materially new mechanism:

- original P7 tournament;
- P10/P10b;
- P5a;
- P6 historical Long72 incremental signal;
- P8 calibration;
- existing weather mechanism;
- old estimator sweeps;
- post-hoc tuning.

## 12. Cold-start command

> Read `AI_BOOTSTRAP.md`, this handoff, `ml/EXECUTION_PLAN_CURRENT.md`, `ml/PROGRESS_TRACKING.md`, Roadmap v4, `ml/P9_BOOKING_CURVE_LEARNER_PRECOMMIT_V1.md`, P7 frozen/prospective files, `ml/ROBOTICKET_INGESTION_SAFETY_NET_2026-10-25.md` and `ml/TICKETING_SOURCE_COVERAGE_EXPANSION_2026-10-25.md`. Query readiness fresh. Ticketing source coverage is 18/18. P9 is 8/9 with learner design frozen and all label paths hard-gated until 9/9 + target-free freeze registration. P7 prospective has 6 immutable rows across 3 events / 0 scores. Long72 has 4 genuine scores. P4a is 4/9 with 3 distinct spacing values. P11 odds capture is resilient and active. Keep production unchanged.
