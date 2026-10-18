# Pre-Live T-7 Robustness Stage 2 v1 — Result 2026-10-18

Status: **COMPLETED / HISTORICAL ROBUSTNESS EVIDENCE / NO PRODUCTION CHANGE**

Workstream:

**a2 — Historical / Structural Prior optimization**

## Decision

The development-only selection chose:

`hist31-a075-cap05`

Policy:

- Hist31 weight `alpha = 0.75`;
- maximum change from incumbent = `±5%` of verified capacity;
- formula: `incumbent + clip(0.75 * (Hist31 - incumbent), ±0.05 * capacity)`.

On the exposed 2024/25 and 2025/26 reference seasons this robust policy:

- improves mean MAE by **69.38 seats** versus the incumbent;
- slightly exceeds pure Hist31's mean improvement of **68.81 seats**;
- improves both reference seasons;
- reduces the maximum observed harmful event-level regression from **4,233.11** seats for pure Hist31 to **2,141.85** seats.

Signal:

`ROBUST_BLEND_IMPROVES_BOTH_REFERENCES_AND_REDUCES_TAIL`

This is the strongest T-7 historical challenger currently available, but:

`promotion_allowed = false`

and production remains unchanged.

---

## Canonical evidence source

Corrected GitHub Actions run:

`39158799946`

PR head commit used by the corrected run:

`2f328fdc68531b52597d3ad2fb985e592a161aed`

Artifact:

`pre-live-t7-robustness-stage2-v1-39158799946`

Artifact ID:

`12148132090`

Artifact ZIP SHA256:

`441a7b3f9648b3e660e6857c30780a08df69732755272a20d85d1568fc104824`

Result JSON SHA256:

`ae578034cc81b71892df738c16f34e020f0be40f7b5fb4e1b81fae529cfc6df0`

CI result:

- compile: PASS;
- unit tests: **5/5 PASS**;
- frozen historical input SHA256 assertion: PASS;
- feature-store quality: PASS;
- incumbent benchmark assertions: PASS;
- exact Stage-1 Hist31 reproduction assertions: PASS;
- development-only policy selection: PASS;
- rolling reference scoring: PASS;
- evidence artifact upload: PASS.

---

## Important invalid run — retained for auditability

An earlier Stage-2 run existed:

`39158637628`

That run is **NON-CANONICAL / INVALID FOR MODEL EVIDENCE**.

Although CI was green, review of the artifact showed that its nominal `pure Hist31` comparator did not reproduce the exact Stage-1 Hist31 MAE.

Root cause:

- Stage 1 passed explicit uniform `sample_weight` to `HistGradientBoostingRegressor.fit()`;
- the first Stage-2 implementation fit the same hyperparameters without passing explicit uniform `sample_weight`;
- with scikit-learn HistGradientBoosting this was sufficient to produce a different fitted result;
- therefore the first Stage-2 run was not comparing against the exact Stage-1 challenger contract.

Fix:

- Stage 2 now passes `sample_weight=np.ones(...)` exactly as Stage 1 did;
- CI now hard-asserts the canonical Stage-1 Hist31 MAE for 2023/24, 2024/25 and 2025/26 with `atol=1e-9`;
- any future fit-contract drift fails the workflow.

This invalid run must not be quoted as model evidence.

The incident demonstrates why Beyond requires exact implementation details and benchmark reproduction, not only matching model names and hyperparameters.

---

## Frozen input contract

Historical artifact:

`structural-prior-runtime-v1-frozen-2026-10-15-t1`

Feature contract:

`structural-prior-pit-v1+verified-capacity-v1`

Input SHA256:

`3c6b35142c6bd20a484f2aa758cd41284fd6f4c6db1353b138f81cf321161569`

Evidence base:

- 5 Ekstraklasa seasons;
- 1,530 matches;
- 7,650 PIT horizon rows;
- verified capacity required;
- T-7 only for this experiment.

Runtime:

- Python 3.12 in GitHub Actions;
- numpy `2.3.5`;
- pandas `2.2.3`;
- scikit-learn `1.8.0`;
- joblib `1.5.3`;
- random seed `42`.

---

## Stage-1 source challenger reproduced exactly

Stage-1 challenger:

`model-hist_absolute_31`

Configuration:

- HistGradientBoostingRegressor;
- `loss=absolute_error`;
- learning rate `0.04`;
- `max_iter=300`;
- `max_leaf_nodes=31`;
- `min_samples_leaf=10`;
- `l2_regularization=1.0`;
- `random_state=42`;
- same T-7 baseline / feature mode as incumbent;
- explicit uniform sample weights.

Exact reproduction assertions:

| Season | Canonical Hist31 MAE |
|---|---:|
| 2023/24 | 2,379.4562743080 |
| 2024/25 | 1,672.1378964152 |
| 2025/26 | 1,770.2165629066 |

All three reproduced in the corrected Stage-2 run.

---

## Candidate contract

The candidate grid was fixed before reference scoring.

Hist31 weights:

- `0.25`;
- `0.50`;
- `0.75`;
- `1.00`.

Trust-region caps:

- `±5%` capacity;
- `±10%` capacity;
- uncapped.

Plus incumbent fallback.

Total:

- 12 non-incumbent policies;
- 1 incumbent;
- 13 policies.

Formula for capped candidates:

`delta = clip(alpha * (Hist31 - incumbent), -cap * capacity, +cap * capacity)`

`prediction = clip(incumbent + delta, 0, capacity)`

---

## Development-only selection

The 2024/25 and 2025/26 reference seasons did not select the policy.

Development folds:

### Fold 1

Train:

- 2021/22.

Validate:

- 2022/23.

### Fold 2

Train:

- 2021/22;
- 2022/23.

Validate:

- 2023/24.

Eligibility rule:

- candidate must improve MAE in **both** development folds;
- mean development improvement must be positive.

Robust selection rule:

1. calculate best mean development MAE improvement;
2. retain policies with at least **80%** of that best improvement;
3. select the policy with minimum maximum worst-event degradation;
4. tie-break by mean p90 delta;
5. then lower alpha;
6. then tighter cap;
7. then deterministic ID.

Best mean development gain:

**96.5654 MAE**.

Minimum retained gain required:

**77.2523 MAE**.

Eligible robustness pool:

- `hist31-a075-cap05`;
- `hist31-a075-cap10`;
- `hist31-a075-uncapped`;
- `hist31-a100-cap05`;
- `hist31-a100-cap10`;
- `hist31-a100-uncapped`.

Selected:

`hist31-a075-cap05`

Selection reason:

`PRESERVE_80_PERCENT_OF_BEST_DEV_MAE_GAIN_THEN_MINIMIZE_TAIL`

---

## Development results

### 2022/23 fold

| Model | MAE | Improvement vs incumbent | Median AE | p90 AE | Bias | Worst degradation |
|---|---:|---:|---:|---:|---:|---:|
| Incumbent | 2,088.94 | — | 1,219.82 | 5,308.71 | +698.15 | — |
| Pure Hist31 | 1,993.17 | **+95.77** | 1,167.36 | 4,783.14 | +246.40 | +5,127.99 |
| Selected robust | **1,999.04** | **+89.89** | **1,154.66** | **4,733.60** | +391.07 | **+2,255.25** |

### 2023/24 fold

| Model | MAE | Improvement vs incumbent | Median AE | p90 AE | Bias | Worst degradation |
|---|---:|---:|---:|---:|---:|---:|
| Incumbent | 2,476.82 | — | 1,288.41 | 5,598.34 | -504.93 | — |
| Pure Hist31 | **2,379.46** | **+97.36** | **1,206.21** | **5,325.76** | +6.52 | +4,317.24 |
| Selected robust | 2,403.08 | **+73.73** | 1,253.38 | 5,447.75 | -176.69 | **+2,255.16** |

Development aggregate for selected robust policy:

- fold improvements: **+89.89**, **+73.73**;
- mean improvement: **+81.81 MAE**;
- mean median-AE delta vs incumbent: **-50.10**;
- mean p90-AE delta vs incumbent: **-362.86**;
- maximum worst-event degradation: **2,255.25**.

The selection therefore preserved approximately 84.7% of pure Hist31's best mean development gain while materially reducing tail exposure.

---

## 2024/25 exposed reference

| Metric | Incumbent | Pure Hist31 | Selected robust |
|---|---:|---:|---:|
| MAE | 1,777.69 | **1,672.14** | 1,687.71 |
| MAE improvement | — | **+105.55** | **+89.99** |
| Median AE | 1,091.35 | 948.92 | **1,012.62** |
| p90 AE | 4,767.84 | 4,340.95 | **4,601.80** |
| Bias | +133.90 | -56.63 | **-1.14** |
| Event improvement rate | — | 51.3% | **54.0%** |
| Worst degradation | — | +3,685.74 | **+2,141.85** |

Worst selected-robust event:

`Lech – Korona Kielce`, 2025-04-05

- actual: 37,457;
- incumbent prediction: 32,831.69;
- incumbent AE: 4,625.31;
- robust prediction: 30,689.84;
- robust AE: 6,767.16;
- degradation vs incumbent: **+2,141.85**.

Pure Hist31's worst degradation on this season was **+3,685.74**.

---

## 2025/26 exposed reference

| Metric | Incumbent | Pure Hist31 | Selected robust |
|---|---:|---:|---:|
| MAE | 1,802.28 | 1,770.22 | **1,753.50** |
| MAE improvement | — | +32.06 | **+48.77** |
| Median AE | 1,153.15 | 1,130.63 | **1,141.25** |
| p90 AE | **3,965.92** | 3,962.48 | 3,993.28 |
| Bias | +78.86 | -129.11 | **-68.05** |
| Event improvement rate | — | 51.5% | **53.5%** |
| Worst degradation | — | +4,233.11 | **+2,141.85** |

Important limitation:

- selected robust p90 AE is **27.36 seats worse** than the incumbent on 2025/26;
- this is small relative to the reduction in maximum event-level degradation, but it must not be hidden.

Worst selected-robust event:

`Lech – Arka Gdynia`, 2026-05-08

- actual: 41,598;
- incumbent prediction: 36,152.69;
- incumbent AE: 5,445.31;
- robust prediction: 34,010.84;
- robust AE: 7,587.16;
- degradation vs incumbent: **+2,141.85**.

Pure Hist31 on the same event degraded by **+4,233.11**.

---

## Reference aggregate

| Measure | Pure Hist31 | Selected robust |
|---|---:|---:|
| Mean MAE improvement vs incumbent | +68.81 | **+69.38** |
| Maximum worst-event degradation | +4,233.11 | **+2,141.85** |

Tail reduction:

**2,091.26 seats**, approximately **49.4% lower maximum harmful degradation**.

Unlike a simple safety trade-off, the selected robust policy did not sacrifice mean reference MAE improvement; it slightly improved it relative to pure Hist31.

---

## Earliest-development-fold warning

During the 2021/22-only training fold, scikit-learn reported features with no observed values in that training sample:

- `prev_season_home_mean`;
- `pair_ratio_mean`;
- `pair_ratio_recent2`;
- `pair_attendance_mean`.

`SimpleImputer(strategy='median')` skipped those all-missing columns for that earliest fold.

This is expected from the one-season development setup, but it is an evidence limitation and is explicitly retained here.

It does not occur because of future leakage or manual data removal.

Any future early-fold tournament must preserve or explicitly redesign this missingness contract rather than suppress the warning silently.

---

## Interpretation

This result materially strengthens the T-7 pre-live path.

The selected robust policy:

- was chosen without looking at 2024/25 or 2025/26;
- improves both development folds;
- improves both exposed reference seasons;
- improves mean reference MAE by approximately **69 seats**;
- cuts the largest observed harmful regression roughly in half;
- keeps bias near zero / moderate compared with the alternatives.

However:

- 2024/25 and 2025/26 remain exposed historical reference evidence;
- Stage 2 is not fresh prospective validation;
- one reference p90 is slightly worse than incumbent;
- the experiment is T-7-specific;
- other horizons still need their a2 optimization path;
- no production artifact has been frozen for this robust policy yet.

Decision:

> **Treat `hist31-a075-cap05` as the preferred T-7 historical challenger for Pre-Live v2. Do not change production from this historical experiment alone. Preserve the policy unchanged for subsequent a2/pre-live candidate integration and fresh evidence.**

Production remains:

`structural-prior-runtime-v1-t7-gbr-base`

and globally:

`live_adjustment = 0`

---

## Next a2 work

Do not move to b2 yet.

Continue a2 across the other horizons using stronger multi-fold development selection and broader justified model-family challengers.

Priorities:

1. build a multi-fold horizon tournament contract that avoids single-season selection instability;
2. evaluate stronger model families / hyperparameter families without tuning on 2024/25–2025/26;
3. keep the T-7 robust policy fixed as the current T-7 challenger benchmark;
4. only after remaining a2 hypotheses are exhausted, choose per-horizon Pre-Live historical champions and proceed to b2.
