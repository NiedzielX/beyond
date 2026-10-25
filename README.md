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
8. [`ml/TICKETING_SOURCE_COVERAGE_EXPANSION_2026-10-25.md`](ml/TICKETING_SOURCE_COVERAGE_EXPANSION_2026-10-25.md)
9. [`ml/MODEL_ACCURACY_DEVELOPMENT_INSTRUCTIONS_V2.md`](ml/MODEL_ACCURACY_DEVELOPMENT_INSTRUCTIONS_V2.md)

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
- **multi-source ticketing coverage is live: RoboTicket + Stellis**;
- alias-resolved coverage now reaches **18/18 current Ekstraklasa home clubs / 0 uncovered**;
- Stellis v3 continuously monitors Widzew, Radomiak, Piast, Motor and Korona;
- the shared ingestion dashboard exposes both source families through one status contract;
- dashboard CI passes with ingestion coverage visible on Overview and Data Quality;
- Long72 has **2 genuine prospective scored events**;
- P7 Long168 frozen tournament executed at genuine 10/9 readiness;
- P7 prospective follow-up is precommitted, fingerprint-pinned and has **6 immutable genuine prediction rows across 3 independent future events**;
- P7 prospective workflow has a real six-hour `predict -> persist -> score` schedule with immutable model/hash gates;
- P9a T-24/T-48 target-free freeze audit completed;
- P11a genuine bookmaker capture is scheduled every 6 hours;
- P11b PIT-safe price `as-known` contract is live;
- P11c/P11d target-free source audit is complete;
- Governance v2 business-threshold framework and P12 audit pre-plan exist.

### Immediate execution order

`preserve P7 prospective schedule -> preserve 18/18 multi-source ticketing coverage -> preserve P11a/P11b/P11d collection -> score P7/Long72 only after genuine outcomes -> accumulate P9 to 9/9 -> accumulate P4a labels -> derive business ΔMAE threshold`

No research result activates production automatically.

## Ticketing ingestion safety net / source coverage

Canonical documents:

- [`ml/ROBOTICKET_INGESTION_SAFETY_NET_2026-10-25.md`](ml/ROBOTICKET_INGESTION_SAFETY_NET_2026-10-25.md)
- [`ml/TICKETING_SOURCE_COVERAGE_EXPANSION_2026-10-25.md`](ml/TICKETING_SOURCE_COVERAGE_EXPANSION_2026-10-25.md)

The 2026-10-25 audit confirmed that the previous round was **not** fully lost: genuine pre-match booking curves were preserved for 5/9 fixtures hosted by onboarded ticketing sources. The four remaining fixtures were hosted by non-onboarded clubs; the onboarded clubs in those matches were away teams.

The real systemic issue was broader than one missing event:

1. RoboTicket discovery needed a robust path from a newly discovered product to canonical `ticket_events`;
2. source coverage itself was too narrow — several Ekstraklasa home clubs use Stellis rather than RoboTicket.

### RoboTicket — live

- hardened discovery and same-element eventId/label identity;
- fail-closed parking/VIP/premium/reserve/non-football exclusions;
- private raw candidate buffer before kickoff mapping;
- football-universe gate;
- verified schedule -> automatic ticket-event promotion + PIT-preserving backfill;
- discovery hourly;
- candidate buffer every 10 minutes.

### Stellis — live

Canonical collector:

`stellis_collect_v3`

Monitored sources:

- Widzew Łódź;
- Radomiak Radom;
- Piast Gliwice;
- Motor Lublin;
- Korona Kielce.

Cadence:

`3,13,23,33,43,53 * * * *`

The collector supports both embedded React event data and legacy server-rendered cards. Raw observations are protected before model-facing promotion.

Promotion is fail-closed:

- unique home/away identity required;
- explicit cup/friendly/non-league products excluded;
- latest raw observation determines the current classification;
- ticketing source supplies exact kickoff;
- league sporting data is used only as a unique pair/league cross-check within +/-4 days;
- no hidden availability is converted to a fake zero;
- no ambiguous fixture is promoted.

### League source coverage

Alias-resolved audit against the current 2026/27 Ekstraklasa club universe:

- league home clubs: **18**;
- covered by at least one active ticketing source: **18**;
- uncovered: **0**.

This is source coverage, not a claim that every future fixture already exposes model-safe inventory. Hidden inventory, unpublished events and fixture-mapping delays remain fail-closed states and are surfaced by ingestion monitoring rather than converted into synthetic data.

### Fresh future coverage

At the latest audit:

- canonical future RoboTicket events: **12**, of which **11 have snapshots**;
- canonical future Stellis events: **1**, with **1 snapshot stream**;
- combined canonical future events: **13**;
- combined future canonical events with snapshots: **12**;
- `TRACKED_NO_SNAPSHOT`: **1** — Wisła Kraków vs Cracovia; source currently exposes no readable sectors;
- schedule watchdog currently surfaces **5 future `SCHEDULE_GAP` fixtures** before ticket products are visible/protected;
- protected pre-promotion buffers remain active for future candidates;
- genuine match discovered without model-safe aggregate inventory remains fail-closed rather than converted to a fake snapshot.

Shared panel-facing contract:

`public.dashboard_ticketing_ingestion_status_v1`

Current status payload version:

`dashboard-ticketing-ingestion-status-v2`

The panel shows both source families, recent completed matches, protected buffers and actionable ingestion gaps without a second frontend API.

This work changes data acquisition only. It does not change model parameters, validation or production forecasts.

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
- fingerprint evidence run `40201818862`: SUCCESS, artifact digest `a6dab7c220e065a9e2d2b5f32954303bf067387b1d24458b1fa1066d5a507184`;
- canonical execution wrapper: `ml/p7_long168_prospective_run_v1.py`;
- first true prospective run `40216860928`: SUCCESS;
- one-shot validation run `40223004586`: SUCCESS, artifact digest `45eaf3abdd77395702d03733f2956da6be76c854346ca8b267c868577fcadbe7`;
- current immutable ledger: **6 prediction rows / 3 independent events / 0 scored outcomes**;
- each repeated row is a new genuine timepoint, not a new independent event;
- evidence status: `PROSPECTIVE_PREDICTIONS_ONLY`;
- target values used in prediction: false;
- production activation allowed: false;
- `live_adjustment=0`.

Scheduled prospective execution is implemented in `.github/workflows/p7-long168-prospective-v1.yml`:

`37 */6 * * *`

Each scheduled execution rebuilds the exact frozen model, hard-checks the pinned fingerprint and training lineage, persists only previously unseen eligible prospective identities, and only then attaches genuine completed outcomes for scoring. Do not interpret MAE until genuine outcomes exist.

## Long72 prospective evidence

Genuine post-match outcomes currently scored:

- event 10 — Pogoń Szczecin vs Radomiak Radom: **19,050**;
- event 16 — Wisła Kraków vs Raków Częstochowa: **33,000**.

Frozen point evidence on n=2:

- anchor MAE: **9,069.52**;
- frozen package MAE: **7,641.71**;
- point improvement: **1,427.80 / 15.74%**.

Preserve and collect more. Do not retune/calibrate/promote from n=2.

## P9 / P9a Booking Curve

P9a target-free audit is complete.

Fresh P9 readiness:

- 168h: **5/9 events / 5 clubs**;
- 72h: **9 / 7**;
- 48h: **12 / 7**;
- 24h: **15 / 9**;
- full 168h status: `DATA_BOUND`;
- learner precommitted: false.

The expanded source coverage improves future evidence only. Do not backfill newly discovered present-day inventory into historical T-168 windows.

## P4a fixture context

Fresh readiness remains:

- READY events: 5;
- genuine labeled READY events: **2**;
- distinct labeled values: **2**;
- required: `>=9 labeled AND >=3 distinct labeled values`;
- research trigger: false.

Gate remains closed.

## P11 context program

### P11a — bookmaker odds

Fresh readiness:

- `GENUINE_PIT_DATA_ACCUMULATING`;
- genuine PIT events: **2**;
- clubs: **2**;
- events with >=3 bookmakers: **2**;
- 24h / 72h / 168h coverage: **1 / 1 / 0**;
- model precommitted: false;
- target values used: false;
- production change: false.

Capture schedule:

`17 */6 * * *`

Never backfill closing odds.

### P11b/c/d

- P11b `public.p11_price_context_as_known_v1(ticket_event_id, as_of_at)`: live, PIT-safe, no inferred promotion;
- P11c: data-bound;
- P11d weather: `research_only_no_uplift`, closed;
- P11d media attention: prospective-only collection continues.

## Governance / P12

Governance framework:

`ml/GOVERNANCE_V2_BUSINESS_DMAE_THRESHOLD.md`

The numerical minimum meaningful `ΔMAE` remains intentionally unset until independently business-derived.

P12 remains lower priority than active prospective/data-coverage lanes.

## Closed loops

Do not reopen without a materially new mechanism:

- original P7 tournament;
- P10/P10b;
- P5a shrinkage;
- P6 historical Long72 signal;
- P8 calibration;
- existing weather mechanism;
- old estimator sweeps;
- post-hoc tuning on inspected evidence.

## Never do these

- do not backfill booking curves or closing odds and label them prospective;
- do not fuzzy-match ambiguous fixtures/products;
- do not promote parking/VIP/reserve/non-football/cup products into Ekstraklasa snapshots;
- do not convert hidden/unknown inventory into zero;
- do not infer promotion from price movement;
- do not use future target trajectory points in P9/P9a;
- do not lower P9/P4 gates;
- do not retune frozen P7/Long72 from early prospective evidence;
- do not change `live_adjustment` from zero without reviewed promotion.

## Engineering rule

`hypothesis -> PIT contract -> code -> tests -> forward/event-safe evaluation -> artifact -> hashes -> result doc -> decision -> canonical docs`

> **Frozen validation protects truth. It does not pause model development.**
