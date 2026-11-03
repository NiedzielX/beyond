# MAE-01 incumbent error decomposition v1

Recorded 2026-11-03 before running this decomposition. Roadmap v6 authorizes this diagnostic; it does not authorize changing the frozen incumbent.

## Evidence and boundaries

- Input: SHA-verified `artifacts/structural_prior_runtime_v1/historical_runtime_v1.csv.gz` and its frozen manifest; 1,530 canonical historical fixtures.
- Rebuild the existing PIT feature contract without adding diagnostic columns to model inputs.
- Reproduce the **existing**, already exposed season splits: train 2021/22–2023/24 → evaluate 2024/25; train 2021/22–2024/25 → evaluate 2025/26. Use all five fixed horizon specifications exactly as recorded in the incumbent manifest.
- These are historical diagnostic replays, **not new independent holdouts or immutable prospective forecasts**. Within-season earlier completed outcomes enter PIT history exactly as in the original benchmark. Archived fixture times and capacity maps do not prove what was publicly available at each historical cutoff.
- Fit only temporary in-memory copies needed to reproduce those old splits. Do not write models, overwrite artifacts, select parameters, update production, backfill prospective observations, or fit the frozen daily-path model again.
- Fail if source/artifact hashes, temporal train/test separation, PIT cutoffs, unique event/horizon rows or frozen benchmark MAEs disagree.

## Fixed analysis

Report equal-event MAE, signed bias, overprediction rate, median/P90 event error, and baseline comparison. Report available-row and common-five-horizon cohorts separately; horizons never count as independent events.

Rank clubs, horizon, season, weekday/weekend, calendar/season phase, attendance level, actual utilization, PIT baseline utilization, PIT opponent demand and opponent sporting position. Fixed bins are descriptive, not optimized from residuals. Actual attendance/fill bins are outcome-conditioned descriptions and must never become inference features. Unknown context remains unknown.

Within each dimension, allocate each event's equal total weight across its eligible horizons so segment contributions sum back to overall MAE. Also report conditional segment MAE and effective event weight; a small high-error segment need not be the biggest contribution.

Rank worst events by their mean absolute error across horizons and retain per-horizon signed errors. Tag only reproducible **associations** (persistent signed error, horizon spread, sparse history, high actual fill, capacity inconsistency). Booking-curve dynamics, source defects and unpredictable shocks remain **unassessed** without supporting observations. Do not infer causality from errors alone.

## Exit

A reproducible report, ranked error tables, explicit limitations, and one next evidence-driven research question for MAE-02. No claim of MAE reduction, promotion or prospective validation follows from this diagnostic. `production_change=false`, `live_adjustment=0`.
