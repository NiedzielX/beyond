# MAE-02 raw-seat objective weighting — precommit v1

Recorded 2026-11-03 **before the first weighted fit**. Experiment: `structural-seat-weighted-median-v1`. Authority: Roadmap v6 MAE-02, derived from `MAE01_INCUMBENT_ERROR_AUDIT_RESULT_V1.md`.

## Hypothesis and fixed mechanism

Lech remains high-seat-error in both exposed historical seasons. This does not establish a cause or support a constant bias offset. Test one specific mechanism: equal normalized-occupancy loss underweights the same absolute seat error at larger stadiums relative to the product's raw-seat MAE objective.

For T-3 and T-1 only, clone the existing frozen-spec absolute-loss HistGradientBoosting learner and its training-only fitted preprocessor. Keep the exact features, target `(attendance - PIT baseline) / capacity`, estimator parameters, seeds, training eligibility and `[0, capacity]` decode unchanged. Fit a separate temporary estimator with `sample_weight = capacity / mean_training_capacity`. One event per horizon receives one training row. No new model family, alpha, cap, feature, capacity-map or weight variant may be selected after results.

Before prediction clipping, capacity times absolute occupancy-residual error equals absolute raw-seat error; mean normalization preserves the existing overall sample-weight scale. This is a hypothesis about objective alignment, not a guarantee of lower generalization error. Old retrospective capacity-map/publication-time limitations remain.

## Evaluation and stop rule

1. Verify the frozen historical input, serving-artifact hashes and canonical PIT feature quality.
2. Train temporary unweighted incumbent copies on2021/22–2022/23; evaluate2023/24. Verify both incumbent MAEs against their existing frozen development values. Training labels must be available before the earliest evaluated cutoff; event sets must be disjoint.
3. Fit exactly one weighted copy per horizon on that same training data; compare paired errors on the same eligible events. Report per-horizon and equal-event-across-two-horizons MAE, bias, median/P90, improvement rate, median Delta AE and worst-event degradation. Show club contributions and fixed simple PIT anchor comparisons with coverage. No actual target-derived feature may enter fitting/inference.
4. **DEVELOPMENT_SUPPORTED** requires negative Delta MAE and nonpositive Delta P90 event AE **at both horizons**. Otherwise **REJECT_FOR_PROSPECTIVE** and stop: no old-holdout weighted fits, no post-result v1 edits or search for another weighting variant.
5. Only if the development gate passes, reproduce the two existing exposed historical season splits2024/25 and2025/26 for a descriptive regression check. Neither development nor those exposed seasons is fresh confirmatory evidence. Report all results, never pick a winning horizon after evaluation. No serving artifact is written by this diagnostic.

Passing the development gate is not promotion: an independent future precommit/freeze, immutable predictions and genuine outcomes are still required. The frozen550-seat attendance business contract is not changed or claimed satisfied. Keep existing prospective lanes and daily-path v1 untouched.

`production_change=false`, `live_adjustment=0`, no new serving artifact, no automatic deployment.
