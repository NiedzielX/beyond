# C1 historical recipe replay v1

Recorded2026-11-05before any new fitting/scoring in this experiment. Latest user explicitly requested historical testing. This authorizes a separate exposed diagnostic; it does not amend `C1_SUPPORT26_PRECOMMIT_V1.md`. Strategy:`MAE_RESEARCH_ROADMAP_V6.md`. Experiment:`c1-historical-recipe-replay-v1`.

## Question and limitations

Does the already fixed direct-person median recipe behave better than structural prior, persisted C1v8 and a fixed Ridge recipe when the target fixture is excluded? How much of that conclusion survives chronological training using only earlier known outcomes? These are exposed historical data; no fresh validation, model selection, prospective MAE claim or promotion. Do not evaluate the actual frozen26artifact on its training events. A fold trained on25fixtures is a counterfactual recipe model, not the live26model.

## Fixed inputs and coverage

Immutable26fixture/80row/12club training frame from support26. Fixed evaluation cohort:all17persisted C1scored fixtures in the captured current view; earlier11use44matched C1time representatives and later6use exactly their single stored latest C1time reconstruction. Verify latest time/prior/target/capacity identities and original9raw numerical parity. Six singletons cannot reproduce a multi-observation history; label their policy outputs as sparse-context counterfactuals. Do not reconstruct missing prefixes or prospective issues. Raw data remain private.

Pin every source checksum in `artifacts/c1_historical_replay_v1_source_hashes.json` before fitting. Same30features/order and fixed quantile0.5/alpha0.1/HiGHS/intercept, direct-person target, equal-event weights and[0,capacity]clipping. **Every fold fits a new median-imputer/missing-indicator/scaler using training rows alone**; no frozen20/26representation reuse. FixedRidge10predicts occupancy with its own fresh training-only preprocessor, then clips person forecasts. No alternative alpha/loss/features/model search.

## Two predeclared evaluation designs

1. **Chronological recipe replay.** One training cutoff per target fixture:earliest available evaluation prefix. Exclude the whole target/canonical fixture and require every training fixture kickoff and every training row before that cutoff. Training label availability is conservatively max(confirmed_at,created_at,updated_at), all explicit and required, at/before cutoff. Fixed minimum9independent training fixtures(originalC1training scale); insufficient folds stay coverage failures. Refit on all eligible earlier fixtures, never on a later match or label. Compare median-expanded, median-base20-restricted and Ridge-expanded. The six new labels first known Nov4cannot train predictions issued by Nov2; report the actual support difference, including equality. No earlier knowledge is inferred from a result's occurrence date.
2. **Leave-one-fixture-out exposed diagnostic.** For each17target fixture exclude every training row of its canonical fixture. Compare median using remaining support26(up to25), median restricted to remaining base20(up to20), and Ridge with the same expanded support. Later fixtures/labels are allowed **only in this explicitly non-temporal diagnostic**; it is not PIT-safe live simulation. No hyperparameter selection or adoption based on this known cohort.

Canonical unit is normalized home club plus Europe/Warsaw kickoff date; aliases cannot split the same fixture. Label consistency, positive finite capacity/target bounds, unique event/prefix rows, strictly pre-kickoff times, feature as-of/snapshot identity, stored T-1prior readiness/time/identity and source hashes must validate. Holdout labels never enter the learner or preprocessing. Existing reconstructed structural inputs retain their previously disclosed historical publication-time assumptions; neither design independently proves those source inputs were published then. No historical result is promoted to fully audited PIT or prospective evidence.

## Comparisons and reporting

Primary descriptive metric:event-balanced latest-row attendance MAE. Compare each model with prior and actual persisted C1policy on exactly the same eligible target events/times. Also report raw and unchanged-v8policy outputs, event-balanced window MAE, bias, median paired DeltaAE, improvement rate, P90/worst errors/degradation, club/horizon groups, train-size ranges and first11/later6coverage. Window reference C1policy is not available for every representative; do not repeat its latest value to fabricate a window baseline. Stored final C1raw/prior/policy metrics are checked against source errors; policy history differences remain explicit.

Paired event bootstrap10000resamples,seed42,95%intervals, descriptive only; no promotion gate or significance-driven model choice. Include all predeclared eligible fixtures, preserve failures and sparse histories. Do not compare numbers from different chronological/LOEO cohorts as a causal gain. No training MAE. No retuning after results. Publish implementation/precommit before actual run; separate immutable run-start marker/results, private model-independent fold manifests/predictions and independently restored backup.

`production_change=false`, `live_adjustment=0`. All frozen artifacts/sources/precommits, review gates and historical misses stay unchanged. Prospective collectors continue separately.
