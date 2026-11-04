# C1 live seat median v1 — precommit before fit

2026-11-04. Package:`c1-live-seat-median-v1-frozen-2026-11-04-n20`. Authorized continuation of `C1_MAE_LITERATURE_EXECUTION_SUPPLEMENT_V1.md`. New separate experiment; no existing frozen model, collector, forecast or evaluation rule changes.

## Exact hypothesis and novelty

Test whether a sparse linear conditional median of **attendance in persons**, using the same compact current live features and identical20eventtraining information, improves genuine future errors over the frozen20eventoccupancy Ridge. This is an alternative learner/objective formulation, **not a pure loss-only ablation**: target decoding and L1regularization also differ. Any gain belongs to the whole declared package until a later separately precommitted ablation establishes its source.

C1v1/v2alreadytestedL1trees/robust/club-aware variants; structuralT1alreadyusesL1; structural capacityweighting was rejected. Native-global quantile-linear research and P7/P4quantile learners also exist. We do not claim to discover quantile regression or reopen those tournaments. This experiment concerns final24live inputs, the exact compact30features and newly expanded20eventlive-training cohort, with prospective-only evaluation. Existing D2P2is not a superior same-time benchmark on the11exposed cases.

## Fixed training and estimator

- Exact private source frame SHA256:`be9aab4721e69661b8f14d3e1e8938abde569dabd6f7878e0986868fc0756549`, already validated by training-expansion freeze. No rows/events added or removed.
-20independent events /74rows /11clubs; IDs`1,3,4,5,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23`; labels confirmed by2026-11-04T12:17:04.736622Z. All20are exposed training, never fresh validation.
- Same30compact feature names/order; **reuse the exact fitted imputer/indicator/scaler from the frozen20eventRidge**, with no refit or new club encoding. This isolates the information representation from the estimator change.
- `sklearn.linear_model.QuantileRegressor(quantile=0.5, alpha=0.1, solver='highs', fit_intercept=True)`; fixed single fit; no grid, loss comparison, CV-based parameter selection, early stopping or alternative after observing coefficients/errors.
- Target directly`actual_attendance`in persons; no occupancy target or capacity sample weighting. Prediction already has person units; clip to[0,stadium_capacity] as before. Never multiply this estimator's output by capacity.
- Sample weights exactly the old equal-event rule, normalized to mean1. For this estimator the objective is `sum(w_i * pinball_0.5(y_i - b - z_i beta))/sum(w_i) + 0.1 * ||beta||_1`; intercept unpenalized. Pinball0.5is half absolute-person loss. The penalty coefficient is fixed before fit, not comparable numerically to Ridgealpha10and not selected from old errors.
- Numerical versions:numpy2.3.5,pandas2.2.3,sklearn1.8.0,joblib1.5.3,scipy1.17.0. Verify exact source-frame/manifest/dependency hashes; use one canonical fresh artifact directory and an exclusive fit-start marker. Load-back finite/bounds checks only; no trainingMAEor reused holdout score.

Record source/precommit/code/manifest/estimator checksums, fit time and coefficient support as descriptive mechanism metadata. A zero/sparse coefficient result is retained, never a reason to select a newalpha underv1. No new historical accuracy claim.

## Forward evidence and serving policy

Freeze after publishing the precommit and implementation. Inference loads models only. Reuse the existing current C1input RPC and exact-prior metadata resolver, with identical validated input for all experts. Require actual current request within15minutes, genuine final24window, latest source at/after this package's freeze and no older than2hours, one representative per6hourbucket, exact timestamps/snapshot/PIT/anchor identity, prior genuinely generated before the representative, no known outcome or training event. Preserve older genuine context; no issue backfill.

For each eligible source observation capture **median**, **frozen20eventRidge**, **original9eventC1v8** and **shared prior** simultaneously. Apply the original unchangedv8policy separately to each live expert. Record raw and governed forecasts; never let the actual outcome select which output to report. Store actual issue/source times, IDs, input hashes and all artifact identities immutably in a new private namespace. Repeated event/snapshot returns original evidence or rejects conflict; failed/stale/missing inputs remain coverage failures.

Old training-expansion collector/scorer helpers are themselves frozen. Import validated reusable functions only; do not edit or relabel them for this package. New collection/scoring implementation has its own source lock and content-addressed `c1-seat-median-v1/`private recovery namespace. A no-candidate run is operational proof, not prediction/DB/accuracy proof. Worker deadline must be explicit and at most72hours; no claim of perpetual coding or managed deployment.

## Future evaluation and decision

All eligible paired captures remain in their cohort. Latest-per-event uses latest captured source time before kickoff; window metric first averages errors within each event. Confirmed attendance must first become available after immutable issue and use consistent provenance; inventory never supplies a label. Preserve immutable scores and the first completed review.

First fixed review: at least30new independently scored events /8clubs, none in training. Early scores descriptive; no retuning/early stopping for a favorable result. Report raw experts and governed outputs separately, equal-event latest/windowMAE, pairedDelta/bias, improvement rate, medianDeltaAE, P90/worst, club/horizon descriptive groups, prediction/failure/missing coverage. Bootstrap paired **event** errors,10000resamples,seed42,95%intervals; this review size is not a precision guarantee.

Primary learner question: median raw vs frozen20eventRidge raw; research support requires negative meanDeltaAE and95%upperendpoint<0. The product objective additionally requires governed median to beat **all three** governed20eventRidge, originalv8policy and shared prior under the same paired rule. Report those gates separately; raw-only success cannot justify a lower governed-C1MAE claim. Bias/tail/coverage remain mandatory review evidence; no automatic production activation. Target1200is a research goal, not a promised score.

If unsupported at first review, record no advancement/rejection; no newalpha/threshold/clubsubset rescue underv1. A verified contract defect may stop collection, preserving all evidence; substantive repair receives a newversion. Existing550-seat and other frozen-lane gates remain unchanged.

`production_change=false`, `live_adjustment=0`.
