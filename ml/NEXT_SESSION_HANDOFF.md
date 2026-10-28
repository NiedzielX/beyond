# Beyond Ticketing — Next Session Handoff

Last updated: **2026-10-28**

Status: **CURRENT HANDOFF — QUERY MACHINE STATE FRESH BEFORE ACTING**

Canonical execution plan: `ml/EXECUTION_PLAN_CURRENT.md`

---

# 1. What matters most

Two parallel jobs remain:

1. protect genuine prospective P7/P9/Form5 evidence;
2. finish the frozen **Lane B v1** strict-forward sequence experiment.

Trajectory infrastructure and Lane A work are no longer pending.

---

# 2. Lane A is closed

Precommit:

`trajectory-lane-a-ridge-residual-v1`

Result:

- incumbent event-balanced MAE **2594.5**;
- Lane A MAE **4153.3**;
- Delta MAE **+1558.8**;
- **60.1% worse**;
- event improvement rate 20%;
- 5 independent strict-forward test events.

Decision:

`REJECT_AS_CANDIDATE_RETAIN_AS_BENCHMARK`

Do not change alpha/features or remove bad events after seeing this result.

Result docs:

- `ml/TRAJECTORY_LANE_A_RESULT_V1.md`;
- `ml/results/trajectory_lane_a_ridge_residual_v1_result.json`.

---

# 3. Lane B v1 is active

Precommit:

`trajectory-lane-b-small-gru-residual-v1`

Implementation:

`ml/demand_engine/trajectory_lane_b_v1.py`

Runner:

`ml/run_trajectory_lane_b_v1.py`

Workflow:

`.github/workflows/trajectory-lane-b-v1.yml`

Frozen model:

- one-layer GRU;
- hidden dimension 8;
- 5 genuine sequence channels;
- 8-unit MLP head;
- dropout .20;
- AdamW 0.001 / wd 0.01;
- weighted L1 loss;
- 200 epochs;
- seeds 17,29,41;
- median prediction across seeds;
- no architecture search.

Lane B must beat both the structural incumbent and frozen Lane A to earn candidate review.

---

# 4. Frozen cohort

`ml/artifacts/trajectory_development_cohort_v1.json`

- 10 labeled independent events;
- 19 frozen persisted checkpoint rows;
- 5 strict-forward outer test events;
- frozen fold SHA256:
  `fc59737ab1c0a306920b4961de35664178b14648f679071522d1d07515cb3091`.

The runner fails closed unless the OIDC export materializes exactly the frozen identities.

Do not expand the cohort after seeing Lane B results.

---

# 5. Research data path

Live service-role RPC:

`public.export_trajectory_development_rows_v1(bigint[])`

Live OIDC Edge Function:

`trajectory_research_export_v1`

Allowed identity:

- repository `NiedzielX/beyond`;
- ref `refs/heads/main`;
- OIDC audience `beyond-trajectory-research`.

GitHub Actions does not need a stored Supabase service-role key.

The export currently validates to **10 events / 19 rows**.

---

# 6. Existing trajectory infrastructure

Already implemented/live:

- PIT trajectory feature store;
- exact daily P-N dataset builder;
- shared Lane A/B data materializer;
- feature contract v1;
- strict-forward fold contract v1;
- immutable daily attempts/predictions/scores;
- post-outcome scoring;
- MAE-by-horizon backend;
- coverage audit;
- research event bundle RPC;
- frozen development export RPC.

Do not build parallel versions of these components.

---

# 7. Data reality

- 32 events / 14 clubs with any genuine pre-kickoff inventory;
- median first observation ~P-9.3;
- earliest ~P-30.3;
- current P-31...P-60 historical coverage = 0.

Use genuine variable-length sequences. No forward-fill/interpolation merely to create input.

---

# 8. Current prospective evidence state

## P9 v1

Historical: `NOT_EVALUABLE_PIT_SUPPORT_INSUFFICIENT`.

First real event443 T-48 attempt: `PIT_SUPPORT_INSUFFICIENT`; 1 attempt / 0 predictions / 0 scored. Correct fail-closed.

## P9 v2

Separate frozen fallback evidence. Never pool with v1.

## P7

53 immutable rows / 6 events / 0 scored. No retuning.

## Form5

First legal T-24 capture: **event443 — 2026-10-29 17:00 UTC**.

## Long72

5 scored; 0.71% point gain; frozen / low priority.

## P11

6 events / 6 clubs; T-24/T-72/T-168 = 5/5/0; no model fit yet.

---

# 9. Near-term protected windows

Unless fresh machine state says otherwise:

- event446 Wisła Płock–Piast T-48: 2026-10-29 11:15 UTC;
- event6 Lech–Wisła Kraków T-48: 2026-10-29 16:30 UTC;
- event443 Cracovia–Motor T-24: 2026-10-29 17:00 UTC;
- event444 GKS Katowice–Widzew T-48: 2026-10-29 19:15 UTC;
- event445 Zagłębie–Korona T-48: 2026-10-31 17:00 UTC;
- event447 Raków–Pogoń T-48: 2026-10-31 19:30 UTC.

Event448 remains an inventory watch. Unknown inventory is not zero.

---

# 10. Next agent action

1. Query current prospective machine state first if a window is imminent.
2. Check the latest `Trajectory Lane B v1` workflow run.
3. If the run is technically red, fix only the execution defect without changing the frozen model protocol.
4. If it succeeds, persist the Lane B machine-readable result and a concise human decision document.
5. Do not tune v1 after seeing the result.
6. If Lane B beats incumbent + Lane A, freeze a separate prospective candidate before future outcomes.
7. If Lane B fails, diagnose and create a separately versioned v2 only if a new hypothesis is justified.
8. Keep `live_adjustment=0`.
