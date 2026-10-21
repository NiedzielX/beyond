# Beyond

Beyond Ticketing engineering workspace.

## Start here

For every new AI / engineering session, read in this order:

1. [`AI_BOOTSTRAP.md`](AI_BOOTSTRAP.md) — cold-start state and immediate work order;
2. [`ml/MODEL_ACCURACY_DEVELOPMENT_INSTRUCTIONS_V2.md`](ml/MODEL_ACCURACY_DEVELOPMENT_INSTRUCTIONS_V2.md) — canonical accuracy-first development rules;
3. [`ml/CURRENT_MODEL.md`](ml/CURRENT_MODEL.md) — current forecasting state;
4. [`ml/DEMAND_FORECAST_DEVELOPMENT_PLAN_V2.md`](ml/DEMAND_FORECAST_DEVELOPMENT_PLAN_V2.md) — canonical two-track roadmap;
5. [`ml/MODEL_DEVELOPMENT_STRATEGY.md`](ml/MODEL_DEVELOPMENT_STRATEGY.md) — non-blocking historical R&D strategy;
6. [`ml/results/A2_EXTERNAL_ENSEMBLE_CLOSURE_V1_2026-10-21.md`](ml/results/A2_EXTERNAL_ENSEMBLE_CLOSURE_V1_2026-10-21.md) — completed all-horizon external/ensemble closure audit;
7. [`ml/A2_EXTERNAL_ENSEMBLE_FIXED_TEMPORAL_V1.md`](ml/A2_EXTERNAL_ENSEMBLE_FIXED_TEMPORAL_V1.md) — active fixed-temporal robustness contract;
8. [`ml/D2_PROSPECTIVE_ACCUMULATION_V1.md`](ml/D2_PROSPECTIVE_ACCUMULATION_V1.md) — frozen d2 prospective scoring/readiness contract;
9. [`ml/results/D2_PROSPECTIVE_READINESS_V1_2026-10-19.md`](ml/results/D2_PROSPECTIVE_READINESS_V1_2026-10-19.md) — tracked-event readiness/evidence classes;
10. [`ml/results/D2_EVENT5_HOLDOUT_V1_2026-10-19.md`](ml/results/D2_EVENT5_HOLDOUT_V1_2026-10-19.md) — first chronological d2 holdout;
11. [`ml/results/D2_STAGE2_RELIABILITY_GATING_V1_2026-10-19.md`](ml/results/D2_STAGE2_RELIABILITY_GATING_V1_2026-10-19.md) — frozen Stage-2 result;
12. [`ml/results/D2_STAGE1_MODEL_TOURNAMENT_V1_2026-10-19.md`](ml/results/D2_STAGE1_MODEL_TOURNAMENT_V1_2026-10-19.md) — frozen Stage-1 expert evidence;
13. [`ml/artifacts/pre_live_v2_historical_candidate_v1/manifest.json`](ml/artifacts/pre_live_v2_historical_candidate_v1/manifest.json) — sealed Pre-Live v2 lineage;
14. [`ml/LIVE_DEMAND_ENGINE_V1_PLAN.md`](ml/LIVE_DEMAND_ENGINE_V1_PLAN.md) — live-engine roadmap;
15. [`ml/MODEL_PROMOTION_GOVERNANCE_V1.md`](ml/MODEL_PROMOTION_GOVERNANCE_V1.md) — promotion gates.

## North star

> **Reduce forecasting MAE as far as possible with honest, reproducible, point-in-time-safe evidence before treating the model as mature.**

## Mandatory two-track rule

### Track A — frozen validation

Keep the current research package unchanged and score newly completed events append-only.

Purpose:

- independent delayed-label diagnostics;
- genuine post-freeze prospective evidence;
- eventual production-promotion evidence.

### Track B — active accuracy R&D

Continue model research immediately whenever the evaluation boundary can be declared honestly.

**Do not wait for a prospective sample-count gate to perform research that can be evaluated now.**

> **Production promotion waits for prospective evidence. R&D does not.**

A failed challenger closes the challenger, not the workstream.

## Frozen architecture — Track A

Pre-Live:

`history + proven current-season regime -> Frozen Pre-Live v2`

Live:

`final_forecast(t) = frozen_pre_live_v2(t) + reliability(t) * ridge_delta(t)`

Frozen IDs:

- Pre-Live v2: `pre-live-v2-historical-candidate-2026-10-18-v1`;
- Stage-1 expert: `ridge-a10`;
- Stage-2 policy: `P2-observation-maturity`;
- d2 package: `d2-stage2-p2-observation-maturity-2026-10-19-v1`.

Production remains:

`live_adjustment = 0`

## Active Track-B result — a2 external + ensemble closure

Canonical run:

`39624170933`

Artifact ID:

`12356162577`

Result JSON SHA256:

`dc2b65359e4841ba84d2bb51485c8b9da68816a33f9413f9208943fecaecf88a`

Artifact ZIP SHA256:

`c86ad72301e95716a908f4e2b4811e33af37b898b3eed54aed094fc4d91658a4`

Result:

| Horizon | Development result | 2024/25 gain | 2025/26 gain | Decision |
|---|---:|---:|---:|---|
| T-30 | +33.50 | **+54.93** | **+29.74** | robustness |
| T-14 | +16.94 | +58.02 | -2.58 | retain current a2 |
| T-7 | +8.90 | **+10.27** | **+27.86** | robustness |
| T-3 | +19.59 | -2.80 | +30.54 | retain current a2 |
| T-1 | +55.46 | **+2.27** | **+6.28** | robustness |

Exact selected ensembles:

- T-30: `0.75 current a2 + 0.25 XGBoost depth3`;
- T-7: `0.25 current a2/HGB + 0.25 CatBoost depth4 + 0.50 LightGBM leaves15`;
- T-1: `0.25 HGB hist31 + 0.50 CatBoost depth4 + 0.25 LightGBM leaves15`.

T-14 and T-3 are closed for this challenger formulation because the exposed references are mixed.

## Active now — fixed-temporal robustness

The exact T-30/T-7/T-1 contracts above are replayed unchanged through four rolling folds:

1. 2022/23;
2. 2023/24;
3. 2024/25;
4. 2025/26.

No weights, models or features are reselected.

Pass gate:

`positive MAE improvement in all four rolling folds`

A pass does not change Frozen Pre-Live v2. It qualifies the horizon only for a new, separately versioned historical / Pre-Live challenger cycle.

## Frozen d2 state

Stage 1 `ridge-a10`:

- Frozen latest MAE `4128.01`;
- Ridge latest `3320.39`;
- improvement `807.62 / 19.56%`;
- window `3619.19`;
- worst degradation `4326.90`.

Stage 2 `P2-observation-maturity`:

- latest `3240.99`;
- uplift `887.02 / 21.49%`;
- window `3657.65`;
- worst degradation `1081.72`.

Do not retune the frozen package from new outcomes.

## Event 5 chronological holdout

Lech Poznań vs Korona Kielce, actual `37,407`.

| Forecast | Latest error |
|---|---:|
| Structural T-1 | 7,669.07 |
| Frozen Pre-Live v2 | 9,832.52 |
| Raw Ridge | **6,652.81** |
| P2 | **6,652.81** |
| persisted C1 v8 | 7,669.07 |

Event 5 is permanently exposed.

## Prospective evidence classes

Freeze cutoff:

`2026-10-19T19:11:01Z`

- `DELAYED_LABEL_HOLDOUT`: kickoff at/before cutoff; diagnostic, not genuine forward promotion N.
- `TRUE_POST_FREEZE_PROSPECTIVE`: kickoff after cutoff; may count toward forward promotion evidence.

Never combine both classes into one headline prospective sample size.

## Delayed-label diagnostics

The current frozen d2 package is not uniformly better match-by-match:

- GKS Katowice–Pogoń: Frozen Pre-Live latest error about `1,356`, d2/P2 about `2,074`;
- Cracovia–Legia: Frozen about `434`, d2/P2 about `1,068`.

These are exposed diagnostics, not permission for post-hoc Ridge/P2 tuning.

## Next Track-B research after historical robustness

Separately versioned d2 research may continue without waiting for a future-event count threshold, e.g.:

- remaining-demand target;
- alternative residual target;
- anchor-error direction/magnitude;
- learned reliability;
- compact heterogeneous live-model ensemble;
- materially different trajectory/TSFM hypothesis.

Forward PIT-safe context collection also continues for rivalry, verified absences, sporting state, media/GDELT and valid hype/search/social signals.

## Engineering rule

`code -> tests -> CI -> artifact -> hashes -> result doc -> decision -> canonical docs`

> **Frozen validation protects evidence integrity. It does not pause model development.**
