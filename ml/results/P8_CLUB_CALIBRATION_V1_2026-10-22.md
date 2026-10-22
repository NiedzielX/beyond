# P8 Club Calibration / Shrinkage v1 — 2026-10-22

## Question

> Does a conservative, strictly forward home-club residual calibration lower incumbent Structural Prior MAE in a stable and statistically defensible way?

## Immutable input

Source: MAE-native global tournament artifact `12378567266`.

- artifact digest: `sha256:5b9bd145124c8ee98b5fddf4849e37a2337ef66a475339a5a00b57fe76528ab1`;
- `predictions.csv` SHA256: `827bebabf14fe3640361e79259893ebc25621b15b97d6eac97a24f9de043674d`;
- incumbent OOS rows: `4491`;
- seasons: `2023/24`, `2024/25`, `2025/26`;
- horizons: T-30/T-14/T-7/T-3/T-1.

## Policy

Primary candidate:

- rolling **home-club median signed-error** correction;
- correction uses only residuals from earlier kickoff timestamps;
- tied kickoff fixtures cannot train each other;
- shrinkage weight: `n / (n + 80)`;
- no future label or future-season access.

Secondary diagnostic uses the same policy keyed by away opponent.

The strong `k=80` shrinkage is intentional: P8 should only advance if a stable club effect survives conservative partial pooling.

## Primary result — home-club calibration

| Horizon | Incumbent MAE | Calibrated MAE | ΔMAE | Relative | 95% paired bootstrap | P(Δ<0) | Season wins |
|---|---:|---:|---:|---:|---:|---:|---:|
| T-30 | 2094.98 | 2086.93 | -8.05 | -0.38% | [-20.47, +4.45] | 0.888 | 2/3 |
| T-14 | 1984.98 | 1977.95 | -7.03 | -0.35% | [-16.49, +2.35] | 0.928 | 2/3 |
| T-7 | 2016.68 | 2011.63 | -5.05 | -0.25% | [-17.12, +7.00] | 0.791 | 2/3 |
| T-3 | 1914.35 | 1911.45 | -2.90 | -0.15% | [-10.84, +4.84] | 0.755 | 1/3 |
| T-1 | 1912.17 | 1908.48 | -3.69 | -0.19% | [-11.43, +4.18] | 0.825 | 2/3 |

No horizon has a 95% interval fully below zero.

The effect is also not broad across clubs:

- home-club improvement rate is about `45.8%` at T-30/T-14/T-3/T-1;
- T-7 is `54.2%`.

So the aggregate point gain is not driven by a generally improving club calibration rule.

## Season stability

Even the strongest point estimates degrade one future season.

Examples:

- T-30: `-14.13`, `-18.05`, then `+7.69` seats by season;
- T-14: `-5.72`, `+3.11`, `-18.32`;
- T-1: `-8.97`, `-5.59`, `+3.36`.

T-3 wins only one of three seasons.

This is consistent with the earlier diagnostic that per-club signed-error bias is not strongly persistent from season to season.

## Secondary away-opponent diagnostic

The away-opponent residual correction is weaker:

- T-30 ΔMAE `-1.98`;
- T-14 `+0.81`;
- T-7 `-4.13`;
- T-3 `-2.34`;
- T-1 `-0.65`.

All 95% intervals cross zero. It does not justify a separate opponent calibration layer.

## Decision

**RETAIN INCUMBENT — NO ROBUST CLUB CALIBRATION GAIN.**

P8 is closed for this simple residual-shrinkage family.

The observed home-club point improvements are only about `0.15–0.38%`, are not broad across clubs, are not consistently positive by season, and are uncertainty-limited.

Do not add a club-specific post-hoc calibration layer to the Structural Prior runtime from this evidence.

A future P8 reopening requires materially new evidence, such as:

- more genuinely forward seasons;
- a hierarchical model with a new predictive mechanism rather than post-hoc residual correction;
- demonstrable cross-club generalization.

## Production boundary

- Structural Prior runtime unchanged;
- frozen packages unchanged;
- no calibration deployed;
- `live_adjustment = 0`.
