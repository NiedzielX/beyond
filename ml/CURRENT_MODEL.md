# Beyond Ticketing — Current Model & Product State

Last updated: **2026-10-25**

Status: **GLOBAL HISTORICAL CORE + FROZEN LIVE EVIDENCE LANES + REPRESENTATION-FIRST MAE R&D**

Canonical strategy: `ml/MAE_RESEARCH_ROADMAP_V4.md`

## North star

> **Minimize true out-of-sample attendance-forecast MAE at decision-relevant horizons with point-in-time-safe, reproducible evidence.**

Production remains unchanged:

`live_adjustment = 0`

---

# 1. Global historical / structural core

Current research champion family: **Global Model v2.1**.

Data foundation:

- 1,530 Ekstraklasa matches across five complete seasons (2021/22–2025/26);
- 7,650 PIT snapshots = 1,530 matches × 5 horizons;
- horizons: T-30d, T-14d, T-7d, T-3d, T-1d.

Architecture:

`point-in-time historical state -> club-history baseline -> global residual model -> structural P50`

Selected family in the frozen v2.1 historical experiment:

- T-30: HistGradientBoosting;
- T-14: XGBoost;
- T-7: HistGradientBoosting;
- T-3: HistGradientBoosting;
- T-1: HistGradientBoosting.

2024/25 and 2025/26 are already exposed research evidence, not unseen holdouts.

---

# 2. Frozen final24 / Pre-Live evidence lanes

Final24 package:

`Frozen Pre-Live v2 + P2 reliability * frozen ridge-a10 delta`

Status: **immutable / prospective scoring only**.

Frozen Pre-Live v3:

`pre-live-v3-historical-candidate-2026-10-21-v1`

Historical 20-cell mean MAE:

`1934.04 -> 1924.64`, point improvement `9.39 / 0.49%`.

Status: **frozen research candidate, not production**.

---

# 3. Frozen Long72 live package

Package:

`d2-long72-stage2-p2-observation-maturity-2026-10-21-v1`

Scope:

`24 < hours_to_kickoff <= 72`

Architecture:

1. frozen T-3 structural anchor;
2. inventory-linear-extrapolation Stage-1 expert;
3. correction cap ±0.10 occupancy;
4. P2 observation-maturity reliability.

Current genuine prospective state:

- reproducible prediction rows: 90;
- genuine scored events: 2;
- anchor MAE: 9069.52;
- frozen package MAE: 7641.71;
- point improvement: 1427.80 / 15.74%.

Status: **immutable / prospective scoring active**.

Do not retune, calibrate or promote from n=2.

---

# 4. P7 Long168 — executed research lane

Research question:

> Does PIT live-ticket trajectory between 72h and 168h reduce event-balanced MAE beyond the frozen Structural Prior T-7 anchor?

Frozen execution completed on 2026-10-25.

- independent frozen events: 10;
- rows: 139;
- forward held-out events/folds: 5/5;
- anchor MAE: 7409.79;
- best candidate: `gbr-l1-depth2-n50-lr003`;
- challenger MAE: 6339.99;
- point improvement: 1069.80 / 14.44%;
- event/fold improvement rate: 80% / 80%;
- 95% paired event-block interval: `[-2566.13, +174.47]`;
- evidence: `POINT_GAIN_UNCERTAINTY_LIMITED`;
- decision: `ADVANCE_RESEARCH`.

The interval crosses zero and held-out N is only 5. This is promising exposed forward-fold evidence, not robust proof.

Do not tune/rerun the inspected tournament.

Next allowed P7 work: a separately precommitted **prospective validation lane for the already-selected mechanism**, with predictions persisted before future attendance labels are available.

Canonical result:

`ml/P7_LONG168_RESULT_2026-10-25.md`

---

# 5. P9 Booking Curve / trajectory representation

Roadmap v4 makes P9 the highest-priority new live representation.

Core hypothesis:

`PIT trajectory -> normalized curve -> historical similarity -> pickup distribution -> remaining-demand estimate -> structural residual challenger`

Current completed reference coverage:

- 168h: 5/9 events / 5 clubs;
- 72h: 9 / 7;
- 48h: 12 / 7;
- 24h: 15 / 9.

Full-168h learner remains `DATA_BOUND` and is not precommitted.

P9a T-24/T-48 target-free freeze is complete. Labels/model remain closed.

---

# 6. P11 match attractiveness / commercial context

Roadmap order:

1. P11a market-implied match quality / uncertainty;
2. P11b price / promotion;
3. P11c lineup / verified absences;
4. P11d weather / attention / hype.

Canonical family audit:

`ml/P11_CONTEXT_AUDIT_2026-10-25.md`

## P11a — genuine bookmaker PIT data

First genuine capture completed successfully:

- raw append-only rows: 34;
- deterministic matched events: 2;
- both kickoff deltas: 0;
- one unmatched fixture failed closed;
- no target values used;
- production unchanged.

Readiness:

- `GENUINE_PIT_DATA_ACCUMULATING`;
- events with genuine PIT 1X2: 2;
- events with >=3 bookmakers: 2;
- 24h / 72h / 168h coverage: 2 / 1 / 0;
- model precommitted: false.

Scheduled capture is enabled every six hours:

`17 */6 * * *`

Live Edge runtime is version 6 and synchronized with the scheduled-capture config on `main`.

Do not backfill closing odds and do not loosen deterministic mapping because of unmatched fixtures.

Canonical capture evidence:

`ml/P11A_FIRST_GENUINE_CAPTURE_2026-10-25.md`

## P11b — price context

Existing ticket-price and price-area collectors are healthy.

Live PIT-safe contract:

`public.p11_price_context_as_known_v1(ticket_event_id, as_of_at)`

Features include:

- min/median/max positive visible price;
- price-area / price-type counts;
- previous-capture median price and delta;
- visible price-area availability mix;
- explicit observation timestamps.

The function was verified against both current and historical cutoffs. It uses only observations known by `as_of_at` and does not reference attendance outcomes.

Promotion remains explicit-only. No explicit promotion source is connected, therefore promotion stays null and price movement is never reclassified as promotion.

No P11b attendance model is open.

## P11c — verified absences

Existing verified-absence refresh is healthy, but current genuine evidence is only 1 active PIT-valid row / 1 team.

Status: **DATA_BOUND**.

Missing absence records are not interpreted as player availability.

## P11d — weather

The existing weather mechanism has already been researched and is classified:

`research_only_no_uplift`

Do not reopen the same mechanism under a new name.

## P11d — media attention

The prospective-only collector is healthy and historical backfill is forbidden.

Current state:

- >1,000 samples;
- 12 events;
- media attention: `prospective_collecting`;
- mention acceleration: warm-up;
- current headline feature lacks adequate useful variance for evaluation.

Continue collection only.

---

# 7. P4a fixture context

Current previous-home-spacing readiness:

- READY events: 5;
- genuine labels: 2;
- distinct labeled values: 2;
- required: >=9 labeled AND >=3 distinct values.

Gate remains closed.

---

# 8. Validation / governance

Historical/global:

- season-blocked / rolling / expanding origin;
- no future-season rows in earlier folds;
- persisted fold identities;
- random row split forbidden as headline evidence.

Live-ticket:

- event is the independent unit;
- strict forward-event evidence preferred;
- target values remain closed until protocol/identities are frozen where prospective evidence is possible.

Decision vocabulary:

- `NO_RESEARCH_GAIN`;
- `POINT_GAIN_UNCERTAINTY_LIMITED`;
- `ROBUST_RESEARCH_ADVANCE`.

Business threshold framework:

`ml/GOVERNANCE_V2_BUSINESS_DMAE_THRESHOLD.md`

A numeric minimum meaningful ΔMAE remains intentionally unset until independently business-derived.

---

# 9. P12 demand regime

Pre-plan:

`ml/P12_DEMAND_REGIME_AUDIT_PLAN.md`

P12 remains below P9/P11 in priority. Any regime classification must be PIT-safe and frozen before outcome comparison.

---

# 10. Closed loops

Do not reopen without a materially new information mechanism:

- P10/P10b;
- old estimator-only sweeps;
- P5a shrinkage;
- P6 historical Long72 incremental signal;
- P8 simple calibration;
- existing weather mechanism;
- blind post-hoc calibration.

---

# 11. Production boundary

No historical uplift, P7 result, Long72 point gain or P11/P9 context result activates production.

Promotion requires genuine future evidence, reproducible lineage, acceptable bias/tails, meaningful business value and explicit review.

Until then:

`live_adjustment = 0`

## Immediate decision

> **Preserve final24 and Long72 for forward evidence. Preserve the exposed P7 result without post-hoc tuning and precommit a prospective P7 validation lane. Keep P11a/P11b/P11d data accumulating under PIT-safe contracts. Continue P9 to 9/9 and P4a to its genuine label gate. Do not reopen closed weather/P10-style loops.**
