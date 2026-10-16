# Beyond Ticketing — Current Model & Product State

Last product-direction update: **2026-10-16**

This is the canonical short-form state. For cold-start instructions read `AI_BOOTSTRAP.md`. For C1-alpha governance read `ml/C1_MODEL_TOURNAMENT_V1.md`. For sector/pricing product behaviour read `ml/SECTOR_DECISION_PRICING_V1.md`.

## Current north star

Beyond is a **live demand decision system**, not only an attendance model.

Primary decision flow:

`Structural Prior -> Live Trajectory -> Expert Reliability -> Sector Gap -> No-action Projection -> Pricing Scenario -> Recommendation -> Execution -> Outcome`

The product must answer where the event is likely to finish, whether the live evidence is strong enough to revise the Structural Prior, which sectors are behind/ahead, what happens if the current trajectory continues, what price action is worth testing, and what happened after execution.

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

Do **not** wait for 20 completed matches before C1-alpha R&D. The 20-match rule is a later promotion gate only.

Current verified current-domain evidence:

- **9 completed Ekstraklasa events**;
- **206 PIT-valid full-trajectory rows**;
- **30 regularized PIT-valid final-24h rows**;
- **8/9 events** with PIT-safe T-24 `hybrid_v6`;
- one additional completed Lech Europa League event kept outside the primary Structural Prior domain.

Versioned exports now include:

- `c1-alpha-training-export-v1` — full trajectory;
- `c1-alpha-training-export-v2` — full trajectory + T-24 hybrid ticketing signal;
- `c1-alpha-event-training-export-v1` — lightweight event payload;
- split v7 service-role-only exports for events / attendance / sporting / aliases / hybrid;
- `c1-alpha-v7-final24-rows-v1` — lightweight 30-row final-24h payload.

## C1-alpha R&D ladder — canonical results

| Version | Formulation | Main result | Decision |
|---|---|---:|---|
| v1 | all-phase trajectory | incumbent remained best | reject mixed-phase formulation |
| v2 | final-24h live expert | **2,929.3 MAE** | strongest learned live expert |
| v3 | nested threshold/blend | 3,054.3 | safer, too conservative |
| v4 | stacked/meta gate | 3,106.8 | reject extra stacking |
| v5 | stack + `hybrid_v6` | 3,073.8 | hybrid informative, still unstable |
| v6 | one-row T-24 challenger | 3,873.2 LOEO / 3,989.8 LOCO | reject T-24-only direction |
| v7 | reliability diagnostic | oracle structure explained by disagreement + trajectory direction | diagnostic only |
| v8 | fixed PIT-safe reliability policy | **2,713.3 window MAE / 1,998.1 latest-row MAE** | **prospective shadow candidate** |

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

Current expert:

`ridge_directocc_compact_generic_a10`

Development LOEO:

- Structural Prior T-1: **3,968.7 MAE**;
- v2 live expert: **2,929.3 MAE**;
- relative improvement: **26.19%**;
- non-deployable prior/live oracle: **1,867.9 MAE**.

The live expert is complementary but too unstable for unconditional replacement.

## v7 reliability finding

The most useful PIT-observable reliability pattern is not a generic quality flag.

Development diagnostics show:

- PRIOR-winner median latest disagreement: **6.63 pp capacity**;
- LIVE-winner median latest disagreement: **18.53 pp capacity**;
- multi-row PRIOR winners generally have falling v2 live estimates;
- LIVE winners generally have non-negative / positive live direction;
- `signal_ready`, feature-quality and raw-vs-matched regime are audit context, not safe standalone confidence gates.

## v8 fixed reliability policy — current C1-alpha candidate

Policy ID:

`c1-alpha-reliability-policy-v8-fixed-10pp-positive-slope-20pp-single`

PIT rule:

- one live observation: use LIVE only if absolute prior/live disagreement >= **20 pp verified capacity**;
- two or more observations: use LIVE only if disagreement >= **10 pp** **and** live prediction slope using observations available up to the current row is strictly positive;
- otherwise use PRIOR.

No threshold grid was run in v8.

Development replay:

- Structural Prior: **3,968.7 MAE**;
- v2 live expert: **2,929.3 MAE**;
- **v8 window MAE: 2,713.3**;
- **v8 latest-row MAE: 1,998.1**;
- relative window improvement vs Prior: **31.63%**;
- worst event degradation vs Prior: **203.3**;
- oracle: **1,867.9**.

Important governance limitation:

> v8 thresholds were designed after inspecting v7 labels on these same 9 events. The replay is development evidence, not a fresh validation set.

Therefore v8 is **EXPERIMENTAL_SHADOW only** until prospective events confirm it.

Production remains:

`live_adjustment = 0`

Do not write v8 into the production forecast output yet.

## Immediate C1-alpha next action — freeze prospective shadow package

Freeze one prospective v2+v8 package **without changing production forecasts**:

1. fit the exact v2 live expert on all currently completed in-domain training events;
2. freeze artifact + training event IDs + hashes + feature contract + package version;
3. freeze the v8 rule exactly as `10 pp + positive slope / 20 pp single observation`;
4. add a load+predict shadow runner — no fitting in scheduled inference;
5. persist every prospective decision before outcome is known:
   - event / timestamp;
   - Structural Prior P50;
   - v2 live P50;
   - disagreement;
   - live observation count;
   - live slope to date;
   - selected expert;
   - reason code;
   - package/model version;
6. score frozen decisions after each newly completed event;
7. do not tune the policy again on the original 9 events.

## C1 promotion gate

The 20-independent-completed-match rule remains a **promotion/validation gate**, not a training-start gate.

Promotion still requires sufficient genuinely prospective independent events, positive uplift, acceptable tail risk, frozen model/data/feature package, human review and no automatic activation.

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

1. freeze and version the **prospective v2+v8 shadow package**;
2. add load+predict shadow inference and pre-outcome evidence persistence;
3. keep production Structural Prior/orchestrator unchanged with `live_adjustment=0`;
4. score each genuinely new completed event against the frozen v8 package;
5. continue sector gap/status and no-action projection;
6. continue price-data ingest and E0 pricing scenarios;
7. persist recommendation/decision/execution history;
8. continue T-30 R&D in parallel, not as the product critical path.

## Non-negotiable labels / rules

- never call public inventory paid sales;
- never report snapshot rows as independent matches;
- never present the oracle as a deployable model;
- never relabel v8 development replay as fresh validation;
- never retune v8 thresholds on the original 9 events;
- scheduled inference must load frozen artifacts, never fit;
- use `EXPERIMENTAL_SHADOW`, `PROVISIONAL`, `SCENARIO` or `ASSUMPTION-BASED` until validated;
- persist source, timestamp, dataset/model version and reason codes behind every recommendation/model result.
