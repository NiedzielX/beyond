# Beyond Ticketing — Next Session Handoff

Last updated: **2026-10-25**

Status: **READ THIS FIRST AFTER `AI_BOOTSTRAP.md`**

## 1. North star

> **Minimize true out-of-sample attendance-forecast MAE at decision-relevant horizons using PIT-safe, reproducible evidence.**

Current phase: **representation-first, not tuning-first**.

Production remains unchanged:

`live_adjustment = 0`

## 2. Immediate execution order

`preserve P7 prospective schedule -> preserve 18/18 multi-source ticketing ingestion -> preserve resilient P11 collection -> score only genuine completed prospective events -> accumulate P9 to 9/9 -> accumulate P4a labels -> define business ΔMAE threshold -> P12 later`

Do not restart the P7 tournament, P9a freeze, P10 or weather loops.

## 3. Ticketing ingestion — MULTI-SOURCE / LIVE

Read:

- `ml/ROBOTICKET_INGESTION_SAFETY_NET_2026-10-25.md`
- `ml/TICKETING_SOURCE_COVERAGE_EXPANSION_2026-10-25.md`

The previous round was **not** fully lost. Genuine curves were preserved for 5/9 round-12 fixtures; the other four were hosted by non-onboarded sources at that time.

The systemic fix is now live and source coverage has been expanded.

### Current league coverage

Alias-resolved audit against the current 2026/27 Ekstraklasa home-club universe:

- current league clubs: **18**;
- covered by at least one active ticketing source: **18**;
- uncovered: **0**.

This is source coverage, not a promise that every event exposes visible aggregate inventory. Hidden inventory and unpublished products remain fail-closed states.

### RoboTicket

Live controls:

- hardened same-element event identity;
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

Shared panel table:

`public.dashboard_ticketing_ingestion_status_v1`

Current payload version:

`dashboard-ticketing-ingestion-status-v2`

Panel repo: `NiedzielX/BeyondTicketingPanel`.

Coverage is visible on Overview/Data Quality. The Events page keeps recent completed matches visible instead of showing only future fixtures.

Current operational watchdog state includes future `SCHEDULE_GAP` rows before ticket products become available; these are early warnings, not fabricated events.

Known source-side exception:

- Wisła Kraków vs Cracovia is mapped but the active RoboTicket source currently exposes no readable sectors; this is monitored as source inventory unavailable rather than treated as a missing event or fake zero.

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

## 5. P7 prospective validation — ACTIVE / SCHEDULED

Frozen training set:

`[1,3,4,5,10,11,15,16,18,19]` / 139 rows.

Training manifest:

`185a9fc90e646bd5fa1bbed3b50c625d65d127a2b2943501761bdfcb89f354ed`

Pinned model fingerprint:

`70fa929181531276c80a75c0b78a60fb821cf50e714e2bc001de8251cea1793f`

Fingerprint evidence:

- GitHub Actions run: `40201818862`;
- artifact digest: `a6dab7c220e065a9e2d2b5f32954303bf067387b1d24458b1fa1066d5a507184`;
- fingerprint mode persisted zero predictions.

Canonical pinned execution wrapper:

`ml/p7_long168_prospective_run_v1.py`

One-shot end-to-end schedule-path validation:

- run: `40223004586`;
- result: SUCCESS;
- artifact digest: `45eaf3abdd77395702d03733f2956da6be76c854346ca8b267c868577fcadbe7`;
- temporary one-shot workflow removed after validation.

Current immutable ledger:

- prediction rows: **6**;
- independent events: **3**;
- scored events: **0**;
- status: `PROSPECTIVE_PREDICTIONS_ONLY`;
- fingerprint count: 1;
- target values used: false;
- production activation allowed: false;
- `live_adjustment=0`.

Repeated rows are genuine later timepoints for the same events and do not increase independent event N.

Actual GitHub Actions schedule is implemented in:

`.github/workflows/p7-long168-prospective-v1.yml`

Cadence:

`37 */6 * * *`

Scheduled/manual predict mode performs:

`target-free inputs -> exact frozen-model rebuild -> fingerprint/lineage hard gates -> immutable prediction persistence -> genuine outcome attachment/scoring`

Never recompute an old prospective prediction after the outcome becomes known. Do not tune until genuine outcomes are scored under the frozen scorer.

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

## 9. P11 — ACTIVE / RESILIENT CAPTURE

P11a fresh genuine state after recovery run `40223646599`:

- status: `GENUINE_PIT_DATA_ACCUMULATING`;
- raw rows: **81**;
- genuine PIT events / clubs: **4 / 4**;
- capture batches: **5**;
- >=3 bookmaker events: **4**;
- 24h / 72h / 168h coverage: **3 / 3 / 0**;
- latest capture: `2026-10-25T18:56:51.448Z`;
- recovery artifact digest: `6c326149cea6d1043eaa3c5a200b5430853a3fb46454aad910cbf0faf188beba`;
- model precommitted: false;
- target values used: false;
- production change: false.

The single six-hour cron was not sufficiently reliable operationally, so capture resilience is now explicit:

- primary: `17 */6 * * *`;
- fallback: `47 0,6,12,18 * * *`;
- health RPC: `public.p11_market_odds_capture_health_v2()`;
- stale threshold: 270 minutes;
- fallback skips the provider when a recent primary capture is healthy;
- the recovery one-shot was deleted after successful verification.

Never backfill closing odds.

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

> Read `AI_BOOTSTRAP.md`, this handoff, `ml/EXECUTION_PLAN_CURRENT.md`, `ml/PROGRESS_TRACKING.md`, Roadmap v4, P7 frozen/prospective files, `ml/ROBOTICKET_INGESTION_SAFETY_NET_2026-10-25.md` and `ml/TICKETING_SOURCE_COVERAGE_EXPANSION_2026-10-25.md`. Query readiness fresh. Ticketing source coverage is 18/18 current league home clubs. P7 prospective has 6 immutable prediction rows across 3 independent events and 0 scores. P11 has 81 genuine raw rows across 4 events with primary+fallback capture health. P9 remains 5/9, P4a 2 labeled, Long72 has 2 genuine scores. Keep production unchanged and never retune exposed evidence.
