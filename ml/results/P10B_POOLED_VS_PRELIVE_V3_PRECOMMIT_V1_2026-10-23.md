# P10b — Pooled Horizon vs Frozen Pre-Live v3 — Precommit v1

Date: **2026-10-23**

Status: **PRECOMMITTED / REAL HISTORICAL RESULT NOT OPENED IN THIS PR**

Production:

`live_adjustment = 0`

## Research question

> Does the pooled cross-horizon learning architecture already frozen in P10 v1 beat Beyond's strongest reproducible structural/pre-live research anchor under a common match-blocked temporal protocol?

This is a new experiment after the P10 v1 result was observed. P10 v1 remains immutable.

## Why the comparator is Pre-Live v3

Older v2.2/v2.3 reports contain useful historical challenger evidence, but the strongest current **sealed and reproducible** structural research anchor is:

`pre-live-v3-historical-candidate-2026-10-21-v1`

Its exact implementation, manifest and fixed-temporal audit are committed in the repository.

Frozen v3 horizon contract:

- T-30: exact Pre-Live v3 T-30 contract;
- T-14: exact Frozen Pre-Live v2 T-14 contract retained by v3;
- T-7: exact Pre-Live v3 T-7 contract, including its frozen same-season regime rule;
- T-3: exact Frozen Pre-Live v2 T-3 contract retained by v3;
- T-1: exact Frozen Pre-Live v2 T-1 contract retained by v3.

P10b imports these functions directly. It does not recreate them from prose or headline MAE values.

The sealed comparator manifest is also pinned:

`b8c1a3cb1ddb70e9f6b67a6bc1db23619f26a8c328bf4b78399fc262394ff70a`

Before any P10b result is interpreted, all **20 horizon × season Pre-Live v3 MAE cells** must reproduce the sealed manifest within absolute tolerance `1e-9`. Comparator drift fails closed.

## Challenger

ID:

`p10-v1-pooled-hgb-residual-baseline-season`

The challenger deliberately reuses the fixed P10 v1 architecture without tuning after the P10 v1 result:

- one HGB residual model across all five horizons;
- fixed P10 v1 HGB hyperparameters;
- `horizon_days` as an input;
- residual target = `target_attendance - baseline_season`;
- equal total training weight per match;
- no candidate/model/hyperparameter sweep;
- no horizon-specific challenger hand-picking.

## Data

Canonical frozen history:

- 1,530 matches;
- five complete seasons;
- 7,650 PIT rows;
- SHA256 `3c6b35142c6bd20a484f2aa758cd41284fd6f4c6db1353b138f81cf321161569`.

Historical seasons are exposed R&D evidence, not a new unseen holdout.

## Common temporal protocol

Independent unit:

`match_key`

All horizon rows for one match remain on the same side of every fold.

P10b uses the exact four expanding-season cells of the frozen Pre-Live v3 audit:

1. train 2021/22 -> test 2022/23;
2. train 2021/22–2022/23 -> test 2023/24;
3. train 2021/22–2023/24 -> test 2024/25;
4. train 2021/22–2024/25 -> test 2025/26.

The canonical temporal helper must reproduce those four cells exactly or P10b fails closed.

## Exact common-support rule

Pre-Live v3 is horizon-specific and some early-season PIT rows are intentionally not forecastable under its frozen contracts. P10b must therefore **not** fabricate comparator predictions or force equal raw row counts.

Headline scoring uses the exact intersection where:

1. frozen Pre-Live v3 emits a valid prediction;
2. the pooled challenger has a prediction for the same `match_key + horizon`;
3. target attendance is identical on both sides.

Every comparator row must resolve to exactly one challenger row. Any challenger-only row is reported and excluded from the headline comparison rather than being used to advantage the pooled model.

This preserves the frozen comparator's real forecastability semantics.

## Primary score

Overall match-balanced MAE across the four forward folds on exact Pre-Live v3 common support:

`pooled challenger vs frozen Pre-Live v3`

Secondary diagnostics:

- per-horizon MAE;
- per-fold MAE;
- common-support row/match counts;
- challenger-only rows excluded;
- match/event improvement rate;
- fold improvement rate;
- paired match-block `Delta MAE` uncertainty;
- 5,000 bootstrap draws;
- seed 42.

## Governance v2

Interpretation uses:

`ml/research_advance_governance_v2.py`

Possible states:

- `NO_RESEARCH_GAIN`;
- `POINT_GAIN_UNCERTAINTY_LIMITED`;
- `ROBUST_RESEARCH_ADVANCE`.

No business-derived minimum meaningful MAE threshold exists yet. Therefore this experiment is **not allowed** to emit `ROBUST_RESEARCH_ADVANCE`, even if the point gain and confidence interval are favorable.

## Freeze-before-result execution rule

Pull request behavior:

1. compile code;
2. run synthetic protocol/leakage tests;
3. verify production remains unchanged;
4. **do not execute the real 1,530-match comparison**.

Only after the precommit is merged to `main` may CI execute the real historical comparison and upload its immutable scorecard/predictions/fold manifest.

Any change after that result is opened requires a new experiment/version (`P10c` or later). P10b itself becomes frozen.

## Decision semantics

A P10b win would mean:

> the simple cross-horizon pooled architecture contains structural value strong enough to outperform the current sealed horizon-specific Pre-Live v3 package on the exact common forecastable support under a common temporal protocol.

A P10b loss would **not** erase the P10 v1 result. It would mean the current pooled architecture does not yet beat the stronger structural champion suite and should not replace it.

Neither outcome changes production automatically.
