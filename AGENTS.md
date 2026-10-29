# Beyond Agent Instructions

Last updated: **2026-10-29**

## Read first

1. `AI_BOOTSTRAP.md`;
2. `ml/EXECUTION_PLAN_CURRENT.md`;
3. `ml/NEXT_SESSION_HANDOFF.md`;
4. `ml/MAE_RESEARCH_ROADMAP_V5.md`;
5. `ml/TRAJECTORY_FROZEN_ENCODER_PROSPECTIVE_SHADOW_V1.md`;
6. `ml/TRAJECTORY_FROZEN_ENCODER_ATTENDANCE_HEAD_V1.md`;
7. `ml/TRAJECTORY_SELF_SUPERVISED_PRETRAIN_V1.md`;
8. `ml/PROGRESS_TRACKING.md`.

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

Do not mutate frozen evidence contracts for:

- P7 prospective;
- P9 v1;
- P9 Family Fallback v2;
- Form5 prospective;
- Long72;
- P11/P4a;
- frozen encoder attendance shadow v1.

An imminent genuine cutoff takes priority over research work.

### Closed supervised trajectory research

Frozen results on the exposed 10-event cohort:

- Lane A v1: 4153.34 vs 2594.54 structural MAE -> rejected;
- Lane B v1: 2595.40 -> do not advance;
- Lane B v2: 4792.42 -> mechanism not supported.

Do not retune those experiments on the same outer events.

---

## SSP v1 — frozen representation

Precommit:

`trajectory-self-supervised-24h-delta-v1`

Target-free validation result:

- zero-change event-balanced MAE 0.0917223592;
- GRU event-balanced MAE 0.0628961688;
- Delta -0.0288261905;
- 5/5 validation events improved;
- attendance labels used false;
- structural prior used false.

Decision:

`REPRESENTATION_SUPPORTED`

Frozen encoder:

`ml/artifacts/trajectory_self_supervised_encoder_v1.json`

Do not call this attendance validation. Do not retune SSP v1 against the same five validation events.

---

## Active attendance candidate

Candidate ID:

`trajectory-frozen-encoder-ridge-ratio-head-v1`

Frozen head:

`ml/artifacts/trajectory_frozen_encoder_attendance_head_v1.json`

Protocol:

- frozen SSP v1 encoder;
- 8-d embedding;
- Ridge alpha 10;
- residual-ratio target;
- correction cap +/-10%;
- exact exposed 10-event / 19-row fit cohort;
- no historical candidate selection;
- prospective horizons P-7 / P-3 / P-1;
- production off.

The head was fitted once. Do not refit it merely to refresh inference.

---

## Prospective frozen-encoder shadow

Precommit:

`ml/TRAJECTORY_FROZEN_ENCODER_PROSPECTIVE_SHADOW_V1.md`

Target RPC:

`public.get_trajectory_frozen_encoder_shadow_due_v1()`

Workflow:

`.github/workflows/trajectory-frozen-encoder-shadow-v1.yml`

Schedule:

`20 * * * *`

Persistence:

- `private.daily_trajectory_attempts_v1`;
- `private.daily_trajectory_predictions_v1`;
- `private.daily_trajectory_scores_v1`.

The workflow passed end-to-end on 2026-10-29 after the exact frozen head artifact was persisted to `main`.

At the first fresh snapshot before a due cutoff, shadow evidence was 0 attempts / 0 predictions / 0 scores. Do not backfill later if a genuine window is missed.

---

## Validation / evidence rules

- event is the independent attendance unit;
- all prefixes from one event stay together;
- no random daily-row/snapshot CV;
- no future target trajectory;
- no target attendance during inference;
- genuine observations only;
- missing/hidden inventory is never zero;
- structural prior must genuinely exist by the target cutoff;
- persist prospective forecasts before outcomes;
- score only after genuine confirmed outcomes;
- prospective attendance evidence outranks historical research.

---

## P9 separation

P9 v1 and Family Fallback v2 are separate frozen evidence contracts.

Never:

- pool their rows;
- lower v1 support because v2 covers more cases;
- retro-predict a missed v1 event with v2;
- tune from early prospective scores and keep the same version.

---

## Next decision rule

Do not start another broad model tournament now.

The supported SSP encoder has answered the representation question. The current question is:

> **Does the frozen encoder + frozen attendance head lower future event-balanced attendance MAE relative to structural P50?**

Answer only from genuinely future immutable P-7/P-3/P-1 predictions and outcomes.

If the candidate is materially changed after outcomes are seen, create a new precommit/version.

---

## Hard rules

- protect imminent P9/Form5/frozen-encoder windows first;
- no fabricated history;
- no support-gate relaxation for coverage;
- no post-result v1 tuning;
- no automatic production activation;
- keep `live_adjustment = 0`.

The old ChatGPT Beyond readiness automations remain disabled. Do not enable them implicitly.
