# C1 history-support residual ablation v1

Recorded 2026-11-05 before fitting either head. User authorized immediate execution of the accepted MAE plan. This is a separate shadow experiment under roadmap v6; frozen C1, median20/26, Ridge20, trajectory, P9, Form5 and P4a contracts remain unchanged.

Package: `c1-history-support-residual-v1-frozen-2026-11-05-n26`.

## Hypothesis and novelty

The live compact30 representation exposes the structural forecast but omits explicit point-in-time verified home-history support, recency and its level relative to that forecast. Test whether exposing that information improves a small residual predictor on future fixtures. This is a representation/information ablation, not a claim that Ridge/quantile loss is new. Existing prior models already consume historical attendance; their use does not establish that this representation helps the live head.

The consumption audit finds all16new records in the serving view, but most earlier priors correctly predate them. They were unavailable at every old26training observation. **They must contribute zero to those historical rows**. This experiment tests explicit known history, not a fictitious historical effect of the16imports. Source metadata allow conservative historical reconstruction; original pre-cutoff source snapshots for these training rows are not independently verified. Training/exposed status remains explicit. Do not reopen LaneA/B/C2, capacity-weighting or context grids on known errors.

## Exact data and source boundary

Use exactly the immutable26fixtures/80rows/12clubs and labels validated by `C1_SUPPORT26_PRECOMMIT_V1.md`, CSV SHA256 `0b8eb22c767d16e07b84b59eaa73aeff5ca55b11a220f4939dbb2ae2aaa9d778`. All26are exposed training, including the17old scored C1fixtures. No candidate MAE is computed on them.

History source is the exact current exporter envelope SHA256 `ad1fc737f607297f20ea171e0ea99d4d3398fccccb959a6980339bceb6d67afa`, captured onNov5 with44history/27outcomes/38canonical events/135sporting rows. Use the existing revision-aware catalog, canonical club aliases and genuine per-row knowledge=max(observed/confirmed,created,updated,verified). At each training observation use only already completed, already known home fixtures in the target season. Deduplicate exact canonical sources, reject conflicting known values and ambiguous same-home matchday clocks; exclude the target fixture. Rejected/unknown sources remain unknown. Do not reinterpret a zero known-source count as zero attendance.

Target-free preparation:34of80rows have known verified home history, spanning13fixtures/9clubs. There are6distinct support values,13distinct nonmissing recent gaps and34ages. This is input coverage/variation, not outcome performance. Keep all other rows, with explicit missing level/age, and retain canonical event-balanced weighting.

## One fixed experiment, two fixed fits

Control features, in exact order:

1. `prior_occupancy = prior_p50/capacity`;
2. `available_share = available_total/capacity`;
3. `removed_24h_share = net_removed_24h/capacity`;
4. `removed_6h_share = net_removed_6h/capacity`;
5. `horizon_days = (real kickoff - actual observation)/24h`;
6. `observed_span_days = observation_window_hours/24`.

Augmented head adds exactly:

7. `verified_home_n_log = log1p(unique known current-season home fixtures)`;
8. `verified_home_recent_gap = (mean of latest up to3known home attendances - shared prior_p50)/capacity`, missing if none;
9. `verified_home_age_days = elapsed days since latest known home fixture`, missing if none.

Availability is public inventory, not paid sales. Keep releases/negative changes and genuine visible zero; missing/hidden remains missing. Neither feature construction nor inference receives the current target attendance.

Both heads use a fresh training-only median imputer with missing indicators, StandardScaler, and **QuantileRegressor(quantile=0.5,alpha=0.1,solver='highs',fit_intercept=True)**. Target is direct-person residual `actual_attendance - shared prior_p50`. Same original mean-normalized equal-event weights. Each head is fitted exactly once on the same26/80data; two declared fits total, no hyperparameter/model/feature/cap search. Decode `clip(shared prior + fitted residual,0,capacity)`. Keep any sparse/zero coefficient result without selection. Also apply the unchanged v8policy separately; never tune its thresholds/slope rule from the result.

Before fit require immutable source checks, canonical26/80/12identity, at least20training fixtures/8clubs, history support at least8fixtures/5clubs and variation in each declared history feature. These are this experiment's target-free screening rules, not a replacement for any frozen Form5/P4a gate. Publish tested source/precommit before fit; fresh canonical artifact directory plus durable fit-start marker. Pin source/data/environment/precommit/benchmark hashes. No training/historical-holdout MAE, alternate fit or rescue configuration.

## Genuine future capture

Both heads are inference-only after freezing. Use identical genuine final24source representatives and an actually available T-1prior. All26training fixtures and aliases of their canonical home/matchday units are excluded; reject known target outcomes. Latest observation must be at/after freeze, at most2hours old, actual request within15minutes, and actual issue before kickoff. No historical prospective backfill.

A separate sidecar may read an immutable support26candidate/input already captured in the same current interval, verify its complete frozen input/benchmark identity and add both new decisions. Its **own actual issue time** is recorded after inference; never reuse the older forecast's issued_at. Benchmark comparisons share the exact observation/anchor, with earlier benchmark issue times preserved.

For every representative, select the latest byte-verified private source archive completed at/before its observation and at most60minutes old. Build new history features from that exact preserved snapshot, not current source rows. Retain complete input/archive/feature manifests before saving the new immutable forecast. Original archived revisions remain unchanged. A missing archive/conflict is failed coverage, not a zero feature or reconstructed past issue. Preserve max4representatives/one per6hourbucket and all actual source clocks. No writes to old forecast tables/ledgers.

Private recovery namespace: `c1-history-residual-v1/`. Bounded, source-locked, host-dependent worker, at most72hours; verified upload/read-back/decompression/restore and exclusive runtime/lifetime locks. It is not a managed permanent deployment.

## Scoring and review

Accept only genuine confirmed attendance first known after the new actual issue. Validate/replay complete benchmark decisions from original input and both new heads from saved feature/source manifests. Modified decisions, source substitutions, alias duplicates, premature/revised labels or changed model/source hashes fail closed. Save immutable scores; missing labels remain unscored.

Primary information question: augmented raw MAE versus control raw MAE. Separate product question: augmented governed policy versus **all six** control policy, median26policy, median20policy, Ridge20policy, original9C1policy and shared prior. A raw gain alone is not a product-MAE claim.

Latest-per-event MAE is primary; also event-balanced window MAE, horizon/club coverage, bias, P90/worst errors/degradation, median paired DeltaAE and improvement rate. All comparisons use identical events/source times. Fixed first review:30new independently scored canonical fixtures/8clubs, none in training; include all then-available eligible scores. Paired event bootstrap10000resamples,seed42,95%intervals. Support requires negative mean DeltaAE and negative upper interval endpoint against control raw; product requires that rule against all six predeclared policy benchmarks. Preserve the first review. Earlier descriptive scores cannot trigger retuning or favorable stopping. Existing550-seat/P9/encoder/Form5/P4a gates remain unchanged. No automatic promotion;1200is a goal, not promised performance.

`production_change=false`, `live_adjustment=0`.
