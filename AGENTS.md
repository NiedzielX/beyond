# Beyond Agent Instructions

Last updated: **2026-11-08**

## Read first

1. `ml/MAE_RESEARCH_ROADMAP_V6.md`;
2. `ml/EXECUTION_PLAN_CURRENT.md`;
3. `ml/PROGRESS_TRACKING.md`;
4. `ml/TRAJECTORY_FORECASTING_PLAN_V1.md`;
5. `ml/NEXT_SESSION_HANDOFF.md` — current operational state only, not MAE strategy;
6. only then inspect code, workflows, SQL, GitHub Actions and live DB.

Query live machine state before acting on prospective windows. Read the exact precommit before touching a frozen experiment.

Roadmap v6 is canonical.

## Required project memory and SDD workflow

All AI agents must use the shared `.ai/` structure, including agents using Claude. `CLAUDE.md` describes the same obligations; these files must not define competing ML plans.

- `.ai/specs/YYYY-MM-DD-slug.md`: specifications and acceptance criteria before a material implementation or experiment. Link the canonical `ml/` plan/precommit rather than duplicating or weakening it. `.ai/specs/implemented/` contains completed specifications with evidence; `.ai/specs/archive/` contains withdrawn or superseded specifications. Keep blocked or partially deployed work in active `specs/`.
- `.ai/runs/YYYY-MM-DD-slug.md`: one audit log for each logical autonomous AI run. Record the goal, concrete changes, checks, evidence locations, remaining blockers and next action. Update the log as the run progresses and before handoff. Multiple steps can belong to one run; do not stop for approval after each step.
- `.ai/lessons.md`: read this index after the canonical ML state files and before implementation. Record reusable findings and link detailed notes in `.ai/lessons/`. After a meaningful bug fix, failed hypothesis or operational discovery, update existing lessons or add a focused note; preserve the evidence and scope of the finding.

Use actual execution dates and lowercase descriptive slugs. Never put credentials, tokens or private raw data in specifications, logs or lessons. Distinguish planned/configured, successfully executed, and proven end-to-end. Update canonical status and `.ai/` records together; never rewrite missed observations or unsuccessful experiments as successful history. Follow the user's authorized scope autonomously; these documentation requirements do not create an additional approval gate.

Protecting frozen experiments does not stop R&D. The restriction on new model search concerns retuning the frozen model on the same exposed evidence. New, separately versioned and precommitted MAE experiments proceed in parallel, without contaminating existing evaluation streams:

`baseline -> new information -> simple challenger -> event-grouped/PIT-safe MAE -> freeze -> prospective shadow -> genuine outcomes`

A new version name alone does not make previously exposed test events independent again.

---

## Current MVP product acceptance

Before implementing the rolling72 model, read `ml/ROLLING_72H_LITERATURE_REVIEW_2026-11-08.md` and its explicit source-access limits. Preserve the distinction between future demand/attendance forecasting and identifying the revenue effect of a price/ad intervention. MAE remains primary; advance warning/sector coverage need their own declared evaluation, and no cited method guarantees1200MAE.

**Whole sales lifecycle:** rolling +24/+48/+72 h forecasts start with the first genuine observed datum after sales open, including the one-observation case, and are re-issued throughout tracking. At P-50 the targets are P-49/P-48/P-47; at P-15 they are P-14/P-13/P-12. These are future horizons, not a final72h eligibility window or a requirement for24h of prior history. Preserve late-start/missing-history gaps and immutable issue times; existing frozen cold-start gates stay unchanged.

Follow `ml/ROLLING_72H_COMMERCIAL_FORECAST_PLAN_V1.md`: begin with the first genuine observation and forecast the following24/48/72hours from all then-known history. Clubs need48–72hours to act under explicit price/promotion/pool assumptions. Do not narrow this to P-15 or final24C1, treat terminal-attendance history as a future path, or infer causal intervention effects from unavailable data. This product scope complements the separate attendance research objective and preserves all frozen contracts.

**Persistent accuracy goal:** minimise genuine prospective event-balanced MAE; continue aiming for **approximately 1200 seats attendance MAE** as a research milestone, with lower better. Evaluate rolling24/48/72h errors separately. A functioning path, attractive plot or low inventory error does not replace this goal or demonstrate attendance accuracy. Preserve exact cohorts, coverage and frozen evidence gates.

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

`20,50 * * * *`

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

Do not restart a broad model tournament to repair frozen results on the same exposed cohort. This is not a global research pause: new-information experiments with their own versions, precommits and valid evaluation designs may proceed now under roadmap v6.

The supported SSP encoder has answered its frozen representation question. For the existing frozen attendance candidate, the current question is:

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
