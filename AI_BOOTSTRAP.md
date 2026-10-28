# Beyond — AI Bootstrap / Read This First

Last updated: **2026-10-28**

Status: **CANONICAL AI ENTRYPOINT**

## 1. Cold-start order

Read in this order:

1. `ml/EXECUTION_PLAN_CURRENT.md`;
2. `ml/NEXT_SESSION_HANDOFF.md`;
3. `ml/MAE_RESEARCH_ROADMAP_V5.md`;
4. `ml/TRAJECTORY_FORECASTING_PLAN_V1.md`;
5. `ml/TRAJECTORY_FEATURE_CONTRACT_V1.md`;
6. `ml/TRAJECTORY_VALIDATION_FOLD_CONTRACT_V1.md`;
7. `ml/TRAJECTORY_LANE_A_RESULT_V1.md`;
8. `ml/TRAJECTORY_LANE_B_PRECOMMIT_V1.md`;
9. `ml/PROGRESS_TRACKING.md`;
10. `ml/MODEL_ACCURACY_DEVELOPMENT_INSTRUCTIONS_V3.md`.

Read the exact precommit before touching any frozen experiment. Query live/machine state fresh before acting on scheduled windows.

Roadmap v5 is canonical. Do not restart from v3/v4.

---

## 2. North Star

> **Minimize true prospective event-balanced attendance-forecast MAE using PIT-safe, reproducible evidence.**

`Delta MAE = challenger MAE - incumbent MAE`

Production remains:

`live_adjustment = 0`

---

## 3. Current state

There are two parallel tracks.

### A. Protect prospective evidence

Do not mutate:

- P7 prospective;
- P9 v1;
- P9 Family Fallback v2;
- Form5 prospective;
- Long72;
- P11/P4a evidence rules.

### B. Active trajectory experiment

Infrastructure is already delivered.

Lane A v1 has been evaluated and **failed**:

- incumbent event-balanced MAE: **2594.5**;
- Lane A Ridge MAE: **4153.3**;
- Delta MAE: **+1558.8**;
- **60.1% worse**;
- 5 strict-forward independent test events.

Decision:

`REJECT_AS_CANDIDATE_RETAIN_AS_BENCHMARK`

Do not retune Lane A v1 on the exposed outer cohort.

The active experiment is **Lane B v1 small GRU**.

---

## 4. Frozen Lane B question

Lane B must answer:

1. Does the ordered genuine trajectory beat the structural incumbent?
2. Does it beat the frozen failed Lane A benchmark on the exact same test identities?

Precommit:

`trajectory-lane-b-small-gru-residual-v1`

Implementation:

`ml/demand_engine/trajectory_lane_b_v1.py`

Runner:

`ml/run_trajectory_lane_b_v1.py`

Workflow:

`.github/workflows/trajectory-lane-b-v1.yml`

No architecture search, no post-result seed selection, no Transformer, no self-supervised pretraining in v1.

---

## 5. Frozen cohort / validation

Cohort:

`ml/artifacts/trajectory_development_cohort_v1.json`

- 10 labeled independent events;
- 5 strict-forward outer test events;
- exact frozen fold-registry SHA256:
  `fc59737ab1c0a306920b4961de35664178b14648f679071522d1d07515cb3091`.

Validation:

- strict expanding temporal event folds;
- only earlier-kickoff events may train a later event;
- same-kickoff events stay together;
- minimum 5 prior events / 4 prior clubs;
- every prefix from one event stays in the same fold;
- random daily-row CV prohibited.

---

## 6. Lane B fixed protocol

- one-layer GRU;
- input dimension 5;
- hidden dimension 8;
- small 8-unit MLP head;
- dropout 0.20;
- AdamW lr 0.001, weight decay 0.01;
- weighted L1 residual loss;
- 200 fixed epochs;
- gradient clip 1.0;
- seeds 17 / 29 / 41;
- median residual across all three seeds;
- event-balanced row weights.

Do not tune these after outer results.

---

## 7. Data/export path

Frozen research export:

`public.export_trajectory_development_rows_v1(bigint[])`

OIDC gateway:

`trajectory_research_export_v1`

GitHub Actions requests an OIDC token with audience:

`beyond-trajectory-research`

The gateway accepts only:

- repository `NiedzielX/beyond`;
- ref `refs/heads/main`.

No service-role secret is stored in GitHub.

The Lane B runner requires exactly **10 events / 19 frozen checkpoint rows** or fails closed.

---

## 8. Data reality

Current genuine pre-kickoff inventory history:

- 32 events / 14 clubs with any observation;
- median first observation ~P-9.3;
- earliest ~P-30.3;
- P-31...P-60 historical coverage currently zero.

P-60 is a collection horizon, not a requirement for a fabricated 60-day input.

Use genuine variable-length sequences; missing/hidden inventory is never zero.

---

## 9. Current protected state

### P9 v1

First genuine attempt event443 T-48: `PIT_SUPPORT_INSUFFICIENT`; 1 attempt / 0 predictions / 0 scored. Correct fail-closed.

### P9 v2

Separate evidence only; unchanged support; no retro-prediction; never pool with v1.

### Form5

First legal T-24 capture: **event443 — 2026-10-29 17:00 UTC**.

### P7

53 immutable rows / 6 events / 0 scored. No retuning.

### Long72

5 scored; 6082.40 -> 6039.39; 0.71% point gain; frozen / low priority.

### P11

6 events / 6 clubs; T-24/T-72/T-168 = 5/5/0; no model fit yet.

---

## 10. Hard rules

- protect genuine prospective windows before lower-priority R&D;
- no future target trajectory;
- no target attendance during inference;
- no fabricated history;
- no random row CV;
- no event-prefix crossing folds;
- no gate relaxation for coverage;
- no post-result Lane A/Lane B v1 tuning;
- persist prospective forecasts before outcomes;
- no automatic production activation.
