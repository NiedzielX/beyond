# Beyond — AI Bootstrap / Read This First

Last updated: **2026-10-25**

## Cold-start order

Read in this order:

1. `ml/NEXT_SESSION_HANDOFF.md`;
2. `ml/EXECUTION_PLAN_CURRENT.md`;
3. `ml/PROGRESS_TRACKING.md`;
4. `ml/MAE_RESEARCH_ROADMAP_V4.md`;
5. `ml/ROBOTICKET_INGESTION_SAFETY_NET_2026-10-25.md`;
6. `ml/TICKETING_SOURCE_COVERAGE_EXPANSION_2026-10-25.md`;
7. `ml/TICKETING_SCHEDULE_WATCHDOG_2026-10-25.md`;
8. `ml/P7_LONG168_RESULT_2026-10-25.md`;
9. `ml/P7_LONG168_PROSPECTIVE_PRECOMMIT_V1.md`;
10. `ml/P7_LONG168_PROSPECTIVE_FINGERPRINT_V1.md`;
11. `ml/P9A_FREEZE_AUDIT_2026-10-25.md`;
12. `ml/P11A_FIRST_GENUINE_CAPTURE_2026-10-25.md`;
13. `ml/P11_CONTEXT_AUDIT_2026-10-25.md`.

Do not restart from Roadmap v3. Do not reconstruct frozen experiments from memory.

## North star

> **Minimize true out-of-sample attendance-forecast MAE at decision-relevant horizons using honest PIT-safe, reproducible evidence.**

Current mode: **representation-first, not tuning-first**.

Production remains:

`live_adjustment = 0`

## Immediate order

`preserve P7 prospective schedule -> preserve 18/18 multi-source ticketing ingestion + fixture watchdog -> preserve resilient P11 context/odds collection -> score only genuine future outcomes -> accumulate P9 to 9/9 -> accumulate P4a labels -> derive business ΔMAE threshold -> P12 later`

## Current canonical state

### Multi-source ticketing ingestion

Three protection layers are live:

`fixture watchdog -> source discovery/private buffer -> canonical ticket_event/model-facing snapshots`

Alias-resolved current-league source coverage:

- current Ekstraklasa home clubs: **18**;
- covered by at least one active source: **18**;
- uncovered: **0**.

#### RoboTicket

- discovery v8, hourly;
- private unmapped-match buffer every 10 minutes;
- football-universe gate;
- fail-closed parking/VIP/premium/reserve/non-football exclusions;
- verified promotion + PIT-preserving backfill.

#### Stellis

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

Promotion is fail closed: source kickoff + unique league pair within +/-4 days, explicit cup/non-league exclusion, no hidden inventory -> zero conversion.

Fresh canonical future state before schedule-gap rows:

- RoboTicket future events: 12 / 11 with snapshots;
- Stellis future events: 1 / 1 with snapshots;
- total canonical future events: 13 / 12 with snapshots;
- one TRACKED_NO_SNAPSHOT: Wisła Kraków vs Cracovia.

#### Fixture schedule watchdog

View:

`public.dashboard_ticketing_fixture_coverage_v1`

Refresh:

`private.refresh_dashboard_ticketing_ingestion_status_v2()`

Cron:

`ticketing_ingestion_dashboard_10m`

Cadence:

`9,19,29,39,49,59 * * * *`

Fresh `SCHEDULE_GAP` count: **5**.

Current gaps:

- Górnik Zabrze – Legia Warszawa;
- Jagiellonia Białystok – GKS Katowice;
- Motor Lublin – Wisła Płock;
- Śląsk Wrocław – Piast Gliwice;
- Widzew Łódź – Pogoń Szczecin.

These were rechecked after fresh RoboTicket/Stellis discovery; they remain genuine missing source events, not stale dashboard rows.

Wieczysta–Jagiellonia is correctly suppressed from the gap list because the raw RoboTicket curve is protected.

Panel CI for schedule-gap UI:

`40222368344` — **SUCCESS**.

### P7 Long168 historical result

- 10 frozen events / 139 rows;
- 5 strict forward held-out events/folds;
- anchor MAE 7409.79;
- selected candidate `gbr-l1-depth2-n50-lr003`;
- challenger MAE 6339.99;
- point gain 1069.80 / 14.44%;
- 95% event-block CI `[-2566.13,+174.47]`;
- evidence `POINT_GAIN_UNCERTAINTY_LIMITED`;
- decision `ADVANCE_RESEARCH`.

The tournament is exposed. Never retune/rerun it.

### P7 prospective validation

Precommitted and live.

Frozen model fingerprint:

`70fa929181531276c80a75c0b78a60fb821cf50e714e2bc001de8251cea1793f`

Current ledger:

- **6 immutable prediction rows**;
- **3 independent events**;
- 0 scored events;
- `PROSPECTIVE_PREDICTIONS_ONLY`;
- no bootstrap backfill;
- target values not used;
- production activation false.

The second three rows are later genuine timepoints for the same three events and do not increase independent N.

Schedule:

`37 */6 * * *`

Pinned execution wrapper:

`ml/p7_long168_prospective_run_v1.py`

End-to-end validation run:

`40223004586` — SUCCESS.

Do not tune from prospective outcomes. The scorer may attach genuine future outcomes without recomputing predictions.

### Long72

- genuine scored events: 2;
- anchor event-balanced MAE 9069.52;
- frozen package MAE 7641.71;
- point gain 1427.80 / 15.74%.

### P9 / P9a

Fresh coverage:

- 168h 5/9 events / 5 clubs;
- 72h 9/7;
- 48h 12/7;
- 24h 15/9.

Full learner remains blocked until 9/9 plus separate precommit.

Expanded source coverage improves future evidence only. Never backfill newly discovered inventory into historical PIT windows.

### P4a

- READY 5;
- labeled READY 2;
- distinct labeled previous-home-spacing values 2;
- gate >=9 labels AND >=3 distinct labeled values;
- trigger false.

### P11a odds

Fresh genuine state:

- raw odds rows: **81**;
- genuine PIT events / clubs: **4 / 4**;
- capture batches: **5**;
- events with >=3 bookmakers: **4**;
- current 24h / 72h / 168h coverage: **3 / 3 / 0**;
- latest capture: `2026-10-25T18:56:51.448Z`;
- model precommitted false;
- target values false;
- production change false.

Capture resilience:

- primary schedule: `17 */6 * * *`;
- fallback schedule: `47 0,6,12,18 * * *`;
- health RPC: `public.p11_market_odds_capture_health_v2()`;
- stale threshold: 270 minutes;
- fallback skips provider work when a fresh primary capture exists;
- recovery run `40223646599` succeeded end to end and the temporary one-shot workflow was removed.

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
- post-hoc tuning on inspected evidence.

The old ChatGPT Beyond readiness automations remain intentionally disabled.
