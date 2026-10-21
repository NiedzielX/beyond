# Beyond — AI Bootstrap / Read This First

Last product-direction update: **2026-10-21**

This file exists so a new AI/chat session continues the actual Beyond plan instead of rediscovering it.

## Cold-start rule

Read in this order:

1. `ml/MODEL_ACCURACY_DEVELOPMENT_INSTRUCTIONS_V2.md`;
2. `ml/CURRENT_MODEL.md`;
3. `ml/DEMAND_FORECAST_DEVELOPMENT_PLAN_V2.md`;
4. `ml/MODEL_DEVELOPMENT_STRATEGY.md`;
5. `ml/results/A2_EXTERNAL_ENSEMBLE_CLOSURE_V1_2026-10-21.md`;
6. `ml/A2_EXTERNAL_ENSEMBLE_FIXED_TEMPORAL_V1.md`;
7. `ml/D2_PROSPECTIVE_ACCUMULATION_V1.md`;
8. `ml/results/D2_PROSPECTIVE_READINESS_V1_2026-10-19.md`;
9. `ml/results/D2_EVENT5_HOLDOUT_V1_2026-10-19.md`;
10. `ml/results/D2_STAGE2_RELIABILITY_GATING_V1_2026-10-19.md`;
11. `ml/results/D2_STAGE1_MODEL_TOURNAMENT_V1_2026-10-19.md`;
12. `ml/artifacts/pre_live_v2_historical_candidate_v1/manifest.json`;
13. `ml/LIVE_DEMAND_ENGINE_V1_PLAN.md`;
14. `ml/C1_V8_PROSPECTIVE_SHADOW_V1.md`;
15. `ml/MODEL_PROMOTION_GOVERNANCE_V1.md`.

## Immediate objective

Run two tracks in parallel:

### Track A — frozen validation

Keep the current frozen research stack unchanged:

`Frozen Pre-Live v2 + P2 reliability * frozen ridge-a10 delta`

Continue delayed-label and true-post-freeze scoring append-only. This track builds production-promotion evidence and must not be retuned from newly exposed outcomes.

### Track B — active accuracy R&D

Do **not** wait for a prospective sample-count gate when honest research can be run now.

Current active R&D:

1. the all-horizon external-family/heterogeneous-ensemble closure audit is COMPLETE;
2. exact T-30/T-7/T-1 selected ensemble contracts are now in a fixed-temporal robustness audit;
3. after that, continue separately versioned d2 target/reliability/ensemble research and PIT-safe context research.

Core rule:

> **Production promotion waits for prospective evidence. R&D does not.**

## Frozen architecture

Pre-live:

`history + proven current-season regime -> Frozen Pre-Live v2`

Frozen ID:

`pre-live-v2-historical-candidate-2026-10-18-v1`

Live:

`final_forecast(t) = frozen_pre_live_v2(t) + reliability(t) * ridge_delta(t)`

Frozen components:

- Stage-1 expert `ridge-a10`;
- Stage-2 policy `P2-observation-maturity`;
- package `d2-stage2-p2-observation-maturity-2026-10-19-v1`.

Production remains:

`live_adjustment = 0`

Track-B experiments never mutate these IDs.

## a2 external + ensemble closure — COMPLETE

Canonical result:

`ml/results/A2_EXTERNAL_ENSEMBLE_CLOSURE_V1_2026-10-21.md`

Run:

`39624170933`

Artifact ID:

`12356162577`

Result JSON SHA256:

`dc2b65359e4841ba84d2bb51485c8b9da68816a33f9413f9208943fecaecf88a`

Artifact ZIP SHA256:

`c86ad72301e95716a908f4e2b4811e33af37b898b3eed54aed094fc4d91658a4`

Result:

- T-30 ADVANCE to fixed-temporal robustness;
- T-7 ADVANCE;
- T-1 ADVANCE;
- T-14 RETAIN current a2 / mixed references;
- T-3 RETAIN current a2 / mixed references.

Selected reference improvements:

### T-30

- 2024/25 `+54.93` MAE;
- 2025/26 `+29.74`.

Fixed ensemble weights:

`current a2 0.75 + XGBoost depth3 0.25`

### T-7

- 2024/25 `+10.27`;
- 2025/26 `+27.86`.

Fixed ensemble weights:

`current a2/HGB 0.25 + CatBoost depth4 0.25 + LightGBM leaves15 0.50`

### T-1

- 2024/25 `+2.27`;
- 2025/26 `+6.28`.

Fixed ensemble weights:

`HGB hist31 0.25 + CatBoost depth4 0.50 + LightGBM leaves15 0.25`

T-1 uplift is tiny and tail degradation is material; robustness is mandatory.

No frozen or production state changed from closure evidence.

## a2 fixed-temporal robustness — ACTIVE

Contract:

`ml/A2_EXTERNAL_ENSEMBLE_FIXED_TEMPORAL_V1.md`

Exact selected T-30/T-7/T-1 contracts are replayed unchanged across:

1. 2022/23 after training 2021/22;
2. 2023/24 after training 2021/22+2022/23;
3. 2024/25 after training all earlier seasons;
4. 2025/26 after training all earlier seasons.

No tuning occurs in this audit.

Pass gate:

`positive MAE improvement in all four rolling folds`

A pass still does not mutate Frozen Pre-Live v2. It only creates evidence for a separately versioned next historical / Pre-Live challenger.

## Historical layers

### Current frozen a2

- T-30 Structural Prior;
- T-14 Structural Prior;
- T-7 `hist31-leaf20-l2-1`;
- T-3 Structural Prior;
- T-1 Structural Prior.

These remain the Frozen Pre-Live v2 historical bases until a separately versioned candidate completes the full evaluation chain.

### Frozen b2

- T-30 no adjustment;
- T-14 no adjustment;
- T-7 `ewma50-resid-k6-cap05-min3`;
- T-3 `ewma50-resid-k2-cap05-min3`;
- T-1 `ewma50-resid-k6-cap05-min3`.

b2 stays frozen in Track A.

### Historical c2

`NO_CONTEXT_ALL_HORIZONS`

Forward-only verified rivalry, absences, sporting/media/hype context remains active collection/research in Track B when PIT-safe.

## Frozen d2 state

### Stage 1

`ridge-a10`

Development:

- Frozen latest MAE `4128.01`;
- Ridge latest `3320.39`;
- uplift `807.62 / 19.56%`;
- window `3619.19`;
- worst degradation `4326.90`.

### Stage 2

`P2-observation-maturity`

Development:

- latest MAE `3240.99`;
- uplift `887.02 / 21.49%`;
- window `3657.65`;
- worst degradation `1081.72`.

Frozen reliability:

- obs1 `0.25`;
- obs2 `0.60`;
- obs3+ `1.00`;
- >18h cap `0.75`;
- >12h <=18h cap `0.90`;
- <=12h cap `1.00`.

Do not mutate Ridge/P2 from individual prospective outcomes.

## Event 5

Lech Poznań vs Korona Kielce, actual `37,407`.

Errors:

- Structural T-1 `7669.07`;
- Frozen Pre-Live `9832.52`;
- raw Ridge `6652.81`;
- P2 `6652.81`;
- persisted C1 v8 `7669.07`.

Event 5 is permanently exposed.

## Prospective evidence classes

Cutoff:

`2026-10-19T19:11:01Z`

`DELAYED_LABEL_HOLDOUT`

- kickoff at/before cutoff;
- diagnostic only;
- does not count toward genuine forward promotion N.

`TRUE_POST_FREEZE_PROSPECTIVE`

- kickoff after cutoff;
- may count toward forward promotion evidence.

Never combine the classes into one headline prospective sample size.

## Delayed-label diagnostic warning

Recovered outcomes already show that frozen d2 is not uniformly beneficial:

- GKS Katowice–Pogoń: Frozen Pre-Live latest error about `1356`, d2/P2 about `2074`;
- Cracovia–Legia: Frozen about `434`, d2/P2 about `1068`.

These events are diagnostic/exposed. They may motivate a future new hypothesis but cannot be used to post-hoc mutate frozen Ridge/P2 and then be called unseen validation.

## d2 next-generation Track-B research

Allowed now under a new versioned evaluation contract:

- remaining-demand target;
- alternative capacity-normalized residual target;
- anchor-error direction/magnitude formulation;
- learned reliability;
- compact Ridge/HGB/LightGBM/CatBoost or transparent expert ensemble;
- materially new TSFM use/target.

Do not tune the existing frozen Ridge/P2 event by event.

## TSFM boundary

Stage-1 Chronos-2 / Bolt-small did not beat plain Ridge.

`TSFM_STAGE1 = NOT_PROVEN_VS_RIDGE`

No same-data fine-tuning to rescue that challenger. Reopen only with materially more independent trajectories or a materially different predeclared use/target.

## Non-negotiable CI/CD

`code -> tests -> CI -> artifact -> hashes -> result doc -> decision -> canonical docs`

Every material change creates a new candidate/version.

## One-line instruction

> **Keep Frozen Pre-Live v2 / Ridge / P2 unchanged for Track-A evidence. Do not wait for prospective N to continue Track-B R&D. Finish exact T-30/T-7/T-1 ensemble robustness; only passing horizons may enter a separately versioned next Pre-Live challenger; meanwhile keep prospective scoring and PIT-safe context collection running. Production remains unchanged.**
