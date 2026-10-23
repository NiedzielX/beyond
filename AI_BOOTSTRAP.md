# Beyond — AI Bootstrap / Read This First

Last updated: **2026-10-23**

## Cold-start rule

Read in this order:

1. `ml/MAE_RESEARCH_ROADMAP_V3.md`;
2. `ml/PROGRESS_TRACKING.md`;
3. `ml/D2_LONG_HORIZON_LIVE_V1_PLAN.md` when P7/Long168 is relevant;
4. `ml/CURRENT_MODEL.md`;
5. `ml/CORE_PRODUCT_STATUS.md`;
6. `ml/MODEL_ACCURACY_DEVELOPMENT_INSTRUCTIONS_V2.md`;
7. `ml/LIVE_DEMAND_ENGINE_V1_PLAN.md`;
8. `ml/MODEL_PROMOTION_GOVERNANCE_V1.md`;
9. only then open detailed results/manifests required for the task.

Do not rebuild frozen historical benchmarks merely to recover context.

## North star

> **Minimize true out-of-sample attendance-forecast MAE at decision-relevant horizons, using honest PIT-safe and reproducible evidence.**

Model complexity is secondary. Predictive information and future MAE are primary.

## Structural core

- 1,530 Ekstraklasa matches / five complete seasons;
- 7,650 PIT snapshots;
- T-30/T-14/T-7/T-3/T-1;
- Structural Prior / Global Model family remains incumbent.

2024/25 and 2025/26 are exposed historical research evidence for future challenger decisions.

## Frozen Long72 live package

`d2-long72-stage2-p2-observation-maturity-2026-10-21-v1`

Historical event-balanced comparison:

- structural anchor MAE `3707.14`;
- frozen P2 MAE `3012.63`;
- `ΔMAE=-694.51` / `18.73%` improvement;
- 95% paired event-block interval `[-1549.89,+148.05]`;
- P2 bias `+917.05`.

The package is immutable and continues genuine prospective evidence collection.

## Closed loops — do not repeat by default

- P2 MAE-native estimator tournament — no replacement;
- P3 estimator `ΔMAE` uncertainty — signals insufficient;
- P5a structural/live convex shrinkage — retain full frozen P2;
- P6 historical Long72 live incremental value — measured, uncertainty-limited;
- P8 club/opponent post-hoc calibration — no robust gain.

## Validation contract

Use `ml/temporal_validation_v1.py`.

Historical/global:

- strict expanding season/group folds;
- no future-season information in earlier training folds.

Live-ticket:

- event is the independent unit;
- strict forward-event validation by kickoff;
- tied kickoffs cannot train one another;
- LOEO is diagnostic only;
- no random snapshot split as headline evidence.

Persist exact fold identities + SHA.

## Current live evidence state

Latest checkpoint on 2026-10-23:

- Long72 reproducible forecast rows: `48`;
- genuine scored Long72 events: `0`;
- fixture-context sidecar: `48`, `46 READY`;
- next-opponent sidecar: `48`, `0 READY`.

All P4 capture infrastructure is operational and fail-closed.

Do not reconstruct missing schedule/opponent context from later knowledge.

## Canonical readiness RPC

Use:

`public.ml_research_readiness_v1()`

Triggers:

1. P7 Long168 at `>=9` independent events with rows >72h;
2. first genuine Long72 score;
3. first READY next-opponent-attractiveness row.

An hourly condition watch exists for these triggers.

## P7 Long168 — IMPORTANT

P7 is **already designed and precommitted**. Do not redesign it at 9/9.

Canonical files:

- `ml/p7_long168_harness_v1.py`;
- `ml/test_p7_long168_harness_v1.py`;
- `.github/workflows/p7-long168-harness-v1.yml`;
- `ml/results/P7_LONG168_HARNESS_V1_2026-10-23.md`;
- `ml/D2_LONG_HORIZON_LIVE_V1_PLAN.md`.

Current readiness:

- `8/9` independent events >72h;
- `110` rows >72h.

The harness must fail closed at 8/9.

### At the ninth event

Do this in exact order:

1. export current Long168 payload;
2. freeze exact `event/as_of/snapshot/bucket` identities for `72<h<=168`;
3. persist deterministic manifest SHA;
4. verify target/outcome is absent;
5. only then attach attendance labels;
6. build strict forward-event fold manifest;
7. run the fixed candidate family;
8. report event-balanced MAE + paired event-block uncertainty;
9. make explicit research decision;
10. keep production unchanged.

### P7 v1 anchor

Use **Structural Prior T-7** throughout 72–168h.

Never:

- use future T-3/T-1 predictions;
- interpolate future checkpoints;
- extrapolate frozen Long72 P2 backward beyond 72h.

### P7 v1 candidates

Fixed before results:

- `anchor-only-t7`;
- `q50-linear-residual-a002`;
- `gbr-l1-depth2-n50-lr003`.

No broad hyperparameter search.

Primary metric: strict-forward event-balanced MAE.

Uncertainty: paired event-block bootstrap, 5,000 resamples, seed 42.

N=9 permits research only; it is never production evidence by itself.

## Remaining roadmap

### P4/P5

Wait only for genuine evidence mathematically required:

1. labeled P4 context events accumulate;
2. inspect feature availability/variance without model results;
3. predeclare ablation sample floor;
4. run controlled P4 ablations;
5. if context contributes incremental MAE signal, run P5 `structural + context + live` combinations with fold-local weights.

### P7

Harness is ready. Only the ninth independent >72h event is missing.

## Hard boundaries

Never:

- call inspected historical holdouts unseen;
- use realized future context at an earlier cutoff;
- reconstruct missing PIT schedule/opponent history;
- retune frozen packages under the same ID;
- learn combination weights on evaluation folds;
- use random snapshot splits as headline evidence;
- open P7 model results before the identity freeze;
- lower P7's nine-event research gate;
- promote from historical uplift alone.

## Production boundary

`live_adjustment = 0`

until explicit reviewed activation based on separate genuine future evidence.

## One-line instruction

> **P7 is precommitted and must fail closed at 8/9. At 9/9 freeze identities first and model second. P4/P5 remain label-bound. Do not invent evidence or reopen closed tuning loops.**
