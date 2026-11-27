# E5 rolling-horizon MAE error diagnosis — 2026-11-27

## Scope and method

Read-only live SQL aggregates were taken at **2026-11-27 11:35 UTC** from E5 predictions/labels and the active paired DRIFT24 lane. No database writes, refits, or recipe changes were made. E5 rows were restricted to `source_status='VALID'`; each label was joined to its prediction by `prediction_id`. Results below are on the shared labeled E5 rows, with MAE computed from each method's absolute error. The live E5 labels contain 678 +24 h, 496 +48 h, and 307 +72 h rows, each spanning the same two labeled fixtures (24377 and 24378). All due valid predictions were labeled at this cut; there were 174/356/545 future unlabeled predictions at +24/+48/+72 respectively. Each horizon has 852 valid prediction rows total.

These are **public available-inventory** errors. Continuity is recorded as `UNKNOWN`; a zero sector-count delta is not proof of unchanged sector membership, and none of these figures is attendance, sales, demand, or revenue MAE. E5 is the exposed five-fixture cohort, but only two fixtures currently contribute labels.

## Event-balanced errors by horizon

For comparability across uneven fixture row counts, each fixture MAE is averaged first, then the two fixture MAEs receive equal weight. Denominators are shared labeled targets / distinct fixtures.

| Horizon | Shared labeled targets / fixtures | PERS | DRIFT6 | DRIFT24 | COMMON_FLOW6 |
|---:|---:|---:|---:|---:|---:|
| +24 h | 678 / 2 | 226.21 | 174.61 | **85.62** | 268.45 |
| +48 h | 496 / 2 | 419.19 | 322.47 | **150.41** | 441.31 |
| +72 h | 307 / 2 | 605.68 | 445.24 | **310.42** | 586.08 |

The horizon numbers are separate repeated-origin summaries, not independent event samples. DRIFT24 beats persistence at all three horizons on these two fixtures; no prospective generalization claim follows.

### Fixture concentration

| Fixture | Horizon | Labels | Scope-count changed | PERS MAE | DRIFT6 MAE | DRIFT24 MAE | COMMON_FLOW6 MAE |
|---|---:|---:|---:|---:|---:|---:|---:|
| 24377 | +24 h | 335 | 3 | 381.15 | 278.00 | **99.97** | 278.00 |
| 24378 | +24 h | 343 | 302 | 71.26 | 71.22 | 71.26 | 258.89 |
| 24377 | +48 h | 247 | 3 | 787.93 | 594.56 | **250.37** | 594.56 |
| 24378 | +48 h | 249 | 247 | 50.45 | 50.38 | 50.45 | 288.06 |
| 24377 | +72 h | 154 | 3 | 1,178.77 | 857.72 | **588.24** | 857.72 |
| 24378 | +72 h | 153 | 153 | 32.59 | 32.75 | 32.59 | 314.43 |

The higher-inventory fixture 24377 supplies essentially all large baseline/drift absolute error at every horizon. Its largest stratum has **stable sector count** (`delta=0`, n=332/244/151 by horizon): PERS MAE grows 381.22 → 787.06 → 1,178.32; DRIFT24 is 99.85 → 251.29 → 597.73. DRIFT24's long-horizon remaining error has positive signed bias (+585.25 at +72), indicating forecasts are generally above observed inventory there. In contrast, the high-churn 24378 has low PERS/DRIFT24 MAE, and nearly all rows have nonzero sector-count delta. PERS signed bias for its changed-count strata is only +10.90, +1.15, +22.38 at +24/+48/+72.

The structural implication is that the **largest MAE is not explained by the scope-change flag**. It is concentrated in the much larger-inventory fixture with nearly unchanged sector counts, where long-horizon inventory decline is under-captured. The count flag is only a weak scope proxy, and its continuity guarantee is absent.

## Regime comparison and method failure mode

A raw (row-weighted) split by `sector_count_delta=0` vs nonzero gives:

| Horizon | Scope count | Labels | PERS MAE | DRIFT6 | DRIFT24 | COMMON_FLOW6 |
|---:|---|---:|---:|---:|---:|---:|
| +24 h | delta = 0 | 373 | 346.99 | 253.24 | **96.55** | 261.84 |
| +24 h | delta ≠ 0 | 305 | 74.42 | 75.73 | **71.86** | 276.28 |
| +48 h | delta = 0 | 246 | 781.01 | 593.07 | **249.60** | 594.66 |
| +48 h | delta ≠ 0 | 250 | 60.20 | 54.02 | **52.00** | 289.19 |
| +72 h | delta = 0 | 151 | 1,178.32 | 840.58 | **597.73** | 840.58 |
| +72 h | delta ≠ 0 | 156 | 55.06 | 65.19 | **34.09** | 341.46 |

These pooled rows are diagnostic only: the two fixtures have very different inventory scales, so this table confounds scope regime with fixture identity and does not equal-weight events. The split nonetheless falsifies a simple “scope churn causes the largest errors” explanation: changed-count rows have much smaller absolute error, dominated by low-inventory 24378, while unchanged-count rows carry the high errors from 24377.

`COMMON_FLOW6` is the clearest failure. It matches DRIFT6 exactly on 24377 at +24/+48/+72 (278.00/594.56/857.72), while it jumps to 258.89/288.06/314.43 on 24378. On 24378, DRIFT24 is a persistence fallback on 343/343, 249/249, and 153/153 rows by horizon; DRIFT6 falls back on 336/343, 245/249, and 152/153. COMMON_FLOW6 has no fallback on these rows and still produces large errors. Earlier diagnosis observed steep negative common-sector slopes when a very small common subset was extrapolated across changing sector scope; current aggregate results are consistent with that mechanism but do not prove it from aggregates alone. The failed regime is therefore better described as **small-common-sector extrapolation under scope churn**, not churn by itself.

## Active paired coverage

The active `rolling72-mvp-paired-drift24-v1` comparator is a distinct, newly registered cohort, not E5. At the same live cut it contains **99 PERS/DRIFT24 prediction pairs for fixture 27049** at +24 h and +48 h, and 99 +72 h rows of which 34 are pre-kickoff numeric pairs and 65 are `OUTSIDE_KICKOFF`. There are only **3 accepted shared +24 h labels**; +48 and +72 have zero labels. Thus 99 is issued numeric pair coverage, not scored evidence.

DRIFT24 falls back to PERS with `SCOPE_MISMATCH` on 95/99 +24 h pairs, 95/99 +48 h pairs, and 34/34 active +72 h pairs. Four pairs at +24 and +48 are `READY`; none at +72. The first three +24 labels exist, but the cohort is still one fixture and labels are too few to compare MAE meaningfully. Do not pool this stream with E5 or the historical E5 labels. Its scope fallback currently protects the paired comparison from an unsupported drift estimate, while restricting evidence about when the drift can operate.

## First actionable hypothesis

A separately versioned, precommitted next diagnosis should test **horizon-scaled trend attenuation or conditional drift for high-inventory, count-stable origins** against PERS and DRIFT24 on the same fixture/time labels, while retaining PERS fallback on sector-membership mismatch. The mechanism to test is whether the +72 positive residual bias on 24377 can be reduced without losing its substantial DRIFT24 advantage at +24/+48. Use fixture-balanced scoring and report a true membership-stability regime if sealed membership data permit it; do not use `sector_count_delta=0` as a membership equivalence guarantee. Separately, retain a guardrail analysis for common-flow forecasts where the common subset is small relative to total inventory, because the live errors indicate that this mechanism can erase overall gains.

This is a research hypothesis only. It does not authorize changing frozen E5, the active paired comparator, production behavior, or the live fallback. Production remains `live_adjustment = 0`.

## Query limits

The E5 error split used saved label `sector_count_delta`, not the full sector membership hash; `continuity='UNKNOWN'` on the labels means membership stability cannot be asserted. Scope-specific pooled MAE is row weighted, not event weighted. The live cohort is only two E5 fixtures and a separate one-fixture paired cohort; many rows within each fixture are serially dependent and are not independent samples. Query watermarks: E5 aggregate **11:35:18.728 UTC**, signed-error regime aggregate **11:35:51.876 UTC**, active paired coverage **11:35:33.554 UTC**, all 2026-11-27. Queries were SELECT-only against the named prediction/label/registry tables; no raw source payload was returned.
