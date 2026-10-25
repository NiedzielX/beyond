# Beyond Ticketing — Next Session Handoff

Last updated: **2026-10-25**

Status: **READ THIS FIRST AFTER `AI_BOOTSTRAP.md`**

## 1. North star

> **Minimize true out-of-sample attendance-forecast MAE at decision-relevant horizons using PIT-safe, reproducible evidence.**

Current phase: **representation-first, not tuning-first**.

Production remains unchanged:

`live_adjustment = 0`

## 2. Immediate execution order

`preserve P7 prospective schedule -> preserve/expand multi-source ticketing ingestion -> preserve P11 collection -> score only genuine completed prospective events -> accumulate P9 to 9/9 -> accumulate P4a labels -> define business ΔMAE threshold -> P12 later`

Do not restart the P7 tournament, P9a freeze, P10 or weather loops.

## 3. Ticketing ingestion — MULTI-SOURCE / LIVE

Read:

- `ml/ROBOTICKET_INGESTION_SAFETY_NET_2026-10-25.md`
- `ml/TICKETING_SOURCE_COVERAGE_EXPANSION_2026-10-25.md`

The previous round was **not** fully lost. Genuine curves were preserved for 5/9 round-12 fixtures; the other four were hosted by non-onboarded sources.

### RoboTicket

Live controls:

- discovery `roboticket-discovery-v8`;
- exact same-element product identity;
- parking/VIP/premium/reserve/non-football fail closed;
- private pre-mapping inventory buffer;
- football-universe gate;
- verified kickoff -> automatic promotion/backfill;
- discovery hourly;
- buffer every 10 minutes.

### Stellis

Canonical collector:

`stellis_collect_v3`

Active source family:

- Widzew Łódź;
- Radomiak Radom;
- Piast Gliwice;
- Motor Lublin;
- Korona Kielce.

Cadence:

`3,13,23,33,43,53 * * * *`

Only v3 is scheduled. Old v1/v2/probe functions are diagnostics.

Stellis promotion is fail closed:

- first-team home/away identity required;
- explicit cup/friendly/non-league excluded;
- latest raw observation wins over stale earlier rows;
- ticketing source supplies exact kickoff;
- sporting shadow is a unique league-pair cross-check within +/-4 days;
- no hidden inventory becomes zero;
- no ambiguous fixture is promoted.

Current genuine state:

- future canonical RoboTicket events: **12**, with **11 snapshot streams**;
- future canonical Stellis events: **1**, with **1 snapshot stream**;
- combined future canonical events: **13**, **12 with snapshots**;
- one `TRACKED_NO_SNAPSHOT`: Wisła Kraków vs Cracovia — mapped, source currently returns no readable sectors;
- two genuine future match candidates have protected raw inventory while fixture confirmation is pending;
- one genuine future match is discovered but does not expose model-safe aggregate inventory.

Stellis examples:

- Korona Kielce vs Radomiak Radom — event 603, `TRACKED`, 2 snapshots at latest audit;
- Piast Gliwice vs Korona Kielce — raw curve protected, waiting for league fixture confirmation;
- Radomiak Radom vs Śląsk Wrocław — match discovered, aggregate availability hidden by active source contract;
- Piast vs Górnik Puchar Polski — `NON_MATCH_EXCLUDED`, no model snapshot.

Shared panel table:

`public.dashboard_ticketing_ingestion_status_v1`

Current payload version:

`dashboard-ticketing-ingestion-status-v2`

Panel repo: `NiedzielX/BeyondTicketingPanel`.

Coverage is visible on Overview/Data Quality and completed matches remain visible historically.

## 4. P7 Long168 — exposed historical result

Run `40197742930`:

- 10 events / 139 rows;
- 5 forward held-out folds;
- anchor MAE 7409.79;
- selected `gbr-l1-depth2-n50-lr003`;
- challenger MAE 6339.99;
- gain 1069.80 / 14.44%;
- event/fold improvement 80% / 80%;
- 95% event-block CI `[-2566.13,+174.47]`;
- evidence `POINT_GAIN_UNCERTAINTY_LIMITED`;
- decision `ADVANCE_RESEARCH`.

Never rerun/tune this tournament.

## 5. P7 prospective validation — ACTIVE

Frozen training set:

`[1,3,4,5,10,11,15,16,18,19]` / 139 rows.

Training manifest:

`185a9fc90e646bd5fa1bbed3b50c625d65d127a2b2943501761bdfcb89f354ed`

Pinned model fingerprint:

`70fa929181531276c80a75c0b78a60fb821cf50e714e2bc001de8251cea1793f`

Current immutable ledger:

- prediction rows: **3**;
- independent events: **3**;
- scored events: **0**;
- status: `PROSPECTIVE_PREDICTIONS_ONLY`;
- fingerprint count: 1;
- target values used: false;
- production activation allowed: false;
- `live_adjustment=0`.

Scheduled prediction cadence:

`37 */6 * * *`

Do not tune until genuine outcomes are scored under the frozen scorer.

## 6. Long72

Genuine scored events remain 2:

- event 10 Pogoń–Radomiak: 19,050;
- event 16 Wisła Kraków–Raków: 33,000.

Point evidence:

- anchor MAE 9069.52;
- frozen package MAE 7641.71;
- gain 1427.80 / 15.74%.

Do not retune from n=2.

## 7. P9 / P9a

Fresh full P9 readiness:

- 168h: **5/9 events / 5 clubs**;
- 72h: **9 / 7**;
- 48h: **12 / 7**;
- 24h: **15 / 9**;
- full status: `DATA_BOUND`;
- learner precommitted: false.

Expanded ticketing coverage improves future evidence only. Do not backfill T-168 history.

## 8. P4a

Current gate remains closed:

- READY events: 5;
- labeled READY events: 2;
- distinct labeled values: 2;
- required: >=9 labeled AND >=3 distinct labeled values.

## 9. P11

P11a fresh readiness:

- `GENUINE_PIT_DATA_ACCUMULATING`;
- genuine PIT events: 2;
- clubs: 2;
- >=3 bookmaker events: 2;
- 24h / 72h / 168h coverage: 1 / 1 / 0;
- model precommitted: false.

Capture cadence:

`17 */6 * * *`

P11b price as-known remains live. P11c remains data-bound. P11d weather remains closed/no-uplift; attention keeps collecting.

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

> Read `AI_BOOTSTRAP.md`, this handoff, `ml/EXECUTION_PLAN_CURRENT.md`, `ml/PROGRESS_TRACKING.md`, Roadmap v4, P7 frozen/prospective files, `ml/ROBOTICKET_INGESTION_SAFETY_NET_2026-10-25.md` and `ml/TICKETING_SOURCE_COVERAGE_EXPANSION_2026-10-25.md`. Query readiness fresh. P7 prospective has 3 immutable predictions and 0 scores. Ticketing ingestion is multi-source: RoboTicket + Stellis v3. P9 remains 5/9, P4a 2 labeled, P11 has 2 genuine odds events, Long72 has 2 genuine scores. Keep production unchanged and never retune exposed evidence.
