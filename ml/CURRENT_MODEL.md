# Beyond Ticketing — Current Model & Product State

Last product-direction update: **2026-10-16**

This is the canonical short-form state. For cold-start instructions read `AI_BOOTSTRAP.md`. For C1-alpha training read `ml/C1_MODEL_TOURNAMENT_V1.md`. For sector/pricing product behaviour read `ml/SECTOR_DECISION_PRICING_V1.md`.

## Current north star

Beyond is a **live demand decision system**, not only an attendance model.

It must answer:

- where the event is likely to finish;
- which sector is underperforming / outperforming;
- what happens if the current trajectory continues;
- what price action is worth testing;
- what happened after the club acted.

Primary decision flow:

`Structural Prior -> Live Trajectory -> Sector Gap -> No-action Projection -> Pricing Scenario -> Recommendation -> Execution -> Outcome`

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

Normal scheduled inference is load + predict only. It must not fit a model.

## Historical validation status

The canonical five-season dataset remains:

- 2021/22–2025/26;
- 1,530 Ekstraklasa matches;
- 7,650 horizon snapshots;
- verified historical capacity coverage 100%.

Important governance update:

**2024/25 and 2025/26 are no longer pristine untouched T-30 holdouts for new R&D cycles.**

They were opened during controlled T-30 challenger verification on 2026-10-16. They may be used as fixed historical regression evidence, but must not be repeatedly tuned against or relabeled as untouched.

Fresh validation for new learned live/pricing decisions comes primarily from prospective **2026/27** evidence.

T-30 governance:

`ml/T30_RND_GOVERNANCE_V2.md`

## T-30 R&D state

Current production T-30 remains:

`structural-prior-runtime-v1-t30-extra-full`

Recent controlled challengers did not justify promotion:

- v2 ExtraTrees regularization: rejected;
- v3 raw historical baseline smoothing: research signal only, not robust enough;
- v4 occupancy-normalized anchor: rejected;
- v5 cold-start-only anchoring: stopped at pre-validation;
- v6 explicit baseline occupancy feature: did not pass the rolling-origin gate.

Merged error audit:

`ml/results/T30_PREVALIDATION_ERROR_AUDIT_V1_2026-10-16.md`

T-30 improvement continues in parallel and is **not** the product critical path.

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

Confidence:

- `NONE`;
- `LOW`;
- `MEDIUM`;
- `HIGH`.

Public seat-map inventory is a **demand proxy, not confirmed paid sales**.

## Phase C — updated interpretation

### C0 — Provisional live decision layer — ACTIVE DEVELOPMENT

We do not wait for the learned-correction evidence gate to make the product useful.

C0 may provide:

- no-action continuation projections;
- explicitly provisional / bounded live revision logic;
- sector diagnosis;
- reason codes;
- dashboard decision support.

It must be labeled provisional/scenario-based and must not claim learned uplift.

### C1-alpha — Full-trajectory model tournament — ACTIVE NOW

Canonical plan:

`ml/C1_MODEL_TOURNAMENT_V1.md`

Decision: **train now on the completed events already collected. Do not wait for 20 matches to begin modelling.**

Current verified versioned export:

- 9 completed Ekstraklasa events compatible with the current Structural Prior domain;
- 206 PIT-valid full-trajectory samples at a regularized 6h cadence;
- current-season attendance/sporting inputs needed to replay frozen Structural Prior checkpoints;
- one completed Lech Europa League event excluded from the primary leaderboard and reserved as a possible transfer test.

Implementation now on `main`:

- `supabase/sql/c1_alpha_training_export_v1.sql`;
- `supabase/functions/c1_alpha_training_export_v1/index.ts`;
- `ml/c1_alpha_model_tournament_v1.py`;
- `.github/workflows/c1-alpha-model-tournament-v1.yml`.

Validation:

- **Leave-One-Event-Out** only;
- all rows from one match stay in one fold;
- equal event weighting;
- no random snapshot split;
- current Structural Prior is the incumbent;
- target is live residual (attendance and occupancy variants are compared).

Tournament families:

- zero correction / bias baselines;
- Ridge;
- ElasticNet;
- Huber;
- HistGradientBoosting;
- constrained ExtraTrees / RandomForest;
- shallow XGBoost;
- shallow LightGBM.

Primary objective:

**lowest stable event-level MAE vs Structural Prior.**

R&D target:

- <1700 MAE;
- stretch <1500 MAE.

### C1 — Learned Live Correction promotion — EVIDENCE-GATED

The 20-independent-completed-match rule remains a **later promotion/validation gate**, not a training-start gate.

It is not a blocker for C1-alpha, C0 or E0.

Promotion still requires:

- enough independent completed events;
- positive uplift vs Structural Prior;
- lower error than incumbent;
- frozen evidence package;
- human review;
- no automatic activation.

## Phase E — now split into E0 and E1

### E0 — Sector Decision & Dynamic Pricing MVP — START NOW

Canonical spec:

`ml/SECTOR_DECISION_PRICING_V1.md`

Required outputs:

1. sector underperformance / outperformance;
2. sector trajectory gap;
3. projected final public sell-through / remaining availability if current trajectory continues;
4. event projected outcome if current trajectory continues;
5. current sector price where available;
6. pricing recommendation: `HOLD / INCREASE / DECREASE`;
7. configurable price scenarios;
8. projected sell-through / revenue proxy under each scenario;
9. confidence / assumptions / reason codes;
10. recommendation decision / execution tracking.

No automatic price execution:

`auto_price_change_allowed = false`

Before learned elasticity exists, pricing scenarios are explicitly assumption-based.

### E1 — Learned Pricing / Intervention Engine — EVIDENCE-GATED

Later learn:

- sector/context-specific price elasticity;
- intervention uplift;
- incremental tickets;
- incremental revenue / contribution;
- action expected value;
- uncertainty.

## Growth relationship

Existing Growth measurement remains the outcome/ROI framework:

`Demand signal -> recommendation -> experiment -> execution -> outcome -> incremental tickets/revenue -> ROI`

Pricing is a first-class intervention family.

Relevant docs:

- `growth/GROWTH_MEASUREMENT_V1.md`;
- `growth/GROWTH_EXECUTION_DATA_V2.md`;
- `growth/DYNAMIC_PRICING_MEASUREMENT_V1.md`.

## Dashboard target

Repository:

`NiedzielX/BeyondTicketingPanel`

Primary page:

`src/pages/EventDetailPage.tsx`

Near-term product block:

**Sector Performance & Pricing**

Minimum table fields:

`Sector | Current price | Availability | Velocity | Expected progress | Actual progress | Gap | No-action final | Status | Price recommendation | Scenario impact | Confidence`

## Immediate implementation sequence

1. run and record `C1-alpha Model Tournament v1` leaderboard against current Structural Prior;
2. freeze the simplest stable winner if it beats the incumbent and run it in experimental/shadow mode;
3. keep five-horizon Structural Prior / orchestrator healthy;
4. implement sector-level trajectory gap/status;
5. implement sector no-action projection;
6. define price data contract / ingest;
7. implement assumption-based dynamic-pricing E0 scenarios;
8. persist recommendation / club decision / execution history;
9. expose Sector Performance & Pricing in Event Detail;
10. continue T-30 R&D in parallel;
11. calibrate P10/P50/P90 when evidence supports it.

## Non-negotiable product/model labels

Until learned/validated:

- use `EXPERIMENTAL`, `PROVISIONAL`, `SCENARIO`, or `ASSUMPTION-BASED` where appropriate;
- never call scenario uplift causal;
- never equate public inventory with paid sales;
- never change production prices automatically;
- never report snapshot-row cross-validation as independent-match validation;
- persist source, timestamp, dataset/model version and reason codes behind every recommendation/model result.
