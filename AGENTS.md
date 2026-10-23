# Beyond Agent Instructions

For any Beyond forecasting / ML / Demand Engine task:

1. **Read `AI_BOOTSTRAP.md` first.**
2. Then read `ml/MAE_RESEARCH_ROADMAP_V3.md`.
3. Read `ml/PROGRESS_TRACKING.md` and `ml/CURRENT_MODEL.md` for current state.
4. For Long168/P7, read `ml/D2_LONG_HORIZON_LIVE_V1_PLAN.md` before touching code or data.
5. Read `ml/CORE_PRODUCT_STATUS.md` when product/model scope matters.
6. Read `ml/LIVE_DEMAND_ENGINE_V1_PLAN.md` for live-ticket / Long72 implementation.
7. Read `ml/MODEL_ACCURACY_DEVELOPMENT_INSTRUCTIONS_V2.md` before creating a new experiment.
8. Do **not** retrain, rebuild or reproduce frozen historical benchmarks merely to recover context.
9. For latest-state questions, prefer targeted repo/DB reads over historical recomputation.
10. Never store secrets, tokens, service-role keys or credentials in repo files.

## Core modelling principle

> **The objective is lower true out-of-sample MAE, not model complexity.**

Always separate:

- **Evidence Lane:** immutable frozen packages collecting forward evidence;
- **MAE R&D Lane:** new challenger versions developed in parallel.

Never fabricate PIT history when the required state was never captured.

## Validation rule

Use `ml/temporal_validation_v1.py`.

Historical/global:

- strict season/group expanding folds;
- no future-season data in earlier training folds;
- persist exact fold identities + SHA.

Live-ticket:

- event is the independent unit;
- strict forward-event validation by kickoff;
- tied kickoff events cannot train each other;
- LOEO is diagnostic, not sufficient;
- no random snapshot split as headline evidence.

## Closed research loops

Do **not** reopen without a materially new hypothesis/data source:

1. MAE-native estimator tournament — no robust incumbent replacement.
2. Estimator `ΔMAE` uncertainty — signals insufficient.
3. Historical Long72 live incremental value — measured, uncertainty-limited.
4. Structural ↔ live convex shrinkage — retain full P2.
5. Simple post-hoc club/opponent calibration — no robust gain.

## Frozen packages

Do not mutate:

- final24 `v2/Ridge/P2`;
- Long72 `d2-long72-stage2-p2-observation-maturity-2026-10-21-v1`;
- Pre-Live / Structural Prior research anchors.

Any material model/feature/weight/target change creates a new challenger/version.

## Current evidence checkpoint

Use `public.ml_research_readiness_v1()` for current gate state instead of relying on prose counts.

Latest checkpoint read on 2026-10-23:

- Long72 reproducible forecasts: `58`;
- genuine scored Long72 events: `0`;
- fixture-context sidecar: `58 / 56 READY`;
- next-opponent sidecar: `58 / 0 READY`;
- Long168: `8/9` independent events >72h, `110` rows >72h.

## P7 Long168 — harness + executor are complete

P7 is no longer a design/coding task. The experiment is fully precommitted and the execution pipeline exists before the ninth event.

Canonical files:

- `ml/p7_long168_harness_v1.py`;
- `ml/p7_long168_anchor_replay_v1.py`;
- `ml/p7_long168_tournament_v1.py`;
- `ml/test_p7_long168_harness_v1.py`;
- `ml/test_p7_long168_executor_v1.py`;
- `.github/workflows/p7-long168-harness-v1.yml`;
- `.github/workflows/p7-long168-executor-v1.yml`;
- `ml/results/P7_LONG168_HARNESS_V1_2026-10-23.md`;
- `ml/results/P7_LONG168_EXECUTOR_V1_2026-10-23.md`.

### Hard gate

Research start requires:

`N>=9` independent events with valid observations >72h.

At `N<9`:

- freeze/model execution must fail closed;
- only the T-7 anchor audit may run;
- do not lower the threshold.

### Historical T-7 anchor boundary

The current historical Long168 events do not have persisted T-7 rows in `private.structural_prior_forecasts_v1`.

Do **not** fabricate a stored prior and do not substitute a later checkpoint.

The executor uses the frozen Structural Prior Runtime v1 replay path at exactly `kickoff - 7 days`, with chronologically prior attendance/sporting facts only.

Evidence class must remain:

`historical_pit_replay`

and:

`persisted_forecast = false`

Never describe these replayed anchors as genuinely persisted or prospective forecasts.

Frozen lineage:

- T-7 artifact SHA256: `97e712245d6539396030e88ea450809f4265bd7538aa90b29e234420231ac927`;
- historical runtime SHA256: `3c6b35142c6bd20a484f2aa758cd41284fd6f4c6db1353b138f81cf321161569`.

The workflow verifies the actual repository bytes and target-attendance invariance before anchor use.

### P7 anchor rule

Use Structural Prior **T-7** as the control throughout `72 < h <= 168`.

Never:

- use future T-3/T-1 predictions;
- interpolate future checkpoints;
- extrapolate Long72 P2 backward beyond 72h.

### Fixed P7 candidates

- `anchor-only-t7`;
- `q50-linear-residual-a002`;
- `gbr-l1-depth2-n50-lr003`.

No broad tuning after seeing results.

### At 9/9 — mandatory execution order

1. re-check `public.ml_research_readiness_v1()`;
2. explicitly dispatch `.github/workflows/p7-long168-executor-v1.yml` with `mode=execute`;
3. freeze exact eligible `ticket_event_id + as_of + snapshot_id + bucket_6h` identities;
4. persist deterministic manifest SHA256;
5. verify target/outcome absence in the freeze payload;
6. verify the historical T-7 replay package and exact frozen event set;
7. only then read/join attendance labels;
8. build strict forward-event folds;
9. run only the fixed P7 v1 candidate family;
10. report event-balanced MAE, guardrails and paired event-block uncertainty;
11. decide research advancement only;
12. keep production unchanged.

Opening real model results before identity freeze violates the experiment contract.

### P7 evaluation

Primary: strict-forward event-balanced MAE.

Required:

- median AE;
- signed bias;
- P90 AE;
- worst-event degradation;
- event-improvement rate;
- forward-fold improvement rate;
- 72–96 / 96–120 / 120–144 / 144–168h band MAE;
- paired event-block bootstrap, 5,000 draws, seed 42.

A learned candidate advances only if MAE beats the anchor **and** more than 50% of held-out events **and** more than 50% of usable forward folds improve. N=9 starts research only; it is not production adequacy.

### Workflow behavior

Automatic push to `main` runs:

- code/contract validation;
- frozen artifact byte checks;
- live support-export fetch;
- T-7 historical replay audit only.

It does **not** fit a real P7 challenger automatically.

Real P7 fitting requires explicit `workflow_dispatch -> mode=execute` and still begins with the N>=9 freeze gate.

## P4/P5 state

P4 evidence capture is operational and fail-closed.

- never backfill today's schedule into a past forecast;
- never reconstruct opponent attractiveness from outcomes not known at the forecast cutoff;
- do not choose the P4 ablation sample floor after seeing model performance.

Once genuine labeled context exists:

1. inspect availability/variance only;
2. predeclare the independent-event floor;
3. freeze the ablation protocol;
4. run P4 ablations;
5. only if context adds signal, run P5 structural + context + live combinations.

## Live runtime operational state

Live Forecast Orchestrator v1 is deployed.

Structural Prior runtimes for T-30/T-14/T-7/T-3/T-1 are active/executable.

Do not rebuild them during normal modelling work unless a dedicated runtime trigger requires it.

## Product principle

Optimize for accurate prediction early enough for the club to act, not only the lowest T-1 error.

## Production boundary

No research result activates production automatically.

`live_adjustment = 0`

until explicit reviewed activation based on genuine future evidence.
