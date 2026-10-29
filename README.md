# Beyond

Beyond Ticketing engineering and ML research workspace.

## Start here

Read in this order:

1. [`AI_BOOTSTRAP.md`](AI_BOOTSTRAP.md)
2. [`ml/EXECUTION_PLAN_CURRENT.md`](ml/EXECUTION_PLAN_CURRENT.md)
3. [`ml/NEXT_SESSION_HANDOFF.md`](ml/NEXT_SESSION_HANDOFF.md)
4. [`ml/MAE_RESEARCH_ROADMAP_V5.md`](ml/MAE_RESEARCH_ROADMAP_V5.md)
5. [`ml/TRAJECTORY_FROZEN_ENCODER_PROSPECTIVE_SHADOW_V1.md`](ml/TRAJECTORY_FROZEN_ENCODER_PROSPECTIVE_SHADOW_V1.md)
6. [`ml/TRAJECTORY_FROZEN_ENCODER_ATTENDANCE_HEAD_V1.md`](ml/TRAJECTORY_FROZEN_ENCODER_ATTENDANCE_HEAD_V1.md)
7. [`ml/TRAJECTORY_SELF_SUPERVISED_PRETRAIN_V1.md`](ml/TRAJECTORY_SELF_SUPERVISED_PRETRAIN_V1.md)
8. [`ml/PROGRESS_TRACKING.md`](ml/PROGRESS_TRACKING.md)

Roadmap v5 is canonical. Read the exact precommit before touching a frozen experiment.

---

## North Star

> **Minimize true prospective event-balanced attendance-forecast MAE using PIT-safe, reproducible evidence.**

Production remains:

`live_adjustment = 0`

---

## Current state in one minute

The structural model remains the attendance incumbent.

The first supervised trajectory cohort is closed:

| Model | Event-balanced MAE | Delta vs incumbent | Decision |
|---|---:|---:|---|
| Structural incumbent | **2594.54** | — | incumbent |
| Lane A v1 — Ridge | 4153.34 | +1558.80 | rejected |
| Lane B v1 — GRU / raw seat residual | 2595.40 | +0.87 | do not advance |
| Lane B v2 — GRU / residual ratio | 4792.42 | +2197.88 | mechanism not supported |

Do not retune those models on the same exposed outer events.

---

## Target-free trajectory representation — supported and frozen

Self-supervised trajectory v1 asked whether a tiny GRU can predict genuine normalized inventory movement ~24h ahead without attendance labels or structural P50.

Frozen validation result:

- zero-change event-balanced MAE: **0.091722**;
- GRU event-balanced MAE: **0.062896**;
- Delta: **-0.028826**;
- validation events improved: **5/5**.

Decision:

`REPRESENTATION_SUPPORTED`

The encoder is frozen in:

[`ml/artifacts/trajectory_self_supervised_encoder_v1.json`](ml/artifacts/trajectory_self_supervised_encoder_v1.json)

This means trajectory dynamics are learnable under the frozen target-free task. It does **not** mean attendance MAE improved.

---

## Active experiment — frozen encoder prospective attendance shadow

Candidate:

`trajectory-frozen-encoder-ridge-ratio-head-v1`

The candidate combines:

- frozen SSP v1 encoder;
- one fixed Ridge residual-ratio head;
- alpha 10;
- +/-10% correction cap;
- no historical candidate selection;
- P-7 / P-3 / P-1 prospective horizons.

Frozen head:

[`ml/artifacts/trajectory_frozen_encoder_attendance_head_v1.json`](ml/artifacts/trajectory_frozen_encoder_attendance_head_v1.json)

Prospective precommit:

[`ml/TRAJECTORY_FROZEN_ENCODER_PROSPECTIVE_SHADOW_V1.md`](ml/TRAJECTORY_FROZEN_ENCODER_PROSPECTIVE_SHADOW_V1.md)

The only important question now is:

> **Does this frozen representation reduce genuinely future attendance MAE relative to the structural incumbent?**

Answer that only with immutable forecasts created before outcomes.

---

## Evidence safety

- P7 / P9 / Form5 remain separate frozen evidence lanes;
- P9 v1 and Family Fallback v2 are never pooled;
- missing/hidden inventory is never zero;
- no retrospective prospective predictions;
- no random daily-row CV;
- no post-result tuning and keeping the same candidate version;
- no automatic production activation.

Current immutable windows and latest machine state live in [`ml/EXECUTION_PLAN_CURRENT.md`](ml/EXECUTION_PLAN_CURRENT.md).

---

## Important semantics

Public inventory is a **demand/inventory proxy**, not confirmed paid ticket sales or attendance.

P-60 is a collection horizon, not a requirement for fabricated complete history.

---

## Engineering rule

`hypothesis -> precommit -> PIT contract -> code -> strict evidence -> result -> decision -> canonical docs`

> **A failed frozen experiment is evidence. Do not repair it after seeing the answer.**
