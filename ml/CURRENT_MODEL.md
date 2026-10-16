# Beyond Ticketing — Current Model & Product State

Last product-direction update: **2026-10-16**

This is the canonical short-form state. Read `AI_BOOTSTRAP.md` first in a cold session. Operational C1 v8 details are in `ml/C1_V8_PROSPECTIVE_SHADOW_V1.md`.

## Current north star

Beyond is a **live demand decision system**, not only an attendance model.

Primary decision flow:

`Structural Prior -> Live Trajectory -> Expert Reliability -> Sector Gap -> No-action Projection -> Pricing Scenario -> Recommendation -> Execution -> Outcome`

Public seat-map inventory is a **demand proxy, not confirmed paid sales**.

## Structural Prior runtime

All five horizons are executable and frozen:

| Horizon | Model spec | 2023/24 dev MAE | 2024/25 historical MAE | 2025/26 historical MAE |
|---|---|---:|---:|---:|
| T-30 | `structural-prior-runtime-v1-t30-extra-full` | 2,559.7 | 1,889.4 | 1,846.3 |
| T-14 | `structural-prior-runtime-v1-t14-hist-base` | 2,340.0 | 1,748.5 | 1,870.4 |
| T-7 | `structural-prior-runtime-v1-t7-gbr-base` | 2,476.8168 | 1,777.6927 | 1,802.2756 |
| T-3 | `structural-prior-runtime-v1-t3-hist-full` | 2,311.6247 | 1,661.7160 | 1,775.0691 |
| T-1 | `structural-prior-runtime-v1-t1-hist-full` | 2,347.9931 | 1,651.7336 | 1,742.8351 |

Frozen bundle:

`structural-prior-runtime-v1-frozen-2026-10-15-t1`

Scheduled Structural Prior inference is load + predict only.

Production remains:

`live_adjustment = 0`

## Historical validation status

Canonical history:

- Ekstraklasa 2021/22–2025/26;
- 1,530 matches;
- 7,650 horizon rows;
- verified historical capacity coverage 100%.

2024/25 and 2025/26 are not pristine untouched T-30 holdouts for new R&D. Prospective 2026/27 evidence is now critical fresh evidence.

## Live trajectory state

Canonical contract:

`live-trajectory-v1.1`

Trajectory gap:

`trajectory-gap-v1`

Statuses:

- `UNDERPERFORMING`;
- `ON_TRACK`;
- `OUTPERFORMING`;
- `INSUFFICIENT_SIGNAL`.

## C1-alpha evidence base

Development evidence currently contains:

- 9 completed in-domain Ekstraklasa events;
- 206 PIT-valid full-trajectory rows;
- 30 regularized PIT-valid final-24h rows;
- 8/9 events with PIT-safe T-24 `hybrid_v6`.

The 20-independent-match rule is a later promotion gate, not a training-start gate.

## C1-alpha R&D ladder

| Version | Formulation | Main result | Decision |
|---|---|---:|---|
| v1 | all-phase trajectory | incumbent remained best | reject mixed-phase formulation |
| v2 | final-24h live expert | **2,929.3 MAE** | retain expert |
| v3 | nested threshold/blend | 3,054.3 | reject |
| v4 | stacked/meta gate | 3,106.8 | reject |
| v5 | stack + `hybrid_v6` | 3,073.8 | reject |
| v6 | one-row T-24 challenger | 3,873.2 LOEO / 3,989.8 LOCO | reject T-24-only direction |
| v7 | expert-reliability diagnostic | disagreement + live direction distinguish experts | diagnostic complete |
| v8 | fixed PIT-safe expert switch | **2,713.3 window / 1,998.1 latest-row MAE** | frozen prospective shadow candidate |

Canonical evidence:

- `ml/results/C1_ALPHA_MODEL_TOURNAMENT_V1_2026-10-16.md`;
- `ml/results/C1_ALPHA_T1_TOURNAMENT_V2_2026-10-16.md`;
- `ml/results/C1_ALPHA_T1_GATED_V3_2026-10-16.md`;
- `ml/results/C1_ALPHA_T1_STACKED_V4_2026-10-16.md`;
- `ml/results/C1_ALPHA_T1_HYBRID_GATE_V5_2026-10-16.md`;
- `ml/results/C1_ALPHA_T24_RESIDUAL_V6_2026-10-16.md`;
- `ml/results/C1_ALPHA_V2_EXPERT_RELIABILITY_V7_2026-10-16.md`;
- `ml/results/C1_ALPHA_RELIABILITY_POLICY_V8_2026-10-16.md`.

## v2 live expert

Frozen expert lineage:

`ridge_directocc_compact_generic_a10`

Development LOEO:

- Structural Prior T-1: **3,968.7 MAE**;
- v2 live expert: **2,929.3 MAE**;
- relative improvement: **26.19%**;
- non-deployable prior/live oracle: **1,867.9 MAE**.

The live expert is complementary but too unstable for unconditional replacement.

## v8 policy

Policy ID:

`c1-alpha-reliability-policy-v8-fixed-10pp-positive-slope-20pp-single`

PIT rule:

- one live observation: LIVE only if prior/live disagreement >= **20 pp verified capacity**;
- two or more observations: LIVE only if disagreement >= **10 pp** and live-prediction slope to date is strictly positive;
- otherwise PRIOR.

No selector model or threshold grid is fitted in v8.

Development replay:

- Prior: **3,968.7 MAE**;
- v2 Live: **2,929.3 MAE**;
- v8 window: **2,713.3 MAE**;
- v8 latest row: **1,998.1 MAE**;
- worst event degradation vs Prior: **203.3**;
- oracle: **1,867.9**.

This replay is development evidence only because the v8 thresholds were designed after v7 on the same 9 events.

## Frozen prospective v2+v8 package — LIVE

Package:

`c1-shadow-v8-frozen-2026-10-16-n9`

Status:

`EXPERIMENTAL_SHADOW`

Frozen artifact:

`ml/artifacts/c1_shadow_v8/c1_v2_live_expert_v1.joblib`

Artifact SHA256:

`df31af5effcda2d2f1e58265c7e954cc04edf0e90b48501403eb4e4afd94edf2`

Training-contract SHA256:

`0a3edde223d8b6e64652f3fc8f79228998ac0d93a90fdaa9fc48311f98dee304`

Artifact commit:

`9bcf8fe83f85ee7e47a555e975352b8438ea4e3d`

Frozen training events:

`[1, 3, 4, 8, 9, 12, 13, 14, 17]`

The scheduled runtime loads the artifact and predicts only. It contains no fitting path.

## Prospective shadow pipeline — LIVE

Operational runbook:

`ml/C1_V8_PROSPECTIVE_SHADOW_V1.md`

Scheduler:

`.github/workflows/c1-shadow-v8-inference.yml`

Cadence:

`9,24,39,54 * * * *`

The live shadow path now performs:

1. forward-only main-branch OIDC authentication;
2. natural T-1 eligibility check;
3. max four PIT-valid final-24h 6-hour representatives;
4. frozen v2 artifact inference;
5. frozen v8 policy selection;
6. append-only pre-outcome decision persistence;
7. post-outcome scoring of only previously persisted decisions.

Pre-outcome evidence:

`private.c1_shadow_v8_predictions_v1`

Post-outcome scores:

`private.c1_shadow_v8_event_scores_v1`

The writer rejects known outcomes and non-PIT/non-T1 evidence. The scorer never reconstructs a missing decision after the outcome is known.

## Current prospective evidence state

As of initial deployment on 2026-10-16:

- prospective prediction rows: **0**;
- prospective scored events: **0**;
- latest full main workflow run completed successfully;
- zero candidates is expected because the next eligible matches were still resolved at T-3 during deployment.

No historical backfill was performed.

The first valid checkpoint is the first non-zero decision created after a genuine T-1 prior becomes naturally due. The second is its post-outcome score after actual attendance is confirmed.

## Governance during prospective validation

Do not:

- retune 10 pp / 20 pp / positive-slope thresholds;
- refit the package automatically;
- silently add prospective events to training;
- backfill a missed prediction after an outcome is known;
- use future timestamps to force T-1 evidence;
- overwrite pre-outcome evidence;
- label the original v8 replay as fresh validation;
- write v8 into production forecast values.

Any retrain requires an explicit new package version and governance decision.

## C1 promotion gate

Promotion requires enough genuinely prospective independent completed events, positive uplift vs Structural Prior, acceptable tail risk, a frozen reproducible package, human review and explicit promotion. No automatic production promotion exists.

## E0 — Sector Decision & Dynamic Pricing MVP

This remains a parallel product priority and does not wait for C1 promotion.

Canonical spec:

`ml/SECTOR_DECISION_PRICING_V1.md`

Required outputs include sector trajectory gap/status, no-action projection, pricing scenarios, recommendation rationale and decision/execution history.

No automatic production price changes:

`auto_price_change_allowed = false`

## Immediate implementation sequence

1. keep the frozen v2+v8 shadow package unchanged and collect the first genuine T-1 prospective decisions;
2. expose read-only prospective shadow status/evidence for dashboard/operations;
3. score every completed prospective event from already-persisted decisions;
4. keep production Structural Prior/orchestrator unchanged with `live_adjustment=0`;
5. continue sector gap/status and no-action projection;
6. continue price-data ingest and E0 pricing scenarios;
7. persist recommendation/decision/execution history;
8. continue T-30 R&D in parallel, not as the product critical path.

## Non-negotiable rules

- never call public inventory paid sales;
- never report snapshot rows as independent matches;
- never present the oracle as deployable;
- never retune v8 on the original 9 events;
- scheduled inference loads frozen artifacts and never fits;
- prospective evidence must exist before outcome to count as prospective;
- production remains `live_adjustment = 0` until explicit promotion.
