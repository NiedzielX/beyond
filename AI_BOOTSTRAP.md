# Beyond — AI Bootstrap / Read This First

Last updated: **2026-10-23**

## Cold-start rule

Read in this order:

1. `ml/MAE_RESEARCH_ROADMAP_V3.md`;
2. `ml/PROGRESS_TRACKING.md`;
3. `ml/D2_LONG_HORIZON_LIVE_V1_PLAN.md` for P7/Long168;
4. `ml/CURRENT_MODEL.md`;
5. `ml/CORE_PRODUCT_STATUS.md`;
6. `ml/MODEL_ACCURACY_DEVELOPMENT_INSTRUCTIONS_V2.md`;
7. `ml/LIVE_DEMAND_ENGINE_V1_PLAN.md`;
8. `ml/MODEL_PROMOTION_GOVERNANCE_V1.md`;
9. only then open detailed result/manifests needed for the task.

Do not rebuild frozen historical benchmarks merely to recover context.

## North star

> **Minimize true out-of-sample attendance-forecast MAE at decision-relevant horizons, using honest PIT-safe and reproducible evidence.**

Model complexity is secondary. Predictive information and future MAE are primary.

## Structural core

- 1,530 Ekstraklasa matches / five complete seasons;
- 7,650 PIT snapshots;
- T-30/T-14/T-7/T-3/T-1;
- Structural Prior / Global Model remains incumbent.

Historical runtime SHA:

`3c6b35142c6bd20a484f2aa758cd41284fd6f4c6db1353b138f81cf321161569`

Previously inspected historical seasons remain exposed research evidence.

## Frozen Long72 package

`d2-long72-stage2-p2-observation-maturity-2026-10-21-v1`

Historical comparison:

- anchor MAE `3707.14`;
- frozen P2 MAE `3012.63`;
- `ΔMAE=-694.51` / `18.73%`;
- 95% interval `[-1549.89,+148.05]`;
- P2 bias `+917.05`.

Immutable. Genuine prospective evidence continues.

## Closed loops

Do not reopen without materially new information:

- P2 estimator tournament;
- P3 estimator uncertainty;
- P5a structural/live shrinkage;
- P6 historical incremental live value;
- P8 simple club/opponent calibration.

## Temporal validation

Use `ml/temporal_validation_v1.py`.

Historical/global:

- strict expanding season/group folds.

Live:

- event is independent unit;
- strict forward-event validation;
- tied kickoffs cannot train one another;
- no random snapshot split as headline evidence;
- persist exact fold identities + SHA.

## Current live checkpoint

Read current state from:

`public.ml_research_readiness_v1()`

Latest checkpoint on 2026-10-23:

- Long72 reproducible forecasts: `58`;
- genuine Long72 scored events: `0`;
- fixture-context sidecar: `58`, `56 READY`;
- next-opponent sidecar: `58`, `0 READY`;
- Long168: `8/9` independent events >72h, `110` rows >72h.

Do not rely on these prose counts if a fresh RPC result is available.

## P4 / P5

P4 evidence capture is operational and fail-closed.

Never reconstruct missing schedule/opponent context from later knowledge.

When genuine labeled context exists:

1. inspect availability/variance only;
2. predeclare independent-event sample floor;
3. freeze ablation protocol;
4. run controlled P4 ablations;
5. only if context adds signal, run P5 structural + context + live combinations with fold-local weights.

## P7 Long168 — fully precommitted and executable

Do not redesign P7 at 9/9.

Canonical files:

- `ml/p7_long168_harness_v1.py`;
- `ml/p7_long168_anchor_replay_v1.py`;
- `ml/p7_long168_tournament_v1.py`;
- `ml/test_p7_long168_harness_v1.py`;
- `ml/test_p7_long168_executor_v1.py`;
- `.github/workflows/p7-long168-harness-v1.yml`;
- `.github/workflows/p7-long168-executor-v1.yml`;
- `ml/results/P7_LONG168_HARNESS_V1_2026-10-23.md`;
- `ml/results/P7_LONG168_EXECUTOR_V1_2026-10-23.md`;
- `ml/D2_LONG_HORIZON_LIVE_V1_PLAN.md`.

### Hard gate

Research start requires:

`>=9` independent events with valid rows >72h.

At 8/9:

- freeze/model execution must fail closed;
- only anchor audit is allowed.

### Historical T-7 anchor

Current historical Long168 events have no persisted T-7 rows in the runtime forecast table.

Use the explicit frozen Runtime v1 historical replay path.

Evidence class:

`historical_pit_replay`

and always:

`persisted_forecast = false`

Never describe replay anchors as genuinely persisted seven-day forecasts.

T-7 artifact SHA:

`97e712245d6539396030e88ea450809f4265bd7538aa90b29e234420231ac927`

The executor workflow verifies actual artifact/runtime bytes and target-attendance invariance before use.

### P7 anchor rule

Use Structural Prior T-7 throughout `72<h<=168`.

Never:

- use future T-3/T-1 forecasts;
- interpolate future checkpoints;
- extrapolate Long72 P2 backward beyond 72h.

### Fixed candidates

- `anchor-only-t7`;
- `q50-linear-residual-a002`;
- `gbr-l1-depth2-n50-lr003`.

No broad search.

### At the ninth event

Exact order:

1. re-check `public.ml_research_readiness_v1()`;
2. explicitly dispatch `.github/workflows/p7-long168-executor-v1.yml` with `mode=execute`;
3. freeze exact event/as-of/snapshot/bucket identities;
4. persist freeze SHA;
5. verify historical T-7 replay package;
6. only then read/join attendance labels;
7. build strict forward folds;
8. run fixed candidates;
9. report event-balanced MAE + guardrails;
10. run paired event-block bootstrap, 5,000 draws, seed 42;
11. issue research-only decision;
12. keep production unchanged.

Automatic `main` pushes run anchor audit only, not the real tournament.

## Hard boundaries

Never:

- call inspected historical holdouts unseen;
- use future context at an earlier cutoff;
- reconstruct missing as-known schedule/opponent state;
- claim historical PIT replay was persisted prospectively;
- retune frozen package IDs;
- learn combination weights on evaluation folds;
- random-split live snapshots as headline evidence;
- open real P7 model results before identity freeze;
- lower the nine-event P7 gate;
- promote from historical uplift alone.

## Production boundary

`live_adjustment = 0`

until explicit reviewed promotion based on separate genuine future evidence.

## One-line instruction

> **P7 is fully coded but remains blocked at 8/9. Historical T-7 anchors are explicit replay evidence, not persisted forecasts. At 9/9 run the manual executor: freeze first, labels/models second.**
