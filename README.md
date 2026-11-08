# Beyond

Beyond Ticketing engineering and ML research workspace.

## Start here

Read in this order:

1. [`ml/MAE_RESEARCH_ROADMAP_V6.md`](ml/MAE_RESEARCH_ROADMAP_V6.md) — primary MAE strategy
2. [`ml/EXECUTION_PLAN_CURRENT.md`](ml/EXECUTION_PLAN_CURRENT.md)
3. [`ml/PROGRESS_TRACKING.md`](ml/PROGRESS_TRACKING.md)
4. [`ml/TRAJECTORY_FORECASTING_PLAN_V1.md`](ml/TRAJECTORY_FORECASTING_PLAN_V1.md)
5. [`ml/NEXT_SESSION_HANDOFF.md`](ml/NEXT_SESSION_HANDOFF.md) — operational state only
6. Only then inspect code, workflows, SQL, GitHub Actions and live DB.

Roadmap v6 is canonical. Read the exact precommit before touching a frozen experiment.

Shared AI working records are mandatory: [AGENTS.md](AGENTS.md) and [CLAUDE.md](CLAUDE.md) describe `.ai/specs/YYYY-MM-DD-slug.md` (with `implemented/` and `archive/`), `.ai/runs/YYYY-MM-DD-slug.md`, and the long-term memory index [.ai/lessons.md](.ai/lessons.md) with detailed notes in `.ai/lessons/`. These records complement the canonical ML plan.

Frozen validation and new R&D run in parallel. "No new model search justified" prohibits retuning frozen models against the same exposed evidence; it is not a stop on separately versioned, precommitted research.

The MAE research loop is:

`baseline -> new information -> simple challenger -> event-grouped/PIT-safe MAE -> freeze -> prospective shadow -> genuine outcomes`

---

## North Star

> **Minimize true prospective event-balanced attendance-forecast MAE using PIT-safe, reproducible evidence.**

Production remains:

`live_adjustment = 0`

---

## Daily-path MVP and cloud validation

[November8rolling72execution](ml/ROLLING_72H_STAGE_A_RESULT_2026-11-08.md): cached coverage audited; separate first-point input/features and genuine future-label modules prepared and tested. Historical source-known clocks and sector coverage remain open. No new fit, MAE or deployed rolling72feed is claimed. Next: receipt-bound source integration and exact precommit before fitting.

The [November8literature verification](ml/ROLLING_72H_LITERATURE_REVIEW_2026-11-08.md) records evidence, actual reading scope and remaining full-text gaps before implementation. It separates forward demand forecasts, sector warning usefulness and the causal revenue effect of pricing/advertising.

Accuracy remains central: minimise true future MAE and continue toward approximately 1200 seats attendance MAE. Evaluate the new24/48/72h path separately; it complements the accuracy goal rather than replacing it.

Current product goal: forecasts from the first genuine match observation, giving clubs24/48/72hour expectations under stated price/promotion/pool assumptions. [The rolling72 plan](ml/ROLLING_72H_COMMERCIAL_FORECAST_PLAN_V1.md) records the hypothesis, work stages, metrics and actual end-to-end acceptance. A terminal-attendance history chart or final24C1alone is insufficient for this goal.

The separate public-inventory lane now predicts every remaining day from the genuine observed prefix. It remains a frozen research shadow with production off. See [implementation](ml/DAILY_INVENTORY_PATH_IMPLEMENTATION_V1.md), [deployment/recovery](ml/DAILY_INVENTORY_PATH_DEPLOYMENT_V1.md), and [verified cloud tests and bounded workers](ml/DAILY_PATH_CLOUD_VALIDATION_2026-11-04.md). Inventory-path MAE and attendance MAE are separate targets; no score is zero merely because future outcomes have not matured.

The [pre-outcome coefficient audit](ml/DAILY_PATH_COEFFICIENT_AUDIT_2026-11-04.md) found that this fit retained no relative-value-history weights: receiving a full prefix does not prove the model learned its changes. Its issued predictions stay frozen. A separate [genuine 24-hour drift comparator](ml/DAILY_INVENTORY_DRIFT_COMPARATOR_PRECOMMIT_V1.md) now tests whether recent observed change beats persistence, using new immutable forecasts and future matched targets. It has no fitted parameters or demonstrated MAE advantage yet. Managed deployment and the live new panel feed remain blocked on project admin binding.

## Attendance input knowledge-time integration

[Separate source export, guarded frozen inference and private archive](ml/STRUCTURAL_KNOWN_AT_INPUT_INTEGRATION_V1.md) retain actual source and row-revision times. The bounded cloud archive captures immutable raw inputs with verified private recovery; a read-only as-of lookup refuses missing pre-cutoff history. This does not activate a model or repair the old managed serving path, which still needs its reviewed release. No new attendance-MAE result is claimed.

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

For this frozen candidate, the prospective question is:

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
