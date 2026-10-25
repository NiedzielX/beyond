# Beyond Ticketing — ML Progress Tracking

Last updated: **2026-10-25**

Status: **CANONICAL PLAN / STATUS / TRACKING SNAPSHOT**

Canonical strategy: `ml/MAE_RESEARCH_ROADMAP_V4.md`

Production: `live_adjustment = 0`.

## Current status

| Item | Status | Current decision |
|---|---|---|
| Multi-source ticketing coverage | ✅ **18/18 LEAGUE HOME CLUBS** | preserve source coverage; hidden inventory stays fail closed |
| RoboTicket ingestion safety | ✅ LIVE | hourly discovery + 10m private buffer + verified promotion/backfill |
| Stellis source expansion | ✅ LIVE | canonical `stellis_collect_v3` every 10m; five additional home sources monitored |
| Panel ingestion coverage | ✅ MULTI-SOURCE | shared RoboTicket + Stellis status contract; Overview + Data Quality + recent completed events |
| Long72 prospective evidence | 🟢 **4 genuine scored events** | current point gain only 118.43 MAE / 1.71%; preserve freeze; no retuning |
| P7 Long168 historical tournament | ✅ EXECUTED | 14.44% point gain; exposed; never retune |
| P7 prospective validation | 🟢 **6 immutable rows / 3 events / 0 scores** | six-hour predict/persist/score workflow validated end to end |
| P9 full-168h Booking Curve | 🟡 **7/9** | learner still blocked; two more independent full-window labeled events required |
| P9a T-24/T-48 freeze | ✅ COMPLETE | target-free audit frozen |
| P4a previous-home spacing | 🟡 **4 labeled / 3 distinct labeled** | variance gate satisfied; event-count gate still 4/9 |
| P10/P10b | ✅ CLOSED | do not reopen fixed pooled-HGB path |
| P11a PIT odds | 🟢 **81 rows / 4 events / 5 batches** | primary + health-guarded fallback capture; no model yet |
| P11b price context | 🟢 AS-KNOWN CONTRACT LIVE | no inferred promotion |
| P11c verified absences | 🟡 DATA_BOUND | continue collection |
| P11d weather | ✅ CLOSED / NO UPLIFT | do not repeat same mechanism |
| P11d media attention | 🟡 PROSPECTIVE COLLECTING | wait for variance/coverage |
| Governance v2 | ✅ FRAMEWORK / threshold pending | business ΔMAE still required |
| P12 | 🟡 PRE-PLAN | lower priority |

## 2026-10-25 genuine outcome update

Two additional genuine reported attendances were added after the matches completed:

- event 21 — Jagiellonia Białystok vs Wisła Płock: **17,021**;
- event 23 — Śląsk Wrocław vs Wieczysta Kraków: **12,391**.

Both were sourced from published post-match reports. No inventory-derived attendance estimate was used.

Immediate effect:

- P9 T-168 readiness: **5/9 -> 7/9**;
- P9 T-72 readiness: **9 -> 11 events**;
- P9 T-48 readiness: **12 -> 14 events**;
- P9 T-24 readiness: **15 -> 17 events**;
- P4a labeled READY events: **2 -> 4**;
- P4a distinct labeled previous-home-spacing values: **2 -> 3**;
- Long72 genuine scored events: **2 -> 4**.

Event 22 — Legia Warszawa vs Lech Poznań — has completed, but its attendance has not yet been added because a sufficiently reliable published attendance value has not been confirmed. Do not estimate it from ticket inventory.

## Multi-source ingestion coverage

Canonical docs:

- `ml/ROBOTICKET_INGESTION_SAFETY_NET_2026-10-25.md`
- `ml/TICKETING_SOURCE_COVERAGE_EXPANSION_2026-10-25.md`

### League coverage

Alias-resolved audit against the current 2026/27 Ekstraklasa home-club universe:

- league clubs: **18**;
- covered by at least one active ticketing source: **18**;
- uncovered: **0**.

Coverage means the club has an active acquisition path. It does not mean every future event already exposes model-safe inventory. Hidden inventory, unpublished products and ambiguous fixture mappings remain explicit fail-closed states.

### RoboTicket

Live controls:

- same-element identity and hardened match classification;
- parking/VIP/premium/reserve/non-football fail closed;
- raw candidate inventory protected before kickoff mapping;
- football-universe gate;
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

Shared panel contract:

`public.dashboard_ticketing_ingestion_status_v1`

Status payload:

`dashboard-ticketing-ingestion-status-v2`

The panel shows future tracked events, protected buffers, ingestion gaps and recent completed matches. The schedule watchdog surfaces future `SCHEDULE_GAP` fixtures before ticket products are available, which is the intended early-warning behavior.

Known source-side exception:

- Wisła Kraków vs Cracovia is correctly mapped, but RoboTicket currently returns no readable sectors; do not create a fake zero snapshot.

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

## P7 prospective validation — ACTIVE / SCHEDULED

Frozen fingerprint:

`70fa929181531276c80a75c0b78a60fb821cf50e714e2bc001de8251cea1793f`

Current immutable ledger:

- prediction rows: **6**;
- independent prediction events: **3**;
- scored events: **0**;
- status: `PROSPECTIVE_PREDICTIONS_ONLY`;
- model fingerprint count: 1;
- target values used: false;
- production activation allowed: false;
- `live_adjustment=0`.

Actual GitHub Actions schedule:

`37 */6 * * *`

No score exists yet, so there is nothing to tune or promote.

## Long72 — 4 genuine prospective events

Genuine scored events now include events **10, 16, 21 and 23**.

Current frozen package evidence:

- anchor event-balanced MAE: **6942.59**;
- package event-balanced MAE: **6824.16**;
- point improvement: **118.43 MAE / 1.71%**;
- event improvement rate: **75%**;
- event-balanced bias: **-712.84**;
- worst event degradation: **3633.23**.

By band:

- 24–48h: package is **5.00 MAE worse** than anchor;
- 48–72h: package improves MAE by **241.87**.

This is materially weaker than the earlier n=2 point result. Preserve the frozen package and continue prospective scoring. **Do not retune, recalibrate or promote from n=4.**

## P9 / P9a — fresh readiness

- 168h: **7 events / 7 clubs**;
- 72h: **11 / 9**;
- 48h: **14 / 9**;
- 24h: **17 / 10**;
- full status: `DATA_BOUND`;
- completed outcome events visible: **19**;
- learner precommitted: false.

Full P9 remains closed until the precommitted 9-event full-168h threshold is reached and a separate learner precommit is frozen.

Expanded source coverage changes future evidence only. Do not backfill P9 windows.

## P4a

Gate remains closed, but the variance condition is now satisfied:

- READY events: 5;
- labeled READY events: **4/9**;
- distinct labeled previous-home-spacing values: **3**;
- required: >=9 labeled AND >=3 distinct labeled values;
- distinct-value condition: **PASS**;
- event-count condition: **FAIL (4/9)**.

Do not open model results before 9 labeled events.

## P11a — ACTIVE / RESILIENT

Fresh state after recovery run `40223646599`:

- raw append-only odds rows: **81**;
- genuine PIT events / clubs: **4 / 4**;
- capture batches: **5**;
- >=3 bookmaker events: **4**;
- 24h / 72h / 168h coverage: **3 / 3 / 0**;
- latest capture: `2026-10-25T18:56:51.448Z`;
- health after capture: `capture_due=false`;
- model precommitted: false;
- target values used: false;
- production change: false.

Capture resilience:

- primary schedule: `17 */6 * * *`;
- fallback schedule: `47 0,6,12,18 * * *`;
- stale threshold: 270 minutes.

Do not backfill closing odds.

## P11b/c/d

- P11b `p11_price_context_as_known_v1(...)`: live, PIT-safe, no inferred promotion;
- P11c: data-bound;
- P11d weather: `research_only_no_uplift`, closed;
- P11d attention: prospective-only collection continues.

## Governance / P12

- business minimum meaningful ΔMAE remains intentionally unset;
- P12 remains lower priority than active prospective/data-accumulation lanes.

## Immediate order

`preserve P7 prospective schedule -> preserve 18/18 multi-source ticketing ingestion -> preserve resilient P11a/P11b/P11d collection -> obtain only genuine post-match labels -> P9 7/9 -> P4a 4/9 -> score Long72/P7 only when genuine outcomes arrive -> derive business ΔMAE threshold -> P12 later`

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
