# Beyond Ticketing — Current Model & Product State

Last product-direction update: **2026-10-16**

This is the canonical short-form state. For cold-start instructions read `AI_BOOTSTRAP.md`. For C1-alpha governance read `ml/C1_MODEL_TOURNAMENT_V1.md`. For sector/pricing product behaviour read `ml/SECTOR_DECISION_PRICING_V1.md`.

## Current north star

Beyond is a **live demand decision system**, not only an attendance model.

Primary decision flow:

`Structural Prior -> Live Trajectory -> Sector Gap -> No-action Projection -> Pricing Scenario -> Recommendation -> Execution -> Outcome`

The product must answer where the event is likely to finish, which sectors are behind/ahead, what happens if the current trajectory continues, what price action is worth testing, and what happened after execution.

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

Scheduled inference is load + predict only. It must never fit a model.

## Historical validation status

Canonical history:

- Ekstraklasa 2021/22–2025/26;
- 1,530 matches;
- 7,650 horizon rows;
- verified historical capacity coverage 100%.

2024/25 and 2025/26 are **not pristine untouched T-30 holdouts** for new R&D. They were exposed during controlled challenger work on 2026-10-16. New T-30 research uses rolling-origin pre-validation and prospective 2026/27 as critical fresh evidence.

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

Public seat-map inventory is a **demand proxy, not confirmed paid sales**.

## C1-alpha — current evidence

Do **not** wait for 20 completed matches before doing C1-alpha R&D. The 20-match rule is a later promotion gate only.

Current verified current-domain evidence:

- **9 completed Ekstraklasa events**;
- **206 PIT-valid trajectory rows** at regularized 6h cadence;
- **8/9 events** with PIT-safe T-24 `hybrid_v6`;
- one additional completed Lech Europa League event kept outside the primary Structural Prior domain.

Versioned exports:

- `c1-alpha-training-export-v1` — full trajectory;
- `c1-alpha-training-export-v2` — full trajectory + T-24 hybrid ticketing signal;
- `c1-alpha-event-training-export-v1` — lightweight one-event payload for event-level diagnostics.

## C1-alpha R&D ladder — canonical results

### v1 — all-phase full-trajectory tournament

Evidence:

`ml/results/C1_ALPHA_MODEL_TOURNAMENT_V1_2026-10-16.md`

Mixing sparse T-14/T-7 evidence with final-24h evidence did not improve the Structural Prior. Conclusion: a single continuous correction across heterogeneous phases is the wrong first formulation.

### v2 — final-24h T-1 live expert — **best aggregate challenger so far**

Evidence:

`ml/results/C1_ALPHA_T1_TOURNAMENT_V2_2026-10-16.md`

Winner:

`ridge_directocc_compact_generic_a10`

Whole-event LOEO:

- Structural Prior: **3,968.7 MAE**;
- v2 live expert: **2,929.3 MAE**;
- uplift: **1,039.4 / 26.19%**;
- event improvement rate: **4/9**;
- worst-event degradation: **4,748.6**.

This proves strong complementary live signal but is too unstable for unconditional replacement.

### v3 — nested threshold/blend gate

Evidence:

`ml/results/C1_ALPHA_T1_GATED_V3_2026-10-16.md`

- MAE: **3,054.3**;
- relative improvement: **23.04%**;
- worst-event degradation reduced to **1,326.1**;
- improvement rate: **2/9**.

Safer, but still not accurate enough.

### v4 — stacked/meta gate

Evidence:

`ml/results/C1_ALPHA_T1_STACKED_V4_2026-10-16.md`

- MAE: **3,106.8**;
- relative improvement: **21.72%**;
- improvement rate: **2/9**.

More stacking did not solve expert selection.

### v5 — stacked gate + PIT-safe `hybrid_v6`

Evidence:

`ml/results/C1_ALPHA_T1_HYBRID_GATE_V5_2026-10-16.md`

- MAE: **3,073.8**;
- relative improvement: **22.55%**;
- improvement rate: **4/9**;
- still unstable.

Hybrid velocity adds information but high-dimensional stacking remains unsuitable for N=9 independent events.

### v6 — one-row-per-event T-24 challenger — **rejected direction**

Evidence:

`ml/results/C1_ALPHA_T24_RESIDUAL_V6_2026-10-16.md`

Winner:

`ridge_direct_occupancy_hybrid_a10`

LOEO:

- Structural Prior: **3,968.7 MAE**;
- v6: **3,873.2 MAE**;
- improvement: **2.41%**;
- improvement rate: **5/9**.

LOCO:

- v6: **3,989.8 MAE**;
- relative change vs prior: **-0.53%**.

Outcome-aware oracle prior-or-v6: **2,942.1 MAE**.

This is materially worse than the v2 expert-pair oracle, so T-24-only compression discards useful live-trajectory information.

## Main C1-alpha conclusion

The best honest aggregate learned challenger remains **v2 at 2,929.3 MAE**, but no candidate is stable enough to freeze as the live correction.

The most important diagnostic is the non-deployable v2 expert-pair oracle:

**Structural Prior vs v2 live expert oracle switch ≈ 1,867.9 MAE.**

This means the primary unsolved problem is **expert reliability / expert selection**, not lack of live signal.

Production remains:

`live_adjustment = 0`

Do **not** activate v2-v6 in production or present the oracle as deployable.

## Immediate C1-alpha next action — v7 reliability diagnostic

Do not build another feature-heavy stacker yet.

Build one event-level diagnostic row per completed match for the **existing v2 pair** and identify PIT-observable characteristics that distinguish:

- events where Structural Prior should be trusted;
- events where the full final-24h live expert should take over.

Required PIT-safe diagnostics:

- Structural Prior P50 / expected occupancy;
- round number / current-season completed home evidence before T-1;
- v2 earliest and latest final-24h estimates;
- prior-vs-live disagreement magnitude and direction;
- live estimate range / standard deviation / slope over final 24h;
- observation window and snapshot count;
- signal readiness / feature quality;
- matched-sector vs raw-only regime;
- release / coverage flags.

Actual outcome and oracle winner may be stored **only as evaluation labels**.

After the diagnostic, define a small predeclared reliability policy and validate it by whole-event holdout. Do not tune rules directly to an outer held-out event.

## C1 promotion gate

The 20-independent-completed-match rule remains a **promotion/validation gate**, not a training-start gate.

Promotion still requires sufficient independent events, positive uplift, acceptable tail risk, frozen model/data/feature package, human review and no automatic activation.

## E0 — Sector Decision & Dynamic Pricing MVP

This remains a parallel product priority and does not wait for C1 promotion.

Canonical spec:

`ml/SECTOR_DECISION_PRICING_V1.md`

Required outputs include sector trajectory gap/status, no-action projection, pricing scenarios, recommendation rationale and decision/execution history.

No automatic production price changes:

`auto_price_change_allowed = false`

## Dashboard target

Repository:

`NiedzielX/BeyondTicketingPanel`

Primary page:

`src/pages/EventDetailPage.tsx`

Target block:

**Sector Performance & Pricing**

## Immediate implementation sequence

1. build and persist **v7 expert reliability diagnostic** for Structural Prior + v2 final-24h expert;
2. define one small predeclared reliability policy from PIT-safe semantics and validate it whole-event;
3. keep Structural Prior / orchestrator healthy with `live_adjustment=0`;
4. continue sector gap and no-action projection work;
5. continue price-data and E0 pricing-scenario implementation;
6. keep collecting prospective 2026/27 evidence;
7. continue T-30 R&D in parallel, not as the product critical path.

## Non-negotiable labels / rules

- never call public inventory paid sales;
- never report snapshot rows as independent matches;
- never present the oracle as a deployable model;
- never tune a selector against its outer held-out event;
- use `EXPERIMENTAL`, `PROVISIONAL`, `SCENARIO` or `ASSUMPTION-BASED` until validated;
- persist source, timestamp, dataset/model version and reason codes behind every recommendation/model result.
