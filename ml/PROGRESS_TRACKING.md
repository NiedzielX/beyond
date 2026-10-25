# Beyond Ticketing — ML Progress Tracking

Last updated: **2026-10-25**

Status: **CANONICAL PLAN / STATUS / TRACKING SNAPSHOT**

Canonical strategy: `ml/MAE_RESEARCH_ROADMAP_V4.md`

Production: `live_adjustment = 0`.

## Current status

| Item | Status | Current decision |
|---|---|---|
| RoboTicket ingestion safety | ✅ LIVE | discovery v8 + hourly scan + 10m private buffer + verified promotion/backfill |
| Stellis source expansion | ✅ LIVE | canonical `stellis_collect_v3` every 10m; five additional home sources monitored |
| Panel ingestion coverage | ✅ MULTI-SOURCE | shared Roboticket + Stellis status contract; Overview + Data Quality |
| Long72 prospective evidence | 🟢 2 genuine scored events | preserve; no retuning |
| P7 Long168 historical tournament | ✅ EXECUTED | 14.44% point gain; exposed; never retune |
| P7 prospective validation | 🟢 3 immutable predictions / 3 events / 0 scores | scheduled every 6h; wait for genuine outcomes |
| P9 full-168h Booking Curve | 🟡 5/9 | learner blocked |
| P9a T-24/T-48 freeze | ✅ COMPLETE | target-free audit frozen |
| P4a previous-home spacing | 🟡 2 labeled / 2 distinct labeled | gate closed |
| P10/P10b | ✅ CLOSED | do not reopen fixed pooled-HGB path |
| P11a PIT odds | 🟢 2 genuine events | scheduled accumulation; no model yet |
| P11b price context | 🟢 AS-KNOWN CONTRACT LIVE | no inferred promotion |
| P11c verified absences | 🟡 DATA_BOUND | continue collection |
| P11d weather | ✅ CLOSED / NO UPLIFT | do not repeat same mechanism |
| P11d media attention | 🟡 PROSPECTIVE COLLECTING | wait for variance/coverage |
| Governance v2 | ✅ FRAMEWORK / threshold pending | business ΔMAE still required |
| P12 | 🟡 PRE-PLAN | lower priority |

## Multi-source ingestion coverage

Canonical docs:

- `ml/ROBOTICKET_INGESTION_SAFETY_NET_2026-10-25.md`
- `ml/TICKETING_SOURCE_COVERAGE_EXPANSION_2026-10-25.md`

### RoboTicket

Live controls:

- `roboticket-discovery-v8`;
- same-element identity;
- parking/VIP/premium/reserve/non-football fail closed;
- raw candidate inventory protected before kickoff mapping;
- verified promotion/backfill;
- discovery hourly;
- raw candidate buffer every 10 minutes.

### Stellis

Canonical collector:

`stellis_collect_v3`

Sources:

- Widzew Łódź;
- Radomiak Radom;
- Piast Gliwice;
- Motor Lublin;
- Korona Kielce.

Cadence:

`3,13,23,33,43,53 * * * *`

Important gates:

- home/away football identity must resolve;
- explicit cup/non-league/friendly signals fail closed;
- latest raw classification wins;
- ticketing source kickoff is canonical for exact time;
- unique league-pair cross-check within +/-4 days;
- hidden inventory is not converted to zero;
- raw evidence is protected before model-facing promotion.

Fresh future state:

- future Roboticket events: **12**, **11 with snapshots**;
- future Stellis canonical events: **1**, **1 with snapshots**;
- total future canonical events: **13**, **12 with snapshots**;
- `TRACKED_NO_SNAPSHOT`: **1** — Wisła Kraków vs Cracovia;
- future protected buffers waiting on fixture confirmation: **2**;
- genuine discovered match without model-safe aggregate inventory: **1**.

Stellis examples:

- event 603 Korona Kielce vs Radomiak Radom: `TRACKED`, 2 snapshots at latest audit;
- Piast Gliwice vs Korona Kielce: raw curve protected while fixture confirmation is pending;
- Radomiak Radom vs Śląsk Wrocław: match discovered, aggregate availability hidden by the active source contract;
- Piast vs Górnik Puchar Polski: `NON_MATCH_EXCLUDED`, no model-facing snapshot.

Shared panel contract:

`public.dashboard_ticketing_ingestion_status_v1`

Status payload:

`dashboard-ticketing-ingestion-status-v2`

The previous round was not fully lost: genuine pre-kickoff curves were preserved for 5/9 fixtures; the other four were hosted by non-onboarded sources.

## P7 Long168 — exposed result

Frozen executor run: `40197742930`.

- frozen events / rows: 10 / 139;
- strict forward held-out events/folds: 5 / 5;
- anchor MAE: 7409.7882;
- selected candidate: `gbr-l1-depth2-n50-lr003`;
- challenger MAE: 6339.9915;
- point improvement: 1069.7967 / 14.4376%;
- event/fold improvement: 0.8 / 0.8;
- 95% event-block interval: `[-2566.13,+174.47]`;
- evidence: `POINT_GAIN_UNCERTAINTY_LIMITED`;
- decision: `ADVANCE_RESEARCH`.

Do not rerun or tune the inspected tournament.

## P7 prospective validation — ACTIVE

Frozen fingerprint:

`70fa929181531276c80a75c0b78a60fb821cf50e714e2bc001de8251cea1793f`

Current immutable ledger:

- prediction rows: **3**;
- independent prediction events: **3**;
- scored events: **0**;
- status: `PROSPECTIVE_PREDICTIONS_ONLY`;
- model fingerprint count: 1;
- target values used: false;
- production activation allowed: false;
- `live_adjustment=0`.

Scheduled cadence:

`37 */6 * * *`

No score exists yet, so there is nothing to tune or promote.

## Long72

Genuine scored events remain **2**:

- event 10 Pogoń Szczecin vs Radomiak Radom: 19,050;
- event 16 Wisła Kraków vs Raków Częstochowa: 33,000.

Point evidence:

- anchor MAE: 9069.5168;
- package MAE: 7641.7132;
- gain: 1427.8036 / 15.7429%.

## P9 / P9a — fresh readiness

- 168h: **5 events / 5 clubs**;
- 72h: **9 / 7**;
- 48h: **12 / 7**;
- 24h: **15 / 9**;
- full status: `DATA_BOUND`;
- completed outcome events visible: 17;
- learner precommitted: false.

Expanded source coverage changes future evidence only. Do not backfill P9 windows.

## P4a

Gate remains closed:

- READY events: 5;
- labeled READY events: 2;
- distinct labeled values: 2;
- required: >=9 labeled AND >=3 distinct labeled values.

## P11a — fresh readiness

- `GENUINE_PIT_DATA_ACCUMULATING`;
- genuine PIT events: 2;
- clubs: 2;
- events with >=3 bookmakers: 2;
- 24h / 72h / 168h coverage: **1 / 1 / 0**;
- model precommitted: false;
- target values used: false;
- production change: false.

Capture cadence remains every six hours.

## P11b/c/d

- P11b `p11_price_context_as_known_v1(...)`: live, PIT-safe, no inferred promotion;
- P11c: data-bound;
- P11d weather: `research_only_no_uplift`, closed;
- P11d attention: prospective-only collection continues.

## Governance / P12

- business minimum meaningful ΔMAE remains intentionally unset;
- P12 remains lower priority than active prospective/data-accumulation lanes.

## Immediate order

`preserve P7 prospective schedule -> preserve/expand multi-source ticketing ingestion -> preserve P11a/P11b/P11d collection -> score Long72/P7 only when genuine outcomes arrive -> accumulate P9 to 9/9 -> accumulate P4a labels -> derive business ΔMAE threshold -> P12 later`

## Closed loops

Do not reopen without a materially new mechanism:

- original P7 tournament;
- P10/P10b;
- P5a;
- P6 historical Long72 incremental signal;
- P8 calibration;
- existing weather mechanism;
- old estimator sweeps;
- post-hoc tuning.
