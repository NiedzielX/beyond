# Beyond Ticketing — Live Demand Engine v1 Plan

Last updated: **2026-10-16**

## Current position

> **Phase A — Foundation: DONE**  
> **Phase B — Shadow Forecasting: DONE**  
> **Five-horizon Structural Prior materialization: DONE / LIVE**  
> **Phase C1-alpha — v8 prospective shadow package: NEXT**  
> **Phase C1 promotion — EVIDENCE-GATED**  
> **Phase E0 — Sector Decision & Dynamic Pricing MVP: START NOW**

| Phase | Scope | Status |
|---|---|---|
| A — Foundation | Canonical live trajectory / PIT evidence / registry | **DONE** |
| B — Shadow Forecasting | Structural Prior, trajectory gap, shadow revisions, audit | **DONE** |
| C0 — Provisional live decision layer | Bounded / versioned continuation logic, not promoted ML | **START NOW** |
| C1-alpha | Frozen v2+v8 expert-reliability package, prospective evidence | **ACTIVE NOW** |
| C1 — Promoted Learned Live Correction | Production promotion after sufficient fresh evidence | **EVIDENCE-GATED** |
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
2. whether the live evidence is strong enough to revise the Structural Prior;
3. which sector is underperforming / outperforming;
4. what happens if the current trajectory continues;
5. what pricing action should be considered;
6. what happened after the club acted.

Primary decision unit:

`event -> sector -> trajectory -> expert reliability -> no-action projection -> pricing scenario -> recommendation`

## Production forecasting stack

`Structural Prior -> live-trajectory-v1.1 -> trajectory-gap-v1 -> decision layer`

Current promoted learned correction:

`live_adjustment = 0`

v8 must run in a separate `EXPERIMENTAL_SHADOW` path until promotion criteria are satisfied.

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
- 206 PIT-valid full-trajectory rows;
- 30 regularized PIT-valid final-24h rows;
- 8/9 events with PIT-safe T-24 `hybrid_v6`.

The 20-independent-match rule is **not a training-start gate**. It remains a later promotion/validation gate.

## C1-alpha completed work

| Version | Formulation | Main result | Status |
|---|---|---:|---|
| v1 | mixed all-phase trajectory | incumbent remained best | reject |
| v2 | final-24h live expert | **2,929.3 MAE** | retain expert |
| v3 | nested threshold/blend gate | 3,054.3 | reject |
| v4 | stacked/meta gate | 3,106.8 | reject |
| v5 | stacked gate + hybrid | 3,073.8 | reject |
| v6 | one-row T-24 | 3,873.2 LOEO / 3,989.8 LOCO | reject |
| v7 | reliability diagnostic | large disagreement + live direction useful | diagnostic complete |
| v8 | fixed PIT-safe expert switch | **2,713.3 window / 1,998.1 latest-row** | prospective shadow candidate |

Evidence:

- `ml/results/C1_ALPHA_MODEL_TOURNAMENT_V1_2026-10-16.md`;
- `ml/results/C1_ALPHA_T1_TOURNAMENT_V2_2026-10-16.md`;
- `ml/results/C1_ALPHA_T1_GATED_V3_2026-10-16.md`;
- `ml/results/C1_ALPHA_T1_STACKED_V4_2026-10-16.md`;
- `ml/results/C1_ALPHA_T1_HYBRID_GATE_V5_2026-10-16.md`;
- `ml/results/C1_ALPHA_T24_RESIDUAL_V6_2026-10-16.md`;
- `ml/results/C1_ALPHA_V2_EXPERT_RELIABILITY_V7_2026-10-16.md`;
- `ml/results/C1_ALPHA_RELIABILITY_POLICY_V8_2026-10-16.md`.

## v2 expert

Exact expert:

`ridge_directocc_compact_generic_a10`

Development LOEO:

- Prior: **3,968.7 MAE**;
- v2 Live: **2,929.3 MAE**;
- oracle Prior-or-Live: **1,867.9 MAE**.

Do not use v2 unconditionally in production.

## v8 reliability policy

Policy ID:

`c1-alpha-reliability-policy-v8-fixed-10pp-positive-slope-20pp-single`

At each PIT point:

### One live observation

Use LIVE only if:

`abs(prior occupancy - live occupancy) >= 0.20`

### Two or more live observations

Use LIVE only if:

- absolute disagreement >= `0.10`; and
- live prediction slope computed from observations available up to the current row is `> 0`.

Otherwise use PRIOR.

No future row is used in an earlier decision.

Development replay:

- Prior **3,968.7**;
- v2 Live **2,929.3**;
- v8 **2,713.3** window MAE;
- v8 **1,998.1** latest-row MAE;
- worst event degradation only **203.3**;
- oracle **1,867.9**.

Governance:

- thresholds were chosen after v7 analysis of the same 9 events;
- therefore replay is development evidence only;
- do not retune 10 pp / 20 pp / positive-slope rule on these 9 events;
- future 2026/27 outcomes provide the valid prospective test.

## C1-alpha next implementation — frozen prospective shadow package

### A. Freeze the v2 live expert

Fit exact v2 winner on all currently completed in-domain training events.

Freeze:

- estimator/preprocessor artifact;
- exact feature list and ordering;
- package/model ID;
- training event IDs;
- training payload/hash;
- dependency/runtime versions;
- generated-at timestamp;
- Structural Prior bundle dependency;
- v8 policy ID and thresholds.

### B. Shadow inference must not fit

Scheduled runtime:

`load frozen v2 artifact -> predict live P50 -> calculate PIT disagreement/slope -> apply frozen v8 policy -> persist EXPERIMENTAL_SHADOW evidence`

Never call `.fit()` in scheduled inference.

### C. Persist pre-outcome evidence

For every eligible prospective row persist at minimum:

- `ticket_event_id`;
- `as_of_at`;
- `structural_prior_id/model_version`;
- `structural_prior_p50`;
- `v2_live_p50`;
- `abs_disagreement_occupancy`;
- `live_observation_count_to_date`;
- `live_slope_occupancy_per_hour_to_date`;
- `selected_expert`;
- `policy_prediction`;
- `reason_code`;
- `shadow_package_version`;
- `created_at`.

Rows must be written before outcome is known and never rewritten after the fact except explicit correction/audit flow.

### D. Post-outcome scoring

After attendance is known, score the frozen pre-outcome rows against:

- Structural Prior;
- v2 Live;
- v8 selected policy;
- latest-row and event-window MAE;
- event-level degradation/tail risk.

Do not regenerate historical decisions using new outcomes and call them prospective.

## C0 — Provisional decision layer

C0 can continue in parallel with C1 shadow validation.

Allowed:

- continuation/no-action event projection;
- sector diagnosis;
- explicit provisional reason codes;
- dashboard decision support.

Required labels:

- `PROVISIONAL`;
- `SCENARIO`;
- `CURRENT TRAJECTORY CONTINUES`.

## C1 promotion

Promotion requires:

- enough genuinely prospective independent completed events;
- positive uplift vs Structural Prior;
- acceptable tail risk;
- frozen model/data/feature/package contract;
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

This remains a near-term product priority and does not wait for C1 promotion.

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

Before learned elasticity exists, label output as assumption-based scenario analysis.

No automatic production price changes:

`auto_price_change_allowed = false`

### Recommendation tracking

Persist recommendation, rationale, assumption/model version, club decision, execution time/action and later outcome from day one.

## Validation rules

- random snapshot split is forbidden;
- all rows from one event stay together in a validation fold;
- snapshot counts are evidence density, not independent match count;
- actual attendance and oracle winner are evaluation labels only;
- do not retune v8 on the original 9 events;
- do not label the v8 development replay as prospective validation;
- scheduled v2+v8 inference must load frozen artifacts, never fit;
- 2024/25 and 2025/26 are not pristine untouched T-30 holdouts for future T-30 R&D.

## Immediate implementation sequence

1. freeze/version exact **v2+v8 prospective shadow package**;
2. add load+predict-only shadow inference;
3. persist pre-outcome v8 evidence and reason codes;
4. keep production Structural Prior/orchestrator unchanged with `live_adjustment=0`;
5. score each genuinely new completed event against the frozen package;
6. continue sector gap/status and no-action projection;
7. continue price-data ingest and E0 pricing scenarios;
8. persist recommendation/decision/execution history;
9. continue T-30 R&D in parallel.

## Product target

> **Beyond should tell the club where the event is going, whether the live trajectory is strong enough to override the Structural Prior, which sectors are falling behind, what is likely to remain unsold if nothing changes, and what price action is worth testing — while learning prospectively from every frozen pre-outcome decision.**
