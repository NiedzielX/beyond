# Pre-Live v3 — Historical Anchor + Current-Season Regime Revalidation v1 — Result

Date: **2026-10-21**

Status: **COMPLETED / T-30 AND T-7 ADVANCE / T-14, T-3, T-1 RETAIN FROZEN V2 / NO FREEZE OR PRODUCTION CHANGE**

Canonical contract:

`ml/PRE_LIVE_V3_REGIME_REVALIDATION_V1.md`

Workflow run:

`39627633502`

Job:

`119316982175`

Artifact:

`pre-live-v3-regime-revalidation-v1-39627633502`

Artifact ID:

`12357223004`

Artifact ZIP SHA256:

`469bf17bc0382ea2e341e9d3b9bd02fb55ff37b448c09f5360e59b41edd1e96e`

Result JSON SHA256:

`020685afde0d3becd0bd115a020df558360f55931638ce8cf6b875312ca7def6`

Head SHA:

`329124bd1bfef465aa49eb45b97155c23b339038`

## Runtime / gates

Pinned runtime, compile checks and unit checks passed.

The experiment:

- hard-reproduced Frozen Pre-Live v2 at tolerance `1e-9`;
- used only the historical development folds for signal/maturity selection;
- opened 2024/25 and 2025/26 only after the v3 regime policy was frozen;
- used no event-5, delayed-label or post-freeze d2 outcome for selection;
- made no production or Frozen-v2 write.

## Overall result

Only two horizons advance to the next fixed-temporal package audit:

- **T-30**;
- **T-7**.

Frozen v2 is retained at:

- T-14;
- T-3;
- T-1.

This is an important narrowing of the historical challenger found in the previous a2 audit: the T-1 historical ensemble was positive in isolation, but the full anchor+regime package does **not** beat Frozen v2 on both exposed references.

---

# T-30 — ADVANCE

v3 historical anchor:

`0.75 current a2 + 0.25 XGBoost depth3`

Stage-A signal selection:

`NO_ADJUSTMENT`

Reason:

`NO_REGIME_VARIANT_MEETS_TWO_FOLD_STABILITY_GATE`

Stage-B policy:

`NO_ADJUSTMENT`

Therefore the T-30 v3 package is the robust historical ensemble with **no current-season regime layer**.

### Exposed references

| Season | Frozen v2 MAE | v3 MAE | Improvement |
|---|---:|---:|---:|
| 2024/25 | 1,889.37 | 1,834.43 | **+54.93** |
| 2025/26 | 1,846.28 | 1,816.54 | **+29.74** |

Mean improvement vs Frozen v2:

**+42.34 MAE**

Regime incremental gain:

`0.00 / 0.00`

Decision:

`ADVANCE_V3_HORIZON_TO_FIXED_TEMPORAL_PACKAGE_AUDIT`

Interpretation:

At T-30 the historical ensemble itself is the useful signal. Adding a same-season residual regime is not stable enough on the development folds and is correctly rejected.

---

# T-14 — RETAIN FROZEN V2

Historical anchor remains current a2 and Stage-A selects:

`NO_ADJUSTMENT`

The v3 candidate is therefore identical to Frozen v2 at this horizon.

Reference improvement vs Frozen v2:

`0.00 / 0.00`

Decision:

`RETAIN_FROZEN_V2_HORIZON`

No new T-14 package is created.

---

# T-7 — ADVANCE

v3 historical anchor:

`0.25 current a2/HGB + 0.25 CatBoost depth4 + 0.50 LightGBM leaves15`

Stage-A selected signal:

`ewma50-resid-k4-cap05`

Stage-B selected policy:

`ewma50-resid-k4-cap05-min2`

This differs from Frozen v2, whose T-7 b2 policy is:

`ewma50-resid-k6-cap05-min3`

### Development selection

On the two development folds, the selected T-7 maturity policy had:

- mean MAE improvement vs v3 historical-only: **+78.46**;
- mean relative improvement: **3.67%**;
- positive improvement in both development folds.

### Exposed references

| Season | Frozen v2 MAE | v3 historical-only | final selected v3 | Final gain vs Frozen v2 |
|---|---:|---:|---:|---:|
| 2024/25 | 1,643.82 | 1,640.70 | **1,630.11** | **+13.71** |
| 2025/26 | 1,738.98 | 1,745.94 | **1,711.10** | **+27.88** |

Mean final gain vs Frozen v2:

**+20.80 MAE**

Selected v3 regime incremental gain vs v3 historical anchor:

- 2024/25: **+10.59**;
- 2025/26: **+34.84**;
- mean: **+22.71**.

### Old frozen b2 applied to new anchor

The old T-7 `k6/min3` formula still helps on the new anchor:

- 2024/25: **+15.46** incremental MAE;
- 2025/26: **+43.13**;
- mean: **+29.30**.

However, policy selection is development-only. The exposed references may not be used to retroactively choose old `k6/min3` over the predeclared development-selected `k4/min2`.

Decision:

`ADVANCE_V3_HORIZON_TO_FIXED_TEMPORAL_PACKAGE_AUDIT`

Interpretation:

T-7 remains the clearest horizon where the current-season layer adds value after reanchoring, but the optimum selected on development changes from `k6/min3` to `k4/min2`.

---

# T-3 — RETAIN FROZEN V2

Historical anchor remains current a2.

Selected policy:

`ewma50-resid-k2-cap05-min3`

This is the same effective package as Frozen v2.

The current-season regime adds value versus historical-only:

- 2024/25: **+50.34**;
- 2025/26: **+21.18**.

But final v3 vs Frozen v2 is exactly:

`0.00 / 0.00`

Decision:

`RETAIN_FROZEN_V2_HORIZON`

Interpretation:

The revalidation confirms the existing T-3 package rather than creating a better v3 horizon.

---

# T-1 — RETAIN FROZEN V2

v3 historical anchor:

`0.25 HGB hist31 + 0.50 CatBoost depth4 + 0.25 LightGBM leaves15`

Selected policy:

`ewma50-resid-k6-cap05-min3`

The selected regime is the same formulation as Frozen v2 and still improves the new historical anchor:

- 2024/25 incremental gain: **+24.31**;
- 2025/26 incremental gain: **+25.20**.

However the full v3 package vs Frozen v2 is mixed:

| Season | Frozen v2 MAE | final v3 MAE | Improvement vs v2 |
|---|---:|---:|---:|
| 2024/25 | 1,627.07 | 1,625.16 | **+1.92** |
| 2025/26 | 1,695.96 | 1,711.36 | **-15.39** |

Mean v3 change vs Frozen v2:

**-6.74 MAE**

Decision:

`RETAIN_FROZEN_V2_HORIZON`

Interpretation:

This rejects T-1 from the v3 package despite the previous 4/4 historical-anchor robustness pass. The new historical anchor does not survive package-level comparison once the current-season layer and Frozen-v2 benchmark are considered.

---

# Canonical v3 package entering the next audit

Only the following changes remain alive:

### T-30

Historical anchor:

`0.75 current a2 + 0.25 XGBoost depth3`

Current-season regime:

`NO_ADJUSTMENT`

### T-7

Historical anchor:

`0.25 current a2/HGB + 0.25 CatBoost depth4 + 0.50 LightGBM leaves15`

Current-season regime:

`ewma50-resid-k4-cap05-min2`

### T-14 / T-3 / T-1

Retain exact Frozen Pre-Live v2 horizon package.

## Next required step

Run a **fixed-temporal package audit** for the exact T-30 and T-7 v3 packages against full Frozen Pre-Live v2 across all four rolling seasons.

No model, ensemble weight, regime signal, shrinkage or maturity selection may occur in that audit.

The audit must answer whether the exact packages improve Frozen v2 consistently over:

1. 2022/23;
2. 2023/24;
3. 2024/25;
4. 2025/26.

Only after that audit can a mixed-horizon Pre-Live v3 freeze candidate be considered.

## Production boundary

Always:

- Frozen Pre-Live v2 unchanged;
- frozen Ridge/P2 unchanged;
- historical c2 unchanged;
- `production_change = false`;
- production `live_adjustment = 0`.
