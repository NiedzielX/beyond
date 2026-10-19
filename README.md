# Beyond

Beyond Ticketing engineering workspace.

## Start here

For every new AI / engineering session, read in this order:

1. [`AI_BOOTSTRAP.md`](AI_BOOTSTRAP.md) — cold-start state and immediate work order;
2. [`ml/MODEL_ACCURACY_DEVELOPMENT_INSTRUCTIONS_V2.md`](ml/MODEL_ACCURACY_DEVELOPMENT_INSTRUCTIONS_V2.md) — canonical accuracy-first development rules;
3. [`ml/CURRENT_MODEL.md`](ml/CURRENT_MODEL.md) — current forecasting state;
4. [`ml/results/D2_STAGE2_RELIABILITY_GATING_V1_2026-10-19.md`](ml/results/D2_STAGE2_RELIABILITY_GATING_V1_2026-10-19.md) — canonical Stage-2 result;
5. [`ml/artifacts/d2_stage2_p2_observation_maturity_v1/manifest.json`](ml/artifacts/d2_stage2_p2_observation_maturity_v1/manifest.json) — frozen d2 Stage-2 candidate;
6. [`ml/D2_STAGE2_RELIABILITY_GATING_V1.md`](ml/D2_STAGE2_RELIABILITY_GATING_V1.md) — frozen policy contract;
7. [`ml/results/D2_STAGE1_MODEL_TOURNAMENT_V1_2026-10-19.md`](ml/results/D2_STAGE1_MODEL_TOURNAMENT_V1_2026-10-19.md) — Stage-1 expert evidence;
8. [`ml/artifacts/pre_live_v2_historical_candidate_v1/manifest.json`](ml/artifacts/pre_live_v2_historical_candidate_v1/manifest.json) — sealed Pre-Live v2 historical lineage;
9. [`ml/DEMAND_FORECAST_DEVELOPMENT_PLAN_V2.md`](ml/DEMAND_FORECAST_DEVELOPMENT_PLAN_V2.md) — canonical accuracy roadmap;
10. [`ml/LIVE_DEMAND_ENGINE_V1_PLAN.md`](ml/LIVE_DEMAND_ENGINE_V1_PLAN.md) — live-engine roadmap;
11. [`ml/C1_V8_PROSPECTIVE_SHADOW_V1.md`](ml/C1_V8_PROSPECTIVE_SHADOW_V1.md) — frozen C1 prospective comparator;
12. [`ml/MODEL_PROMOTION_GOVERNANCE_V1.md`](ml/MODEL_PROMOTION_GOVERNANCE_V1.md) — promotion gates.

## North star

> **Reduce forecasting MAE as far as possible with honest, reproducible, point-in-time-safe evidence before treating the model as mature.**

Do not optimize for roadmap completion. Do not use new outcomes to rescue previously selected models or policies.

## Canonical architecture

### Frozen Pre-Live v2

`history + proven current-season regime -> frozen pre-live anchor`

Freeze ID:

`pre-live-v2-historical-candidate-2026-10-18-v1`

Historical c2:

`NO_CONTEXT_ALL_HORIZONS`

### Frozen d2 live candidate

`final_forecast(t) = frozen_pre_live_v2(t) + reliability(t) * ridge_delta(t)`

Frozen Stage-1 expert:

`ridge-a10`

Frozen Stage-2 policy:

`P2-observation-maturity`

Frozen d2 candidate ID:

`d2-stage2-p2-observation-maturity-2026-10-19-v1`

## Current development state

Canonical sequence:

`a2 CLOSED -> b2 CLOSED -> c2 historical CLOSED -> Pre-Live v2 FROZEN -> d2 Stage 0 DONE -> d2 Stage 1 DONE -> d2 Stage 2 FROZEN -> EVENT 5 HOLDOUT ACTIVE`

Current status:

- **a2:** `CLOSED FOR CURRENT HISTORICAL DATA`;
- **b2:** `CLOSED / FROZEN INTO PRE-LIVE V2`;
- **c2 historical:** `SUFFICIENTLY EVALUATED / NO HISTORICAL EXTENSION`;
- **Pre-Live v2:** `SEALED / REPRODUCIBLE / HISTORICAL CANDIDATE ONLY`;
- **d2 Stage 0:** `FROZEN_V2_EXACT_COMPATIBILITY_READY`;
- **d2 Stage 1:** `COMPLETED / ridge-a10 FROZEN RESEARCH EXPERT`;
- **d2 Stage 2:** `COMPLETED / P2-observation-maturity FROZEN`;
- **next:** score reserved event `5` once as chronological holdout.

## d2 Stage 2 canonical result

Canonical run:

`39308629738`

Main commit:

`4dc653f0f021c4b05aecadc985d55b69afa1dc11`

Artifact ID:

`12214478156`

Artifact ZIP SHA256:

`b4ae9183f398a8cd13542390ce05734f050697e903d34242d793b28854bf9296`

Selected policy:

`P2-observation-maturity`

| Metric | Frozen v2 | Raw Ridge | P2 governed Ridge |
|---|---:|---:|---:|
| Latest-row MAE | 4,128.01 | 3,320.39 | **3,240.99** |
| Window MAE | 4,128.01 | **3,619.19** | 3,657.65 |
| Worst latest-event degradation | 0 | 4,326.90 | **1,081.72** |
| p90 degradation | 0 | 1,683.09 | **1,034.05** |

P2 versus Frozen v2:

- latest MAE improvement: **887.02 seats / 21.49%**;
- window MAE improvement: **470.36 seats / 11.39%**.

P2 versus raw Ridge:

- latest MAE improves another **79.40 seats**;
- retains **92.44%** of Ridge window uplift;
- reduces worst-event degradation by **75%**.

Only P2 passed all predeclared Stage-2 gates.

## Frozen P2 reliability contract

Observation maturity:

- first observation: `0.25`;
- second observation: `0.60`;
- third or later: `1.00`.

Time-to-kickoff cap:

- >18h: `0.75`;
- >12h and <=18h: `0.90`;
- <=12h: `1.00`.

Final reliability:

`min(observation_index_weight, time_weight)`

No fitted threshold search and no outcome information are used by P2.

## Chronos / TSFM decision

Stage-1 Chronos-2 and Chronos-Bolt-small both lost to plain Ridge.

Decision:

`TSFM_STAGE1 = NOT_PROVEN_VS_RIDGE`

Do not fine-tune Chronos or add Lag-Llama / NeuralProphet on the same exposed development set.

## Chronological holdout — active now

Reserved event:

- event ID `5`;
- **Lech Poznań vs Korona Kielce**;
- kickoff `2026-10-18T15:30:00Z`;
- actual attendance `37,407`;
- capacity `43,269`;
- 4 final-24h live rows.

This event was excluded from Stage-1 and Stage-2 selection.

Now that Stage 2 is frozen, score exactly once:

1. Frozen Pre-Live v2;
2. raw frozen `ridge-a10`;
3. frozen P2 governed Ridge;
4. frozen C1 v8 where contract-compatible.

**No retuning after opening the holdout.**

## Production boundary

Production Structural Prior remains unchanged.

`live_adjustment = 0`

Frozen Pre-Live v2, Ridge and P2 are research candidates, not automatic production promotion.

Frozen C1 v8 remains unchanged.

## Engineering accuracy / CI/CD

Every material experiment must have committed code, executable CI, pinned runtime, exact data/model/policy versions, PIT checks, event-independent evaluation, machine-readable artifacts, hashes, human-readable results and an explicit decision.

Mandatory rule:

> **A new holdout validates a frozen decision; it does not become tuning data retroactively.**
