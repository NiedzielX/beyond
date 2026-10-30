# Beyond Ticketing — Agent Start Here

Last updated: **2026-10-30**

## Mission

The primary objective is:

> **Minimize true prospective event-balanced attendance-forecast MAE using PIT-safe, reproducible evidence.**

Do not optimize for number of workflows, snapshots, experiments, model complexity or prediction coverage. Those are enabling metrics only.

Operational protection of prospective cutoffs is mandatory, but it is **not the research objective**. The research objective is lower future MAE.

Production remains OFF unless separately reviewed:

- `live_adjustment = 0`
- `production_change = false`

---

## Read in this order

### 1. `ml/MAE_RESEARCH_ROADMAP_V5.md`

Read this first for the research strategy.

It defines:

- the MAE North Star;
- the difference between evidence collection and model development;
- the daily trajectory programme;
- simple-model and sequence-model lanes;
- PIT-safe / event-grouped evaluation rules;
- how new research is allowed without mutating frozen prospective lanes.

### 2. `ml/EXECUTION_PLAN_CURRENT.md`

Read this second for the current execution state and frozen contracts.

Use it to understand:

- which models/candidates are frozen;
- which cutoffs are protected;
- current eligibility contracts;
- current prospective evidence;
- scheduler/data-collection safeguards;
- the precommitted prospective evaluation method;
- the current business-meaningful MAE threshold.

If a research idea conflicts with a frozen evidence contract, create a **new version / new research lane**. Never mutate the frozen lane.

### Important interpretation rule

If `ml/EXECUTION_PLAN_CURRENT.md` says that no new model search is justified, interpret that statement **only as a prohibition on post-hoc retuning or reopening the frozen/exposed trajectory candidate on the same evidence**.

It does **not** mean that MAE R&D stops.

The MAE programme explicitly continues in parallel through separately versioned hypotheses that add genuinely new PIT-safe information or a materially new representation. `ml/MAE_RESEARCH_ROADMAP_V5.md` and this file define that research direction.

### 3. `ml/PROGRESS_TRACKING.md`

Use this to understand what has already been tried and what must not be repeated blindly.

Especially distinguish:

- supported findings;
- rejected mechanisms;
- frozen candidates;
- prospective evidence still collecting;
- infrastructure that is already complete.

### 4. `ml/TRAJECTORY_FORECASTING_PLAN_V1.md`

Read before changing trajectory features, daily cutoffs, sequence representations or trajectory evaluation.

### 5. `ml/NEXT_SESSION_HANDOFF.md`

Use this for **live operational context only**:

- imminent cutoffs;
- current source quirks;
- scheduler state;
- known missed windows;
- what needs immediate verification.

Do not treat the handoff as the MAE research strategy.

### 6. Actual implementation

Only after reading the documents above, inspect:

- `.github/workflows/`
- `ml/`
- `supabase/sql/`
- `supabase/functions/`
- recent GitHub Actions runs
- live DB state / decision RPCs

The implementation and live DB are the authority for whether something actually ran. Markdown is the authority for the intended research contract unless implementation proves that documentation is stale.

---

# MAE improvement programme

Two workstreams run in parallel.

## Workstream A — protect clean prospective evidence

Before starting R&D, check whether an immutable P9 / trajectory / Form5 cutoff is currently due or about to close.

Rules:

1. Protect genuine cutoffs first.
2. Never backfill missed prospective windows.
3. Fail closed when source semantics are unknown.
4. Never loosen frozen eligibility rules to create a prediction.
5. Distinguish `configured`, `workflow succeeded`, and `proven end-to-end in DB`.

This workstream protects the truth of the evaluation stream. It does not replace model R&D.

## Workstream B — actively reduce MAE

Continue model development in **separately versioned research lanes** while frozen prospective candidates collect evidence.

### Priority 1 — maintain a hard baseline

Always compare against the current structural incumbent using event-balanced MAE.

Do not accept a challenger because it is more sophisticated. It must reduce error.

### Priority 2 — add genuinely new predictive information

Research should prioritize signals that may explain attendance error not already captured by the structural baseline.

Current hypothesis families:

1. **Historical + current-season team strength/context**
   - league position at the forecast cutoff;
   - recent results / form;
   - opponent strength;
   - season state and comparable historical matches.

2. **Future-fixture context**
   - attractiveness of the next match(es);
   - fixture congestion;
   - whether a materially stronger / more attractive fixture shortly after the target event may shift demand.

3. **Squad context**
   - expected / available squad strength;
   - important absences;
   - material changes in player availability where the information was genuinely known at the cutoff.

4. **Live ticket-demand trajectory**
   - current inventory/demand proxy;
   - 1d / 3d / 7d change;
   - velocity / acceleration;
   - plateau vs late acceleration;
   - observation density and staleness;
   - similarity to prior PIT-safe completed trajectories;
   - frozen/self-supervised trajectory representations where justified.

5. **Additional PIT-safe context**
   - odds / market information;
   - other context only when it adds new information and can be timestamped correctly.

Do not throw all features into one model first. Test hypothesis families independently enough to understand where the gain comes from.

### Priority 3 — simple benchmark before added complexity

For each new information family, first establish whether signal exists with a restrained benchmark, typically as a residual correction over the structural incumbent.

Preferred order:

1. Ridge / ElasticNet residual benchmark;
2. restrained tree/boosting challenger where justified;
3. trajectory similarity / engineered-trajectory model;
4. sequence model only when the ordered trajectory could contain information the engineered representation misses.

Do not perform broad cosmetic hyperparameter sweeps on an exposed evaluation cohort.

### Priority 4 — evaluation protocol

Every MAE experiment must be:

- PIT-safe;
- event-grouped;
- reproducible;
- compared on the same eligible events;
- scored primarily by **event-balanced MAE**.

Also report:

- Delta MAE vs incumbent;
- event improvement rate;
- median event Delta AE;
- P90 AE / worst-event degradation;
- signed bias;
- coverage;
- number of independent events and clubs;
- per-horizon MAE when applicable.

Daily rows from the same event are not independent observations.

### Priority 5 — promotion path

A research result is not production evidence.

Path:

`historical/event-grouped research -> precommit -> freeze -> prospective shadow -> genuine outcomes -> event-balanced Delta MAE -> review`

Current precommitted business-resolution threshold for the active prospective comparison is:

> **Delta MAE <= -550 seats**

Treat this as a business-meaningful accuracy threshold, not as permission to tune toward exactly 550.

---

# What not to do

- Do not retune the current frozen trajectory head after seeing early prospective outcomes.
- Do not rewrite missed historical/prospective windows.
- Do not convert unknown or hidden ticket inventory to zero.
- Do not use future league position, future results, future squad knowledge or future ticket observations at an earlier cutoff.
- Do not count multiple horizons from one event as multiple independent events.
- Do not restart rejected model families on the same exposed cohort without a materially new mechanism or new information.
- Do not change production automatically from a research result.

---

# First question for every next task

Ask:

> **What is the highest-value next action that can honestly reduce future prospective MAE, while preserving the validity of already-running evidence streams?**

If there is an imminent evidence cutoff, protect it first.

Otherwise continue the highest-value MAE hypothesis or experiment — do not spend the session only maintaining infrastructure.