# Beyond Ticketing — Current MAE Execution Plan

Last updated: **2026-10-25**

Status: **CURRENT EXECUTION ORDER**

Canonical strategy: `ml/MAE_RESEARCH_ROADMAP_V4.md`.

## North star

> **Minimize true out-of-sample attendance-forecast MAE at decision-relevant horizons with PIT-safe, reproducible evidence.**

Production remains:

`live_adjustment = 0`

## Priority 0 — protect data and evidence integrity

- Multi-source ticketing ingestion is live: RoboTicket + Stellis.
- Alias-resolved current-league source coverage is **18/18 home clubs / 0 uncovered**.
- RoboTicket discovery is hourly; unmapped genuine match candidates are buffered privately every 10 minutes.
- Verified schedule promotion preserves original `captured_at` when buffered rows are promoted.
- Fixture schedule watchdog remains live so future fixtures cannot silently disappear.
- Original P7 tournament is exposed; never retune/rerun it.
- P7 prospective model fingerprint is pinned; any drift must fail closed.
- P9 learner design is frozen **before the ninth full-window label**.
- P9 labels remain physically blocked until the 9/9 gate and both target-free identity freezes are registered.
- Preserve frozen Long72 and P4a contracts.
- Preserve P11 primary + health-guarded fallback schedules.
- Never backfill closing odds or booking curves and call them prospective.
- Do not promote parking/VIP/reserve/non-football/cup ticket products.
- Do not convert hidden/unknown availability into zero.
- Do not infer promotions from price movement.
- Do not enable production.

## Priority 1 — P9 is now the nearest research gate: 8/9

Fresh full-window readiness:

- 168h: **8/9 events / 8 clubs**;
- 72h: **12 / 10**;
- 48h: **15 / 10**;
- 24h: **18 / 11**;
- full status: `DATA_BOUND`.

Genuine full-168h event IDs:

`[5,10,15,18,19,20,21,23]`

Event 20 (Wisła Płock vs Radomiak Radom) supplied the eighth genuine full-window label with reported attendance **5,014**.

Event 22 (Legia Warszawa vs Lech Poznań) is technically full-window ready but still has no trusted published attendance label. Its 6–168h curve contains 648 snapshots and the maximum gap is about 0.25h. Do not estimate attendance from inventory.

### P9 learner is already precommitted

Canonical precommit:

`ml/P9_BOOKING_CURVE_LEARNER_PRECOMMIT_V1.md`

Precommit ID:

`p9-knn-median-residual-k5-v1`

Frozen v1 mechanism:

- fixed cutoffs: T-48 and T-24;
- canonical P9 normalized booking-curve representation;
- max interpolation gap: 12h;
- minimum overlap: 3 canonical points;
- weighted-L1 curve distance;
- fixed nearest-neighbor `k=5`;
- minimum 3 residual-bearing neighbors;
- same incumbent source family for target/reference residuals;
- correction = median reference residual;
- no fitted coefficient;
- no regression model;
- no candidate sweep;
- final clipping only to `[0, verified_stadium_capacity]`;
- primary metric = event-balanced MAE across both fixed cutoffs.

Machine status:

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

Hard execution order at 9/9:

1. export fresh target-free T-48/T-24 P9 inputs;
2. run canonical P9a representation/reference freeze;
3. register immutable P9a manifest;
4. export target-free incumbent catalog;
5. run `ml/p9_learner_support_freeze_v1.py` to freeze exact target/reference incumbent row IDs;
6. register immutable support manifest;
7. only then call `public.export_p9_learner_labels_v2(...)`;
8. run fixed `ml/p9_booking_curve_learner_v1.py`;
9. report all precommitted metrics; do not tune based on the result.

At 8/9 all relevant gates were negative-tested and correctly rejected:

- P9a freeze registration;
- target-free incumbent catalog export;
- label export v2.

Both freeze registries are still empty.

Do not lower the 12h quality ceiling. Events 3 and 4 remain correctly excluded because their maximum 6–168h gaps are about 13.26h and 19.02h.

## Priority 2 — P7 prospective validation is active

Historical P7 evidence:

- anchor MAE: 7409.79;
- challenger MAE: 6339.99;
- point improvement: 1069.80 / 14.44%;
- 95% event-block interval: `[-2566.13,+174.47]`;
- evidence: `POINT_GAIN_UNCERTAINTY_LIMITED`.

Prospective lane:

- precommitted before outcomes;
- fixed mechanism: `gbr-l1-depth2-n50-lr003`;
- fixed training set: `[1,3,4,5,10,11,15,16,18,19]` / 139 rows;
- training manifest: `185a9fc90e646bd5fa1bbed3b50c625d65d127a2b2943501761bdfcb89f354ed`;
- model fingerprint: `70fa929181531276c80a75c0b78a60fb821cf50e714e2bc001de8251cea1793f`;
- no bootstrap backfill;
- prediction persistence only while genuinely 72–168h before kickoff.

Current prospective ledger:

- prediction rows: **6**;
- independent events: **3**;
- scored events: **0**;
- evidence: `PROSPECTIVE_PREDICTIONS_ONLY`;
- production activation false.

Schedule:

`37 */6 * * *`

Next P7 action is collection/scoring only. Do not tune.

## Priority 3 — preserve full multi-source ticketing coverage

Read:

- `ml/ROBOTICKET_INGESTION_SAFETY_NET_2026-10-25.md`
- `ml/TICKETING_SOURCE_COVERAGE_EXPANSION_2026-10-25.md`
- `ml/TICKETING_SCHEDULE_WATCHDOG_2026-10-25.md`

League source coverage:

- current Ekstraklasa home clubs: **18**;
- covered by at least one active source: **18**;
- uncovered: **0**.

### RoboTicket safety net

- hardened same-element product identity;
- parking/VIP/premium/reserve/non-football fail closed;
- football-universe gate;
- discovery hourly;
- candidate raw inventory buffer every 10m;
- exact schedule verification before canonical promotion;
- original PIT timestamps preserved during backfill.

### Stellis

Canonical collector:

`stellis_collect_v3`

Cadence:

`3,13,23,33,43,53 * * * *`

Monitored sources:

- Widzew;
- Radomiak;
- Piast;
- Motor;
- Korona.

Hidden inventory remains hidden; ambiguous products fail closed.

### Panel / watchdog

Shared panel status:

`public.dashboard_ticketing_ingestion_status_v1`

The panel now exposes:

- tracked future events;
- protected pre-mapping buffers;
- schedule gaps;
- recent completed matches;
- source family;
- actionable ingestion reason.

The Events screen exposes `Nadchodzące / Zakończone / Wszystkie` and recent completed matches so data no longer appears to disappear after kickoff.

Panel CI for the ingestion/schedule-gap update is green on main.

## Priority 4 — preserve P11a PIT odds accumulation with resilience

Fresh state:

- raw append-only odds rows: **81**;
- genuine PIT events / clubs: **4 / 4**;
- capture batches: **5**;
- >=3 bookmaker events: **4**;
- 24h / 72h / 168h coverage: **3 / 3 / 0**;
- latest audited capture: `2026-10-25T18:56:51.448Z`;
- model precommitted: false;
- target values used: false;
- production change: false.

Capture schedules:

- primary: `17 */6 * * *`;
- fallback: `47 0,6,12,18 * * *`;
- stale threshold: 270 minutes.

Do not fit a P11a attendance model yet and never backfill closing odds.

## Priority 5 — preserve P11b/P11d context collection

### P11b price

`public.p11_price_context_as_known_v1(ticket_event_id, as_of_at)` remains live and target-free.

No explicit promotion source exists; promotion stays null.

### P11c absences

Still data-bound. Continue verified collection only.

### P11d weather

Existing mechanism remains `research_only_no_uplift`; closed unless a materially new mechanism is proposed.

### P11d attention

Continue prospective-only collection. Do not force evaluation before useful variance/coverage exists.

## Priority 6 — continue Long72 frozen prospective scoring

Current genuine scored events:

`[10,16,21,23]`

Current n=4 evidence:

- anchor event-balanced MAE: **6942.59**;
- package event-balanced MAE: **6824.16**;
- point improvement: **118.43 / 1.71%**;
- event improvement rate: **75%**;
- worst event degradation: **3633.23**.

By band:

- 24–48h: package is about **5 MAE worse** than anchor;
- 48–72h: package improves by about **241.85 MAE**.

This is materially weaker than the earlier n=2 point estimate. Preserve the freeze; do not retune/calibrate/promote.

## Priority 7 — P4a genuine label accumulation

Fresh readiness:

- READY events: 5;
- labeled READY events: **4/9**;
- distinct labeled previous-home-spacing values: **3**;
- distinct-value gate: PASS;
- event-count gate: FAIL;
- research trigger: false.

Only genuine new labels should move this gate.

## Priority 8 — business minimum meaningful ΔMAE

Framework:

`ml/GOVERNANCE_V2_BUSINESS_DMAE_THRESHOLD.md`

Derive the threshold independently from real forecast-driven operational decisions.

## Priority 9 — P12 later

`ml/P12_DEMAND_REGIME_AUDIT_PLAN.md`

Do not start a regime-aware challenger while higher-priority prospective/data-coverage lanes remain immature.

## Completed in this execution cycle

- ticketing-source coverage expanded to 18/18 current league home clubs;
- RoboTicket discovery/buffer/promotion safety net deployed;
- panel ingestion coverage + recent completed UX deployed to main and CI green;
- genuine event 21 attendance added: 17,021;
- genuine event 23 attendance added: 12,391;
- missing genuine event 20 attendance recovered: 5,014;
- P9 advanced from 5/9 to **8/9** without relaxing any quality rule;
- P4a advanced from 2 to **4 labeled events** and reached 3 distinct spacing values;
- Long72 advanced from 2 to **4 genuine scores**;
- P9 v1 learner design frozen before ninth full-window label;
- machine-readable P9 precommit registry deployed;
- hard 9/9 + freeze-before-label DB gates deployed and negative-tested;
- target-free incumbent catalog deployed and gate-tested;
- target-free target/reference incumbent support-freeze harness committed;
- fixed P9 evaluator committed with no fit/search path;
- deterministic synthetic P9 evaluator tests added;
- P9 learner precommit CI added;
- P7 prospective lane remains frozen and scheduled;
- P11 odds capture remains resilient and scheduled;
- production unchanged.

## Next meaningful milestones

1. obtain the ninth **genuine** full-window P9 attendance label without estimating it;
2. execute the already-frozen P9 target-free freeze -> support freeze -> label export -> evaluator chain;
3. first genuine P7 prospective scored event;
4. additional Long72 genuine outcomes;
5. P4a reaches 9 labeled events (variance gate already passed);
6. P11a reaches genuine 168h coverage and broader multi-event accumulation;
7. media attention becomes evaluation-ready;
8. business minimum meaningful ΔMAE is approved.
