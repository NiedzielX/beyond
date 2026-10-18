# Beyond Ticketing — Current Model & Product State

Last product-direction update: **2026-10-18**

This is the canonical short-form model state.

Read first in a cold session:

1. `AI_BOOTSTRAP.md`;
2. `ml/MODEL_ACCURACY_DEVELOPMENT_INSTRUCTIONS_V2.md`;
3. this file;
4. `ml/DEMAND_FORECAST_DEVELOPMENT_PLAN_V2.md`.

## North star

> **Reduce forecasting MAE as far as possible with honest, reproducible, point-in-time-safe evidence before treating the model as mature.**

Architecture:

`history + current-season regime + match context -> Pre-Live Model v2`

then:

`Pre-Live v2 + continuous live trajectory -> Continuous Live Updater v2`

Canonical sequence:

`a2 -> b2 -> c2 -> freeze Pre-Live v2 -> d2`

Current active workstream:

**c2 — match context**.

Production remains unchanged throughout current historical research.

---

# Production boundary

Production Structural Prior:

| Horizon | Production runtime | 2024/25 MAE | 2025/26 MAE |
|---|---|---:|---:|
| T-30 | `structural-prior-runtime-v1-t30-extra-full` | 1,889.4 | 1,846.3 |
| T-14 | `structural-prior-runtime-v1-t14-hist-base` | 1,748.5 | 1,870.4 |
| T-7 | `structural-prior-runtime-v1-t7-gbr-base` | 1,777.7 | 1,802.3 |
| T-3 | `structural-prior-runtime-v1-t3-hist-full` | 1,661.7 | 1,775.1 |
| T-1 | `structural-prior-runtime-v1-t1-hist-full` | 1,651.7 | 1,742.8 |

Frozen production bundle:

`structural-prior-runtime-v1-frozen-2026-10-15-t1`

Historical evidence base:

- 5 Ekstraklasa seasons;
- 1,530 matches;
- 7,650 PIT horizon rows;
- verified capacity coverage 100%.

Production:

`live_adjustment = 0`

No historical candidate below is a production promotion.

---

# a2 — Historical / Structural Prior optimization

Status: **SUFFICIENTLY EXHAUSTED FOR CURRENT DATA / HISTORICAL CANDIDATE STATE FROZEN**.

Canonical a2 evidence includes:

- feature-group ablation;
- season-recency weighting;
- internal estimator families;
- T-7 regularization and robustness;
- CatBoost / LightGBM / XGBoost for T-7;
- four-fold fixed temporal audit;
- stronger multi-fold unresolved-horizon tournament;
- two materially different persistent cross-season club-calibration formulations.

Do not restart the same grids on the same exposed references without materially new data or a materially new hypothesis.

## Historical base after a2

| Horizon | Frozen historical candidate |
|---|---|
| T-30 | retained Structural Prior incumbent |
| T-14 | retained Structural Prior incumbent |
| T-7 | **`hist31-leaf20-l2-1`** |
| T-3 | retained Structural Prior incumbent |
| T-1 | retained Structural Prior incumbent |

### T-7 fixed historical audit

`hist31-leaf20-l2-1` improves the incumbent on all four rolling folds:

| Season | Improvement |
|---|---:|
| 2022/23 | +103.95 MAE |
| 2023/24 | +159.48 |
| 2024/25 | +126.73 |
| 2025/26 | +28.48 |

Mean fold improvement:

**+104.66 MAE**.

It remains historical-only because tail and club heterogeneity are material.

### Unresolved horizons

`ml/results/PRE_LIVE_UNRESOLVED_MULTIFOLD_V1_2026-10-18.md`

- T-30: incumbent retained;
- T-14: incumbent retained;
- T-3: incumbent retained;
- T-1: development candidate failed reference stability -> incumbent retained.

### Persistent club calibration

`ml/results/PERSISTENT_CLUB_CALIBRATION_V1_2026-10-18.md`

Fixed empirical-Bayes cross-season club residual calibration is rejected on development for all horizons. A separate predeclared median/shrinkage formulation also failed to establish stable uplift.

Decision:

> **No persistent cross-season club correction. a2 closed for current evidence.**

---

# b2 — Current-season regime

Status: **SUFFICIENTLY EVALUATED FOR CURRENT DATA / HISTORICAL CANDIDATE POLICIES FROZEN / PRODUCTION UNCHANGED**.

## Old formulation

`Current Season Adjustment v1` compared raw current-season attendance with historical club norm and was `NOT PROVEN`.

That did not close b2.

## Residual-regime v1

Evidence:

`ml/results/CURRENT_SEASON_RESIDUAL_REGIME_V1_2026-10-18.md`

Run:

`39161525672`

The new question was:

> **Is the club running above/below what our own strongest Pre-Live base expected earlier in this same season?**

Critical PIT rule:

`prior kickoff_at + 3h <= current forecast as_of_at`

A nominally earlier fixture cannot enter current-season state before it actually completes.

Signals tested included mean/median residual, EWMA, last-3 residual and actual/expected ratio with shrinkage and a fixed +/-5% capacity correction cap.

Stage 1 found:

- T-30: no stable b2 signal;
- T-14: no stable b2 signal;
- T-7: strong development signal but mixed references;
- T-3: material lead;
- T-1: material lead.

## Maturity Stage 2

Evidence:

`ml/results/CURRENT_SEASON_REGIME_MATURITY_STAGE2_V1_2026-10-18.md`

Run:

`39162095068`

Only activation maturity was changed. Stage-1 signal/k/cap stayed frozen.

All advancing horizons selected:

`minimum 3 earlier completed same-season home matches`

Frozen historical b2 policies:

| Horizon | b2 historical policy |
|---|---|
| T-30 | `NO_ADJUSTMENT` |
| T-14 | `NO_ADJUSTMENT` |
| T-7 | `ewma50-resid-k6-cap05-min3` |
| T-3 | `ewma50-resid-k2-cap05-min3` |
| T-1 | `ewma50-resid-k6-cap05-min3` |

Stage-2 reference mean gains:

- T-7: **+20.98 MAE**;
- T-3: **+35.76**;
- T-1: **+35.77**.

## Fixed temporal audit — final b2 gate

Evidence:

`ml/results/CURRENT_SEASON_REGIME_FIXED_TEMPORAL_AUDIT_V1_2026-10-18.md`

Run:

`39162448305`

Artifact ID:

`12149610912`

ZIP SHA256:

`9a8bb3ed2f3ba4dbcf6b786c8cb1ab067ef1bca62afebbe674f6dec277141f0a`

JSON SHA256:

`1d0556a831166ae665d2be209450122461329e584c6c4751ba130502c8afbccb`

No parameter selection occurred in this audit.

All three candidates reproduce exactly and improve all four rolling folds:

| Horizon | Mean 4-fold MAE improvement | Minimum fold improvement | Mean active share | Club-season cells improved |
|---|---:|---:|---:|---:|
| T-7 | **+51.47** | +7.15 | 78.4% | 61.1% |
| T-3 | **+70.44** | +21.18 | 79.1% | 63.9% |
| T-1 | **+69.54** | +24.66 | 79.4% | 59.7% |

Audit:

`PASS`

Tail remains explicit:

- maximum observed event degradation: **+2,760.55 seats**;
- fixed safety cap remains +/-5% verified capacity;
- event improvement rate is below 50% in several folds;
- club-level heterogeneity remains material.

Decision:

> **Freeze b2 policies as historical Pre-Live candidates. Do not tune them further against the same exposed seasons. Advance to c2.**

---

# Current Pre-Live candidate stack before c2

This is the historical candidate stack that c2 must treat as the baseline to beat.

| Horizon | Historical base after a2 | b2 current-season layer |
|---|---|---|
| T-30 | Structural Prior incumbent | none |
| T-14 | Structural Prior incumbent | none |
| T-7 | `hist31-leaf20-l2-1` | `ewma50-resid-k6-cap05-min3` |
| T-3 | Structural Prior incumbent | `ewma50-resid-k2-cap05-min3` |
| T-1 | Structural Prior incumbent | `ewma50-resid-k6-cap05-min3` |

c2 must measure incremental value over this stack, not over an older weaker baseline.

---

# c2 — Match context

Status: **ACTIVE / EXISTING CONTEXT AUDITED / FUTURE-FIXTURE V1 NOT PROVEN / NEW CONTEXT HYPOTHESES NEXT**.

Existing PIT-safe context already includes:

- opponent draw and pair history;
- home/away PPG;
- GD per game;
- last-5 points / GD;
- table position / gaps;
- top/bottom interactions;
- rest / congestion.

`Future Fixture Context v1` was `NOT PROVEN` and must not be repeatedly retuned against the same references.

## Next c2 priorities

1. **match stakes / table-pressure context**
   - title-race relevance;
   - European qualification relevance;
   - relegation relevance;
   - direct-table-rival / points-pressure interactions;
   - late-season importance.
2. **sequence-aware form**
   - winning streak;
   - unbeaten streak;
   - losing streak;
   - recent points acceleration/deceleration;
   - home-specific streak where justified.
3. **rivalry / derby / exceptional opponent draw** only with deterministic maintainable mapping.
4. **squad availability** only after a reliable historical PIT source exists.

## c2 rules

- new context must add information not already represented by existing PPG/form/table features;
- all context must exist at historical `as_of_at`;
- future final table state is forbidden;
- match-stakes calculations must use only standings/results known at `as_of_at`;
- exposed references cannot select features/thresholds;
- measure incremental MAE over the current Pre-Live candidate stack above;
- no production change from c2 historical experiments.

Immediate task:

> **Build c2 Context Extension v2 with PIT-safe match-stakes + sequence-aware form candidates, development-only selection and full temporal/tail diagnostics.**

---

# Pre-Live v2 freeze point

After c2 is sufficiently evaluated, freeze exact per horizon:

- a2 base model ID;
- b2 regime policy where proven;
- c2 context policy where proven;
- feature/state contract;
- training data/version;
- preprocessing;
- hyperparameters;
- seeds;
- artifacts/hashes;
- scorecard;
- limitations.

Only then train the next learned live updater.

---

# d2 — Continuous Live Updater

Status: **LIVE DATA INFRASTRUCTURE EXISTS / NEW LEARNED d2 AFTER PRE-LIVE v2 FREEZE**.

Already available:

- public inventory collection;
- PIT trajectory / velocity / acceleration;
- release / coverage-change handling;
- frozen C1 v8 prospective shadow;
- sector / price-area trajectories;
- Roboticket price observations;
- guarded sector/pricing decision support.

Target d2:

`frozen Pre-Live v2 + continuous live evidence -> delta / remaining demand / reliability-weighted revision`

T-30/T-14/T-7/T-3/T-1 remain evaluation checkpoints, not the only update moments.

---

# Frozen C1 v8

Package:

`c1-shadow-v8-frozen-2026-10-16-n9`

Status:

`EXPERIMENTAL_SHADOW`

Historical boundary:

- raw Live LOEO: 2,929.3;
- conservative synthetic: 2,261.5;
- stress synthetic: 2,498.8;
- four-event chronological Prior: 452.8;
- raw Live: 2,103.7;
- frozen v8: 452.8 with PRIOR selected 16/16.

Frozen v8 remains unchanged while prospective evidence accumulates.

---

# Engineering governance

Full rules:

`ml/MODEL_ACCURACY_DEVELOPMENT_INSTRUCTIONS_V2.md`

Non-negotiable:

- MAE primary; tail and bias mandatory;
- event is independent evaluation unit;
- all state must exist at forecast as-of;
- no random snapshot split;
- exact data/model/feature versions;
- code + tests + CI + artifact + result doc + decision;
- hard reproduction gates where canonical values exist;
- exposed references cannot rescue development failures;
- no silent retuning;
- CI green != production promotion.

## Current development decision

**c2 match context -> freeze Pre-Live v2 -> d2**.

Production remains unchanged.