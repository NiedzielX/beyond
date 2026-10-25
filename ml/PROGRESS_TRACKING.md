# Beyond Ticketing — ML Progress Tracking

Last updated: **2026-10-25**

Status: **CANONICAL PLAN / STATUS / TRACKING SNAPSHOT**

Canonical strategy: `ml/MAE_RESEARCH_ROADMAP_V4.md`

Production: `live_adjustment = 0`.

## Current status

| Item | Status | Current decision |
|---|---|---|
| RoboTicket ingestion safety | ✅ **LIVE** | hourly discovery + 10m private buffer + verified promotion/backfill |
| Panel ingestion coverage | ✅ **MAIN / CI PASS** | Overview + Data Quality; completed matches remain visible |
| Long72 prospective evidence | 🟢 **2 genuine scored events** | preserve; no retuning |
| P7 Long168 historical tournament | ✅ **EXECUTED** | 14.44% point gain; exposed; never retune |
| P7 prospective validation | 🟢 **3 immutable predictions / 3 events / 0 scores** | scheduled every 6h; wait for genuine outcomes |
| P9 full-168h Booking Curve | 🟡 **5/9** | learner blocked |
| P9a T-24/T-48 freeze | ✅ COMPLETE | target-free audit frozen |
| P4a previous-home spacing | 🟡 **2/9 labels / 2 distinct labeled** | gate closed |
| P10/P10b | ✅ CLOSED | do not reopen fixed pooled-HGB path |
| P11a PIT odds | 🟢 **2 genuine events** | scheduled accumulation; no model yet |
| P11b price context | 🟢 AS-KNOWN CONTRACT LIVE | no inferred promotion |
| P11c verified absences | 🟡 DATA_BOUND | continue collection |
| P11d weather | ✅ CLOSED / NO UPLIFT | do not repeat same mechanism |
| P11d media attention | 🟡 PROSPECTIVE COLLECTING | wait for variance/coverage |
| Governance v2 | ✅ FRAMEWORK / threshold pending | business ΔMAE still required |
| P12 | 🟡 PRE-PLAN | lower priority |

## Ingestion safety net

Canonical incident/safety document:

`ml/ROBOTICKET_INGESTION_SAFETY_NET_2026-10-25.md`

Live controls:

- `roboticket-discovery-v7` uses same-element eventId/label identity;
- parking/VIP/premium/reserve/non-football products fail closed;
- real unmapped football matches can accumulate private raw inventory before exact kickoff mapping;
- buffer collector requires two recognized football club identities including the home club;
- verified schedule mapping promotes the event and backfills original PIT `captured_at` values;
- discovery cadence: hourly;
- candidate buffer cadence: every 10 minutes;
- client dashboard relations are read-only.

Fresh operational state:

- future `TRACKED`: **11**;
- `TRACKED_NO_SNAPSHOT`: **1** — Wisła Kraków vs Cracovia, event 448; mapped correctly but RoboTicket currently returns zero sectors;
- no genuine football match is silently hanging as an unbuffered candidate;
- early false-positive raw candidate captures remain private and were never promoted into `public.snapshots`.

Round 12 was not fully lost. Genuine pre-kickoff curves were preserved for 5/9 fixtures; the other four were hosted by non-onboarded clubs while our onboarded clubs were away teams.

## P7 Long168 — exposed result

Frozen executor run: `40197742930`.

- frozen events / rows: `10 / 139`;
- strict forward held-out events/folds: `5 / 5`;
- anchor MAE: `7409.7882`;
- selected candidate: `gbr-l1-depth2-n50-lr003`;
- challenger MAE: `6339.9915`;
- point improvement: `1069.7967 / 14.4376%`;
- event/fold improvement rate: `0.8 / 0.8`;
- 95% event-block interval: `[-2566.13, +174.47]`;
- evidence: `POINT_GAIN_UNCERTAINTY_LIMITED`;
- decision: `ADVANCE_RESEARCH`.

Do not rerun or tune the inspected tournament.

## P7 prospective validation — ACTIVE

Precommit:

`ml/P7_LONG168_PROSPECTIVE_PRECOMMIT_V1.md`

Pinned fingerprint:

`70fa929181531276c80a75c0b78a60fb821cf50e714e2bc001de8251cea1793f`

Fingerprint run `40201818862`: **SUCCESS**.

First true prospective run `40216860928`: **SUCCESS**.

Current immutable ledger:

- prediction rows: **3**;
- independent prediction events: **3**;
- scored events: **0**;
- evidence status: `PROSPECTIVE_PREDICTIONS_ONLY`;
- model fingerprint count: 1;
- target values used in prediction: false;
- bootstrap backfill: false;
- production activation allowed: false;
- `live_adjustment=0`.

Persisted event IDs:

- 6 — Lech Poznań vs Wisła Kraków;
- 444 — GKS Katowice vs Widzew Łódź;
- 446 — Wisła Płock vs Piast Gliwice.

Scheduled predict/persist cadence:

`37 */6 * * *`

No score exists yet, so there is nothing to tune or promote.

## Long72

Genuine scored events remain **2**:

- event 10 Pogoń Szczecin vs Radomiak Radom: 19,050;
- event 16 Wisła Kraków vs Raków Częstochowa: 33,000.

Fresh scorer state:

- anchor event-balanced MAE: `9069.5168`;
- frozen package event-balanced MAE: `7641.7132`;
- point improvement: `1427.8036 / 15.7429%`;
- event improvement rate: 1.0;
- newly inserted scores: 0;
- production change: false.

## P9 / P9a — fresh readiness

- 168h: **5 events / 5 clubs**;
- 72h: **9 / 7**;
- 48h: **12 / 7**;
- 24h: **15 / 9**;
- full 168h status: `DATA_BOUND`;
- completed-outcome events visible to readiness: 17;
- learner precommitted: false.

P9a remains target-free and frozen. Do not fit the full P9 learner before 9/9 plus a separate precommit.

## P4a — fresh readiness

- READY events: 5;
- labeled READY events: 2;
- previous-home-spacing distinct values among READY: 4;
- labeled non-null events: 2;
- distinct labeled values: 2;
- required: >=9 labeled AND >=3 distinct labeled values;
- research trigger: false.

## P11a — fresh readiness

- status: `GENUINE_PIT_DATA_ACCUMULATING`;
- events with any genuine PIT 1X2: 2;
- clubs with any: 2;
- events with >=3 bookmakers: 2;
- horizon coverage at the latest check: 24h / 72h / 168h = **1 / 1 / 0**;
- model precommitted: false;
- target values used: false;
- production change: false.

Scheduled capture remains every six hours. The horizon counters are time-relative and can change as events move through the window; use fresh RPC state rather than older documentation values.

## P11b/c/d

- P11b `p11_price_context_as_known_v1(...)`: live, PIT-safe, no synthetic promotion flag;
- P11c: data-bound; missing absence records are not negative evidence;
- P11d weather: existing mechanism `research_only_no_uplift`, closed;
- P11d attention: prospective-only collection continues.

## Governance / P12

- business minimum meaningful ΔMAE remains intentionally unset until independently business-derived;
- P12 remains lower priority than current prospective/data-accumulation lanes.

## Immediate order

`preserve P7 prospective schedule -> preserve RoboTicket safety net -> preserve P11a/P11b/P11d collection -> score Long72/P7 only when genuine outcomes arrive -> accumulate P9 to 9/9 -> accumulate P4a labels -> derive business ΔMAE threshold -> P12 later`

## Closed loops

Do not reopen without a materially new mechanism:

- original P7 tournament;
- P10/P10b;
- P5a shrinkage;
- P6 historical Long72 incremental signal;
- P8 simple calibration;
- existing weather mechanism;
- old estimator sweeps;
- post-hoc tuning on inspected evidence.
