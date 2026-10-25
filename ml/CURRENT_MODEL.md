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

## 3. Long72 — frozen prospective lane

Frozen package:

`d2-long72-stage2-p2-observation-maturity-2026-10-21-v1`

Current genuine prospective state:

- scored events: **4** — events `[10,16,21,23]`;
- anchor event-balanced MAE: **6942.59**;
- package event-balanced MAE: **6824.16**;
- point improvement: **118.43 / 1.71%**;
- event improvement rate: **75%**;
- package event-balanced bias: **-712.84**;
- worst event degradation: **3633.23**.

By horizon band:

- 24–48h: package is about **5 MAE worse** than anchor;
- 48–72h: package improves by about **241.85 MAE**.

The n=4 evidence is materially weaker than the earlier n=2 point estimate. Status remains **immutable / prospective scoring active**.

Do not retune, recalibrate or promote.

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

Current immutable evidence ledger:

- prediction rows: **6**;
- independent events: **3**;
- scored events: **0**;
- evidence status: `PROSPECTIVE_PREDICTIONS_ONLY`;
- model fingerprint count: 1;
- bootstrap backfill: false;
- target values used in prediction: false;
- production activation: false.

Scheduled prediction cadence:

`37 */6 * * *`

Prediction is persisted before outcome. Scoring may only attach a genuine attendance outcome confirmed after `predicted_at` and never recomputes the forecast.

## 6. P9 Booking Curve — 8/9 and design frozen before ninth label

Fresh readiness:

- 168h: **8/9 events / 8 clubs**;
- 72h: **12 / 10**;
- 48h: **15 / 10**;
- 24h: **18 / 11**;
- full-168h status: `DATA_BOUND`.

Full-window event IDs:

`[5,10,15,18,19,20,21,23]`

Event 20 — Wisła Płock vs Radomiak Radom — supplied the eighth genuine full-window label with reported attendance **5,014**.

Event 22 — Legia Warszawa vs Lech Poznań — is technically full-window ready but still has no trusted attendance label. Its 6–168h curve contains about 648 snapshots and the maximum gap is only about 0.25h. Do not estimate attendance from inventory.

Events 3 and 4 remain correctly excluded because their maximum 6–168h gaps exceed the frozen 12h quality ceiling. Do not relax the rule.

### P9a representation freeze

Target-free T-24/T-48 representation audit remains complete.

Canonical representation:

`ml/p9_booking_curve_v1.py`

Core rules:

- canonical hours: `168,144,120,96,72,60,48,36,24,18,12,6`;
- max interpolation gap: 12h;
- min overlap: 3 canonical points;
- weighted-L1 distance;
- fixed default neighbors: 5;
- target future trajectory points forbidden.

### P9 learner design precommitted before ninth label

Canonical precommit:

`ml/P9_BOOKING_CURVE_LEARNER_PRECOMMIT_V1.md`

Precommit ID:

`p9-knn-median-residual-k5-v1`

Frozen v1 mechanism:

`PIT booking-curve similarity -> fixed 5 nearest completed curves -> same-incumbent-family historical residuals -> median residual -> incumbent P50 correction`

Rules:

- cutoffs T-48 and T-24 only;
- fixed `k=5`;
- minimum 3 residual-bearing neighbors;
- no fitted scaling coefficient;
- no intercept;
- no regression model;
- no candidate/hyperparameter sweep;
- final clipping only to `[0, verified_stadium_capacity]`;
- primary metric = event-balanced MAE across both fixed cutoffs.

Machine status:

`public.p9_learner_gate_status_v1()`

Current state:

- `design_precommitted=true`;
- `readiness_168_events=8`;
- `readiness_168_clubs=8`;
- `full_window_gate_open=false`;
- `registered_target_free_manifests=0`;
- `labels_export_allowed=false`;
- `model_results_opened=false`;
- `production_activation_allowed=false`.

Hard enforced order when 9/9 arrives:

1. export target-free P9a T-48/T-24 inputs;
2. freeze representation/reference identities;
3. register immutable P9a manifest;
4. export target-free incumbent catalog;
5. freeze exact target/reference incumbent identities with `ml/p9_learner_support_freeze_v1.py`;
6. register immutable support manifest;
7. only then export labels through `public.export_p9_learner_labels_v2(...)`;
8. run fixed `ml/p9_booking_curve_learner_v1.py`;
9. report all frozen metrics without post-result tuning.

At 8/9, freeze registration, incumbent-catalog export and v2 label export have all been negative-tested and rejected. Both freeze registries remain empty.

P9 learner CI run `40225788533`: **SUCCESS**.

## 7. P4a fixture context

Fresh readiness:

- READY events: 5;
- labeled READY events: **4/9**;
- distinct labeled previous-home-spacing values: **3**;
- distinct-value requirement: PASS;
- event-count requirement: FAIL;
- trigger: false.

Do not open model results before 9 labeled events.

## 8. P11 match attractiveness / commercial context

### P11a odds

Genuine PIT odds capture remains active and resilient:

- raw append-only bookmaker rows: **81**;
- genuine PIT events / clubs: **4 / 4**;
- capture batches: **5**;
- events with >=3 bookmakers: **4**;
- 24h / 72h / 168h coverage: **3 / 3 / 0**;
- latest audited capture: `2026-10-25T18:56:51.448Z`;
- model precommitted: false;
- target values used: false;
- production change: false.

Schedules:

- primary: `17 */6 * * *`;
- fallback: `47 0,6,12,18 * * *`;
- stale threshold: 270 minutes.

Do not backfill closing odds or loosen deterministic mapping.

### P11b price

`public.p11_price_context_as_known_v1(ticket_event_id, as_of_at)` is live and PIT-safe.

No explicit promotion source exists; price movement is not interpreted as promotion.

### P11c absences

Still data-bound. Missing records are not negative evidence.

### P11d weather / attention

- weather: existing mechanism `research_only_no_uplift`, closed;
- media attention: prospective-only collection continues.

## 9. Multi-source ticketing ingestion safety net

This is acquisition infrastructure, not a model change.

League source coverage:

- current Ekstraklasa home clubs: **18**;
- covered by at least one active ticketing source: **18**;
- uncovered: **0**.

### RoboTicket

Live protections:

- hardened same-element event identity;
- explicit parking/VIP/premium/reserve/non-football exclusions;
- hourly discovery;
- private raw candidate buffer every 10 minutes;
- football-universe gate;
- verified schedule promotion;
- original PIT timestamps retained when candidate-buffer rows are promoted.

### Stellis

Canonical collector:

`stellis_collect_v3`

Active sources:

- Widzew Łódź;
- Radomiak Radom;
- Piast Gliwice;
- Motor Lublin;
- Korona Kielce.

Hidden/ambiguous inventory remains fail closed.

### Panel / schedule watchdog

Panel-facing shared contract:

`public.dashboard_ticketing_ingestion_status_v1`

Panel repo:

`NiedzielX/BeyondTicketingPanel`

Panel displays tracked events, protected buffers, schedule gaps, source family and recent completed matches. Events have `Nadchodzące / Zakończone / Wszystkie`, avoiding the false impression that completed curves disappeared.

Schedule-gap UI CI is green on main.

## 10. Validation / governance

Historical/global:

- season-blocked / rolling / expanding origin;
- no future-season rows in earlier folds;
- random row split forbidden as headline evidence.

Live-ticket:

- event is the independent unit;
- strict prospective/forward evidence preferred;
- prediction/feature identity frozen before target access whenever possible.

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

No historical uplift, Long72 point gain, P7 prospective prediction, P9 representation/result or P11 context signal activates production automatically.

Until explicit reviewed promotion:

`live_adjustment = 0`

## Immediate decision

> **Protect the now-complete 18/18 ticketing acquisition coverage and keep P7/P11 prospective lanes running unchanged. P9 is the nearest research gate at 8/9; its learner is already frozen and all label paths are hard-blocked until a genuine ninth full-window label plus target-free identity freezes exist. Continue Long72 and P4a only with genuine labels. Do not tune any exposed lane while waiting for new evidence.**
