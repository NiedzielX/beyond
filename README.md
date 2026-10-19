# Beyond

Beyond Ticketing engineering workspace.

## Start here

For every new AI / engineering session, read in this order:

1. [`AI_BOOTSTRAP.md`](AI_BOOTSTRAP.md) — cold-start state and immediate work order;
2. [`ml/MODEL_ACCURACY_DEVELOPMENT_INSTRUCTIONS_V2.md`](ml/MODEL_ACCURACY_DEVELOPMENT_INSTRUCTIONS_V2.md) — canonical accuracy-first development rules;
3. [`ml/CURRENT_MODEL.md`](ml/CURRENT_MODEL.md) — current forecasting state;
4. [`ml/results/D2_STAGE1_MODEL_TOURNAMENT_V1_2026-10-19.md`](ml/results/D2_STAGE1_MODEL_TOURNAMENT_V1_2026-10-19.md) — current d2 evidence and research lead;
5. [`ml/D2_STAGE2_RELIABILITY_GATING_V1.md`](ml/D2_STAGE2_RELIABILITY_GATING_V1.md) — active next-stage contract;
6. [`ml/artifacts/pre_live_v2_historical_candidate_v1/manifest.json`](ml/artifacts/pre_live_v2_historical_candidate_v1/manifest.json) — sealed Pre-Live v2 historical lineage;
7. [`ml/results/PRE_LIVE_V2_HISTORICAL_FREEZE_V1_2026-10-18.md`](ml/results/PRE_LIVE_V2_HISTORICAL_FREEZE_V1_2026-10-18.md) — freeze evidence;
8. [`ml/DEMAND_FORECAST_DEVELOPMENT_PLAN_V2.md`](ml/DEMAND_FORECAST_DEVELOPMENT_PLAN_V2.md) — canonical accuracy roadmap;
9. [`ml/LIVE_DEMAND_ENGINE_V1_PLAN.md`](ml/LIVE_DEMAND_ENGINE_V1_PLAN.md) — live-engine roadmap;
10. [`ml/C1_V8_PROSPECTIVE_SHADOW_V1.md`](ml/C1_V8_PROSPECTIVE_SHADOW_V1.md) — frozen C1 prospective comparator;
11. [`ml/MODEL_PROMOTION_GOVERNANCE_V1.md`](ml/MODEL_PROMOTION_GOVERNANCE_V1.md) — promotion gates.

## North star

> **Reduce forecasting MAE as far as possible with honest, reproducible, point-in-time-safe evidence before treating the model as mature.**

Do not optimize for roadmap completion. Do not use new outcomes to rescue previously selected models or policies.

## Canonical architecture

### Frozen Pre-Live v2

`history + proven current-season regime -> frozen pre-live anchor`

Historical c2:

`NO_CONTEXT_ALL_HORIZONS`

Freeze ID:

`pre-live-v2-historical-candidate-2026-10-18-v1`

Historical reference mean MAE:

- T-30: `1867.82`;
- T-14: `1809.45`;
- T-7: `1691.40`;
- T-3: `1682.63`;
- T-1: `1661.52`.

### d2 Continuous Live Updater

Current target architecture:

`final_forecast(t) = frozen_pre_live_v2(t) + reliability(t) * ridge_delta(t)`

The live layer is continuous over time-to-kickoff. Named horizons remain evaluation checkpoints, not separate live models.

## Current development state

Canonical sequence:

`a2 CLOSED -> b2 CLOSED -> c2 historical CLOSED -> Pre-Live v2 FROZEN -> d2 Stage 0 DONE -> d2 Stage 1 DONE -> d2 Stage 2 ACTIVE`

Current status:

- **a2 Historical data:** `CLOSED FOR CURRENT HISTORICAL DATA`;
- **b2 Current season:** `CLOSED FOR CURRENT HISTORICAL DATA / FROZEN INTO PRE-LIVE V2`;
- **c2 Historical context:** `SUFFICIENTLY EVALUATED / NO HISTORICAL EXTENSION`;
- **Pre-Live v2:** `SEALED / REPRODUCIBLE / HISTORICAL CANDIDATE ONLY`;
- **d2 Stage 0:** `FROZEN_V2_EXACT_COMPATIBILITY_READY`;
- **d2 Stage 1:** `COMPLETED / ridge-a10 RESEARCH LEAD`;
- **d2 Stage 2:** `ACTIVE NEXT — RELIABILITY / TAIL-RISK GATING`.

## d2 Stage 1 result

Canonical result:

`ml/results/D2_STAGE1_MODEL_TOURNAMENT_V1_2026-10-19.md`

Development lineage:

- 9 independent completed events;
- 30 final-24h live rows;
- exact Frozen Pre-Live v2 anchor;
- event-level LOEO;
- event-balanced training weights.

Research lead:

`ridge-a10`

Key metrics:

| Metric | Frozen v2 | Ridge | Improvement |
|---|---:|---:|---:|
| Latest-row MAE | 4,128.01 | **3,320.39** | **+807.62 / 19.56%** |
| Event-balanced window MAE | 4,128.01 | **3,619.19** | **+508.83 / 12.33%** |

Ridge improves the latest row on **6/9 events**.

Critical risk:

`worst latest-event degradation = +4,326.90 seats`

Therefore Ridge is a research lead, not a production champion.

Canonical Stage-1 run:

`39256585339`

Artifact ID:

`12187853899`

Artifact ZIP SHA256:

`c494ba609f3c9ee376e8285a9af975cc78d813337bd219fbaf94c7a9a336c6de`

## Chronos / TSFM decision

Stage 1 tested:

- `amazon/chronos-2`;
- `amazon/chronos-bolt-small`.

Both ran as zero-shot causal forecasters of public inventory trajectory and both improved Frozen v2 when added to Ridge.

However, neither improved the matching plain Ridge candidate:

- Ridge: `3320.39` latest MAE;
- Ridge + Chronos-2: `3428.25`;
- Ridge + Bolt-small: `3428.08`.

Decision:

`TSFM_STAGE1 = NOT_PROVEN_VS_RIDGE`

Do not fine-tune Chronos or add Lag-Llama / NeuralProphet on the same 9-event development set. Reopen the TSFM family only with materially more independent live events or a materially new predeclared hypothesis.

## d2 Stage 2 — active now

Canonical contract:

`ml/D2_STAGE2_RELIABILITY_GATING_V1.md`

Objective:

> **Preserve as much of Ridge's MAE improvement as possible while materially reducing its tail risk.**

Stage 2 must govern the frozen Stage-1 Ridge rather than retune it.

Primary form:

`final_forecast = frozen_v2 + reliability * ridge_delta`

Reliability may use only PIT-safe live evidence such as:

- observation count / span;
- time-to-kickoff;
- trajectory stability;
- velocity / acceleration;
- correction magnitude / disagreement with Frozen v2;
- release / coverage-change flags;
- data gaps and feature-quality signals.

Stage 2 selection remains restricted to the original **9-event / 30-row development set**.

## Untouched chronological holdout

The append-only exporter now contains a new completed event:

- event ID `5`;
- **Lech Poznań vs Korona Kielce**;
- kickoff: `2026-10-18T15:30:00Z`;
- actual attendance: `37,407`;
- capacity: `43,269`;
- 4 final-24h live rows.

This event was deliberately excluded from Stage-1 selection.

Mandatory rule:

> **Do not use event 5 to tune Ridge or Stage-2 reliability. Freeze Stage 2 first, then score Lech–Korona once as the first chronological/prospective holdout.**

After Stage 2 is frozen, compare on event 5:

1. Frozen Pre-Live v2;
2. raw frozen `ridge-a10`;
3. frozen Stage-2 governed Ridge;
4. frozen C1 v8 where contract-compatible.

No retuning after opening the holdout.

## What happens after event 5

- persist the result regardless of whether it is good or bad;
- keep collecting new completed live events append-only;
- score the frozen d2 candidate prospectively;
- do not silently fold new outcomes into training;
- require a materially larger independent sample before any production promotion.

## Production boundary

Production Structural Prior remains unchanged.

Production remains:

`live_adjustment = 0`

Frozen Pre-Live v2 does not automatically replace production.

Frozen C1 v8 remains `EXPERIMENTAL_SHADOW` and unchanged.

No d2 result is a production promotion until explicit governance permits it.

## Engineering accuracy / CI/CD

Every material model or policy experiment must have:

- committed code;
- executable CI workflow;
- pinned dependencies / external model revisions;
- exact data/feature/model versions;
- PIT and leakage checks;
- event-independent evaluation;
- machine-readable evidence artifact;
- run/artifact IDs and hashes;
- committed human-readable result;
- explicit decision;
- canonical docs update;
- no production activation without an explicit promotion step.

Mandatory interpretation rule:

> **A failed challenger closes the challenger, not the whole workstream. A new holdout validates a frozen decision; it does not become tuning data retroactively.**
