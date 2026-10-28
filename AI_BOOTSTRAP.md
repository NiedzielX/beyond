# Beyond — AI Bootstrap / Read This First

Last updated: **2026-10-28**

Status: **CANONICAL AI ENTRYPOINT**

## 1. Cold-start order

Read in this order:

1. `ml/EXECUTION_PLAN_CURRENT.md`;
2. `ml/NEXT_SESSION_HANDOFF.md`;
3. `ml/MAE_RESEARCH_ROADMAP_V5.md`;
4. `ml/TRAJECTORY_FORECASTING_PLAN_V1.md`;
5. `ml/CURRENT_MODEL.md`;
6. `ml/PROGRESS_TRACKING.md`;
7. `ml/MODEL_ACCURACY_DEVELOPMENT_INSTRUCTIONS_V3.md`.

Then read the exact precommit for any frozen experiment you are about to touch.

Do not restart from Roadmap v3/v4.

Always query machine/live state fresh before changing operational assumptions. Do not reconstruct frozen experiments from memory.

---

## 2. North Star

> **Minimize true prospective event-balanced attendance-forecast MAE at decision-relevant horizons using PIT-safe, reproducible evidence.**

Primary metric:

`Delta MAE = challenger event-balanced MAE - incumbent event-balanced MAE`

Desired:

`Delta MAE < 0`

Readiness, snapshot counts, trajectory rows, support counts, odds rows and prediction rows are prerequisites, not model success.

Production remains:

`live_adjustment = 0`

---

## 3. Current execution mode

Beyond is in **prospective validation + trajectory capability build** mode.

Do both in parallel:

### Protect frozen evidence

- P7 prospective: collect/score only;
- P9 v1: protect every T-48/T-24 window;
- P9 Family Fallback v2: run separately, never pool with v1;
- Form5: protect genuine T-24 captures;
- Long72: frozen / low MAE priority;
- P11/P4a: genuine evidence accumulation only.

### Build next-generation trajectory research

Start now:

1. canonical daily trajectory dataset;
2. immutable daily forecast/attempt ledger;
3. horizon-wise MAE reporting;
4. Lane A simple trajectory challenger;
5. Lane B small sequence challenger;
6. self-supervised trajectory representation research where useful.

Target behaviour:

`P-60 -> P-59 -> ... -> today -> predicted remaining path -> final attendance`

This is **daily inference, not daily retuning**.

---

## 4. Accepted model-risk decision

Do **not** wait for a conventionally large labeled dataset before testing sequence models.

Accepted:

- early research with small GRU/LSTM/TCN models;
- later compact attention/Transformer only if simpler sequence models show promise;
- self-supervised/target-free trajectory pretraining;
- residual prediction over the structural incumbent.

Not accepted:

- random daily-row splits;
- treating prefixes as independent events;
- future target trajectory leakage;
- outcome leakage;
- retuning frozen challengers on exposed prospective outcomes;
- using complexity as a success metric.

Research risk is allowed. Evidence shortcuts are not.

---

## 5. Current key state

### P9 historical v1

Closed:

`NOT_EVALUABLE_PIT_SUPPORT_INSUFFICIENT`

- T-168: 9/9 events / 9 clubs;
- no valid historical challenger MAE;
- do not retrospectively repair/backfill.

### P9 prospective v1

First genuine attempt:

- event443 Cracovia–Motor T-48;
- cutoff 2026-10-28 17:00 UTC;
- result `PIT_SUPPORT_INSUFFICIENT`;
- correct fail-closed;
- 1 genuine attempt / 0 predictions / 0 scored.

Do not relax support.

### P9 Family Fallback v2

Precommitted/deployed separately.

It may only use Structural fallback on the same exact v1 neighbors when the frozen v1 D2 family lacks the unchanged minimum support.

Never retro-predict event443 and never merge v1/v2 evidence.

### Form5

First legal T-24 capture:

**event443 — 2026-10-29 17:00 UTC**.

### P7

Latest verified handoff:

- 53 immutable rows;
- 6 events;
- 0 scored;
- no retuning.

### Long72

Latest verified:

- 5 scored events;
- MAE 6082.40 -> 6039.39;
- 43.01 / 0.71% improvement;
- low priority;
- frozen.

### P11

Latest verified:

- 6 events / 6 clubs;
- >=3 bookmakers on all 6;
- T-24 / T-72 / T-168 = 5 / 5 / 0;
- no model fit yet.

---

## 6. Near-term protected windows

Protect these unless fresh machine state says otherwise:

- event446 Wisła Płock–Piast T-48: 2026-10-29 11:15 UTC;
- event6 Lech–Wisła Kraków T-48: 2026-10-29 16:30 UTC;
- event443 Cracovia–Motor T-24: 2026-10-29 17:00 UTC;
- event444 GKS Katowice–Widzew T-48: 2026-10-29 19:15 UTC;
- event445 Zagłębie–Korona T-48: 2026-10-31 17:00 UTC;
- event447 Raków–Pogoń T-48: 2026-10-31 19:30 UTC.

Event448 remains a genuine inventory watch. Unknown inventory is not zero.

---

## 7. Rejected lanes

Do not reopen on the same outcomes without a materially new mechanism:

- previous Live Ticketing challenger;
- Sporting Match Stakes;
- timing context candidate;
- existing weather point-forecast mechanism;
- Hype/Attention 48h;
- old estimator sweeps/post-hoc tuning.

The new daily trajectory program is allowed because it is a materially different representation/mechanism.

---

## 8. Hard rules

- protect genuine prospective windows before lower-priority research work;
- never lower a gate just to get coverage;
- never manufacture PIT history;
- never infer attendance from inventory/capacity/model output;
- never treat hidden inventory as zero;
- never treat daily prefixes as independent events;
- keep all prefixes from one event in one fold;
- persist forecasts before outcomes;
- keep frozen learners separately auditable;
- query machine state fresh;
- keep `live_adjustment=0` until explicit reviewed promotion.
