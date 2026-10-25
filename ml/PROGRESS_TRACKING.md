# Beyond Ticketing — ML Progress Tracking

Last updated: **2026-10-25 11:55 Europe/Warsaw**

Status: **CANONICAL PLAN / STATUS / TRACKING SNAPSHOT**

Canonical strategy: `ml/MAE_RESEARCH_ROADMAP_V4.md`

Operational handoff: `ml/NEXT_SESSION_HANDOFF.md`

Current execution order: `ml/EXECUTION_PLAN_CURRENT.md`

## North star

> **Minimize true out-of-sample attendance-forecast MAE at decision-relevant horizons with PIT-safe, reproducible evidence.**

Production: `live_adjustment = 0`.

## Current status

| Item | Status | Current decision |
|---|---|---|
| Branch reconciliation | ✅ DONE | main/active history reconciled; P9a/P11a source already on main |
| Long72 prospective evidence | 🟢 **2 genuine scored events** | preserve evidence, collect more, no retuning |
| P4a previous-home spacing | 🟡 **2/9 genuine labels** | gate closed; needs >=9 labels + >=3 distinct labeled values |
| P7 Long168 | 🟢 **10/9 — GATE OPEN** | run frozen executor exactly as precommitted |
| P9 full-168h Booking Curve | 🟡 **5/9** | continue collection; learner blocked |
| P9a T-24/T-48 freeze | 🟡 READY | run/verify main manifests; labels/model remain closed |
| P10/P10b | ✅ CLOSED | do not retune fixed pooled-HGB path |
| P11a PIT odds | 🟠 **ACTIVE v2 / 0 genuine rows** | first manual capture is immediate priority |
| Governance v2 | ✅ IMPLEMENTED / threshold pending | robust state unavailable until business ΔMAE threshold exists |
| Production | ⛔ UNCHANGED | `live_adjustment = 0` |

## Genuine outcome update — 2026-10-25

The hourly outcome sync was healthy, but its upstream attendance source had not yet published/ingested the 24.10 outcomes for the first post-freeze Long72 events.

Verified genuine attendance from `frekwencyjny.pl`, consistent with the source used by existing canonical outcomes:

- event 10 — Pogoń Szczecin vs Radomiak Radom: **19,050**;
- event 16 — Wisła Kraków vs Raków Częstochowa: **33,000**.

Inserted into `public.ticket_event_outcomes` at approximately `2026-10-25 10:54 UTC` as `reported_match_attendance`.

No synthetic or estimated target was used.

## Long72 first prospective score

Existing frozen scorer executed after outcome insertion.

Result:

- scored events: **2**;
- anchor event-balanced MAE: `9069.5168`;
- frozen package event-balanced MAE: `7641.7132`;
- point MAE improvement: `1427.8036`;
- relative point improvement: `15.7429%`;
- event improvement rate: `1.0`;
- production change: false.

Evidence classification: **first prospective observations only**. Sample n=2 is insufficient for promotion, redesign, calibration or robust inference.

## Fresh readiness — 2026-10-25 10:54 UTC

### Long72

- reproducible rows: **90**;
- genuine scored events: **2**;
- first score trigger: true.

### P7 Long168

- rows >72h: **139**;
- independent eligible events: **10**;
- threshold: 9;
- start trigger: **true**.

This unlock came from genuine completed outcomes for events 10 and 16. Event 6 is no longer required for the start gate.

Next action: manual `P7 Long168 Executor v1` dispatch on `main` with `mode=execute`. Do not change the frozen candidate set or thresholds before execution.

### P9 booking curve

- 168h: **5 events / 5 clubs**;
- 72h: **9 events / 7 clubs**;
- 48h: **12 events / 7 clubs**;
- 24h: **15 events / 9 clubs**;
- full 168h model status: `DATA_BOUND`;
- learner precommitted: false.

### P4a

- READY events: 5;
- genuine labeled READY events: **2**;
- labeled previous-home-spacing events: 2;
- distinct labeled values: **2**;
- research trigger: false.

## P11a v2

Live:

- DB capture/readiness/consensus contract;
- Edge Function `p11_odds_capture_v2` ACTIVE v2;
- workflow on main;
- schedule off.

Still missing:

- first genuine bookmaker quote rows;
- first audited capture.

Immediate manual action:

`Actions -> P11 Odds Capture v2 -> Run workflow -> main -> capture=true`

The workflow verifies `THE_ODDS_API_KEY` and fails closed if missing.

Do not enable schedule before audit.

## P9a freeze

Keep:

- target-free export only;
- no post-cutoff target snapshots;
- `target_values_opened=false`;
- `model_training_performed=false`.

After P11/P7, run the canonical main T-24/T-48 freeze audit and persist/check manifest SHAs.

## Governance

Closed loops remain closed: P10/P10b, P5a, P6 historical Long72, P8 simple calibration, old estimator sweeps.

Business minimum meaningful `ΔMAE` is still intentionally undefined. Do not infer it from the first two genuine scores.
