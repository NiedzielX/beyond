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
- alias-resolved coverage reaches **18/18 current Ekstraklasa home clubs / 0 uncovered**;
- Stellis v3 continuously monitors Widzew, Radomiak, Piast, Motor and Korona;
- the shared ingestion dashboard exposes both source families through one status contract;
- panel shows ingestion coverage, schedule gaps and recent completed matches; Dashboard CI is green;
- Long72 has **4 genuine prospective scored events**;
- P7 Long168 frozen tournament executed at genuine 10/9 readiness;
- P7 prospective follow-up is precommitted, fingerprint-pinned and has **6 immutable genuine prediction rows across 3 independent future events**;
- P7 prospective workflow has a real six-hour `predict -> persist -> score` schedule with immutable model/hash gates;
- P9a T-24/T-48 target-free freeze audit completed;
- full P9 T-168 readiness is now **7/9** after two new genuine 2026-10-25 outcomes;
- P4a now has **4 labeled events / 3 distinct labeled spacing values**;
- P11a genuine bookmaker capture has **81 raw rows / 4 genuine events / 5 capture batches** and a primary + stale-health fallback schedule;
- P11b PIT-safe price `as-known` contract is live;
- P11c/P11d target-free source audit is complete;
- Governance v2 business-threshold framework and P12 audit pre-plan exist.

### Immediate execution order

`preserve P7 prospective schedule -> preserve 18/18 multi-source ticketing coverage -> preserve resilient P11a/P11b/P11d collection -> obtain only genuine post-match labels -> P9 7/9 -> P4a 4/9 -> score frozen forward lanes only when genuine outcomes arrive -> derive business ΔMAE threshold`

No research result activates production automatically.

## 2026-10-25 outcome update

Two additional genuine reported attendances were added after publication of post-match reports:

- event 21 — Jagiellonia Białystok vs Wisła Płock: **17,021**;
- event 23 — Śląsk Wrocław vs Wieczysta Kraków: **12,391**.

No attendance value was inferred from inventory, capacity or model output.

These two labels moved:

- P9 T-168: **5/9 -> 7/9**;
- P9 T-72: **9 -> 11 events**;
- P9 T-48: **12 -> 14 events**;
- P9 T-24: **15 -> 17 events**;
- P4a labeled events: **2 -> 4**;
- P4a distinct labeled previous-home-spacing values: **2 -> 3**;
- Long72 genuine scored events: **2 -> 4**.

Event 22 — Legia Warszawa vs Lech Poznań — is completed, but no attendance label is stored yet because a sufficiently reliable published attendance value has not been confirmed. Do not estimate it.

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

- exact training set: events `[1,3,4,5,10,11,15,16,18,19]` / 139 rows;
- training manifest: `185a9fc90e646bd5fa1bbed3b50c625d65d127a2b2943501761bdfcb89f354ed`;
- pinned model fingerprint: `70fa929181531276c80a75c0b78a60fb821cf50e714e2bc001de8251cea1793f`;
- current immutable ledger: **6 prediction rows / 3 independent events / 0 scored outcomes**;
- evidence status: `PROSPECTIVE_PREDICTIONS_ONLY`;
- production activation allowed: false;
- `live_adjustment=0`.

Scheduled execution:

`37 */6 * * *`

Each scheduled execution rebuilds the exact frozen model, hard-checks the pinned fingerprint and training lineage, persists only previously unseen eligible prospective identities, and only then attaches genuine completed outcomes for scoring.

## Long72 prospective evidence

Genuine scored events now: **4** — events 10, 16, 21 and 23.

Current frozen point evidence:

- anchor event-balanced MAE: **6,942.59**;
- frozen package event-balanced MAE: **6,824.16**;
- point improvement: **118.43 MAE / 1.71%**;
- event improvement rate: **75%**;
- event-balanced bias: **-712.84**;
- worst event degradation: **3,633.23**.

By horizon band:

- 24–48h: package is **5.00 MAE worse** than anchor;
- 48–72h: package improves MAE by **241.87**.

This is much weaker than the earlier n=2 point result. Preserve the frozen package and collect more. Do not retune/calibrate/promote from n=4.

## P9 / P9a Booking Curve

P9a target-free audit is complete.

Fresh P9 readiness:

- 168h: **7/9 events / 7 clubs**;
- 72h: **11 / 9**;
- 48h: **14 / 9**;
- 24h: **17 / 10**;
- full 168h status: `DATA_BOUND`;
- learner precommitted: false.

The expanded source coverage improves future evidence only. Do not backfill newly discovered present-day inventory into historical T-168 windows.

## P4a fixture context

Fresh readiness:

- READY events: 5;
- genuine labeled READY events: **4/9**;
- distinct labeled previous-home-spacing values: **3**;
- distinct-value requirement: **PASS**;
- event-count requirement: **FAIL**;
- research trigger: false.

Do not open P4a model results before the 9-event gate.

## P11 context program

### P11a — bookmaker odds

Fresh genuine state:

- status: `GENUINE_PIT_DATA_ACCUMULATING`;
- raw append-only bookmaker rows: **81**;
- genuine PIT events / clubs: **4 / 4**;
- capture batches: **5**;
- events with >=3 bookmakers: **4**;
- 24h / 72h / 168h coverage: **3 / 3 / 0**;
- latest capture: `2026-10-25T18:56:51.448Z`;
- model precommitted: false;
- target values used: false;
- production change: false.

Capture resilience:

- primary schedule: `17 */6 * * *`;
- fallback schedule: `47 0,6,12,18 * * *`;
- stale threshold: **270 minutes**.

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
