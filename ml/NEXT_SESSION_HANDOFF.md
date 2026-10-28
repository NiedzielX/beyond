# Beyond Ticketing — Next Session Handoff

Last updated: **2026-10-28**

Status: **CURRENT HANDOFF — QUERY MACHINE STATE FRESH BEFORE ACTING**

Canonical execution plan:

`ml/EXECUTION_PLAN_CURRENT.md`

Canonical strategy:

`ml/MAE_RESEARCH_ROADMAP_V5.md`

Trajectory plan:

`ml/TRAJECTORY_FORECASTING_PLAN_V1.md`

---

# 1. What matters most

Beyond has moved from building P9 infrastructure into **genuine prospective validation**.

At the same time, a new separately versioned R&D direction is accepted:

> **daily full-trajectory forecasting from P-N to kickoff, with simple and sequence models tested in parallel.**

Do not confuse these two jobs:

- protect frozen prospective evidence;
- build new trajectory research without mutating frozen lanes.

---

# 2. Current prospective state

## P9 v1

Historical result:

`NOT_EVALUABLE_PIT_SUPPORT_INSUFFICIENT`

First genuine prospective attempt:

- event443 Cracovia–Motor;
- T-48 cutoff 2026-10-28 17:00 UTC;
- immutable attempt persisted;
- result `PIT_SUPPORT_INSUFFICIENT`;
- 1 genuine attempt;
- 0 predictions;
- 0 scored.

This is correct fail-closed behaviour. Do not lower the support gate and do not retro-predict.

## P9 Family Fallback v2

Precommitted/deployed separately.

Rules:

- exact same v1 five neighbors;
- only Structural fallback when v1 selected D2 and D2 support is insufficient;
- unchanged minimum support;
- no retroactive event443 prediction;
- evidence remains separate from v1.

Latest verified state:

- 0 attempts;
- 0 predictions;
- 0 scored.

## Form5

First legal T-24 capture:

**event443 — 2026-10-29 17:00 UTC**.

## P7

Latest verified:

- 53 immutable prediction rows;
- 6 independent events;
- 0 scored;
- no retuning.

## Long72

Latest verified:

- 5 scored events;
- anchor MAE 6082.40;
- package MAE 6039.39;
- improvement 43.01 / 0.71%;
- low MAE priority;
- frozen.

## P11

Latest verified:

- 6 events / 6 clubs;
- all with >=3 bookmakers;
- T-24/T-72/T-168 = 5/5/0;
- no attendance model fit yet.

## P4a

- 4/9 labeled READY events;
- 3 distinct values;
- event-count gate closed.

---

# 3. Near-term windows to protect

Unless fresh machine state says otherwise:

- event446 Wisła Płock–Piast T-48: 2026-10-29 11:15 UTC;
- event6 Lech–Wisła Kraków T-48: 2026-10-29 16:30 UTC;
- event443 Cracovia–Motor T-24: 2026-10-29 17:00 UTC;
- event444 GKS Katowice–Widzew T-48: 2026-10-29 19:15 UTC;
- event445 Zagłębie–Korona T-48: 2026-10-31 17:00 UTC;
- event447 Raków–Pogoń T-48: 2026-10-31 19:30 UTC.

Event448 remains an inventory watch. Unknown inventory is not zero.

---

# 4. New accepted trajectory direction

Target product/model behaviour:

`P-60 -> P-59 -> ... -> today -> predicted remaining trajectory -> final attendance P10/P50/P90`

Every day should create a new immutable forecast from the complete genuine prefix visible by that cutoff.

This is **daily inference, not daily retuning**.

## Lane A

Simple trajectory residual benchmark:

- level;
- 1d/3d/7d change;
- velocity;
- acceleration;
- slopes;
- volatility;
- curve similarity;
- structural P50 anchor.

## Lane B

Controlled high-risk sequence research:

1. small GRU;
2. small LSTM;
3. small TCN;
4. compact attention/Transformer only if justified.

Start early even with limited labels, but keep it research/shadow only.

Never count multiple prefixes from one event as independent events.

---

# 5. Immediate work order for the next agent

1. Read `ml/EXECUTION_PLAN_CURRENT.md`.
2. Query current P9/P7/Form5/P11 machine state before making assumptions.
3. Protect any imminent prospective window first.
4. Do not modify frozen P9 v1/v2, P7, Form5 or Long72 contracts.
5. If no urgent window is at risk, start/continue Daily Trajectory infrastructure:
   - canonical PIT-safe daily dataset;
   - immutable daily attempts/forecasts;
   - horizon-wise MAE view;
   - data density/missingness audit.
6. Only after the data contract is stable, precommit Lane A and Lane B.
7. Keep sequence and simple-model evaluation on identical event-grouped folds.
8. Begin prospective shadow forecasts before outcomes are known.
9. Keep `live_adjustment=0`.

---

# 6. Rejected lanes

Do not reopen the same exposed mechanisms:

- previous Live Ticketing challenger;
- Match Stakes;
- timing context;
- existing weather point forecast;
- Hype/Attention 48h;
- broad old estimator sweeps.

The daily trajectory program is a new representation/mechanism and is allowed.

---

# 7. Hard safety rules

- no future target trajectory at an earlier cutoff;
- no target attendance during prediction;
- no manufactured history;
- no random daily-row split;
- all prefixes from one event stay together;
- no gate relaxation for coverage;
- no retuning on exposed prospective outcomes;
- no inventory-derived attendance labels;
- no hidden inventory = zero assumption;
- no production activation without explicit reviewed promotion.
