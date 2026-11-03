# MAE-01 — reproduced incumbent error map

Date: 2026-11-03. Protocol: `MAE01_INCUMBENT_ERROR_AUDIT_PROTOCOL_V1.md`. Reproducible runner: `python -m ml.mae01_incumbent_error_audit_v1 --output /tmp/mae01-new-directory`.

## Evidence

All ten frozen horizon/season MAEs reproduce. Historical data and all five frozen serving-artifact hashes pass before and after analysis. No artifact is replaced. The report contains603independent events /3,010horizon rows from2024/25–2025/26;599events have all five horizons. The input contains612candidate fixtures; existing history/eligibility/baseline gates are retained.

Available-cohort equal-event MAE: **1,773.89people**. Signed bias:+14.59; median event AE:1,129.28; P90:4,195.79. Common-five-horizon MAE:1,784.64. These are diagnostic replays of previously exposed historical seasons, **not a new prospective result or a reduction from the separate10-event trajectory cohort's2,594.54MAE**.

Machine-readable tables, per-event predictions, hashes and generated report: `artifacts/mae01_incumbent_error_audit_v1/`. Output columns are historical public-match metadata and diagnostic forecasts, with no private current source export.

## Where the error is concentrated

| Club | Independent events | Mean event AE | Contribution to overall MAE | Share of all error |
|---|---:|---:|---:|---:|
| Lech |34|5,477.45|308.84|17.41%|
| Lechia Gdańsk |34|3,149.96|177.61|10.01%|
| Górnik Zabrze |34|2,660.65|150.02|8.46%|
| Śląsk Wrocław |17|4,841.01|136.48|7.69%|

These four clubs account for43.57%of error on19.73%of events. Lech remains high-error in both seasons:5,430.50and5,524.40MAE. Its signed bias changes from−64.44to−1,940.78, so a constant club offset is not justified by this decomposition.

On the same599events, MAE changes from1,867.64atT-30 to1,707.34atT-1: a160.30-seat descriptive reduction. This does not show that shortening the horizon or adding more sequence layers will remove the main error.

Actual fill below50%has+1,573.19signed bias; actual fill85–95%has−996.17. **These are outcome-conditioned descriptions**, not a usable inference rule. At inference, PIT baseline/context may proxy regimes; actual future fill cannot. Seven events exceed the old capacity map and need source review; their contribution is only0.21%of total error, so capacity anomalies alone do not explain the result.

The largest miss is Lechia–Arka on2025-08-24:37,500observed attendance vs11,329–13,644predictions, mean AE25,101.72. The error persists across all horizons. A derby/context mismatch is a hypothesis for investigation, not a proven causal diagnosis; historical booking curves, source defects and event-specific shocks were not assessed.

## Decision and next hypothesis

**MAE-01 historical diagnostic deliverable complete**, subject to hosted reproducibility checks. No challenger was selected, no prospective gates opened, no production change.

Proceed to a restrained **MAE-02 structural objective audit**. The incumbent learns residual occupancy; an absolute occupancy error contributes fewer objective units for a large stadium even when it corresponds to many more seats. Test whether aligning a separately versioned median learner's training weights with raw-seat absolute error helps the persistent high-seat-error clubs. Use fixed historical development splits; label exposed-season regression checks as exposed and require new future evidence before promotion. Start with the existing absolute-lossT-3/T-1 specification so weighting can be isolated without a model tournament. Also retain the current structural anchor and simple existing PIT summaries as benchmarks. Do not change serving weights or frozen models.

`production_change=false`, `live_adjustment=0`.
