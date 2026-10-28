# Beyond Agent Instructions

Last updated: **2026-10-28**

For any Beyond forecasting / ML / Demand Engine task:

1. **Read `AI_BOOTSTRAP.md` first.**
2. Read `ml/EXECUTION_PLAN_CURRENT.md`.
3. Read `ml/NEXT_SESSION_HANDOFF.md`.
4. Read `ml/MAE_RESEARCH_ROADMAP_V5.md`.
5. Read `ml/TRAJECTORY_FORECASTING_PLAN_V1.md` for trajectory work.
6. Read `ml/CURRENT_MODEL.md` and `ml/PROGRESS_TRACKING.md` for the latest recorded state.
7. Read `ml/MODEL_ACCURACY_DEVELOPMENT_INSTRUCTIONS_V3.md` before model-development work.
8. Read the exact precommit before touching any frozen experiment.
9. Query live/machine state fresh before acting on a data gate or scheduled window.
10. Never rebuild frozen history merely to recover context.
11. Never store secrets/tokens/service-role keys in repository files.

Do **not** restart from Roadmap v3/v4. Roadmap v5 is canonical.

---

## Core principle

> **The objective is lower true prospective event-balanced MAE, not model complexity.**

Current phase:

**protect genuine prospective evidence + build daily trajectory capability in parallel.**

Production remains:

`live_adjustment = 0`

No research result activates production automatically.

---

## Current research mode

### Protect frozen/precommitted evidence

Do not mutate these contracts after their relevant outcomes are exposed:

- P7 prospective;
- P9 v1;
- P9 Family Fallback v2;
- Form5 prospective;
- Long72 frozen package;
- P11/P4a evidence collection rules.

### Build the next trajectory-first capability

Accepted target behaviour:

`P-60 -> P-59 -> ... -> today -> predicted remaining trajectory -> final attendance`

This is **daily inference, not daily retuning**.

New work starts with:

1. canonical PIT-safe daily trajectory dataset;
2. immutable daily attempt/forecast ledger;
3. horizon-wise MAE reporting;
4. Lane A simple trajectory residual benchmark;
5. Lane B small sequence residual challenger;
6. target-free/self-supervised trajectory representation research where useful.

---

## Daily trajectory implementation rule

Use existing trajectory infrastructure. **Do not duplicate trajectory semantics.**

Canonical feature builder:

`ml/demand_engine/live_trajectory_feature_store.py`

Canonical daily dataset wrapper:

`ml/demand_engine/daily_trajectory_dataset.py`

The daily dataset must reuse `build_live_trajectory_features(...)` for every exact daily cutoff.

Hard rules:

- exact cutoff: `as_of_at = kickoff_at - N * 24h`;
- no target snapshot after `as_of_at`;
- no future target trajectory point;
- missing daily history stays missing;
- do not interpolate/manufacture history merely to obtain complete sequences;
- structural/incumbent data must have genuinely existed by the cutoff;
- public inventory is a demand proxy, not confirmed paid sales or attendance;
- unknown/hidden inventory is never zero.

---

## Validation / evidence

The independent evaluation unit is the **event/match**.

A large number of daily prefixes does not create a large number of independent events.

Example:

`50 events x 40 prefixes = 2,000 rows`

still means:

`50 independent events`.

Therefore:

- all prefixes from one event stay in the same fold;
- no random daily-row/snapshot split as headline evidence;
- strict forward/time-respecting validation;
- tied kickoffs cannot train one another where chronological ordering matters;
- normalization/scalers are fitted inside training folds;
- target outcomes remain closed during prediction construction;
- immutable prospective forecasts must exist before outcome exposure;
- event-block uncertainty is used for independent-event inference.

Prospective evidence outranks favorable historical/grouped evidence when they disagree.

---

## Model program

### Lane A — simple benchmark

Default formulation:

`structural P50 + trajectory residual model`

Typical inputs:

- current proxy level;
- 1d/3d/7d change;
- velocity;
- acceleration;
- short/long slope;
- slope change;
- volatility;
- observation maturity/density;
- curve similarity.

Candidate families stay small and hypothesis-driven: Ridge/ElasticNet, restrained tree/boosting models, nearest-curve/pickup residual methods.

### Lane B — accepted high-risk sequence research

Do **not** wait for a conventionally large labeled dataset before testing sequence models.

Preferred order:

1. small GRU;
2. small LSTM;
3. small TCN;
4. compact attention/Transformer encoder only if simpler sequence models establish value.

Sequence models remain research/shadow-only until genuine evidence supports them.

They must beat Lane A under the same event-grouped/PIT-safe folds before extra complexity is justified.

Research/model risk is accepted. Evidence/leakage shortcuts are not.

---

## Self-supervised trajectory research

Allowed target-free tasks include:

- next genuine proxy observation prediction;
- short-window proxy-change prediction;
- chronology-safe trajectory representation learning;
- masked/reconstruction tasks that do not expose a target event's future trajectory to its own earlier cutoff.

Self-supervised prefixes may improve representation learning but do **not** increase the number of independent attendance evaluation events.

---

## Current key state — recorded 2026-10-28

Always query fresh before acting.

### P9 v1

Historical: `NOT_EVALUABLE_PIT_SUPPORT_INSUFFICIENT`.

First genuine prospective attempt:

- event443 Cracovia–Motor T-48;
- cutoff 2026-10-28 17:00 UTC;
- immutable attempt persisted;
- result `PIT_SUPPORT_INSUFFICIENT`;
- 1 attempt / 0 predictions / 0 scored.

This is correct fail-closed. Do not lower support and do not retro-predict.

### P9 Family Fallback v2

Separately precommitted/deployed:

- same exact five v1 neighbors;
- unchanged support gate;
- Structural fallback only under the frozen v2 rule;
- never retro-predict event443;
- never pool v1/v2 evidence.

### P7

Latest recorded handoff:

- 53 immutable prediction rows;
- 6 independent events;
- 0 scored;
- no retuning.

### Form5

First legal T-24 capture:

**event443 — 2026-10-29 17:00 UTC**.

### Long72

Latest recorded:

- 5 scored events;
- MAE 6082.40 -> 6039.39;
- improvement 43.01 / 0.71%;
- low priority / frozen.

### P11

Latest recorded:

- 6 events / 6 clubs;
- >=3 bookmakers on all 6;
- T-24/T-72/T-168 = 5/5/0;
- no model fit yet.

---

## Near-term protected windows

Unless fresh machine state says otherwise:

- event446 Wisła Płock–Piast T-48: 2026-10-29 11:15 UTC;
- event6 Lech–Wisła Kraków T-48: 2026-10-29 16:30 UTC;
- event443 Cracovia–Motor T-24: 2026-10-29 17:00 UTC;
- event444 GKS Katowice–Widzew T-48: 2026-10-29 19:15 UTC;
- event445 Zagłębie–Korona T-48: 2026-10-31 17:00 UTC;
- event447 Raków–Pogoń T-48: 2026-10-31 19:30 UTC.

Event448 remains a genuine inventory watch. Unknown inventory is not zero.

---

## Governance

Use the existing governance framework and explicit evidence states.

A negative point Delta MAE is necessary but not automatically a robust advance.

The business minimum meaningful Delta MAE must be derived independently from real operational decisions, not from the experiment being judged.

Mandatory diagnostics include:

- incumbent/challenger MAE;
- absolute/relative Delta MAE;
- signed bias;
- median AE;
- P90 AE;
- event improvement rate;
- worst event degradation;
- per-club diagnostics;
- event-block uncertainty;
- for daily trajectory work: MAE by precommitted horizon/band.

---

## Rejected/closed mechanisms

Do not reopen on the same exposed evidence without a materially new mechanism/information source:

- previous Live Ticketing challenger;
- Sporting Match Stakes;
- timing-context candidate;
- existing weather point-forecast mechanism;
- Hype/Attention 48h;
- old estimator/broad weight sweeps;
- post-hoc retuning of frozen results.

The new daily trajectory program is allowed because it is a materially different representation/model contract.

---

## Immediate development order

1. protect any imminent genuine P9/Form5 window first;
2. score frozen P7/P9 only after genuine outcomes;
3. keep P11/P4a collection healthy;
4. build/audit the canonical daily trajectory dataset and tests;
5. build immutable daily attempt/forecast persistence;
6. add horizon-wise MAE reporting;
7. only then freeze/precommit Lane A and Lane B contracts;
8. evaluate both on identical event-grouped/PIT-safe folds;
9. begin prospective daily shadow inference before target outcomes;
10. derive the business minimum meaningful Delta MAE;
11. keep `live_adjustment=0` until explicit reviewed promotion.

The old ChatGPT Beyond readiness automations are intentionally disabled. Do not enable them implicitly.
