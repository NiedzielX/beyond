# Beyond Ticketing — Current Model & Product State

Last updated: **2026-10-26**

Status: **GLOBAL HISTORICAL CORE + FROZEN PROSPECTIVE EVIDENCE LANES**

Canonical execution plan: `ml/EXECUTION_PLAN_CURRENT.md`

## North Star

> **Minimize true prospective event-balanced attendance-forecast MAE at decision-relevant horizons with PIT-safe, reproducible evidence.**

Primary decision metric:

`ΔMAE = challenger event-balanced MAE - incumbent event-balanced MAE`

Desired direction: `ΔMAE < 0`.

Production remains unchanged:

`live_adjustment = 0`

## 1. Global historical / structural core

Current research champion family remains **Global Model v2.1**.

Foundation:

- 1,530 Ekstraklasa matches across complete 2021/22–2025/26 seasons;
- 7,650 historical PIT snapshots = 1,530 × 5 horizons;
- horizons: T-30d, T-14d, T-7d, T-3d, T-1d.

Architecture:

`PIT historical state -> club-history baseline -> global residual model -> structural P50`

Historical evidence is supporting research evidence, not prospective promotion evidence.

## 2. Final24 / Pre-Live

Final24 remains frozen prospective evidence only:

`Frozen Pre-Live v2 + P2 reliability * frozen ridge-a10 delta`

Frozen Pre-Live v3 remains research-only:

`1934.04 -> 1924.64` historical 20-cell mean MAE, point gain `9.39 / 0.49%`.

No production activation.

## 3. Long72 — frozen prospective lane

Frozen package:

`d2-long72-stage2-p2-observation-maturity-2026-10-21-v1`

Last verified genuine state:

- scored events: **4** — `[10,16,21,23]`;
- anchor event-balanced MAE: **6942.59**;
- package event-balanced MAE: **6824.16**;
- point improvement: **118.43 / 1.71%**;
- event improvement rate: **75%**;
- worst event degradation: **3633.23**.

This is not sufficient promotion evidence. Do not retune, recalibrate or promote.

## 4. P7 Long168 — historical result frozen

Frozen exposed result:

- 10 independent events / 139 rows;
- anchor MAE: 7409.79;
- selected challenger: `gbr-l1-depth2-n50-lr003`;
- challenger MAE: 6339.99;
- point gain: 1069.80 / 14.44%;
- 95% event-block CI: `[-2566.13,+174.47]`;
- evidence: `POINT_GAIN_UNCERTAINTY_LIMITED`.

Do not rerun or retune this tournament.

## 5. P7 Long168 — active prospective validation

Precommit:

`ml/P7_LONG168_PROSPECTIVE_PRECOMMIT_V1.md`

Model fingerprint:

`70fa929181531276c80a75c0b78a60fb821cf50e714e2bc001de8251cea1793f`

Fresh state at 2026-10-26:

- immutable prediction rows: **16**;
- independent prediction events: **3**;
- scored events: **0**;
- evidence: `PROSPECTIVE_PREDICTIONS_ONLY`;
- production activation false.

Collection/scoring only; no tuning.

## 6. P9 Booking Curve — historical v1 closed without MAE result

The historical full-window gate is complete:

- T-168: **9/9 events / 9 clubs**;
- learner design precommitted before evaluation;
- `full_window_gate_open=true`.

Canonical frozen learner:

`p9-knn-median-residual-k5-v1`

Historical execution status:

`NOT_EVALUABLE_PIT_SUPPORT_INSUFFICIENT`

Frozen diagnostic:

- T-24 comparator/support-ready: **11 / 0**;
- T-48 comparator/support-ready: **9 / 0**;
- learner attendance labels opened: false;
- learner result produced: false.

The failure is caused by insufficient same-incumbent-family historical PIT forecast support among the selected booking-curve neighbors. It is **not** a shortage of T-168 booking curves.

No valid historical challenger-vs-incumbent MAE exists for P9 v1.

Do not reconstruct/backfill historical incumbent forecasts to force a result.

Read:

`ml/P9_SUPPORT_POSTMORTEM_2026-10-26.md`

## 7. P9 Booking Curve — active prospective validation

Precommit:

`ml/P9_BOOKING_CURVE_PROSPECTIVE_PRECOMMIT_V1.md`

Mechanism remains frozen:

`PIT booking-curve similarity -> fixed k=5 prior curves -> same-incumbent-family genuine PIT residuals -> median residual -> incumbent P50 correction`

Fixed rules:

- T-48 and T-24 only;
- k=5;
- minimum 3 residual-bearing neighbors;
- no fitted coefficient/intercept/regression;
- no candidate sweep;
- target attendance unavailable during prediction;
- no late bootstrap;
- immutable prediction window = cutoff through cutoff +90m;
- primary metric = prospective event-balanced MAE.

Infrastructure:

- Supabase Edge Function `p9_booking_curve_prospective_v1` deployed;
- GitHub workflow `.github/workflows/p9-booking-curve-prospective-v1.yml`;
- schedule `7,37 * * * *`;
- end-to-end workflow test passed on 2026-10-26.

Current evidence:

- prediction events: **0**;
- prediction rows: **0**;
- scored events: **0**;
- production activation false;
- `live_adjustment=0`.

This is expected before the first prediction window. First T-48 window: **2026-10-28 17:00 UTC**, Cracovia–Motor.

Do not create P9 v2 merely to force a prediction. Consider a new design only after genuine prospective v1 windows demonstrate structural support starvation despite accumulated PIT incumbent history.

Canonical machine state:

- `public.p9_learner_gate_status_v1()`;
- `public.p9_historical_cohort_status_v1()`;
- `public.p9_booking_curve_prospective_summary_v1()`.

Legacy `public.p9_booking_curve_readiness_v1()` is not the canonical learner/precommit source.

## 8. P4a fixture context

Last verified readiness:

- labeled READY events: **4/9**;
- distinct labeled previous-home-spacing values: **3**;
- variance gate: PASS;
- event-count gate: FAIL.

Only genuine future labels move the gate.

## 9. P11 market/context lane

### Odds

Fresh state at 2026-10-26:

- status: `GENUINE_PIT_DATA_ACCUMULATING`;
- genuine PIT events / clubs: **4 / 4**;
- events with >=3 bookmakers: **4**;
- T-24 / T-72 / T-168 coverage: **3 / 3 / 0**;
- model precommitted: false;
- target values used: false;
- production change: false.

Continue append-only capture. Never backfill closing odds.

### Other context

- price as-known remains live;
- absences remain data-bound;
- existing weather mechanism remains closed/no-uplift;
- attention remains prospective collecting.

## 10. Ticketing acquisition safety net

This is evidence infrastructure, not a model improvement by itself.

Last verified current-league source coverage: **18/18 home clubs**.

Preserve:

- fixture watchdog;
- RoboTicket discovery/private buffer/verified promotion;
- Stellis collection;
- original PIT timestamps;
- hidden/unknown availability != zero;
- recent completed-event visibility.

## 11. Panel / research visibility

Canonical P9 dashboard view:

`public.dashboard_p9_mae_status_v1`

It exposes readiness separately from MAE evidence:

- historical 9/9 gate;
- historical NOT_EVALUABLE result;
- T-24/T-48 support counts;
- prospective prediction/scored coverage;
- incumbent/challenger event-balanced MAE;
- ΔMAE;
- event-level downside metrics;
- production guards.

`NiedzielX/BeyondTicketingPanel` Model Lab now includes `P9MaeStatusPanel` based on this view.

## 12. Governance

Promotion must be based on prospective evidence and acceptable event-level risk, not on readiness or a single historical point gain.

Business minimum meaningful ΔMAE remains intentionally unset until independently derived from operational decisions.

P12/new feature families remain behind the active prospective evidence lanes and should be ranked by expected incremental prospective MAE reduction.

## 13. Production boundary

No historical uplift, readiness counter, Long72 point estimate, P7 prediction, P9 prediction or P11 context signal activates production automatically.

Until explicit reviewed promotion:

`live_adjustment = 0`

## Immediate decision

> **Protect the active P7/P9 prospective evidence lanes and the acquisition pipeline. Historical P9 is closed as NOT_EVALUABLE, not waiting for a tenth T-168 event. The next P9 objective is the first immutable prospective T-48/T-24 prediction and, later, a genuine challenger-vs-incumbent ΔMAE.**
