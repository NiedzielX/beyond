# Beyond Ticketing — Current Model & Product State

Last updated: **2026-10-25**

Status: **GLOBAL HISTORICAL CORE + FROZEN LIVE EVIDENCE LANES + ACTIVE PROSPECTIVE VALIDATION**

Canonical strategy: `ml/MAE_RESEARCH_ROADMAP_V4.md`

## North star

> **Minimize true out-of-sample attendance-forecast MAE at decision-relevant horizons with point-in-time-safe, reproducible evidence.**

Production remains unchanged:

`live_adjustment = 0`

## 1. Global historical / structural core

Current research champion family: **Global Model v2.1**.

Foundation:

- 1,530 Ekstraklasa matches across complete 2021/22–2025/26 seasons;
- 7,650 PIT snapshots = 1,530 × 5 horizons;
- horizons: T-30d, T-14d, T-7d, T-3d, T-1d.

Architecture:

`PIT historical state -> club-history baseline -> global residual model -> structural P50`

2024/25 and 2025/26 are exposed research evidence, not unseen holdouts.

## 2. Final24 / Pre-Live

Final24 remains frozen prospective evidence only:

`Frozen Pre-Live v2 + P2 reliability * frozen ridge-a10 delta`

Frozen Pre-Live v3 remains research-only:

`1934.04 -> 1924.64` historical 20-cell mean MAE, point gain `9.39 / 0.49%`.

No production activation.

## 3. Long72

Frozen package:

`d2-long72-stage2-p2-observation-maturity-2026-10-21-v1`

Fresh genuine prospective state:

- scored events: 2;
- anchor event-balanced MAE: 9069.52;
- package event-balanced MAE: 7641.71;
- point improvement: 1427.80 / 15.74%;
- latest refresh added 0 new scores.

Status: **immutable / prospective scoring active**.

Do not retune from n=2.

## 4. P7 Long168 — exposed historical/forward-fold result

Frozen tournament:

- 10 independent events / 139 rows;
- 5 strict forward held-out events/folds;
- anchor MAE: 7409.79;
- selected candidate: `gbr-l1-depth2-n50-lr003`;
- challenger MAE: 6339.99;
- point gain: 1069.80 / 14.44%;
- event/fold improvement: 80% / 80%;
- 95% paired event-block CI: `[-2566.13,+174.47]`;
- evidence: `POINT_GAIN_UNCERTAINTY_LIMITED`;
- decision: `ADVANCE_RESEARCH`.

The original tournament is exposed and must never be retuned/rerun.

## 5. P7 Long168 — active prospective validation

Precommit:

`ml/P7_LONG168_PROSPECTIVE_PRECOMMIT_V1.md`

Pinned training set:

`[1,3,4,5,10,11,15,16,18,19]`, 139 rows.

Training manifest:

`185a9fc90e646bd5fa1bbed3b50c625d65d127a2b2943501761bdfcb89f354ed`

Pinned deterministic model fingerprint:

`70fa929181531276c80a75c0b78a60fb821cf50e714e2bc001de8251cea1793f`

Fingerprint run `40201818862`: SUCCESS.

First true prospective predict/persist run `40216860928`: SUCCESS.

Current immutable evidence ledger:

- prediction rows: 3;
- independent events: 3;
- scored events: 0;
- evidence status: `PROSPECTIVE_PREDICTIONS_ONLY`;
- model fingerprint count: 1;
- bootstrap backfill: false;
- target values used in prediction: false;
- production activation: false.

Persisted event IDs:

- 6 — Lech Poznań vs Wisła Kraków;
- 444 — GKS Katowice vs Widzew Łódź;
- 446 — Wisła Płock vs Piast Gliwice.

Scheduled prediction cadence:

`37 */6 * * *`

Prediction is persisted before outcome. Scoring may only attach a genuine attendance outcome confirmed after `predicted_at` and never recomputes the forecast.

## 6. P9 Booking Curve

Fresh readiness:

- 168h: 5/9 events / 5 clubs;
- 72h: 9 / 7;
- 48h: 12 / 7;
- 24h: 15 / 9;
- full-168h status: `DATA_BOUND`;
- learner precommitted: false.

P9a target-free T-24/T-48 freeze remains complete.

Do not fit/select a full P9 learner before 9/9 plus a separate precommit.

## 7. P11 match attractiveness / commercial context

### P11a odds

Genuine PIT odds capture is active:

- events with genuine PIT 1X2: 2;
- clubs: 2;
- events with >=3 bookmakers: 2;
- latest time-relative horizon coverage 24h / 72h / 168h: 1 / 1 / 0;
- model precommitted: false;
- target values used: false.

Schedule:

`17 */6 * * *`

The most recent audited database capture remains 2026-10-25 13:53 UTC; the next scheduled slot had not yet become due at the latest health check.

Do not backfill closing odds or loosen deterministic mapping.

### P11b price

`public.p11_price_context_as_known_v1(ticket_event_id, as_of_at)` is live and PIT-safe.

No explicit promotion source exists; price movement is not interpreted as promotion.

### P11c absences

Still data-bound. Missing records are not negative evidence.

### P11d weather / attention

- weather: existing mechanism `research_only_no_uplift`, closed;
- media attention: prospective-only collection continues.

## 8. P4a fixture context

Fresh readiness:

- READY events: 5;
- labeled READY events: 2;
- previous-home-spacing distinct READY values: 4;
- distinct labeled values: 2;
- threshold: >=9 labeled AND >=3 distinct labeled values;
- trigger: false.

## 9. RoboTicket ingestion safety net

Canonical document:

`ml/ROBOTICKET_INGESTION_SAFETY_NET_2026-10-25.md`

This is acquisition infrastructure, not a model change.

Live protections:

- same-element discovery v7;
- explicit non-match/non-football exclusions;
- hourly discovery;
- private raw candidate buffering every 10 minutes;
- football-universe gate;
- verified schedule promotion + original-timestamp backfill;
- dashboard ingestion coverage/history.

Fresh state:

- 11 future matches TRACKED;
- one `TRACKED_NO_SNAPSHOT`: Wisła Kraków vs Cracovia, source currently returns zero sectors;
- latest normal collector/discovery/buffer/dashboard cron runs all succeeded;
- false-positive early buffer rows remained private and did not contaminate model-facing snapshots.

## 10. Validation / governance

Historical/global:

- season-blocked / rolling / expanding origin;
- no future-season rows in earlier folds;
- random row split forbidden as headline evidence.

Live-ticket:

- event is the independent unit;
- strict prospective/forward evidence preferred;
- prediction/feature identity must be frozen before target access where possible.

Decision vocabulary:

- `NO_RESEARCH_GAIN`;
- `POINT_GAIN_UNCERTAINTY_LIMITED`;
- `ROBUST_RESEARCH_ADVANCE`.

A numeric minimum meaningful business ΔMAE remains intentionally unset until independently business-derived.

## 11. P12

P12 pre-plan exists but remains lower priority than active prospective and coverage lanes.

## 12. Closed loops

Do not reopen without a materially new mechanism:

- original P7 tournament;
- P10/P10b;
- old estimator sweeps;
- P5a shrinkage;
- P6 historical Long72 incremental signal;
- P8 calibration;
- existing weather mechanism;
- blind post-hoc calibration.

## 13. Production boundary

No historical uplift, Long72 point gain, P7 prospective prediction, P9 representation or P11 context signal activates production automatically.

Until explicit reviewed promotion:

`live_adjustment = 0`

## Immediate decision

> **Keep the P7 prospective lane and ingestion safety net running unchanged. Preserve P11 accumulation and Long72 scoring. Let P9 mature to 9/9 and P4a to its genuine-label gate. Do not tune any exposed lane while waiting for new genuine evidence.**
