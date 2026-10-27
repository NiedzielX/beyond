# Hype / Attention research status — 2026-10-27

## Decision

Do not promote or tune Hype/Attention into production P50.

The current prospective T-24 `hype.media_attention` signal is not testable because it is constant across the completed eligible sample. A single pre-specified 48-hour attention-window hypothesis was also tested and rejected because it worsened the true baseline MAE.

Production impact remains **none**. `live_adjustment` remains **0**.

## Current prospective 24h feature

Source: `GDELT Web News NGrams v2 broad event-team attention`.

Current completed prospective T-24 sample:

- 10 completed eligible events,
- 10 home clubs,
- `hype.media_attention` distinct values: **1**,
- all 10 frozen T-24 values are **0**,
- therefore the existing leakage-safe LOEO/LOCO view correctly emits no `media_attention` CV rows because training-fold `x_sd = 0`.

This is **not** a snapshot timing bug:

- T-24 snapshots were captured at their exact checkpoint,
- snapshot immutability is preserved,
- historical Hype observations must not be backfilled.

Positive GDELT samples exist for some events, but for the completed sample they were outside the current 24-hour attention window at the exact T-24 checkpoint. The zero feature values are therefore consistent with the current feature definition.

## Mention acceleration

`hype.mention_acceleration` has non-constant values, but the current eligible sample is still below the evaluation gate:

- 4 completed eligible events,
- 4 clubs,
- 3 distinct values,
- required gate: at least 8 completed events, 5 clubs and >=2 distinct values.

Continue forward-only collection. Do not lower the gate to manufacture a result.

## One 48-hour attention hypothesis

Rationale: the 24-hour signal is too sparse, while genuinely PIT-acquired GDELT samples showed some event-team mentions in the preceding comparison window.

To avoid window-shopping, only one alternative was tested:

- feature: sum of `union_mentions_pl` in `[T-72h, T-24h]` represented as the 48 hours immediately preceding the exact T-24 checkpoint,
- every included sample required `sample_at <= cutoff`, `source_file_timestamp <= cutoff` and `created_at <= cutoff`,
- comparator: immutable `baseline` prediction for the same T-24 snapshot, **not** the now-rejected Ticketing challenger,
- fixed ridge alpha: 30,
- correction cap: +/-25%,
- fold rules matched the existing Hype CV design.

Sample:

- 10 events,
- 10 clubs,
- only 2/10 held-out events had non-zero 48h attention,
- because every event currently comes from a different home club, LOEO and LOCO are the same split and are **not independent confirmations**.

Result:

| Metric | Value |
|---|---:|
| True baseline MAE | 4,156.0 |
| Bias-control MAE | 4,565.9 |
| 48h Hype challenger MAE | 4,225.4 |
| Challenger improvement vs baseline | **-69.4** |
| Incremental improvement vs bias control | +340.5 |

Interpretation:

- the 48h Hype challenger is **69.4 MAE worse than the true baseline**,
- improving over a deliberately weaker bias-only control is not sufficient,
- only 2 non-zero events make the signal structurally fragile even before considering the negative North-Star result.

Decision: **REJECTED_NO_UPLIFT**.

## Next action

1. Keep the current 24h Hype collector forward-only.
2. Wait until `mention_acceleration` reaches the fixed 8-event / 5-club / non-constant-value gate.
3. Do not backfill historical observations or rewrite immutable T-24 snapshots.
4. Do not search additional attention windows on the same outcomes. More window search would turn this into post-outcome tuning.
5. Prioritize prospective P9/P7 scoring and genuinely new, precommitted feature hypotheses over further Hype tuning.
