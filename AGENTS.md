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

2026-10-23:

- Long72 reproducible forecasts: `48`;
- genuine scored Long72 events: `0`;
- fixture-context sidecar: `48 / 46 READY`;
- next-opponent sidecar: `48 / 0 READY`;
- Long168: `8/9` independent events >72h, `110` rows >72h.

Use `public.ml_research_readiness_v1()` for current gate state rather than relying on stale prose.

## P7 Long168 — precommitted contract

P7 design work is complete before the ninth event.

Canonical harness:

- `ml/p7_long168_harness_v1.py`;
- `ml/test_p7_long168_harness_v1.py`;
- `.github/workflows/p7-long168-harness-v1.yml`;
- `ml/results/P7_LONG168_HARNESS_V1_2026-10-23.md`.

### Hard gate

`N>=9` independent events with valid observations >72h.

At `N<9` the freeze/model path must fail closed. Do not lower the gate.

### At 9/9 — mandatory order

1. export Long168 payload;
2. freeze exact eligible `ticket_event_id + as_of + snapshot_id + bucket_6h` identities for `72<h<=168`;
3. persist deterministic manifest SHA256;
4. prove target/outcome is absent from freeze payload;
5. only then join attendance labels;
6. build strict forward-event folds;
7. run only the fixed P7 v1 candidate family;
8. report event-balanced MAE and event-block uncertainty;
9. decide research advancement only;
10. never auto-activate production.

Opening model results before identity freeze violates the experiment contract.

### P7 anchor

Use Structural Prior **T-7** as the control anchor throughout 72–168h.

Never use future T-3/T-1 predictions and never extrapolate Long72 P2 backward beyond 72h.

### Fixed P7 candidates

- `anchor-only-t7`;
- `q50-linear-residual-a002`;
- `gbr-l1-depth2-n50-lr003`.

No broad tuning after seeing results.

### P7 evaluation

Primary: strict-forward event-balanced MAE.

Required:

- median AE;
- signed bias;
- P90 AE;
- worst-event degradation;
- event-improvement rate;
- forward-fold consistency;
- 24h horizon-band MAE;
- paired event-block bootstrap, 5,000 draws, seed 42.

N=9 starts research only. It is not production adequacy.

## P4/P5 state

P4 evidence capture is operational and fail-closed.

- never backfill today's schedule into a past forecast;
- never reconstruct opponent attractiveness from outcomes not known at the forecast cutoff;
- do not choose the P4 ablation sample floor after seeing model performance.

Once genuine labeled context exists:

1. inspect availability/variance only;
2. predeclare the independent-event floor;
3. run P4 ablations;
4. only if context adds signal, run P5 structural + context + live combinations.

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
