# Beyond Agent Instructions

Last updated: **2026-10-28**

## Read first

1. `AI_BOOTSTRAP.md`;
2. `ml/EXECUTION_PLAN_CURRENT.md`;
3. `ml/NEXT_SESSION_HANDOFF.md`;
4. `ml/MAE_RESEARCH_ROADMAP_V5.md`;
5. `ml/TRAJECTORY_FEATURE_CONTRACT_V1.md`;
6. `ml/TRAJECTORY_VALIDATION_FOLD_CONTRACT_V1.md`;
7. `ml/TRAJECTORY_LANE_A_RESULT_V1.md`;
8. `ml/TRAJECTORY_LANE_B_PRECOMMIT_V1.md`;
9. `ml/PROGRESS_TRACKING.md`.

Query live machine state before acting on prospective windows. Read the exact precommit before touching a frozen experiment.

Roadmap v5 is canonical.

---

## Core objective

> **Lower true prospective event-balanced attendance MAE, not model complexity.**

Production remains:

`live_adjustment = 0`

---

## Current phase

### Protect prospective evidence

Do not mutate:

- P7 prospective;
- P9 v1;
- P9 Family Fallback v2;
- Form5 prospective;
- Long72;
- P11/P4a evidence rules.

### Active R&D experiment

Lane A v1 is closed and rejected as a candidate.

Frozen Lane A result:

- incumbent MAE 2594.5;
- Lane A MAE 4153.3;
- Delta +1558.8;
- 60.1% worse;
- 5 strict-forward independent test events.

Do **not** retune Lane A v1.

Active experiment:

`trajectory-lane-b-small-gru-residual-v1`

---

## Lane B fixed protocol

- one-layer GRU;
- input dim 5;
- hidden dim 8;
- MLP head 8;
- dropout .20;
- AdamW lr .001, weight decay .01;
- event-balanced weighted L1 residual loss;
- 200 fixed epochs;
- gradient clipping 1.0;
- seeds 17 / 29 / 41;
- median residual across all seeds;
- no architecture search;
- no Transformer;
- no self-supervised pretraining in v1.

Any change after outer results requires a new version/precommit.

---

## Frozen evidence identities

Cohort:

`ml/artifacts/trajectory_development_cohort_v1.json`

- 10 labeled events;
- 19 persisted checkpoint rows;
- 5 strict-forward outer test events;
- fold SHA256:
  `fc59737ab1c0a306920b4961de35664178b14648f679071522d1d07515cb3091`.

Lane B runner must reject any export that does not exactly match this cohort.

Do not add newer events/cutoffs after seeing the result.

---

## Validation rules

Primary validation is strict expanding temporal event folds:

- only earlier-kickoff events train later events;
- same-kickoff events held out together;
- min 5 previous train events;
- min 4 previous train clubs;
- all prefixes from one event stay in one fold;
- no random daily-row/snapshot CV.

Event is the independent unit.

---

## Data/export path

Frozen export RPC:

`public.export_trajectory_development_rows_v1(bigint[])`

OIDC Edge Function:

`trajectory_research_export_v1`

Workflow:

`.github/workflows/trajectory-lane-b-v1.yml`

OIDC restrictions:

- repository `NiedzielX/beyond`;
- ref `refs/heads/main`;
- audience `beyond-trajectory-research`.

Do not add a Supabase service-role key to GitHub Secrets for this workflow.

---

## Sequence rules

Lane B uses genuine ordered variable-length inventory trajectories:

- exact timestamp dedupe;
- max one genuine observation per integer hour-to-kickoff bucket;
- no interpolation;
- no forward-fill;
- explicit sequence lengths/masks;
- padded zero is not genuine zero inventory.

Public inventory is a demand proxy, not confirmed sales/attendance.

Unknown/hidden inventory is never zero.

---

## Decision rule after Lane B result

### If Lane B beats incumbent and Lane A

Review downside/seed spread, then freeze a **new prospective candidate** before future outcomes. Do not activate production.

### If Lane B beats Lane A but not incumbent

Do not promote. Ordered representation may be interesting but not useful enough.

### If Lane B fails both

Do not run a broad GRU/LSTM/Transformer sweep on the same outer cohort. Diagnose first. Any material change becomes v2.

### If later prospective evidence disagrees with historical research

Prospective evidence wins.

---

## Hard rules

- protect imminent P9/Form5 windows first;
- no future target trajectory;
- no target attendance during inference;
- no fabricated history;
- no event-prefix crossing folds;
- no random row CV;
- no support-gate relaxation for coverage;
- no post-result v1 tuning;
- persist prospective forecasts before outcomes;
- no automatic production activation.

The old ChatGPT Beyond readiness automations remain disabled. Do not enable them implicitly.
