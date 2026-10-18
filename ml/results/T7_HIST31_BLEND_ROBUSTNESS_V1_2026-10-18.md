# T-7 Hist31 Blend Robustness v1 — Result 2026-10-18

Status: **COMPLETED / FIXED BLEND DOES NOT SOLVE TAIL / NO PRODUCTION CHANGE**

Workstream:

**a2 — Historical / Structural Prior optimization — T-7 robustness stage 2**

## Evidence source

GitHub Actions run: `39157403710`  
Tested branch head: `a64bb38a7ea14c01dd0f55307c8e9d4b3a75ee3b`  
Artifact: `t7-hist31-blend-robustness-v1-39157403710`  
Artifact ID: `12147596754`  
Artifact ZIP SHA256: `82e437cde3e69918b6724a9e9945305ceb4a5fa90322061e4f569ebfa8b1d875`  
Result JSON SHA256: `170cf7bc10437ca4f0b5bb724e7db7ffab0941600932b7c53544c150007b7703`

CI result:

- compile: PASS;
- unit tests: **6/6 PASS**;
- historical input hash assertion: PASS;
- incumbent benchmark assertions: PASS;
- full experiment: PASS;
- artifact upload: PASS.

Stage-1 dependency:

`PRE_LIVE_BASELINE_OPTIMIZATION_V1_2026-10-18`

Stage-1 result JSON SHA256:

`55ea6ee19309771b54e0b0336ecaa2871de19d95d2bf4360400ff76e4c2ddc79`

## Question

Stage 1 found a material T-7 MAE lead for `model-hist_absolute_31`, but also large single-event regressions.

This experiment tested whether a fixed incumbent/Hist31 blend could keep the MAE improvement while reducing tail risk.

## Frozen protocol

Blend:

`prediction(alpha) = (1-alpha) * incumbent + alpha * Hist31`

Predeclared alpha candidates:

- 0.00;
- 0.25;
- 0.50;
- 0.75;
- 1.00.

Selection:

- train components: 2021/22 + 2022/23;
- select alpha: **2023/24 only**;
- primary metric: MAE;
- exact tie within `1e-9` -> lower alpha / more incumbent.

After alpha selection:

- score 2024/25 with rolling training through 2023/24;
- score 2025/26 with rolling training through 2024/25;
- reference holdouts do not choose alpha.

Evidence class:

`EXPOSED_HISTORICAL_REFERENCE_SEASONS`

`promotion_allowed = false`

## Development result

| Alpha | Interpretation | MAE | Improvement vs incumbent | Median AE | p90 AE | Worst degradation |
|---:|---|---:|---:|---:|---:|---:|
| **1.00** | full Hist31 | **2,379.46** | **+97.36** | **1,206.21** | **5,325.76** | 4,317.24 |
| 0.75 | 75% Hist31 | 2,381.95 | +94.86 | 1,247.30 | 5,345.37 | 3,237.93 |
| 0.50 | 50% Hist31 | 2,400.99 | +75.83 | 1,294.58 | 5,445.47 | 2,158.62 |
| 0.25 | 25% Hist31 | 2,433.51 | +43.30 | 1,400.64 | 5,443.77 | 1,079.31 |
| 0.00 | incumbent | 2,476.82 | 0.00 | 1,288.41 | 5,598.34 | 0.00 |

Development selection is unambiguous:

`selected_alpha = 1.00`

The more Hist31 weight is used, the better development MAE becomes. Fixed blending creates an expected smooth trade-off: lower alpha reduces worst-event degradation but also gives up validated development MAE.

There is no development-MAE basis for selecting a partial blend.

## Frozen selected result on references

Because development selected alpha `1.00`, the frozen selected candidate is full Hist31.

### 2024/25

- incumbent MAE: **1,777.69**;
- selected MAE: **1,672.14**;
- improvement: **+105.55 MAE**;
- worst-event degradation: **+3,685.74**.

Worst event remains:

`Śląsk Wrocław – Raków`, 2024-10-26

- actual: 16,265;
- incumbent prediction: 19,833.43;
- selected prediction: 23,519.18;
- incumbent AE: 3,568.43;
- selected AE: 7,254.18;
- degradation: **+3,685.74**.

Tail reduction vs stage-1 full Hist31:

**0.0**.

### 2025/26

- incumbent MAE: **1,802.28**;
- selected MAE: **1,770.22**;
- improvement: **+32.06 MAE**;
- worst-event degradation: **+4,233.11**.

Worst event remains:

`Lech – Arka Gdynia`, 2026-05-08

- actual: 41,598;
- incumbent prediction: 36,152.69;
- selected prediction: 31,919.58;
- incumbent AE: 5,445.31;
- selected AE: 9,678.42;
- degradation: **+4,233.11**.

Tail reduction vs stage-1 full Hist31:

**0.0**.

## Aggregate result

- mean reference incumbent MAE: **1,789.98**;
- mean selected/full-Hist31 MAE: **1,721.18**;
- mean improvement: **+68.81 MAE**;
- improves both reference seasons: **true**;
- reduces stage-1 worst degradation on both references: **false**.

Automated signal:

`FULL_HIST31_SELECTED_NO_BLEND_ROBUSTNESS_GAIN`

## Decision

1. **Do not change production T-7 champion from this experiment.**
2. Full Hist31 remains the strongest MAE candidate found so far.
3. Fixed unconditional blending does **not** solve the tail problem under the declared MAE-first development protocol.
4. Do not choose alpha 0.25/0.50/0.75 from reference-season behavior; that would be holdout retuning.
5. Do not invent a tail penalty after seeing these reference outcomes and call the result unseen.
6. Keep the current T-7 incumbent in production while a2 continues.

## What this means technically

The stage-1 T-7 lead is not an artifact of one blend weight: development consistently rewards moving toward Hist31, with alpha 1.0 best.

The remaining problem is therefore **not** “find the right constant blend.”

The next useful questions are:

- does fixed Hist31 beat the incumbent consistently in a broader chronological season walk-forward when its configuration is kept unchanged?;
- can a materially different robust estimator / model family retain the MAE gain with safer event-level behavior?;
- is there a pre-outcome, PIT-safe reliability signal that can identify situations where Hist31 should be distrusted, without training that rule on the exposed reference outcomes?

The next experiment should add evidence, not retune this fixed blend on 2024/25 or 2025/26.
