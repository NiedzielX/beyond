# C1 training expansion v1 — one new-information experiment

Precommitted2026-11-04, before candidate fitting. Candidate/package: `c1-training-expansion-v1-frozen-2026-11-04-n20`. This is a separate shadow experiment, not a replacement or refreeze of C1 v8.

## Hypothesis and single intervention

The matched audit (`C1_LIVE_MATCHED_AUDIT_RESULT_V1.md`) found no numerical serving mismatch; the compact generic live expert had only9training events and no Wisła/Górnik examples. Eleven newly confirmed events provide genuinely additional training labels and four additional clubs. Test whether **expanding training support alone** improves future paired attendance MAE. This does not repair missing season history or demonstrate that sample size caused the old errors.

Hold unchanged: the exact original30compact features, median imputation with indicators, standard scaling, generic Ridge alpha10, direct-occupancy target, equal total event weights, clipping to[0,capacity], original v8policy thresholds/slope logic and T-1structural runtime. No club encoding, new seat-map feature, hyperparameter search, loss change, tuning on the11audit errors, or ensemble selection. One fit only.

## Fixed training evidence

Input pack captured2026-11-04T12:17:04.736622Z. Training cutoff equals that time. All target outcomes must have been confirmed before it and equal the canonical DB exports. Exactly20events /74final24representatives /11clubs:

`1,3,4,5,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23`.

Original9events/30rows remain exactly identifiable. Verify all900old feature cells and their targets against the old frozen training contract before the new fit. Use the existing legacy structural-prior replay compatibility wrapper and original capacity audit; no b2 correction in C1 training features. Training rows use the canonical final24/6-hour representatives, not C1-matched timestamps chosen after the audit. Every prefix ends before kickoff, uses PIT-validated features and an eligible T-1anchor. Target attendance is not an input feature. Historical source-publication times are not independently verified; declare this limitation rather than claiming a historical out-of-time evaluation.

All20events, including the former11holdouts, become training/exposed data. **No in-sample, cross-validation or reused holdout MAE is an accuracy claim or promotion gate.** Training load-back predictions are finite-output correctness checks only. Do not pick a candidate after viewing fitted errors. Hash private inputs, training feature/target contract, code, this precommit, original frozen dependencies and new artifact. Keep raw source exports and per-row training records private; commit only safe manifests and the serialized estimator.

## Forward inference and immutable capture

An inference-only adapter loads the new artifact and the original C1v8artifact. It accepts only genuine current `get_c1_shadow_v8_inputs_v1` inputs; using that existing read-only collector does not authorize writing the new package to the old gateway. Require input `requested_at` within15minutes of wall clock, eligible kickoff within24hours, actual prior generated/target timestamps no later than latest snapshot, exact snapshot/feature timestamps and PIT flags, at most one genuine representative per6-hour bucket, strictly before kickoff. Latest source timestamp must be at/after the new artifact freeze and no older than2hours at capture. Preserve older genuine prefix representatives as context. A stale source is failed coverage, never a retro-prediction.

Reject any included target whose canonical outcome already exists. Persist the complete paired prior/originalv8/newraw/newpolicy predictions with artifact IDs, snapshot IDs, source as-of timestamps and actual issue time **before outcomes**, in an exclusive immutable local file under a new namespace outside Git. Repeated event/as-of attempts must return the original identical evidence or reject conflict; never overwrite. No fitting during inference. Guard both artifact hashes and the new manifest/precommit hashes. A no-candidate execution is operational proof only, not a forecast or DB persistence proof. Any later private recovery or managed deployment must preserve original file bytes/times and use a separate namespace.

## Prospective evaluation and stop rule

Primary: latest eligible paired snapshot per event, selected solely by source time before kickoff, comparing the new **unchanged-policy output** with actual C1v8policy and the shared structural prior at the same issue/as-of. Also report raw experts separately and event-balanced window MAE over identical captured snapshots. Do not substitute the better of raw/policy after seeing outcomes. Only outcomes first confirmed after immutable capture may score; retain their source, confirmation time and definition. Inventory availability never supplies an attendance label.

First fixed review requires at least30new scored independent events from8clubs, all after freeze and outside the20training IDs. Report coverage/failures, paired delta, event-bootstrap uncertainty (10,000resamples, seed42), signed bias, P90/worst absolute error, and per-club/horizon descriptive results. Event rows/prefixes remain grouped. Scheduled forecast freshness gates may narrow coverage; report that rather than equating better filtered MAE with broad coverage. Early scores remain descriptive; no interim retuning or early stopping for a favorable result.

Continue this version unchanged until that first review, or stop for a verified contract/capture defect (preserve failures and issue a new version for any substantive repair). Research advancement requires paired mean AE lower than **both** benchmarks and the upper endpoint of each95%paired event-bootstrap mean-delta interval below0. Also report, without optimization, whether bias/tail or missing coverage worsens. This is a research evidence gate, **not production approval**. If not met, reject/no advancement under this version; do not search caps/thresholds on the same30events. MAE1200is achieved only if this genuinely future headline supports it, never by a training fit. Existing550-seat/frozen-lane gates remain unchanged.

## Operational bounds

Before launching collection, check live fixture eligibility and record a concrete host-dependent deadline. No perpetual coding, no missed-window backfill, no writes to old C1forecasts/scores, no automatic production activation. The existing short-lived cloud workers stopNov5 09:30UTC; their continued operation does not prove this candidate is collecting. New scheduled/main deployment needs its own actual execution and persistence evidence.

`production_change=false`, `live_adjustment=0`.
