# Beyond — AI Bootstrap / Read This First

Last updated: **2026-10-25**

## Cold-start order

Read in this order:

1. `ml/NEXT_SESSION_HANDOFF.md`;
2. `ml/EXECUTION_PLAN_CURRENT.md`;
3. `ml/PROGRESS_TRACKING.md`;
4. `ml/MAE_RESEARCH_ROADMAP_V4.md`;
5. `ml/ROBOTICKET_INGESTION_SAFETY_NET_2026-10-25.md`;
6. `ml/P7_LONG168_RESULT_2026-10-25.md`;
7. `ml/P7_LONG168_PROSPECTIVE_PRECOMMIT_V1.md`;
8. `ml/P7_LONG168_PROSPECTIVE_FINGERPRINT_V1.md`;
9. `ml/P9A_FREEZE_AUDIT_2026-10-25.md`;
10. `ml/P11A_FIRST_GENUINE_CAPTURE_2026-10-25.md`;
11. `ml/P11_CONTEXT_AUDIT_2026-10-25.md`.

Do not restart from Roadmap v3. Do not reconstruct frozen experiments from memory.

## North star

> **Minimize true out-of-sample attendance-forecast MAE at decision-relevant horizons using honest PIT-safe, reproducible evidence.**

Current mode: **representation-first, not tuning-first**.

Production remains:

`live_adjustment = 0`

## Immediate order

`preserve P7 prospective schedule -> preserve RoboTicket safety net -> preserve P11 context/odds collection -> score only genuine future outcomes -> accumulate P9 to 9/9 -> accumulate P4a labels -> derive business ΔMAE threshold -> P12 later`

## Current canonical state

### RoboTicket ingestion

Safety net is live:

- discovery v7, hourly;
- private unmapped-match buffer, every 10 minutes;
- football-universe gate;
- fail-closed non-match/non-football exclusions;
- verified promotion + PIT-preserving backfill;
- dashboard monitoring on Overview and Data Quality.

Fresh future state:

- 11 TRACKED;
- 1 TRACKED_NO_SNAPSHOT: Wisła Kraków vs Cracovia, mapped but source currently exposes zero sectors;
- no genuine match silently unbuffered.

Round 12 was not fully lost: 5/9 hosted-by-onboarded-club fixtures have genuine pre-kickoff curves; the other four were hosted by non-onboarded teams.

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

Frozen deterministic fingerprint:

`70fa929181531276c80a75c0b78a60fb821cf50e714e2bc001de8251cea1793f`

First prospective run `40216860928`: SUCCESS.

Current ledger:

- 3 immutable prediction rows;
- 3 independent events;
- 0 scored events;
- `PROSPECTIVE_PREDICTIONS_ONLY`;
- no bootstrap backfill;
- target values not used;
- production activation false.

Events: 6, 444, 446.

Schedule:

`37 */6 * * *`

Do not tune until genuine outcomes arrive, and then do not retune this frozen lane from those outcomes.

### Long72

- genuine scored events: 2;
- anchor event-balanced MAE 9069.52;
- frozen package MAE 7641.71;
- point gain 1427.80 / 15.74%;
- latest refresh added 0 scores.

### P9 / P9a

Fresh coverage:

- 168h 5/9 events / 5 clubs;
- 72h 9/7;
- 48h 12/7;
- 24h 15/9.

Full learner remains blocked until 9/9 plus separate precommit.

### P4a

- READY 5;
- labeled READY 2;
- distinct labeled previous-home-spacing values 2;
- gate >=9 labels AND >=3 distinct labeled values;
- trigger false.

### P11a odds

Fresh readiness:

- genuine PIT events: 2;
- >=3 bookmakers: 2;
- latest time-relative 24h / 72h / 168h coverage: 1 / 1 / 0;
- model precommitted false;
- target values false.

Capture schedule:

`17 */6 * * *`

Never backfill closing odds.

### P11b/c/d

- P11b price as-known contract live; no inferred promotion;
- P11c absences data-bound;
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
