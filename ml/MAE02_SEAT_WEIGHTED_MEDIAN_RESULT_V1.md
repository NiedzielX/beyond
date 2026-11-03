# MAE-02 — raw-seat weighting rejected

Date:2026-11-03. Experiment:`structural-seat-weighted-median-v1`. Precommit:`MAE02_SEAT_WEIGHTED_MEDIAN_PRECOMMIT_V1.md`. Runner:`python -m ml.mae02_seat_weighted_median_v1 --output /tmp/mae02-new-directory`.

## Result

Train2021/22–2022/23; development2023/24.297independent events /594paired horizon rows. Incumbent development metrics reproduce exactly; the only learner change is normalized capacity sample weighting. Frozen files and incumbent predictions remain unchanged.

| Horizon | Incumbent MAE | Weighted MAE | Delta MAE | Delta P90 AE | Event improvement rate |
|---|---:|---:|---:|---:|---:|
|T-3|2,311.62|2,466.63|+155.01|+152.01|41.08%|
|T-1|2,347.99|2,452.74|+104.75|−43.36|41.75%|

Equal-event mean across both horizons:2,329.81→2,459.68; **Delta+129.88people**, P90Delta+246.20. Median event Delta AE:+12.95; worst event degradation:+4,974.83. Signed bias changes from−183.43to+265.61.

Decision: **REJECT_FOR_PROSPECTIVE**. Both-horizon MAE/P90 development gate fails. **No weighted fits on2024/25 or2025/26 were performed.** No new weights, caps or per-club fallback variants were tried. Lech improves on this development sample, but aggregate harm cannot be rescued by selecting that club after seeing results.

All four fixed simple PIT anchors have100%coverage here and worse MAE than the incumbent:

| Anchor |T-3 MAE|T-1 MAE|
|---|---:|---:|
|Season/history mean|2,852.10|2,853.97|
|Rolling-three home mean|2,906.98|2,917.64|
|Last home attendance|3,307.82|3,305.37|
|Long-run home median|3,849.82|3,851.49|

Machine results and per-event pairs:`artifacts/mae02_seat_weighted_median_v1/`. Development is previously exposed historical evidence, not a new independent test or prospective result.

## Existing research anchor must not be forgotten

The serving Structural Prior is not the only historical research benchmark already in the repository. The existing **Pre-Live v3 historical research freeze** contains a stronger fixed mixed-horizon package:

- manifest:`artifacts/pre_live_v3_historical_candidate_v1/manifest.json`, SHA`b8c1a3cb1ddb70e9f6b67a6bc1db23619f26a8c328bf4b78399fc262394ff70a`;
- recorded successful seal run39633561065; result:`results/PRE_LIVE_V3_HISTORICAL_FREEZE_V1_2026-10-21.md`;
- recorded reference mean MAEs:T-30 1,825.49;T-14 1,809.45;T-7 1,670.60;T-3 1,682.63;T-1 1,661.52.

Those figures are preserved recorded historical results, not newly replayed prospective evidence or a new event-level comparison in this audit. Keep that frozen research anchor available to future benchmarks; do not silently replace the active prospective incumbent or treat the source manifest as current inference executed successfully.

## Context experiments already closed

`results/CONTEXT_EXTENSION_V2_2026-10-18.md` already tests sporting streaks, points acceleration and continuous match stakes against the frozen A2+B2 stack. No stable incremental uplift was accepted; the T-1 selected family failed both exposed reference seasons. Do not repeat this tournament as a newly named MAE-03 experiment.

Weather was historically negative; rivalry/absences/media collection is forward-only or incomplete for historical PIT replay. Next useful step: inventory genuinely new timestamped fixture/market/price context, its paired outcome coverage and collector health. Then precommit one small residual challenger against the appropriate available anchor. Missing outcomes or timestamp evidence block fitting; they do not justify fabricated history or a new sequence-model search.

`production_change=false`, `live_adjustment=0`.
