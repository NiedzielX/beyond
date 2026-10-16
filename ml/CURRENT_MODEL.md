# Beyond Ticketing — Current Model & Product State

Last product-direction update: **2026-10-16**

This is the canonical short-form state. Read `AI_BOOTSTRAP.md` first in a cold session. Operational C1 v8 details are in `ml/C1_V8_PROSPECTIVE_SHADOW_V1.md`. Active E0 implementation details are in `ml/E0_SECTOR_TRAJECTORY_IMPLEMENTATION_V1.md`.

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

The live shadow path performs forward-only T-1 inference, persists append-only pre-outcome decisions and scores only decisions that existed before the outcome.

Read-only operational surfaces are available:

- `public.dashboard_c1_shadow_v8_status_v1`;
- `public.dashboard_c1_shadow_v8_events_v1`.

Current prospective evidence remains at zero until the first naturally due T-1 decision. No historical backfill was performed.

## Governance during prospective validation

Do not retune v8, refit the frozen package automatically, expand its training set silently, force T-1 with future timestamps, backfill missed predictions after outcomes, or write v8 into production forecast values.

Any retrain requires an explicit new package version and governance decision.

## C1 promotion gate

Promotion requires enough genuinely prospective independent completed events, positive uplift vs Structural Prior, acceptable tail risk, a frozen reproducible package, human review and explicit promotion. No automatic production promotion exists.

## E0 — Sector Decision & Dynamic Pricing MVP — ACTIVE IMPLEMENTATION

Canonical product specification:

`ml/SECTOR_DECISION_PRICING_V1.md`

Canonical implementation plan:

`ml/E0_SECTOR_TRAJECTORY_IMPLEMENTATION_V1.md`

### Confirmed data state

Real sector inventory history is already available in `public.sector_inventory` for active events.

Critical ownership rule:

`sector_inventory.snapshot_id -> snapshots.id -> snapshots.ticket_event_id`

Do **not** use `sector_inventory.event_id` as the E0 ownership key; it is nullable and produced the initial false zero-sector result.

Verified active-event coverage at the implementation checkpoint included approximately:

- Lech Poznań: **151 sectors**;
- Pogoń Szczecin: **42**;
- GKS Katowice: **23**;
- Wisła Płock: **17**;
- Zagłębie Lubin: **14**.

Sector data is therefore sufficient to start real E0 trajectory work now.

### E0 target

`sector state -> release-aware trajectory -> relative gap -> no-action projection -> pricing scenario -> recommendation`

Public sector inventory remains a proxy and must never be presented as confirmed paid sales.

### Immediate E0 implementation

1. create versioned `sector-trajectory-v1` with one PIT-safe event/sector/as-of row;
2. derive reference/current availability, absorption/sell-through proxy, 6h/24h/72h/7d velocity and acceleration;
3. detect release/inventory increase/sector coverage/data-gap anomalies before status classification;
4. derive provisional event-relative expected progress and continuous sector gap using `PROVISIONAL_RELATIVE_EVENT_BASELINE`;
5. inspect real gap stability/distribution, then freeze deterministic versioned status thresholds;
6. implement bounded **Projected outcome if current trajectory continues** at sector level;
7. expose read-only sector status/projection for `BeyondTicketingPanel`;
8. audit/implement price source and `PRICE_DATA_MISSING` contract;
9. implement assumption-based `HOLD / INCREASE / DECREASE` pricing scenarios;
10. persist recommendation/decision/execution/outcome evidence for future E1 learning.

No automatic production price changes:

`auto_price_change_allowed = false`

Do not claim learned elasticity or causal price uplift in E0.

## Immediate implementation sequence

1. **Build `sector-trajectory-v1` now.**
2. Build release-aware continuous sector gap features before status thresholds.
3. Build provisional sector no-action projection.
4. Expose read-only E0 dashboard data.
5. Add price-data contract and assumption-based pricing scenarios.
6. Add recommendation/decision/execution persistence.
7. Let frozen C1 v8 collect prospective evidence in parallel without modification.
8. Keep production Structural Prior/orchestrator unchanged with `live_adjustment=0`.
9. Continue T-30 R&D separately; it is not the E0 critical path.

## Non-negotiable rules

- never call public inventory paid sales;
- never report snapshot rows as independent matches;
- never present the oracle as deployable;
- never retune v8 on the original 9 events;
- scheduled C1 inference loads frozen artifacts and never fits;
- prospective evidence must exist before outcome to count as prospective;
- E0 sector ownership comes through the snapshot, not `sector_inventory.event_id`;
- E0 no-action projection is a continuation scenario, not a causal counterfactual;
- E0 pricing is `ASSUMPTION_BASED_SCENARIO` until learned elasticity is validated;
- production remains `live_adjustment = 0` and `auto_price_change_allowed = false` until explicit promotion/approval.
