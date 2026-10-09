# Beyond historical demand model lineage

The version number is a research checkpoint identifier, **not a guarantee that a later version supersedes the previous champion**.

## v1.3 — generic historical/context benchmark

- Gradient Boosting historical/context model.
- Still referenced by the current stored live `beyond-forecast-v0.3` observations.
- Useful incumbent/reproducibility baseline, but not the final horizon-specific champion.

## v1.4 — horizon-specific operational redesign

Main architectural change: rebuild features **as of the forecast checkpoint** instead of using sporting state immediately before kickoff.

- T-30 Ridge: MAE 5279.0
- T-7 Ridge: MAE 4370.3
- T-1 Ridge: MAE 4414.2

This established the strict T-30/T-7 architecture.

## v1.5 — error anatomy

No replacement model. Research showed that large forecast errors were concentrated in demand shocks and supported shifting investment toward live ticket/inventory trajectory rather than adding more historical context.

## v1.6.1 — hardened horizon models

Frequency-gated opponent categories reduced sparse-category overfit risk.

- T-30 MAE: 5228.6
- T-7 MAE: 4232.4

The surviving v1.6.1 package contains fitted Ridge joblibs and exact feature contracts and is therefore the main reconstruction control for v1.7 inference.

## v1.7 — frozen historical champion

Accepted strict historical/context baseline.

- T-30 OOS MAE: **4723.8**
- T-7 OOS MAE: **4151.1**

Key changes:

- residual target around current-season attendance level;
- T-30 online same-season residual correction with shrinkage k=3;
- hard stadium capacity cap;
- T-7 residual target + capacity cap, without the unstable online correction.

The original benchmark archive and the later strict-tournament bundle both survive. The original v1.7 package does not contain its training source/model binary, so exact new-fixture inference is still under controlled reconstruction.

## v1.8 — league-wide feature factory research

**v1.8 was not a promoted model. It was a challenger/research package using v1.7 as its baseline.**

### League-wide Elo

Rejected:

- best T-30 overall MAE: 5087.5
- best T-7 overall MAE: 4364.6

Both were worse than v1.7.

### Prior-season opponent home-attendance popularity

Promising T-30 challenger:

- candidate: `T30_pop_ratio_missing_a0.3`
- overall MAE: **4568.2** vs v1.7 4723.8
- development MAE: **4578.5** vs v1.7 4571.3 (slightly worse)
- holdout improvement existed, but most of the gain was concentrated in 2025/26
- fresh 2026/27 two-match check was mixed
- decision: **research only, not promoted**

T-7 popularity and blend/stage-switch variants were rejected.

### v1.8 conclusion

The package explicitly says:

- frozen baseline remains v1.7;
- historical/context feature engineering is near diminishing returns;
- primary next signal should be kickoff-anchored live ticket inventory trajectory.

## Current Beyond policy

We therefore keep two distinct concepts:

1. **Champion** — the last model that passed the promotion decision: v1.7.
2. **Challengers** — newer research such as the v1.8 T-30 popularity signal, CatBoost, future LightGBM/Chronos/global models.

A challenger replaces the champion only after the same no-leakage protocol shows robust improvement, not because its version number is higher.

## Current runtime reality

The live production/shadow pipeline still uses the stored v1.3-derived historical forecast because executable v1.7 inference has not yet been reproduced exactly. This is a migration gap, not a statement that v1.3 is better than v1.7.

Next historical-model work:

1. finish exact v1.7 runtime reconstruction;
2. run v1.7 as shadow historical champion;
3. keep the v1.8 T-30 popularity feature as an explicit challenger;
4. evaluate both against genuinely future matches;
5. promote only if the challenger passes the promotion gate.
