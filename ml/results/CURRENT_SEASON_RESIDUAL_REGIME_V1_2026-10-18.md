# Current-Season Residual Regime v1 — Result 2026-10-18

Status: **COMPLETED / B2 HISTORICAL CHALLENGER EVIDENCE / T-3 & T-1 MATERIAL LEADS / NO PRODUCTION CHANGE**

Workstream:

**b2 — Current-season regime**

## Evidence source

GitHub Actions run: `39161525672`  
Tested head: `9b418479fc4c0c78a2034d1bd5c31b9b0ba74023`  
Artifact: `current-season-residual-regime-v1-39161525672`  
Artifact ID: `12149111168`  
Artifact ZIP SHA256: `2296ed2c1e7c4594a3e94a8059c7789a3d15c20df2878c68b45292029dd63e90`  
Result JSON SHA256: `a2cda5a6a47afb974df3a3c7e9c337cd14f57504c7829c0280d40ced5868f85b`

CI:

- pinned runtime: PASS;
- compile: PASS;
- unit tests: **6/6 PASS**;
- same-match leakage test: PASS;
- uncompleted-prior-match leakage test: PASS;
- frozen historical input SHA: PASS;
- canonical base-model reproduction: PASS;
- exact frozen T-7 candidate reproduction: PASS;
- full scoring: PASS;
- artifact upload: PASS.

`promotion_allowed = false`

Production remains unchanged.

## Why this experiment is different from Current Season Adjustment v1

The old v1 used:

`current raw attendance level - historical attendance norm`

This experiment instead uses:

`actual attendance - our own Pre-Live prediction`

from earlier completed same-season home matches.

It therefore asks whether the **current season is systematically beating or missing the model's own expectation**, after the model's existing current-season features have already been applied.

## PIT rule

A previous match may enter regime state only after:

`previous kickoff_at + 3 hours <= current as_of_at`

This is critical for T-30 / T-14 and prevents a forecast from using the outcome of a nominally earlier fixture that had not completed yet.

## Candidate contract

Signals:

- mean capacity-normalized residual;
- EWMA(0.50) capacity-normalized residual;
- mean actual/expected ratio.

Shrinkage:

`n / (n + k)` with `k = 2 / 4 / 6`.

Safety:

- residual fraction clip: +/-25pp capacity;
- demand ratio clip: +/-50%;
- final correction cap: +/-5% capacity;
- first earlier completed home match may activate a signal, but shrinkage is strong at low n.

Total:

- 9 non-zero candidates;
- `NO_ADJUSTMENT` fallback.

## Selection protocol

Development-only rolling folds:

1. train 2021/22 -> evaluate 2022/23;
2. train through 2022/23 -> evaluate 2023/24.

A candidate must:

- improve MAE in both development folds;
- achieve at least 0.5% mean relative MAE improvement.

Among candidates retaining >=90% of best mean development gain, selection minimizes worst-event degradation before p90 / event-improvement tie breaks.

Only after selection is frozen are 2024/25 and 2025/26 scored.

References do not select or rescue candidates.

## Base model state

- T-30: retained Structural Prior incumbent;
- T-14: retained Structural Prior incumbent;
- T-7: frozen historical candidate `hist31-leaf20-l2-1`;
- T-3: retained Structural Prior incumbent;
- T-1: retained Structural Prior incumbent.

## Result summary

| Horizon | Selected | Dev Fold A | Dev Fold B | Ref 2024/25 | Ref 2025/26 | Mean ref improvement | Interpretation |
|---|---|---:|---:|---:|---:|---:|---|
| T-30 | `NO_ADJUSTMENT` | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | no stable residual regime |
| T-14 | `NO_ADJUSTMENT` | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | no stable residual regime |
| T-7 | `ewma50-resid-k6-cap05` | **+80.21** | **+75.33** | -3.89 | +33.69 | **+14.90** | strong dev, mixed references |
| T-3 | `ewma50-resid-k2-cap05` | **+65.63** | **+120.91** | **+31.46** | **+32.86** | **+32.16** | positive dev + both references |
| T-1 | `ewma50-resid-k6-cap05` | **+106.90** | **+81.22** | **+18.80** | **+51.51** | **+35.15** | positive dev + both references |

## T-7

Selected:

`ewma50-resid-k6-cap05`

Mean reference base MAE:

`1712.38`

Mean reference adjusted MAE:

`1697.48`

Mean improvement:

**+14.90 MAE**.

But references disagree:

- 2024/25: **-3.89**;
- 2025/26: **+33.69**.

Decision:

> **Do not freeze T-7 b2 v1 as a stable current-season layer. Keep as research evidence.**

The historical T-7 base `hist31-leaf20-l2-1` remains unchanged.

## T-3

Selected:

`ewma50-resid-k2-cap05`

Reference result:

- 2024/25: `1661.72 -> 1630.26`, improvement **+31.46**;
- 2025/26: `1775.07 -> 1742.20`, improvement **+32.86**.

Mean reference improvement:

**+32.16 MAE**.

Supporting reference diagnostics:

2024/25:

- median AE improves by **131.06**;
- p90 AE improves by **44.51**;
- worst single-event degradation: **+2141.85**;
- event improvement rate: 49.0%.

2025/26:

- median AE improves by **53.94**;
- p90 AE worsens by **163.49**;
- worst single-event degradation: **+2141.85**;
- event improvement rate: 48.8%.

Decision:

> **Material b2 historical lead. Advance to signal-maturity / activation robustness before freezing.**

## T-1

Selected:

`ewma50-resid-k6-cap05`

Reference result:

- 2024/25: `1651.73 -> 1632.94`, improvement **+18.80**;
- 2025/26: `1742.84 -> 1691.32`, improvement **+51.51**.

Mean reference improvement:

**+35.15 MAE**.

2025/26 median and p90 both improve materially. 2024/25 mean MAE improves but median/p90 are not uniformly better.

Worst single-event degradation remains **+2141.85**.

Decision:

> **Material b2 historical lead. Advance to signal-maturity / activation robustness before freezing.**

## Signal maturity — key finding

The selected b2 signal is not equally useful at every sample size.

### Development evidence — T-3

2022/23:

- 1 prior home match: **-281.94 MAE**;
- 2 prior: **-100.22**;
- 3+ prior: **+109.27**.

2023/24:

- 1 prior: **+185.66**;
- 2 prior: **-184.36**;
- 3+ prior: **+147.69**.

### Development evidence — T-1

2022/23:

- 1 prior: **-147.42**;
- 2 prior: **-64.29**;
- 3+ prior: **+146.34**.

2023/24:

- 1 prior: **+64.77**;
- 2 prior: **-158.21**;
- 3+ prior: **+106.19**.

### Development evidence — T-7

The same pattern is weaker but visible:

- 2022/23: 1 prior **-234.68**, 2 prior +22.71, 3+ prior **+114.30**;
- 2023/24: 1 prior +9.83, 2 prior +62.53, 3+ prior **+86.86**.

This finding exists already in development folds and therefore justifies the next robustness hypothesis independently of reference behavior.

## Reference maturity context

Reference seasons reinforce the same concern: regime correction is generally strongest with mature same-season state and can be unstable with only one or two prior home matches.

For example, T-3 2024/25:

- 1 prior: -274.81;
- 2 prior: -26.11;
- 3+ prior: **+61.39**.

T-3 2025/26:

- 1 prior: +60.38;
- 2 prior: +136.34;
- 3+ prior: +25.77.

These exposed references are diagnostic only and must not choose the next threshold.

## Next step

Run **b2 Stage 2 — signal-maturity activation robustness**.

Keep each v1-selected source/k fixed and test only activation maturity:

- activate after 1 prior completed same-season home match;
- activate after 2;
- activate after 3.

Selection must remain development-only on 2022/23 + 2023/24.

The next experiment should answer:

> Can we preserve T-3/T-1 MAE uplift while avoiding low-sample regime corrections that are visibly unstable in development?

T-30/T-14 do not advance to Stage 2 because no b2 v1 candidate passed development.

T-7 may be included as a research robustness comparator, but mixed reference evidence means it must not be treated as frozen b2 candidate without materially stronger evidence.

## Decision

- T-30: retain no b2 adjustment;
- T-14: retain no b2 adjustment;
- T-7: research-only current-season regime signal;
- T-3: advance selected EWMA residual regime to Stage 2 maturity gating;
- T-1: advance selected EWMA residual regime to Stage 2 maturity gating;
- no production change;
- do not advance to c2 until Stage 2 resolves the b2 maturity question.
