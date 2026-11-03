# Beyond — AI Bootstrap / Read This First

Last updated: **2026-10-30**

Status: **CANONICAL AI ENTRYPOINT**

## 1. Cold-start order

Read in this order:

1. `ml/MAE_RESEARCH_ROADMAP_V5.md` — primary MAE strategy;
2. `ml/EXECUTION_PLAN_CURRENT.md` — current experiments, frozen lanes, cutoffs and constraints;
3. `ml/PROGRESS_TRACKING.md` — completed/rejected evidence and what not to repeat;
4. `ml/TRAJECTORY_FORECASTING_PLAN_V1.md` — trajectory design, with historical experiment status resolved by the execution plan/tracker;
5. `ml/NEXT_SESSION_HANDOFF.md` — current operational state only, not MAE strategy;
6. only then inspect code, workflows, SQL, GitHub Actions and live DB.

Query live machine state before acting on scheduled prospective windows. Read the exact precommit before touching a frozen experiment.

Roadmap v5 is canonical.

The operational RPC is the first live-state read after these documents, not a replacement for reading the strategy. For a specific experiment, read its exact precommit before changing or executing it.

## Interpretation: frozen lanes and parallel R&D

"No new model search justified" means no retuning a frozen model on the same exposed evidence. It does not mean stop R&D until prospective outcomes arrive. Protect the existing lanes while running new, separately versioned/precommitted experiments with genuinely new information or a distinct justified mechanism and valid held-out evaluation.

`baseline -> new information -> simple challenger -> event-grouped/PIT-safe MAE -> freeze -> prospective shadow -> genuine outcomes`

Previously exposed outer events never become untouched validation merely because the candidate receives a new version name. Existing frozen artifacts, parameters, missed windows and production boundaries stay unchanged.

---

## 2. North Star

> **Minimize true prospective event-balanced attendance-forecast MAE using PIT-safe, reproducible evidence.**

Production remains:

`live_adjustment = 0`

---

## 3. Current model state

Structural forecast remains the attendance incumbent.

Supervised trajectory experiments on the exposed 10-event cohort are closed:

| Model | MAE | Delta vs incumbent | Decision |
|---|---:|---:|---|
| Structural incumbent | **2594.54** | — | incumbent |
| Lane A v1 | 4153.34 | +1558.80 | rejected |
| Lane B v1 | 2595.40 | +0.87 | do not advance |
| Lane B v2 | 4792.42 | +2197.88 | mechanism not supported |

Do not retune these experiments on the same exposed outer events.

---

## 4. SSP v1 result — frozen

Precommit:

`trajectory-self-supervised-24h-delta-v1`

Target-free temporal validation result:

- zero-change event-balanced MAE: **0.091722**;
- GRU event-balanced MAE: **0.062896**;
- Delta: **-0.028826**;
- validation events improved: **5/5**;
- attendance labels used: false;
- structural P50 used: false.

Decision:

`REPRESENTATION_SUPPORTED`

Frozen encoder:

`ml/artifacts/trajectory_self_supervised_encoder_v1.json`

Interpretation:

> The encoder learned useful inventory-trajectory dynamics. This is not evidence that attendance MAE improved.

Do not retune SSP v1 against the same five validation events.

---

## 5. Active attendance experiment

Candidate:

`trajectory-frozen-encoder-ridge-ratio-head-v1`

Precommit:

`ml/TRAJECTORY_FROZEN_ENCODER_PROSPECTIVE_SHADOW_V1.md`

Frozen components:

- SSP v1 encoder;
- one fixed Ridge residual-ratio head;
- alpha 10;
- +/-10% correction cap;
- exact exposed 10-event / 19-row fit cohort;
- no historical candidate selection;
- P-7 / P-3 / P-1 only.

Frozen head artifact:

`ml/artifacts/trajectory_frozen_encoder_attendance_head_v1.json`

The head was fitted once by the successful fit-only workflow and the exact artifact is now persisted on `main`. Do not refit merely because the prospective runner needs an artifact.

---

## 6. Prospective shadow contract

The shadow asks:

> **Does the frozen encoder + frozen attendance head reduce future attendance MAE relative to the structural incumbent?**

Hard rules:

- exact PIT cutoff;
- genuine observations only;
- no later snapshot leakage;
- PIT-valid structural prior required;
- immutable attempt/prediction before outcome;
- no retrospective prediction;
- no tuning after early future outcomes under the same version;
- production off.

Persistence:

- `private.daily_trajectory_attempts_v1`;
- `private.daily_trajectory_predictions_v1`;
- `private.daily_trajectory_scores_v1`.

Workflow:

`.github/workflows/trajectory-frozen-encoder-shadow-v1.yml`

Schedule:

`20,50 * * * *`

The full shadow workflow was verified end-to-end on 2026-10-29 after persisting the frozen head artifact.

---

## 7. Current prospective state

Fresh snapshot at **2026-10-29 16:09 UTC**:

- P9 v1: 2 attempts / 0 predictions / 0 scored; both support-insufficient;
- P9 v2: 1 attempt / 1 immutable prediction / 0 scored;
- Form5: collecting, 0/8 completed eligible events;
- frozen-encoder shadow: 0 attempts / 0 predictions / 0 scores before first due P-1 cutoff;
- production change false everywhere.

Imminent windows are listed in `ml/EXECUTION_PLAN_CURRENT.md` and take priority over new research.

---

## 8. What not to do

Do not:

- reopen Lane A/B tuning on the exposed cohort;
- use SSP validation as attendance evidence;
- change encoder/head alpha/cap after seeing early prospective scores and keep the same candidate ID;
- manufacture missing inventory;
- random-split daily rows;
- pool P9 v1/v2 evidence;
- lower support gates for coverage;
- auto-activate production.

Any material candidate change after future outcomes requires a new precommit/version.
