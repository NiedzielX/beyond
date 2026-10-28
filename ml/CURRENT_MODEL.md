# Beyond Ticketing — Current Model & Product State

Last updated: **2026-10-28**

Status: **STRUCTURAL INCUMBENT + FROZEN PROSPECTIVE LANES + ACTIVE LANE B SEQUENCE R&D**

Canonical execution plan: `ml/EXECUTION_PLAN_CURRENT.md`

Production: `live_adjustment = 0`

---

# 1. North Star

> **Minimize true prospective event-balanced attendance-forecast MAE with PIT-safe, reproducible evidence.**

`Delta MAE = challenger MAE - incumbent MAE`

---

# 2. Structural incumbent

Current structural research champion family remains **Global Model v2.1**.

Foundation:

- 1,530 Ekstraklasa matches;
- complete 2021/22–2025/26 seasons;
- 7,650 historical PIT rows;
- structural horizons T-30d / T-14d / T-7d / T-3d / T-1d.

Architecture:

`PIT historical state -> club-history baseline -> global residual model -> structural P50`

This structural P50 is the anchor that every trajectory challenger must beat.

---

# 3. Trajectory research — current answer

The trajectory program is no longer at the infrastructure-design stage.

## Lane A v1 — failed

Model:

`structural P50 + engineered trajectory features -> Ridge residual correction`

Strict-forward historical research result:

- independent test events: **5**;
- incumbent event-balanced MAE: **2594.5**;
- Lane A MAE: **4153.3**;
- Delta MAE: **+1558.8**;
- **60.1% worse**;
- event improvement rate: **20%**.

Decision:

`REJECT_AS_CANDIDATE_RETAIN_AS_BENCHMARK`

Lane A v1 must not be retuned after this result.

## Lane B v1 — active

Model:

`structural P50 + genuine ordered variable-length trajectory -> small GRU -> residual correction`

Frozen protocol:

- one GRU layer;
- hidden dimension 8;
- 5 sequence channels;
- small 8-unit MLP head;
- AdamW;
- weighted L1 residual loss;
- 200 fixed epochs;
- seeds 17 / 29 / 41;
- median residual across seeds;
- no architecture search.

Lane B must beat both:

1. structural incumbent MAE;
2. frozen Lane A MAE.

---

# 4. Frozen development cohort

`ml/artifacts/trajectory_development_cohort_v1.json`

- 10 labeled independent events;
- 19 persisted eligible checkpoint rows;
- 5 strict-forward outer test events;
- only earlier-kickoff events train later targets;
- all prefixes from one event stay in the same fold.

Fold registry SHA256:

`fc59737ab1c0a306920b4961de35664178b14648f679071522d1d07515cb3091`

Random row CV is prohibited.

---

# 5. Trajectory data reality

Current genuine pre-kickoff history:

- 32 events / 14 clubs with any observation;
- median first observation ~P-9.3;
- earliest ~P-30.3;
- P-31...P-60 historical coverage currently zero.

Therefore:

- P-60 is a collection horizon;
- models use genuine variable-length prefixes;
- no fake complete 60-day vector;
- no forward-fill/interpolation merely for model convenience;
- hidden/unknown inventory is never zero.

---

# 6. Current trajectory engineering stack

Implemented/live:

- PIT trajectory feature store;
- exact P-N dataset builder;
- shared A/B dataset materializer;
- frozen feature contract v1;
- frozen strict-forward validation contract v1;
- frozen cohort manifest;
- Lane A learner/result;
- Lane B GRU learner/runner;
- immutable daily attempt/prediction/score ledgers;
- post-outcome scoring;
- MAE-by-horizon backend;
- service-role development export RPC;
- GitHub OIDC export gateway;
- Lane B GitHub Actions experiment workflow.

No production activation is connected to this workflow.

---

# 7. P7 prospective

Historical result remains frozen:

- anchor MAE 7409.79;
- challenger MAE 6339.99;
- point gain 1069.80 / 14.44%;
- uncertainty limited.

Latest recorded prospective state:

- 53 immutable prediction rows;
- 6 events;
- 0 scored.

No retuning.

---

# 8. P9

## v1

Historical: `NOT_EVALUABLE_PIT_SUPPORT_INSUFFICIENT`.

First genuine event443 T-48 attempt:

- `PIT_SUPPORT_INSUFFICIENT`;
- 1 attempt / 0 predictions / 0 scored;
- correct fail-closed.

## Family Fallback v2

Separate frozen evidence only. Never pool with v1 and never retro-predict event443.

---

# 9. Form5 / Long72 / P11 / P4a

## Form5

First legal prospective T-24 capture:

**event443 — 2026-10-29 17:00 UTC**.

## Long72

- 5 scored events;
- 6082.40 -> 6039.39 MAE;
- 0.71% point gain;
- frozen / low priority.

## P11

- 6 events / 6 clubs;
- T-24/T-72/T-168 = 5/5/0;
- no attendance-model fit yet.

## P4a

Still below event-count gate. Continue genuine labels only.

---

# 10. Product interpretation

Public inventory is a **demand/inventory proxy**, not confirmed paid sales or attendance.

Intended future product view:

`observed trajectory | today | predicted remaining trajectory -> final attendance P10/P50/P90`

But a trajectory challenger must first beat the structural incumbent under honest evidence.

---

# 11. Immediate model decision

> **Keep the structural model as incumbent. Lane A v1 failed and is frozen as a benchmark. Finish the precommitted Lane B v1 GRU experiment without tuning; only a clean win over both incumbent and Lane A can justify freezing a prospective daily-shadow candidate.**
