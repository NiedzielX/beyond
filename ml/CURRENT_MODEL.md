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

Later-season historical results:

| Horizon | 2024/25 model MAE | 2025/26 model MAE | Improvement vs club-history baseline |
|---|---:|---:|---:|
| T-30 | 2092.6 | 2061.5 | ~16–22% |
| T-14 | 1998.5 | 1979.6 | ~18–21% |
| T-7 | 1800.5 | 1896.4 | ~22–23% |
| T-3 | 1785.3 | 1851.7 | ~23% |
| T-1 | 1749.6 | 1833.7 | ~24% |

Important evidence rule:

**2024/25 and 2025/26 have already been opened and influenced research. For new challengers they are exposed historical evidence, not unseen holdouts.**

Future challenger decisions must increasingly rely on strict rolling/forward evaluation and genuinely future 2026/27 evidence.

---

# 2. Frozen final24 live package — Evidence Lane

Pre-Live anchor:

`pre-live-v2-historical-candidate-2026-10-18-v1`

Final24 package:

`Frozen Pre-Live v2 + P2 reliability * frozen ridge-a10 delta`

IDs:

- Stage-1 expert `ridge-a10`;
- Stage-2 package `d2-stage2-p2-observation-maturity-2026-10-19-v1`.

Pre-Live v3 T-1 is exactly equivalent to v2 T-1 on the frozen replay (`0.0` seat anchor delta), so no cosmetic retrain is justified.

Status: **immutable / prospective scoring only**.

---

# 3. Frozen Pre-Live v3 research anchor

Freeze:

`pre-live-v3-historical-candidate-2026-10-21-v1`

Only T-30 and T-7 differ from v2. T-14/T-3/T-1 retain the v2 horizon contracts.

Historical 20-cell mean MAE:

`1934.04 -> 1924.64`, improvement `+9.39 / +0.49%`.

Status: **frozen research candidate, not production**.

---

# 4. Frozen Long72 live package — Evidence Lane

Package:

`d2-long72-stage2-p2-observation-maturity-2026-10-21-v1`

Scope:

`24 < hours_to_kickoff <= 72`

Architecture:

1. frozen T-3 checkpoint anchor;
2. Stage-1 expert `inventory-linear-extrapolation`;
3. correction cap `±0.10` occupancy;
4. Stage-2 `P2-observation-maturity` reliability.

Frozen development evidence remains exposed historical research evidence.

Current genuine prospective state:

- reproducible prediction rows: **90**;
- genuine scored events: **2**;
- anchor MAE: **9069.52**;
- frozen package MAE: **7641.71**;
- point improvement: **1427.80 / 15.74%**;
- event improvement rate: 1.0 on n=2.

Status: **immutable / prospective scoring active**.

Interpretation: n=2 is not enough to retune, calibrate, promote or claim robust improvement.

---

# 5. P7 Long168 — executed research lane

Research question:

> Does PIT live-ticket trajectory between 72h and 168h reduce event-balanced MAE beyond the frozen Structural Prior T-7 anchor?

Frozen execution completed on 2026-10-25 after the genuine start gate opened.

Freeze:

- independent events: **10**;
- rows: **139**;
- exact event/as-of identities frozen before model evaluation;
- target values absent from freeze;
- target-attendance invariance PASS;
- no candidate/hyperparameter search added post hoc.

Forward result:

- forward held-out events/folds: **5 / 5**;
- anchor MAE: **7409.79**;
- best candidate: `gbr-l1-depth2-n50-lr003`;
- challenger MAE: **6339.99**;
- point improvement: **1069.80 / 14.44%**;
- event improvement rate: **80%**;
- fold improvement rate: **80%**;
- paired event-block 95% interval for challenger-minus-anchor MAE: **[-2566.13, +174.47]**;
- evidence interpretation: `POINT_GAIN_UNCERTAINTY_LIMITED`;
- research decision: `ADVANCE_RESEARCH`.

The interval crosses zero and the independent held-out sample is only five events. Therefore P7 is **promising exposed forward-fold research**, not robust proof and not a production promotion candidate.

Do not tune/rerun the frozen P7 candidate set after seeing this result. Any continuation requires a separately precommitted follow-up or prospective lane.

Canonical result:

`ml/P7_LONG168_RESULT_2026-10-25.md`

---

# 6. P9 Booking Curve / trajectory representation

Roadmap v4 makes P9 the highest-priority new live representation.

Core hypothesis:

> Compare the observed current-event path with genuinely prior/comparable booking curves at the same point in the window and estimate remaining pickup from historical trajectory shape, instead of relying only on local velocity/acceleration features.

Conceptual pipeline:

`PIT trajectory -> normalized curve -> historical similarity -> pickup distribution -> remaining-demand estimate -> structural residual challenger`

Current completed reference coverage:

- 168h: **5/9 events / 5 clubs**;
- 72h: **9 / 7**;
- 48h: **12 / 7**;
- 24h: **15 / 9**.

Full-168h first learner remains `DATA_BOUND` and is not precommitted.

## P9a target-free freeze

Main T-24/T-48 audit completed on 2026-10-25.

T-24:

- manifest `738a42da33b46361f0ba29d3f90c72e2e0019c0057ef00b78ac7e6a073f0bd1c`;
- representation ready 16;
- freeze ready 12;
- comparator ready 9.

T-48:

- manifest `ffa6dd178332bf328a24fc7ce15ef346214a0037325d7161426f9f96664babd4`;
- representation ready 13;
- freeze ready 10;
- comparator ready 7.

Labels remain closed, no model was trained, no future target trajectory point was used.

Canonical audit:

`ml/P9A_FREEZE_AUDIT_2026-10-25.md`

---

# 7. P11 match attractiveness / commercial context

Roadmap v4 context order:

1. P11a market-implied match quality / uncertainty / stakes;
2. P11b price / promotion context;
3. P11c lineup / star strength / verified absences;
4. P11d weather / attention / hype.

P11a current state:

- DB capture/consensus/readiness contract live;
- `THE_ODDS_API_KEY` configured and verified;
- main-only GitHub OIDC capture authorization works;
- provider adapter tests/type-check pass;
- genuine odds rows: **0**;
- schedule off.

First provider request failed closed with `422 INVALID_COMMENCE_TIME_FROM` because the deployed Edge runtime included milliseconds in the provider cutoff timestamp. No odds rows were inserted.

Corrected source is committed on `main` (`d27d797578f18f09140ccc1723219a3e690d339a`) and CI-green. Runtime inspection after a Dashboard redeploy still showed the pre-fix code, so the remaining P11 blocker is **runtime/source synchronization**, not the provider key.

After runtime sync, perform one genuine capture and audit it before enabling any schedule.

Every P11 family still requires a separate controlled ablation before combination.

---

# 8. P4a fixture context

Current previous-home-spacing readiness:

- READY events: 5;
- genuine labels: **2**;
- distinct labeled values: **2**;
- required: `>=9 labeled AND >=3 distinct values`.

Gate remains closed. Preserve the frozen contract and accumulate genuine labels only.

---

# 9. Validation / governance rules

Historical/global:

- season-blocked / rolling / expanding origin;
- never train earlier folds with future-season rows;
- persist fold identities;
- report by horizon, season/fold and club;
- random row split is not headline evidence.

Live-ticket:

- complete event is the independent unit;
- strict forward-event evaluation is preferred for headline research;
- random snapshot split is forbidden as headline evidence;
- target values remain closed until the experiment identities/protocol are frozen where prospective evidence is possible.

Decision vocabulary:

- `NO_RESEARCH_GAIN`;
- `POINT_GAIN_UNCERTAINTY_LIMITED`;
- `ROBUST_RESEARCH_ADVANCE`.

A business-derived minimum meaningful `ΔMAE` is still required before `ROBUST_RESEARCH_ADVANCE` is available. Never derive that threshold from the challenger result it will judge.

---

# 10. Closed research loops

Do not reopen without a materially new information mechanism:

- P10/P10b fixed pooled-HGB path;
- old estimator-only sweeps;
- P5a shrinkage;
- P6 historical Long72 incremental signal;
- P8 simple club/opponent calibration;
- blind post-hoc calibration.

---

# 11. Production boundary

Historical uplift, P7 research success, Long72 point gains, P9/P11 research or a new research champion do not activate production.

Production promotion requires genuine future evidence, reproducible lineage, acceptable bias/tail behavior, meaningful business value and explicit review.

Until then:

`live_adjustment = 0`

## Immediate decision

> **Keep final24 and Long72 frozen for forward evidence. Preserve the completed P7 result without post-hoc tuning. Complete P11 runtime synchronization so genuine PIT odds can start accumulating, continue P9 full-168h data collection to 9/9, keep P4a data-bound, and use Roadmap v4 representation-first research rather than another broad estimator sweep.**
