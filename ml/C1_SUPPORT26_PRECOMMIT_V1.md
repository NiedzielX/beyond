# C1 direct-person median, expanded support26 v1

Recorded November 5, 2026, before implementing or fitting this candidate. User authorized continuation of the announced 20-to-26-event training experiment. Canonical strategy: `MAE_RESEARCH_ROADMAP_V6.md`; accepted objective programme: `C1_MAE_LITERATURE_EXECUTION_SUPPLEMENT_V1.md`. Existing frozen experiments, forecasts and review gates are unchanged.

Package: `c1-live-seat-median-support26-v1-frozen-2026-11-05-n26`.
Live expert: `c1-live-linear-seat-median-q50-a01-n26`.

## Hypothesis and isolated difference

Six additional independently confirmed fixtures extend training support from 20 to 26 events. Test whether that new information reduces future raw attendance MAE relative to the already frozen median20, with the learner and representation held fixed. This is a training-information comparison, not a new loss/architecture search. Earlier C1v8 errors identify limited support as a plausible hypothesis, not an established cause.

All 26 fixtures, including the old 17 scored C1 events, are exposed training. None becomes fresh validation. Do not score this candidate on them, optimize a coefficient/threshold from their errors, or claim that training fit or numerical reconstruction proves improvement. All prior closed trajectory/weighting experiments remain closed.

## Exact immutable training information

- 26 canonical independent home-matchday fixtures, 12 clubs, 80 rows. Original 20 fixtures retain 74 historical prefixes; exactly one latest actually persisted C1-time row is added for each of6/443/444/445/446/447. This unequal prefix sampling is declared, not selected by error. Equal-event training weights keep every fixture's total mass equal.
- CSV SHA256: `0b8eb22c767d16e07b84b59eaa73aeff5ca55b11a220f4939dbb2ae2aaa9d778`.
- The first18554bytes are the original median20 CSV, SHA256 `be9aab4721e69661b8f14d3e1e8938abde569dabd6f7878e0986868fc0756549`.
- Dataset manifest SHA256: `426bcceedb871adf1044160c13cfc956e83008bb6f201f3e80c2c75519cc7ae4`.
- Final validation receipt SHA256: `63238c38aa64f47c5a15de32e2a82e7813b687872f6376d06fcdb1e783da953f`.
- Sources SHA256 and canonical catalog SHA256 are pinned in the implementation before fit. Revalidate canonical independence, six source/prior/snapshot/time identities and original-runtime numerical parity without computing candidate attendance MAE.
- Label knowledge cutoff:2026-11-04T18:45:48.637107Z. Preserve that actual source history, the original CSV bytes and documented reconstruction/publication-time limitations. The new six feature rows are historical frozen-feature reconstructions, not original private feature dumps. No old prior is regenerated with newly obtained history.
- Source count, identities/order, target bounds, exact feature schema, explicit time zones and label availability must validate. Raw data stay outside Git. A mismatch stops this experiment instead of causing a revised fitting frame.

## Fixed estimator and representation

Use exactly the frozen median20's fitted imputer/indicator/scaler, without refitting, adding features or changing missingness. Reuse all 30 original features in their exact order. Read the CSV with the same pandas parsing convention used for median20. Fit one new head:

`QuantileRegressor(quantile=0.5, alpha=0.1, solver='highs', fit_intercept=True)`.

Target is `actual_attendance` directly in persons. Weights use the original equal-event rule, normalized to mean1; no capacity weighting. Reuse the exact inference-only direct-person runtime, overriding package/model/training identities only. Predictions are already in persons; clip to[0,stadium_capacity], with no capacity multiplication. Apply the unchanged C1v8 expert-selection policy separately to each paired expert.

No hyperparameter search, alternative fit, selection from training errors, scaler update, target transformation, club offset or threshold change. Keep a sparse/zero coefficient outcome if it occurs. Record coefficient count only as descriptive metadata. Pinned environment:numpy2.3.5,pandas2.2.3,sklearn1.8.0,joblib1.5.3,scipy1.17.0.

Frozen median20 manifest: `8c59720f0f34f39e3590d35eb002d2050d05383b22d87676a4c680df388d4367`; estimator `96e3b1a86eafd1922eb09f2f0493c054b7eac4e8e017b4b0a9c1e193cdf08c4a`. New fitting must preserve all benchmark artifact/source hashes and this exact preprocessor identity. Publish protocol and tested implementation before fit; use one fresh canonical artifact directory and an exclusive fit-start marker. Load-back finite/bounds checks only; no training MAE. Hash precommit, implementation, data and lineage, old dependencies, new estimator and manifest. Inference never fits.

## New immutable prospective stream

Independently capture **median26, median20, Ridge20, original C1v8 and shared prior** at the same source observation and exact resolved T-1 anchor. Preserve raw and governed outputs. Require current collector request within15minutes, genuine final24 eligibility, explicit timestamps, exact prior/snapshot/PIT identity, at most one representative per6-hour bucket, prior genuinely available before each representative and latest source at/after this freeze and at most2hours old. Exclude all26training IDs and any target whose outcome is already known. Preserve older genuine context, never reconstruct missed issues.

Store actual issue/source times, complete input hashes, source snapshot ID, every package/artifact identity and raw/policy decisions outside Git in a new marked runtime. Retry preserves original issue bytes or rejects conflict. Keep exact input envelopes for replay validation. A failed candidate remains failed coverage; don't silently drop it from accounting. Private recovery namespace: `c1-support26-v1/`, with verified read-back, decompression and individual file checksums. A runtime/source lock prevents changes under this version. Do not write old DB forecasts/scores or other experiment namespaces.

Collect with an explicit host-dependent deadline of at most72hours. This is bounded inference/scoring, not permanent autonomous coding or managed deployment. A successful no-due cycle establishes operational health, not a forecast/DB/accuracy result.

## Future scoring, first review and decision

Only genuine confirmed attendance first known after immutable issue may score. Require consistent canonical fixture/club/kickoff and label provenance, source snapshot/manifest/package identities, correct paired decision values and source hash. Preserve immutable score rows and the first completed review; reject revisions/conflicts. Inventory is never an attendance label.

Primary support question: raw median26 versus raw median20. Separately report governed median26 versus **all four** governed median20, governed Ridge20, governed original C1v8 and shared prior. A raw-only gain cannot support a lower governed-C1 MAE claim. Every comparison uses exactly the same captured/scored events and times, with latest-per-event selected only by actual source time; also report event-balanced window errors and horizon/club diagnostics. Multiple prefixes are not independent events.

First fixed review: at least30new scored independent canonical fixtures and8clubs, none in the26training events. Before this, results are descriptive; no retuning, favorable early stop or promotion. Include every scored fixture then available. Bootstrap paired **event** absolute-error differences with10000resamples,seed42,95%intervals. Support requires mean DeltaAE<0 and upper interval endpoint<0 for the raw median26-versus-median20 comparison. The separate product gate requires the same paired rule against all four declared product benchmarks. No choosing a favorable benchmark after outcomes. Report latest/window MAE, signed bias, median DeltaAE, improvement rate, P90/worst errors/degradation, horizon groups, clubs, source/label/failure coverage and uncertainty.

The review size is not a precision guarantee. MAE1200remains a research goal; no automatic promotion or production activation. If unsupported, retain/reject this version honestly; no new alpha/lookback/club subset rescue. A verified contract defect may stop collection while preserving all evidence; a substantive repair requires a new version before future use. Existing550-seat/P9/encoder/Form5 gates remain unchanged.

`production_change=false`, `live_adjustment=0`.
