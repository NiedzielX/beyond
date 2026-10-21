# Beyond Ticketing — Current Model & Product State

Last updated: **2026-10-21**

Status: **GLOBAL HISTORICAL CORE + FROZEN LIVE EVIDENCE LANES + ACTIVE MAE-FIRST CHALLENGER R&D**

Canonical strategy: `ml/MAE_RESEARCH_ROADMAP_V3.md`

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

**2024/25 and 2025/26 have already been opened and influenced research. For all new challengers they are exposed historical evidence, not unseen holdouts.**

Future challenger selection must increasingly rely on rolling/forward historical folds and genuinely future 2026/27 evidence.

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

# 4. Frozen long72 live package — Evidence Lane

Package:

`d2-long72-stage2-p2-observation-maturity-2026-10-21-v1`

Scope:

`24 < hours_to_kickoff <= 72`

Frozen dataset/anchor:

- 14 events / 130 rows in 0–72h;
- modeling slice 24–72h: 80 rows / 13 events;
- 48–72h: 35 rows / 10 events;
- `0<h<=24 -> T-1`;
- `24<h<=72 -> T-3`;
- future checkpoint use forbidden.

Architecture:

1. frozen T-3 checkpoint anchor;
2. Stage-1 expert `inventory-linear-extrapolation`;
3. correction cap `±0.10` occupancy;
4. Stage-2 `P2-observation-maturity` reliability.

P2 reliability:

- observation #1 `0.25`;
- observation #2 `0.60`;
- observation #3+ `1.00`;
- `60<h<=72` time weight `0.75`;
- `48<h<=60` time weight `0.90`;
- `24<h<=48` time weight `1.00`;
- applied reliability = minimum of observation/time weights.

Historical development performance:

- anchor MAE `3707.14`;
- package MAE `3012.63`;
- improvement `+694.51 / +18.73%`;
- 24–48h uplift `+954.58 / +25.75%`;
- 48–72h uplift `+664.71 / +14.47%`;
- event improvement rate `61.54%`;
- worst event degradation `1488.34`;
- bias `+917.05`.

All of this remains exposed historical research evidence.

Status: **immutable / prospective scoring active**.

---

# 5. Current R&D interpretation

Do not confuse validation with development.

## Evidence Lane

- persist final24 and long72 forecasts forward;
- for long72, materialize the prediction before the attendance label is available;
- attach attendance later without recomputing forecasts;
- report MAE, bands, bias, P90/worst degradation and event improvement rate.

## MAE R&D Lane

Active challengers are built independently from frozen packages.

Priority order:

1. rolling/forward evaluation;
2. MAE-native residual objectives (`q=0.50`, absolute-error losses);
3. event/fixture-block uncertainty around `ΔMAE`;
4. next-fixture / cannibalization context;
5. other PIT-safe context families;
6. forecast combinations;
7. live-ticket residual uplift over the strongest global structural forecast;
8. 72–168h experiment when coverage reaches `N>=9`;
9. club calibration / shrinkage only if it improves cross-club generalization.

---

# 6. Validation rules for new challengers

Historical/global:

- season-blocked / rolling / expanding origin;
- never train an earlier fold with future-season rows;
- persist fold identities;
- report by horizon, season/fold and club;
- random row split is not headline evidence.

Live-ticket:

- complete event is the independent unit;
- LOEO remains a useful diagnostic;
- add forward-event evaluation ordered by kickoff;
- random snapshot split is forbidden as headline evidence.

---

# 7. Context state

Already useful inside the global model:

- attendance/home-demand history;
- opponent demand;
- calendar/seasonality;
- sporting state;
- home–opponent pair history;
- recent-vs-long-run demand trends.

Highest-priority new context hypothesis:

**fixture substitution / cannibalization** — whether proximity and attractiveness of the next home match changes demand for the current match.

Candidate features:

- days to next home match;
- next-opponent attractiveness;
- next-match competition/importance;
- fixture density 7/14/30d;
- previous-home proximity.

Then test verified absences, rivalry/importance, PIT weather forecast and PIT-safe attention/hype signals.

---

# 8. Forecast combination direction

Component sources should be meaningfully different:

- global structural forecast;
- MAE-native residual challenger;
- context challenger;
- live inventory / long72 correction;
- final24 live correction where applicable.

Test in order:

1. mean;
2. median;
3. fixed convex weights;
4. MAE-optimized convex weights learned only inside train folds;
5. regularized stacker only if simpler methods fail.

---

# 9. 72–168h state

Last audited coverage beyond 72h: `8` independent events.

Predeclared research-start floor: `N>=9`.

When reached, freeze the event/as-of set first and open a separate challenger cycle. `N=9` is a start threshold, not proof of adequate sample size.

---

# 10. Production boundary

Historical uplift, LOEO success or a new research champion does not activate production.

Production promotion requires genuine future evidence, reproducible lineage, acceptable bias/tail behavior and explicit review.

Until then:

`live_adjustment = 0`

## Immediate decision

> **Keep final24 and long72 frozen for forward evidence. Do not wait for that evidence to continue development. The active modelling program is MAE-first: forward validation, MAE-aligned losses, PIT-safe context, forecast combinations and incremental live corrections over Global Model v2.1 / the strongest structural forecast.**
