# Beyond Ticketing — Next Session Handoff

Last updated: **2026-10-28**

Status: **CURRENT HANDOFF — QUERY MACHINE STATE FRESH BEFORE ACTING**

Canonical execution plan: `ml/EXECUTION_PLAN_CURRENT.md`

---

# 1. What matters most

Two parallel jobs remain:

1. protect genuine prospective P7/P9/Form5 evidence;
2. finish the frozen **target-free self-supervised trajectory v1** experiment.

Do not restart supervised trajectory tuning on the exposed 10-event cohort.

---

# 2. Supervised trajectory experiments are closed

## Lane A v1

- incumbent MAE 2594.54;
- Lane A MAE 4153.34;
- +1558.80 worse;
- rejected.

## Lane B v1

- MAE 2595.40;
- +0.87 worse than incumbent;
- stable but learned almost zero correction;
- do not advance.

## Lane B v2

- MAE 4792.42;
- +2197.88 worse than incumbent;
- target scaling unlocked large corrections but caused harmful over-correction;
- mechanism not supported.

Decision:

> **Stop supervised tuning on those same exposed five outer test events.**

No post-hoc shrinkage, caps, loss/LR/epoch sweeps or architecture tournament on the same cohort.

---

# 3. Active target-free experiment

Precommit:

`ml/TRAJECTORY_SELF_SUPERVISED_PRETRAIN_V1.md`

Precommit ID:

`trajectory-self-supervised-24h-delta-v1`

Frozen cutoff:

`2026-10-28T22:09:43.958409Z`

Usable sample:

- 26 events / 12 clubs;
- 3565 usable ~24h pairs;
- 21 train events / 3397 train pairs;
- 5 later validation events / 168 validation pairs.

Validation events:

`[447,449,450,451,452]`

No attendance labels. No structural P50.

---

# 4. Frozen SSP task

Input:

- genuine inventory sequence prefix;
- max 168h context;
- >=4 observations;
- >=24h observed span;
- no interpolation/forward-fill.

Target:

`normalized inventory change ~24h later`

Baseline:

`predict no change`

Model:

- one-layer GRU input 4 / hidden 8;
- 8-unit MLP head;
- dropout .20;
- AdamW .001 / wd .01;
- event-balanced weighted L1;
- batch 128;
- 100 epochs;
- grad clip 1;
- seed 17;
- no early stopping;
- no hyperparameter search.

---

# 5. SSP pipeline

Split manifest:

`ml/artifacts/trajectory_self_supervised_v1_split.json`

Export RPC:

`public.export_trajectory_self_supervised_v1()`

OIDC Edge Function:

`trajectory_self_supervised_export_v1`

Runner:

`ml/run_trajectory_self_supervised_v1.py`

Workflow:

`.github/workflows/trajectory-self-supervised-v1.yml`

The runner fails closed unless it reconstructs exactly:

- 3397 train pairs;
- 168 validation pairs;
- 21 train events;
- 5 validation events.

---

# 6. What a result means

## If `REPRESENTATION_SUPPORTED`

This means only that the encoder predicts target-free trajectory dynamics better than zero-change on temporally later events.

Then:

1. freeze the encoder artifact;
2. do not call this attendance validation;
3. precommit a small downstream attendance head;
4. evaluate attendance value on genuinely future immutable predictions/outcomes.

## If `REPRESENTATION_NOT_SUPPORTED`

Do not tune v1 against the same five validation events. Any material change becomes SSP v2.

Prospective attendance evidence remains the final authority.

---

# 7. Existing trajectory infrastructure

Already implemented/live:

- PIT feature store;
- daily P-N builder;
- immutable daily attempts/predictions/scores;
- MAE-by-horizon backend;
- feature/validation contracts;
- target-free export and OIDC gateway.

Do not build parallel versions.

---

# 8. Current prospective evidence state

- P9 v1 first genuine attempt: `PIT_SUPPORT_INSUFFICIENT`, correct fail-closed;
- P9 v2 separate evidence only;
- P7: 53 immutable rows / 6 events / 0 scored;
- Form5 first legal T-24: event443 — 2026-10-29 17:00 UTC;
- Long72 frozen / low priority;
- P11 6 events / 6 clubs, no model fit yet.

Near-term prospective windows in `ml/EXECUTION_PLAN_CURRENT.md` remain higher priority when imminent.

---

# 9. Next agent action

1. Query current prospective machine state if a protected window is imminent.
2. Check latest `Trajectory Self-Supervised v1` workflow run.
3. Fix technical defects only; do not change the frozen SSP protocol mid-run.
4. Persist result and encoder artifact metadata.
5. Update canonical docs with the frozen decision.
6. Do not tune v1 after validation outcome.
7. Keep `live_adjustment=0`.
