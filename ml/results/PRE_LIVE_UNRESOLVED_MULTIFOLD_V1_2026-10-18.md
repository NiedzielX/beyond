# Pre-Live Unresolved-Horizon Multi-Fold v1 — Result 2026-10-18

Status: **COMPLETED / T-30 T-14 T-3 INCUMBENTS RETAINED / T-1 CHALLENGER NOT PROVEN ON REFERENCES / NO PRODUCTION CHANGE**

Workstream:

**a2 — Historical / Structural Prior optimization — unresolved-horizon multi-fold selection**

## Evidence source

GitHub Actions run: `39159907426`  
Tested branch head: `34b14017f2d09eeda7af04a60d4900b884b6afb6`  
Artifact: `pre-live-unresolved-multifold-v1-39159907426`  
Artifact ID: `12148169124`  
Artifact ZIP SHA256: `2a5ea9793a0f730c5622096bfab6621649b8f16d06f5883434a61d5a1003658d`  
Result JSON SHA256: `f7bf178bad293547f3e866dd312997e2415744b68d66f5d4ed5db9cc8b984b1a`

CI:

- compile: PASS;
- unit tests: **5/5 PASS**;
- frozen historical input SHA256 assertion: PASS;
- feature-store quality: PASS;
- exact Stage-1 2023/24 incumbent assertions: PASS;
- full two-fold tournament: PASS;
- frozen-candidate reference scoring: PASS;
- artifact upload: PASS.

`promotion_allowed = false`

Production remains unchanged.

---

## Scope

Horizons evaluated:

- T-30;
- T-14;
- T-3;
- T-1.

T-7 was deliberately excluded because `hist31-leaf20-l2-1` is already frozen as the historical T-7 Pre-Live candidate after Stages 1–5.

## Candidate contract

The experiment reused the attributable Stage-1 families:

- production incumbent;
- one feature-group ablation at a time;
- explicit recency weighting;
- small internal model-family challenger set.

No external model zoo or open-ended hyperparameter search was added.

## Stronger development protocol

### Development fold A

Train:

- 2021/22.

Validate:

- 2022/23.

### Development fold B

Train:

- 2021/22;
- 2022/23.

Validate:

- 2023/24.

Exact canonical 2023/24 incumbent assertions:

| Horizon | MAE |
|---|---:|
| T-30 | 2,559.7406941267 |
| T-14 | 2,339.9504993284 |
| T-3 | 2,311.6246893163 |
| T-1 | 2,347.9931110468 |

Tolerance:

`1e-9`

## Recency identifiability rule

Recency weighting is not identifiable with one training season.

Therefore on 2022/23:

- recency candidates are explicitly marked non-identifiable;
- implementation differences caused only by explicit sample-weight plumbing cannot count as recency evidence;
- a challenger needs two identifiable development folds to advance.

This prevents using the exposed 2024/25 or 2025/26 seasons as a second tuning fold for recency.

## Advancement rule

A non-incumbent candidate must:

1. be identifiable in at least two development folds;
2. improve incumbent MAE by more than `1e-9` in every identifiable development fold.

Among eligible candidates:

1. maximize mean development MAE improvement;
2. tie-break by smaller maximum worst-event degradation;
3. then use predeclared Stage-1 candidate order.

If no candidate qualifies, incumbent is retained before reference scoring.

Only the incumbent plus the development-selected candidate are scored on 2024/25 and 2025/26 references.

---

# T-30

Decision:

`incumbent`

Selection reason:

`NO_NON_INCUMBENT_IMPROVES_ALL_IDENTIFIABLE_DEVELOPMENT_FOLDS`

Eligible non-incumbent candidates:

**0**

Examples of instability:

- `ablate-sporting_form`: +11.34 MAE on 2022/23, **-21.31** on 2023/24;
- `ablate-rest_congestion`: **-27.75** on 2022/23, +9.31 on 2023/24;
- `model-extra_leaf5`: +20.07 on 2022/23, **-57.99** on 2023/24;
- Stage-1 recency is not multi-fold identifiable and is also negative on its identifiable 2023/24 fold.

Reference result remains exact production incumbent:

| Season | MAE |
|---|---:|
| 2024/25 | 1,889.37 |
| 2025/26 | 1,846.28 |

Conclusion:

> **No tested T-30 Stage-1 hypothesis is stable enough across both development folds to advance. Retain incumbent.**

---

# T-14

Decision:

`incumbent`

Selection reason:

`NO_NON_INCUMBENT_IMPROVES_ALL_IDENTIFIABLE_DEVELOPMENT_FOLDS`

Eligible non-incumbent candidates:

**0**

Important Stage-1 recency interpretation:

- `recency-linear_075` improves the identifiable 2023/24 fold by only +8.70 MAE;
- recency cannot be identified on the 2022/23 fold because training contains one season;
- therefore it does not have the two independent development-era signals required to advance.

Other examples:

- `ablate-table_context`: +12.37 on 2022/23, **-67.56** on 2023/24;
- `ablate-sporting_form`: +60.96 on 2022/23, **-118.69** on 2023/24;
- `model-rf_absolute_leaf3`: negative on both folds.

Reference result remains exact incumbent:

| Season | MAE |
|---|---:|
| 2024/25 | 1,748.50 |
| 2025/26 | 1,870.39 |

Conclusion:

> **The earlier mild recency signal is insufficiently identified for multi-fold promotion. Retain incumbent.**

---

# T-3

Decision:

`incumbent`

Selection reason:

`NO_NON_INCUMBENT_IMPROVES_ALL_IDENTIFIABLE_DEVELOPMENT_FOLDS`

Eligible non-incumbent candidates:

**0**

Several challengers look attractive on average only because the two development folds disagree:

- `ablate-rest_congestion`: +81.25 on 2022/23, **-31.67** on 2023/24;
- `ablate-home_history`: +48.09, **-2.90**;
- `ablate-sporting_form`: +29.01, **-7.92**;
- `ablate-current_season`: +49.68, **-34.95**;
- `model-hist_absolute_31`: +34.59, **-26.26**;
- `model-extra_leaf5`: +92.31, **-99.60**.

Reference result remains exact incumbent:

| Season | MAE |
|---|---:|
| 2024/25 | 1,661.72 |
| 2025/26 | 1,775.07 |

Conclusion:

> **T-3 demonstrates why a one-fold or average-only selection rule is unsafe: multiple apparently positive hypotheses reverse sign on the next development fold. Retain incumbent.**

---

# T-1

Development selected:

`ablate-rest_congestion`

Eligible development candidates:

- `ablate-rest_congestion`;
- `ablate-capacity`.

Selected development-fold result:

| Season | MAE improvement vs incumbent |
|---|---:|
| 2022/23 | **+63.47** |
| 2023/24 | **+11.97** |
| Mean | **+37.72** |

Development diagnostics for the selected candidate:

- mean p90 AE delta vs incumbent: **-144.03**;
- mean median AE delta: **+53.59** — median is worse despite lower MAE;
- maximum worst-event degradation across development folds: **+2,564.08**.

The candidate was frozen before reference scoring.

## T-1 2024/25 reference

- incumbent MAE: **1,651.73**;
- selected MAE: **1,690.10**;
- MAE change: **-38.36** — worse;
- incumbent median AE: 962.47;
- selected median AE: 1,023.86 — worse;
- incumbent p90 AE: 4,082.06;
- selected p90 AE: 4,361.60 — worse;
- event improvement rate: 44.0%;
- worst degradation: **+2,198.19** on `Lech – Legia`, 2024-11-10.

## T-1 2025/26 reference

- incumbent MAE: **1,742.84**;
- selected MAE: **1,717.57**;
- MAE improvement: **+25.26**;
- incumbent median AE: 1,065.88;
- selected median AE: 1,038.97;
- p90 is effectively flat/slightly worse: 3,802.29 -> 3,803.73;
- event improvement rate: 46.20%;
- worst degradation: **+1,115.12** on `Lech – Radomiak`, 2025-11-23.

Aggregate reference result:

- incumbent mean MAE: **1,697.28**;
- selected mean MAE: **1,703.84**;
- mean MAE improvement: **-6.55** — worse;
- signal: `MULTIFOLD_SELECTED_CANDIDATE_NOT_PROVEN_ON_REFERENCES`.

Important governance consequence:

`ablate-capacity` is **not** now scored/selected post hoc to rescue T-1. The protocol froze `ablate-rest_congestion` from development before reference scoring.

Conclusion:

> **The T-1 multi-fold winner fails the exposed-reference check. Retain the production incumbent as the historical T-1 candidate.**

---

# Overall decision

| Horizon | Multi-fold development selection | Reference outcome | Historical candidate decision |
|---|---|---|---|
| T-30 | incumbent fallback | unchanged | **incumbent** |
| T-14 | incumbent fallback | unchanged | **incumbent** |
| T-3 | incumbent fallback | unchanged | **incumbent** |
| T-1 | `ablate-rest_congestion` | mean -6.55 vs incumbent | **incumbent** |

Together with the completed T-7 work, the current a2 historical model state is now:

- T-30: current production incumbent retained;
- T-14: current production incumbent retained;
- T-7: `hist31-leaf20-l2-1` frozen as **historical Pre-Live candidate**, production still incumbent;
- T-3: current production incumbent retained;
- T-1: current production incumbent retained.

## Interpretation

This is a useful negative result, not a failure of the process.

The stronger multi-fold protocol removes several apparently positive single-fold signals and prevents exposed-reference rescue.

The result means:

- do not keep micro-tuning the same ablation/recency/internal-estimator hypotheses on these horizons;
- do not use 2024/25–2025/26 to choose a different challenger after the fact;
- move a2 to a **materially different justified hypothesis**, not another permutation of the same Stage-1 grid.

## Next a2 hypothesis

The remaining justified a2 direction is historical **residual / club calibration**:

- calculate PIT residuals against the correct rolling incumbent/historical candidate;
- test whether stable home-club residual structure persists out-of-sample;
- shrink low-sample clubs toward zero;
- prevent memorization;
- use multi-fold development selection;
- report club-level and tail behavior;
- keep T-7 estimator configuration frozen while calibration is evaluated as a separate layer.

If residual/club calibration is also not proven, a2 historical model optimization should be considered sufficiently exhausted for the current data and we should advance to b2 current-season regime rather than continue model-grid tuning.

Production remains unchanged:

`live_adjustment = 0`
