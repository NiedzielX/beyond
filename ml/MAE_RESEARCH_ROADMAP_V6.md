# Beyond Ticketing — MAE Research Roadmap v6

Last updated: **2026-11-03**

Status: **CANONICAL MAE RESEARCH STRATEGY**

Supersedes the strategic direction in `ml/MAE_RESEARCH_ROADMAP_V5.md`.

Operational source of truth remains:

`ml/EXECUTION_PLAN_CURRENT.md`

Detailed trajectory design remains:

`ml/TRAJECTORY_FORECASTING_PLAN_V1.md`

---

# 1. North Star

> **Minimize true prospective event-balanced attendance-forecast MAE at decision-relevant horizons using PIT-safe, reproducible evidence.**

Primary selector:

`Delta MAE = challenger event-balanced MAE - incumbent event-balanced MAE`

Desired direction:

`Delta MAE < 0`

Current business-meaningful scale for the active frozen prospective comparison remains:

`Delta MAE <= -550 seats`

This threshold is a business-resolution guard for the active frozen comparison. It is not a tuning target and does not permit post-hoc optimization toward exactly 550 seats.

Production remains unchanged unless separately reviewed:

- `live_adjustment = 0`
- `production_change = false`

---

# 2. Strategic change in v6

V5 correctly moved Beyond toward daily trajectory modelling. V6 keeps that programme, but changes the research operating model.

The main research question is no longer:

> Which trajectory model should we try next?

It is:

> **Where does the incumbent lose MAE, what information could explain that error, and does that information reduce the same-event PIT-safe error under event-grouped validation?**

Therefore the programme becomes **error-driven rather than feature-driven**.

Trajectory remains a high-priority signal family, but it competes with structural, contextual, horizon-specific and club-specific explanations of error.

Do not add a feature merely because it is available. Add it because a documented error pattern creates a falsifiable hypothesis that the feature can explain.

---

# 3. Scientific rules that do not change

1. Event/fixture is the independent attendance-evaluation unit.
2. All rows/prefixes from one event stay in the same train/test fold.
3. Random daily-row/snapshot splitting is forbidden as headline evidence.
4. Every feature must satisfy point-in-time availability at the forecast cutoff.
5. No target future trajectory may enter an earlier cutoff.
6. No target attendance may enter prediction construction.
7. Frozen prospective lanes remain immutable after exposure to evaluation outcomes.
8. Failed or insufficient experiments are valid evidence and must not be silently repaired.
9. Historical reconstruction/backfill may be research data only when explicitly labelled as such; it is never prospective evidence.
10. Any material model, target, feature, cap, horizon or eligibility change requires a new version/precommit before prospective use.
11. Event-balanced MAE remains the primary point-forecast selector.
12. Bias, median event Delta AE, P90/worst-event degradation, improvement rate and coverage remain mandatory guardrails.
13. Multiple horizons from one event do not create multiple independent events.
14. No research result activates production automatically.
15. Missing/hidden inventory remains missing/hidden. Unknown is never converted to zero to improve coverage.

---

# 4. Two parallel workstreams

## Workstream A — protect evidence integrity

Protect genuine immutable cutoffs and source semantics:

- P9 v1/v2;
- frozen trajectory shadow;
- Form5 prospective;
- P11/P4a genuine collection;
- any later precommitted prospective challenger.

Rules:

- protect an imminent legal cutoff before optional R&D;
- never backfill a missed prospective window;
- distinguish `configured`, `workflow succeeded`, and `proven end-to-end in DB`;
- operational fixes may improve reliability but must not change frozen prediction semantics.

This workstream protects the truth of evaluation. It is not the primary research objective.

## Workstream B — actively reduce MAE

Outside imminent evidence windows, the default priority is model/data research that can reduce future prospective MAE.

Do not stop R&D merely because one frozen candidate is collecting evidence.

New research must use separately versioned lanes and must not mutate frozen candidates.

---

# 5. MAE-01 — Error decomposition of the incumbent

## Purpose

Before adding features, identify where the current structural incumbent actually loses seats of error.

## Required analysis

Calculate event-level and grouped error at minimum by:

- club;
- forecast horizon;
- attendance level/bucket;
- stadium utilization / fill-rate bucket where verified capacity exists;
- weekday vs weekend;
- competition/season context where available;
- opponent strength/attractiveness proxy where PIT-safe;
- low-demand / normal / near-sellout / sellout-prone regime;
- signed error (overprediction vs underprediction).

Create a ranked review of the largest absolute-error events.

For the worst events, inspect whether error is primarily associated with:

- structural level;
- club-specific bias;
- opponent/context mismatch;
- booking-curve dynamics;
- source/data-quality limitations;
- horizon effects;
- genuinely unpredictable event-specific shocks.

## Deliverable

A reproducible error-decomposition report/table that answers:

> **Which event types currently contribute most to total event-balanced MAE?**

Do not proceed by feature intuition alone when this decomposition can answer the question.

---

# 6. MAE-02 — Re-benchmark the structural baseline

## Purpose

Ensure the incumbent is a genuinely strong baseline before attributing gains to complex challengers.

## Candidate structural signals

Use only PIT-safe information available at the forecast cutoff, such as:

- historical attendance level;
- home-club level;
- opponent strength/attractiveness;
- verified capacity / utilization;
- recent attendance form;
- day/time/calendar context;
- competition/season state;
- current-season standing/form when historically reproducible at the cutoff.

This is not permission for an unrestricted model tournament.

Start with restrained, interpretable baselines and event-grouped temporal validation.

## Decision

The strongest honest structural baseline becomes the research anchor for new versioned research.

Do not replace the currently frozen prospective incumbent retrospectively. A stronger research baseline becomes a new version for future precommit/prospective comparison only.

---

# 7. MAE-03 — Residual context modelling

## Core formulation

Prefer learning what the structural model misses instead of forcing each challenger to relearn attendance from scratch.

`residual_target = actual_attendance - structural_forecast`

Question:

> **What is known about this specific fixture at the cutoff that the structural baseline does not know?**

## Context hypothesis families

Test independently enough to understand incremental value:

1. current-season league position;
2. recent results/form;
3. opponent strength/attractiveness;
4. future-fixture context and fixture congestion;
5. market/odds information when genuinely PIT-safe;
6. squad/absence information only after a reliable timestamped data source exists.

Do not invent a squad/injury feature layer without a trustworthy PIT-safe source.

## First models

Start with small residual learners:

- Ridge;
- ElasticNet;
- restrained tree/boosting challenger only when justified.

The goal is signal detection, not algorithmic novelty.

---

# 8. MAE-04 — Trajectory benchmark

Trajectory remains a major candidate for incremental signal because two events with the same current inventory can have very different demand momentum.

For each eligible cutoff derive PIT-safe features such as:

- current inventory/demand proxy;
- proxy as share of verified capacity;
- 1d / 3d / 7d change;
- velocity;
- acceleration;
- short vs long slope;
- slope change;
- volatility;
- plateau duration/detection;
- late acceleration/surge;
- observation density;
- observation staleness;
- distance from expected historical trajectory;
- similarity to prior completed PIT-safe trajectories.

Compare at least:

1. structural incumbent;
2. engineered-trajectory residual benchmark;
3. trajectory similarity method;
4. frozen/self-supervised trajectory representation where applicable;
5. sequence model only if ordered trajectory plausibly contains information missed by engineered features.

Do not interpret public inventory as confirmed paid sales or attendance.

---

# 9. MAE-05 — Horizon-specific correction

Do not assume one correction mechanism should work equally at every horizon.

Information quality differs materially between early and late forecasts.

Evaluate horizon-specific or horizon-conditioned residual corrections for the product-relevant horizons, including where applicable:

- early/long horizon;
- T-72 / T-48;
- T-24;
- P-7;
- P-3;
- P-1.

Preferred architecture to test:

`Structural Base + Horizon-Specific Residual Correction`

rather than one unconstrained model forced to learn all horizons identically.

Report a horizon MAE curve, not only one aggregate number.

---

# 10. MAE-06 — Demand-regime and club heterogeneity

## Demand regimes

Test whether residual behaviour differs between:

- low-demand events;
- normal-demand events;
- near-sellout events;
- sellout-prone events.

Avoid brittle hard segmentation unless supported by data. Prefer regime features/interactions or partial pooling where sample size is small.

## Club heterogeneity

Clubs may have materially different booking patterns.

Compare carefully:

- global correction;
- club intercept/bias correction;
- club-aware residual model;
- partial-pooling/hierarchical representation.

Do not create independent high-variance ML models per club without enough independent events.

---

# 11. MAE-07 — Controlled ablations and combination tests

Once individual signal families are measured, test whether they are complementary.

Minimum useful ablation structure:

| Variant | Structural | Context | Trajectory | Horizon | Club/regime | Purpose |
|---|---|---|---|---|---|---|
| A | yes | no | no | base | no | anchor |
| B | yes | yes | no | base | no | context incremental value |
| C | yes | no | yes | base | no | trajectory incremental value |
| D | yes | yes | yes | base | no | complementarity |
| E | yes | yes | yes | specific | optional | horizon effect |

Do not throw all available features into the first challenger.

The experiment must reveal **where the gain comes from**.

---

# 12. MAE-08 — Ensemble / calibrated blend

Only after independent signal families demonstrate value should Beyond test blending.

Example research form:

`forecast = structural + alpha * trajectory_residual + beta * context_residual`

or a calibrated blend of independently validated models.

The reason to ensemble must be complementary error, not model count.

Measure error correlation between challengers before increasing complexity.

A more complex ensemble must beat the strongest simpler challenger under the same event-grouped evaluation.

---

# 13. Sequence-model lane

Sequence modelling remains allowed but is no longer automatically the next research step.

Use it when:

1. engineered trajectory features show incremental signal;
2. ordered trajectory plausibly contains residual information they miss;
3. evaluation remains event-grouped and PIT-safe;
4. the sequence model is compared against the same simple trajectory benchmark.

Architecture order remains deliberately small:

1. GRU;
2. LSTM;
3. TCN;
4. compact attention/Transformer only if earlier sequence evidence supports further complexity.

No large TFT/Transformer search without evidence that sequence complexity is warranted.

---

# 14. Error-driven research loop

After every experiment, do not ask:

> What feature can we add next?

Ask:

> **Which remaining event types now contribute most to MAE, and what new PIT-safe information could explain that residual error?**

Research loop:

`measure error -> classify residual failure -> state hypothesis -> add one information family/mechanism -> event-grouped test -> update scoreboard -> freeze/reject -> repeat`

This is the default working method for MAE R&D.

---

# 15. Mandatory experiment scoreboard

Every serious experiment must register at least:

| Field | Required |
|---|---|
| Experiment/version ID | yes |
| Hypothesis | yes |
| Incumbent/version | yes |
| Eligible independent events | yes |
| Distinct clubs | yes |
| Coverage | yes |
| Event-balanced incumbent MAE | yes |
| Event-balanced challenger MAE | yes |
| Delta MAE | yes |
| Event improvement rate | yes |
| Median event Delta AE | yes |
| P90 AE / worst-event degradation | yes |
| Signed bias | yes |
| Per-horizon MAE when relevant | yes |
| PIT audit status | yes |
| Decision | yes |

Do not rely on narrative memory of which model "looked promising".

The scoreboard is the research memory.

---

# 16. Evaluation protocol

Every headline MAE result must be:

- PIT-safe;
- event-grouped;
- reproducible;
- evaluated on the same eligible events for incumbent and challenger;
- primarily scored by event-balanced MAE.

Where sample size permits, use temporal/event-grouped outer validation and keep model selection inside the training side of the split.

Never choose hyperparameters on the same exposed outer outcomes used to claim the final gain.

Daily trajectory rows from one event remain dependent observations.

---

# 17. Promotion path

Historical/grouped research is not prospective evidence.

Promotion path:

`research hypothesis -> event-grouped PIT-safe result -> independent review -> precommit -> freeze -> prospective shadow -> genuine outcomes -> event-balanced Delta MAE -> business/risk guards -> explicit promotion review`

For the active frozen prospective comparison, retain the existing evidence gate and business threshold unless replaced by a separately justified precommit before seeing the relevant future outcomes.

No production activation occurs automatically.

---

# 18. Current execution priority

Unless an immutable evidence window is currently at risk, execute in this order:

1. **MAE-01 — incumbent error decomposition**;
2. **MAE-02 — structural baseline benchmark/audit**;
3. **MAE-03 — context residual benchmark**;
4. **MAE-04 — engineered trajectory benchmark**;
5. **MAE-05 — horizon-specific residual correction**;
6. **MAE-06 — demand-regime and club heterogeneity**;
7. **MAE-07 — controlled context/trajectory ablations**;
8. **MAE-08 — ensemble/calibrated blend**;
9. sequence modelling only where simpler evidence justifies it.

Evidence protection interrupts this order only when a genuine immutable cutoff or source-integrity issue requires immediate action.

---

# 19. What not to do

- Do not retune frozen prospective candidates after seeing early outcomes.
- Do not reopen rejected supervised trajectory mechanics on the same exposed cohort through cosmetic hyperparameter changes.
- Do not backfill missed prospective windows.
- Do not convert hidden/unknown ticket inventory to zero.
- Do not use future league position, future results, future squad knowledge, future odds or future ticket observations at an earlier cutoff.
- Do not count daily prefixes as independent events.
- Do not add squad/injury features until a trustworthy PIT-safe source/lineage exists.
- Do not select a model because it is more sophisticated.
- Do not treat better training fit as evidence.
- Do not change production from research code.

---

# 20. Agent decision rule

For every next task ask:

1. Is an immutable prospective evidence window currently at risk?
2. If not, what error segment contributes most to current MAE?
3. What genuinely new PIT-safe information or mechanism could explain that error?
4. What is the smallest reproducible experiment that can falsify the hypothesis?
5. Will the result be comparable to the incumbent on the same independent events?

> **Choose the next task because it can produce honest evidence about lower future MAE — not because it adds another model, feature, workflow or dataset.**
