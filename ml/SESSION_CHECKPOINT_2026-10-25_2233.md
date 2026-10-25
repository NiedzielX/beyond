# Beyond Ticketing — Session Checkpoint

Checkpoint time: **2026-10-25 22:33 Europe/Warsaw**

Status: **CANONICAL SESSION SAVEPOINT**

Production remains unchanged:

`live_adjustment = 0`

## 1. Ticketing ingestion safety

The ingestion incident found on 2026-10-25 is no longer treated as a one-off manual event-mapping problem.

Current protection stack:

`fixture watchdog -> source discovery -> private raw buffer -> verified mapping/promotion -> canonical snapshots`

### RoboTicket

Live controls:

- same-element event ID / label parsing;
- fail-closed parking / VIP / premium / reserve / non-football exclusions;
- football-universe validation before raw candidate buffering;
- hourly discovery;
- private candidate buffer every 10 minutes;
- exact verified kickoff required before canonical promotion;
- original `captured_at` preserved when buffered inventory is promoted/backfilled.

Primary implementation:

- `supabase/functions/roboticket_discover_clubs/index.ts`
- `supabase/functions/roboticket_buffer_candidates_v1/index.ts`
- `supabase/sql/roboticket_candidate_buffer_v1.sql`
- `supabase/sql/roboticket_ingestion_cadence_v1.sql`

### Stellis

Canonical collector:

`stellis_collect_v3`

Current monitored home sources:

- Widzew Łódź;
- Radomiak Radom;
- Piast Gliwice;
- Motor Lublin;
- Korona Kielce.

Current-league alias-resolved source coverage:

- Ekstraklasa home clubs: **18**;
- covered by at least one active source: **18**;
- uncovered: **0**.

Coverage means an active acquisition path exists. It does not mean every future product exposes model-safe inventory immediately. Hidden inventory and ambiguous mapping remain fail-closed.

## 2. Panel

Panel repo:

`NiedzielX/BeyondTicketingPanel`

Current panel behavior:

- ingestion coverage is visible;
- tracked / buffering / schedule-gap states are visible;
- source family is visible;
- recent completed matches are visible;
- Events view exposes `Nadchodzące / Zakończone / Wszystkie`, so completed matches do not appear to disappear after kickoff.

Shared backend contract:

`public.dashboard_ticketing_ingestion_status_v1`

Current status payload version:

`dashboard-ticketing-ingestion-status-v2`

Panel CI for the ingestion/schedule-gap update is green on `main`.

## 3. Round-12 loss assessment

The previous round was **not fully lost**.

Genuine pre-match booking curves were preserved for 5/9 fixtures hosted by onboarded sources.

The four fixtures without curves were hosted by clubs that were not yet onboarded as home ticketing sources at that time; the already-onboarded clubs in those fixtures were away teams.

The issue was therefore primarily **source-coverage + event-ingestion continuity**, not a total data loss.

## 4. P9 — nearest research gate

Current full-window readiness:

- T-168: **8/9 events / 8 clubs**;
- T-72: **12 / 10**;
- T-48: **15 / 10**;
- T-24: **18 / 11**.

P9 learner design is already frozen before the ninth full-window label.

Canonical precommit:

`ml/P9_BOOKING_CURVE_LEARNER_PRECOMMIT_V1.md`

Precommit ID:

`p9-knn-median-residual-k5-v1`

Current gate:

- `design_precommitted=true`;
- `readiness_168_events=8`;
- `full_window_gate_open=false`;
- target-free manifests registered: 0;
- labels export allowed: false;
- results opened: false;
- production activation allowed: false.

Next allowed P9 sequence after the ninth genuine full-window label:

1. fresh target-free P9a T-48/T-24 export;
2. representation/reference freeze;
3. immutable base manifest registration;
4. target-free incumbent catalog;
5. exact target/reference incumbent support freeze;
6. immutable support manifest registration;
7. label export;
8. fixed precommitted evaluator;
9. report result without post-result tuning.

## 5. P7 Long168

Historical frozen result remains exposed:

- point improvement: **1069.80 MAE / 14.44%**;
- 95% event-block interval: `[-2566.13, +174.47]`;
- evidence: `POINT_GAIN_UNCERTAINTY_LIMITED`.

Do not rerun or retune the original tournament.

Prospective validation lane:

- pinned model fingerprint: `70fa929181531276c80a75c0b78a60fb821cf50e714e2bc001de8251cea1793f`;
- immutable prediction rows: **6**;
- independent prospective events: **3**;
- scored events: **0**;
- schedule: `37 */6 * * *`;
- production activation: false.

Next P7 action: collection and scoring only.

## 6. Long72

Current genuine scored events:

`[10,16,21,23]`

Current n=4 evidence:

- anchor event-balanced MAE: **6942.59**;
- package event-balanced MAE: **6824.16**;
- point improvement: **118.43 / 1.71%**;
- event improvement rate: **75%**;
- worst event degradation: **3633.23**.

Do not retune/calibrate/promote from this evidence.

## 7. P4a

Current gate:

- READY events: 5;
- labeled READY events: **4/9**;
- distinct labeled previous-home-spacing values: **3**;
- variance condition: PASS;
- event-count condition: FAIL.

## 8. P11

P11a current audited genuine state:

- raw odds rows: **81**;
- genuine PIT events / clubs: **4 / 4**;
- capture batches: **5**;
- 24h / 72h / 168h coverage: **3 / 3 / 0**;
- primary schedule: `17 */6 * * *`;
- fallback schedule: `47 0,6,12,18 * * *`;
- stale threshold: 270 minutes;
- no model precommit yet;
- no production change.

P11b price as-known remains live. P11c remains data-bound. Existing weather mechanism stays closed/no-uplift. Media attention remains prospective-only.

## 9. Immediate execution order

`preserve multi-source ingestion safety -> preserve P7/P11 schedules -> obtain only genuine ninth full-window P9 label -> execute frozen P9 chain -> continue genuine Long72/P4a scoring -> derive business minimum meaningful ΔMAE -> P12 later`

## 10. Non-negotiable rules

- no synthetic attendance labels;
- no inventory-derived attendance labels;
- no backfilled present-day inventory presented as historical/prospective PIT evidence;
- no closing-odds backfill;
- no fuzzy ambiguous fixture promotion;
- no fake zero when inventory is hidden;
- no post-result retuning of frozen P7/P9/Long72 lanes;
- no production activation without explicit reviewed promotion.
