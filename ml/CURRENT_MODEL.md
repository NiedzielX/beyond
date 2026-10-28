# Beyond Ticketing — Current Model & Product State

Last updated: **2026-10-28**

Status: **STRUCTURAL CORE + FROZEN PROSPECTIVE LANES + DAILY TRAJECTORY R&D**

Canonical execution plan:

`ml/EXECUTION_PLAN_CURRENT.md`

Canonical strategy:

`ml/MAE_RESEARCH_ROADMAP_V5.md`

---

# 1. North Star

> **Minimize true prospective event-balanced attendance-forecast MAE at decision-relevant horizons with PIT-safe, reproducible evidence.**

Primary metric:

`Delta MAE = challenger event-balanced MAE - incumbent event-balanced MAE`

Desired:

`Delta MAE < 0`

Production remains:

`live_adjustment = 0`

---

# 2. Structural core

Current structural research champion family remains **Global Model v2.1**.

Foundation:

- 1,530 Ekstraklasa matches;
- complete 2021/22–2025/26 seasons;
- 7,650 historical PIT rows;
- horizons T-30d / T-14d / T-7d / T-3d / T-1d.

Architecture:

`PIT historical state -> club-history baseline -> global residual model -> structural P50`

This structural forecast is the default anchor for incremental trajectory research.

Historical evidence is supporting R&D evidence, not prospective promotion evidence.

---

# 3. P7 prospective

Historical frozen result:

- anchor MAE 7409.79;
- challenger MAE 6339.99;
- point gain 1069.80 / 14.44%;
- 95% event-block CI `[-2566.13,+174.47]`;
- evidence `POINT_GAIN_UNCERTAINTY_LIMITED`.

Latest verified prospective state:

- 53 immutable prediction rows;
- 6 independent events;
- 0 scored.

No retuning. Score genuine outcomes only.

---

# 4. P9 historical v1

Closed:

`NOT_EVALUABLE_PIT_SUPPORT_INSUFFICIENT`

- T-168 gate: 9/9 events / 9 clubs;
- T-24 support-ready: 0/11;
- T-48 support-ready: 0/9;
- no valid historical challenger MAE.

Do not reconstruct/backfill historical incumbents to force a result.

---

# 5. P9 prospective v1

Frozen mechanism:

`PIT booking-curve similarity -> fixed 5 prior curves -> same-family PIT residuals -> median residual -> incumbent correction`

Frozen prediction windows:

- T-48;
- T-24.

First genuine attempt:

- event443 Cracovia–Motor T-48;
- cutoff 2026-10-28 17:00 UTC;
- immutable attempt persisted;
- result `PIT_SUPPORT_INSUFFICIENT`;
- predictions 0;
- scored 0.

This is correct fail-closed behaviour.

---

# 6. P9 Family Fallback v2

Separately precommitted and deployed.

It keeps:

- the exact five v1 neighbors;
- the same minimum support gate;
- the same T-48/T-24 windows.

It may use Structural family only when v1 selected D2 and D2 selected-neighbor support is insufficient.

Latest verified state:

- attempts 0;
- predictions 0;
- scored 0.

Never pool v1/v2 evidence.

---

# 7. Form5 prospective

Frozen prospective T-24 challenger.

Key contract:

- TheSportsDB v1 shadow;
- LOCO primary / LOEO secondary;
- ridge alpha 30;
- +/-25% correction cap;
- 8-event / 5-club / >=2-distinct gate;
- production OFF.

First legal capture:

**event443 — 2026-10-29 17:00 UTC**.

---

# 8. Long72

Frozen / low MAE priority.

Latest verified scored sample:

- 5 events;
- anchor MAE 6082.40;
- package MAE 6039.39;
- improvement 43.01 / 0.71%;
- event improvement rate 60%;
- worst event degradation ~3633.

Do not retune.

---

# 9. P11 / P4a

## P11 odds

Latest verified:

- 6 events / 6 clubs;
- all 6 with >=3 bookmakers;
- T-24/T-72/T-168 coverage = 5/5/0;
- model precommitted false.

Continue append-only genuine capture. No attendance-model fit yet.

## P4a

- 4/9 labeled READY;
- 3 distinct previous-home-spacing values;
- variance gate PASS;
- event-count gate FAIL.

Only genuine labels move the gate.

---

# 10. New daily trajectory R&D

Accepted next-generation model direction:

`P-60 -> P-59 -> ... -> today -> predicted remaining path -> final attendance`

The model should receive the **complete genuine observed prefix** at each daily cutoff.

This is **daily inference, not daily retuning**.

Detailed plan:

`ml/TRAJECTORY_FORECASTING_PLAN_V1.md`

## Required infrastructure

- canonical PIT-safe daily trajectory dataset;
- immutable daily attempt/forecast ledger;
- horizon-wise MAE reporting;
- missingness/coverage audit.

## Lane A

Simple residual trajectory models over the structural incumbent.

## Lane B

Small sequence residual models started early in research/shadow mode:

- GRU;
- LSTM;
- TCN;
- compact Transformer only if justified.

The sequence lane must beat Lane A under identical event-grouped/PIT-safe evaluation before more complexity is justified.

---

# 11. Why daily trajectory is different from the rejected Live Ticketing challenger

The earlier Live Ticketing challenger is rejected on current evidence.

The new program is not a rerun of that mechanism.

It explicitly models:

- the complete observed prefix;
- daily forecast revisions;
- trajectory shape/dynamics;
- sequence representations;
- horizon-wise MAE;
- residual learning over a strong structural anchor.

It therefore receives a new versioned research contract.

---

# 12. Product interpretation

Public inventory remains a **demand/inventory proxy**, not confirmed sales or attendance.

The intended future dashboard model is:

`observed proxy trajectory | today | predicted future proxy trajectory -> final attendance P10/P50/P90`

Do not imply that capacity minus public inventory equals paid ticket sales.

---

# 13. Governance

- event is the independent unit;
- daily prefixes from one event remain grouped;
- no target future trajectory leakage;
- no target outcome leakage;
- no manufactured history;
- prospective evidence outranks favorable historical evidence;
- business minimum meaningful Delta MAE remains to be independently derived;
- no automatic production promotion.

---

# 14. Immediate model decision

> **Keep P7/P9/Form5 prospective evidence frozen and honest. In parallel, build the daily trajectory data/forecast infrastructure and then compare a simple trajectory residual model against a small sequence residual model. Start sequence research early, but keep all evidence safeguards intact.**
