# Beyond Ticketing — Live Demand Engine v1 Plan

Last updated: **2026-10-16**

## Current position

> **Phase A — Foundation: DONE**  
> **Phase B — Shadow Forecasting: DONE**  
> **Five-horizon Structural Prior materialization: DONE / LIVE**  
> **Phase C1-alpha — Live expert reliability R&D: ACTIVE NOW**  
> **Phase C1 promotion — EVIDENCE-GATED**  
> **Phase E0 — Sector Decision & Dynamic Pricing MVP: START NOW**

| Phase | Scope | Status |
|---|---|---|
| A — Foundation | Canonical live trajectory / PIT evidence / registry | **DONE** |
| B — Shadow Forecasting | Structural Prior, trajectory gap, shadow revisions, audit | **DONE** |
| C0 — Provisional live decision layer | Bounded / versioned continuation logic, not promoted ML | **START NOW** |
| C1-alpha | Learn when to trust Structural Prior vs final-24h live expert | **ACTIVE NOW** |
| C1 — Promoted Learned Live Correction | Production promotion after sufficient evidence | **EVIDENCE-GATED** |
| D — Probabilistic | Calibrated P10/P50/P90 | TODO |
| E0 — Sector Decision & Dynamic Pricing | Sector diagnosis, no-action projection, pricing scenarios, dashboard | **START NOW** |
| E1 — Learned Pricing / Intervention | Learned elasticity and intervention uplift | **EVIDENCE-GATED** |

Canonical state:

- `ml/CURRENT_MODEL.md`;
- `AI_BOOTSTRAP.md`;
- `ml/C1_MODEL_TOURNAMENT_V1.md`;
- latest `ml/results/C1_ALPHA_*.md`.

## Product purpose

Beyond must continuously answer:

1. where the event is likely to finish;
2. which sector is underperforming / outperforming;
3. what happens if the current trajectory continues;
4. what pricing action should be considered;
5. what happened after the club acted.

Primary decision unit:

`event -> sector -> trajectory -> no-action projection -> pricing scenario -> recommendation`

## Current forecasting stack

`Structural Prior -> live-trajectory-v1.1 -> trajectory-gap-v1 -> live evidence -> decision layer`

Current promoted learned correction:

`live_adjustment = 0`

No C1-alpha challenger has been frozen for production/shadow correction yet.

## Structural Prior

All five horizons are executable and frozen:

- T-30 `structural-prior-runtime-v1-t30-extra-full`;
- T-14 `structural-prior-runtime-v1-t14-hist-base`;
- T-7 `structural-prior-runtime-v1-t7-gbr-base`;
- T-3 `structural-prior-runtime-v1-t3-hist-full`;
- T-1 `structural-prior-runtime-v1-t1-hist-full`.

Frozen bundle:

`structural-prior-runtime-v1-frozen-2026-10-15-t1`

Scheduled inference is load + predict only.

## C1-alpha evidence base

Current-domain completed evidence:

- 9 Ekstraklasa events;
- 206 PIT-valid trajectory rows at regularized 6h cadence;
- 8/9 events with PIT-safe T-24 `hybrid_v6`;
- 7 distinct current home clubs in the event-level dataset.

Versioned exports:

- full trajectory `c1-alpha-training-export-v1`;
- full trajectory + hybrid `c1-alpha-training-export-v2`;
- lightweight event payload `c1-alpha-event-training-export-v1`.

The 20-independent-match rule is **not a training-start gate**. It remains a later promotion/validation gate.

## C1-alpha completed experiments

| Version | Formulation | MAE | Main conclusion |
|---|---|---:|---|
| v1 | all-phase trajectory | ~3,685 incumbent remained best | mixed phase coverage is wrong formulation |
| v2 | final-24h live expert | **2,929.3** | strongest aggregate challenger, but unstable |
| v3 | nested threshold/blend gate | 3,054.3 | safer tail risk, too conservative |
| v4 | stacked/meta gate | 3,106.8 | more stacking did not solve selection |
| v5 | stacked gate + `hybrid_v6` | 3,073.8 | hybrid helps, still unstable |
| v6 | one-row T-24 challenger | 3,873.2 LOEO / 3,989.8 LOCO | T-24-only discards useful trajectory signal |

Canonical evidence files:

- `ml/results/C1_ALPHA_MODEL_TOURNAMENT_V1_2026-10-16.md`;
- `ml/results/C1_ALPHA_T1_TOURNAMENT_V2_2026-10-16.md`;
- `ml/results/C1_ALPHA_T1_GATED_V3_2026-10-16.md`;
- `ml/results/C1_ALPHA_T1_STACKED_V4_2026-10-16.md`;
- `ml/results/C1_ALPHA_T1_HYBRID_GATE_V5_2026-10-16.md`;
- `ml/results/C1_ALPHA_T24_RESIDUAL_V6_2026-10-16.md`.

## Most important C1 finding

The best honest aggregate live challenger is the v2 final-24h expert:

`ridge_directocc_compact_generic_a10`

- Structural Prior T-1: **3,968.7 MAE**;
- v2 live expert: **2,929.3 MAE**;
- relative improvement: **26.19%**;
- improvement rate: **4/9**;
- worst-event degradation: **4,748.6**.

The pair has a non-deployable outcome-aware oracle switch around:

**1,867.9 MAE**

That is the key opportunity. The next problem is **expert reliability / expert selection**, not another generic learner tournament.

Do not present the oracle as deployable.

## C1-alpha v7 — Expert Reliability Diagnostic — NEXT

Build one diagnostic row per completed event for the existing Structural Prior + v2 live pair.

### Required PIT-safe features

Structural Prior context:

- P50;
- expected occupancy;
- round number;
- current-season completed home evidence available before T-1.

Final-24h live expert behaviour:

- earliest v2 estimate;
- latest v2 estimate;
- prior-vs-live disagreement at earliest/latest observation;
- prediction range;
- standard deviation;
- slope / direction across the final 24h;
- number of live observations;
- observation-window duration.

Evidence quality:

- signal readiness;
- feature quality;
- matched-sector vs raw-only regime;
- release activity;
- sector-coverage change;
- data-gap flags where available.

Evaluation-only labels:

- actual attendance;
- Structural Prior error;
- v2 error;
- oracle winner (`PRIOR` / `LIVE`).

These evaluation labels must never enter the PIT feature matrix.

### Purpose

Answer:

> What observable reliability pattern separates the events where Structural Prior is already excellent from the events where the final-24h live expert repairs a large miss?

Do not start v7 with another broad model/hyperparameter sweep.

After diagnosis, define one small predeclared reliability policy and validate it by whole-event holdout.

## C0 — Provisional decision layer

C0 can continue in parallel with C1 R&D.

Allowed:

- continuation/no-action event projection;
- explicitly provisional bounded live revision logic;
- sector diagnosis;
- reason codes;
- dashboard decision support.

Required labels:

- `PROVISIONAL`;
- `SCENARIO`;
- `CURRENT TRAJECTORY CONTINUES`.

## C1 promotion

Promotion still requires:

- enough independent completed events;
- positive uplift vs Structural Prior;
- acceptable tail risk;
- frozen model/data/feature package;
- human review;
- no automatic activation.

## Phase D — Probabilistic

Later:

- P10/P50/P90;
- pinball loss;
- empirical coverage;
- horizon-specific calibration.

Do not fabricate confidence intervals before calibration.

## E0 — Sector Decision & Dynamic Pricing MVP

This remains part of the near-term product and does not wait for C1 promotion.

### Sector trajectory

For every observable sector track:

- current availability;
- absorption/sell-through proxy;
- velocity/acceleration;
- expected progress;
- observed progress;
- trajectory gap;
- status/confidence;
- release/coverage/data-quality flags.

### No-action projection

Preferred wording:

**Projected outcome if current trajectory continues**

This is a continuation scenario, not a causal counterfactual.

### Dynamic pricing scenarios

Per sector / price band evaluate configurable scenarios such as:

- `-10%`;
- `-5%`;
- `HOLD`;
- `+5%`;
- `+10%`.

Before learned elasticity exists, label the output as assumption-based scenario analysis.

No automatic production price changes:

`auto_price_change_allowed = false`

### Recommendation tracking

Persist recommendation, rationale, assumption/model version, club decision, execution time/action and later outcome from day one.

## Validation rules

- random snapshot split is forbidden;
- all rows from one event stay together in a validation fold;
- snapshot counts are evidence density, not independent match count;
- actual attendance and oracle winner are evaluation labels only;
- do not tune a selector to its outer held-out event;
- 2024/25 and 2025/26 are not pristine untouched T-30 holdouts for future T-30 R&D.

## Immediate implementation sequence

1. build and persist **v7 expert reliability diagnostic**;
2. define one small predeclared reliability policy from v7 PIT semantics;
3. validate that policy with whole-event holdout;
4. keep Structural Prior/orchestrator healthy and `live_adjustment=0`;
5. continue sector gap/status and no-action projection;
6. continue price-data ingest and E0 pricing scenarios;
7. persist recommendation/decision/execution history;
8. keep collecting prospective 2026/27 evidence;
9. continue T-30 R&D in parallel.

## Product target

> **Beyond should tell the club where the event is going, whether the live evidence is strong enough to revise the Structural Prior, which sectors are falling behind, what is likely to remain unsold if nothing changes, and what price action is worth testing — while learning from every real decision and outcome.**
