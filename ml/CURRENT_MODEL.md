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

**b2 — current-season residual regime**.

---

# Production boundary

Production Structural Prior remains unchanged:

| Horizon | Production runtime | 2024/25 MAE | 2025/26 MAE |
|---|---|---:|---:|
| T-30 | `structural-prior-runtime-v1-t30-extra-full` | 1,889.4 | 1,846.3 |
| T-14 | `structural-prior-runtime-v1-t14-hist-base` | 1,748.5 | 1,870.4 |
| T-7 | `structural-prior-runtime-v1-t7-gbr-base` | 1,777.7 | 1,802.3 |
| T-3 | `structural-prior-runtime-v1-t3-hist-full` | 1,661.7 | 1,775.1 |
| T-1 | `structural-prior-runtime-v1-t1-hist-full` | 1,651.7 | 1,742.8 |

Frozen production bundle:

`structural-prior-runtime-v1-frozen-2026-10-15-t1`

Evidence base:

- 5 Ekstraklasa seasons;
- 1,530 matches;
- 7,650 PIT horizon rows;
- verified capacity coverage 100%.

Production remains:

`live_adjustment = 0`

No historical challenger described below is a production promotion.

---

# a2 — Historical / Structural Prior optimization

Status: **SUFFICIENTLY EXHAUSTED FOR CURRENT DATA / HISTORICAL CANDIDATE STATE FROZEN / PRODUCTION UNCHANGED**.

The objective of a2 was not to search indefinitely. It was to test the main realistic ways the historical baseline could improve before b2/c2.

## What a2 tested

Canonical evidence now covers:

- feature-group contribution / ablation;
- season-recency weighting;
- internal estimator-family challengers;
- regularization / robustness for the strongest horizon;
- CatBoost / LightGBM / XGBoost external family challengers for T-7;
- fixed-config rolling temporal robustness;
- stronger multi-fold selection for unresolved horizons;
- persistent cross-season club residual calibration;
- empirical-Bayes cross-season club calibration.

Do not restart the same grids on exposed historical references without materially new data or a materially new hypothesis.

## Current historical Pre-Live candidate state

| Horizon | Historical candidate after a2 | Production changed? |
|---|---|---|
| T-30 | retained Structural Prior incumbent | no |
| T-14 | retained Structural Prior incumbent | no |
| T-7 | **`hist31-leaf20-l2-1` frozen historical candidate** | no |
| T-3 | retained Structural Prior incumbent | no |
| T-1 | retained Structural Prior incumbent | no |

## T-7 historical candidate

Canonical evidence:

- `ml/results/PRE_LIVE_BASELINE_OPTIMIZATION_V1_2026-10-18.md`;
- `ml/results/T7_HIST31_BLEND_ROBUSTNESS_V1_2026-10-18.md`;
- `ml/results/T7_ROBUST_ESTIMATOR_V1_2026-10-18.md`;
- `ml/results/T7_EXTERNAL_MODEL_FAMILY_V1_2026-10-18.md`;
- `ml/results/T7_FIXED_TEMPORAL_ROBUSTNESS_V1_2026-10-18.md`.

Frozen historical T-7 config:

`hist31-leaf20-l2-1`

- HistGradientBoostingRegressor;
- absolute-error loss;
- learning rate 0.04;
- 300 iterations;
- max leaf nodes 31;
- min samples leaf 20;
- L2 = 1.0;
- seed 42;
- T-7 base feature contract;
- capacity-normalized residual target.

Fixed rolling audit:

| Season | Incumbent MAE | Candidate MAE | Improvement |
|---|---:|---:|---:|
| 2022/23 | 2,088.94 | **1,984.99** | +103.95 |
| 2023/24 | 2,476.82 | **2,317.34** | +159.48 |
| 2024/25 | 1,777.69 | **1,650.97** | +126.73 |
| 2025/26 | 1,802.28 | **1,773.80** | +28.48 |

Mean fold improvement:

**+104.66 MAE**.

The candidate improves all 4 rolling folds, but tail / club heterogeneity remains explicit. It is frozen as a **historical candidate**, not production champion.

## Unresolved-horizon tournament

Evidence:

`ml/results/PRE_LIVE_UNRESOLVED_MULTIFOLD_V1_2026-10-18.md`

Run:

`39159907426`

Result:

- T-30: no stable non-incumbent -> retain incumbent;
- T-14: no stable non-incumbent -> retain incumbent;
- T-3: no stable non-incumbent -> retain incumbent;
- T-1: development selected `ablate-rest_congestion`, but exposed references were mixed and mean worsened -> retain incumbent.

References were not allowed to rescue a different candidate.

## Persistent cross-season club calibration

Canonical empirical-Bayes evidence:

`ml/results/PERSISTENT_CLUB_CALIBRATION_V1_2026-10-18.md`

Run:

`39160907508`

Artifact ZIP SHA256:

`3a38374a9ebd4527b482e488ff7879ef6509581d572f4e2b78e0d2c1605e3bde`

Result JSON SHA256:

`1dc52a9bd060eeddde70637f1c5923c86e6f76f0b41dedd4dac91169ba089956`

Fixed PIT-safe empirical-Bayes correction is rejected on 2023/24 development for every horizon:

- T-30: -40.61 MAE;
- T-14: 0.00;
- T-7: -66.16;
- T-3: -80.59;
- T-1: -62.97.

Exposed references cannot rescue a development-negative candidate.

A separate predeclared fixed median / `n/(n+10)` calibration audit also failed to establish stable uplift and was intentionally not made canonical.

Decision:

> **Do not add persistent cross-season club calibration. a2 is sufficiently exhausted for the current dataset. Advance to b2.**

---

# b2 — Current-season regime

Status: **ACTIVE / RESIDUAL-REGIME V1 COMPLETED / T-3 AND T-1 MATERIAL HISTORICAL LEADS / SIGNAL-MATURITY ROBUSTNESS NEXT**.

## Old current-season formulation

`Current Season Adjustment v1` compared current raw attendance level with historical club norm.

It was `NOT PROVEN` and remains rejected.

Evidence:

`ml/results/CURRENT_SEASON_ADJUSTMENT_V1_2026-10-18.md`

That result did not exhaust b2.

## Current-Season Residual Regime v1

Canonical evidence:

`ml/results/CURRENT_SEASON_RESIDUAL_REGIME_V1_2026-10-18.md`

Run:

`39161525672`

Artifact ID:

`12149111168`

Artifact ZIP SHA256:

`2296ed2c1e7c4594a3e94a8059c7789a3d15c20df2878c68b45292029dd63e90`

Result JSON SHA256:

`a2cda5a6a47afb974df3a3c7e9c337cd14f57504c7829c0280d40ced5868f85b`

### New hypothesis

Instead of raw attendance-vs-history, b2 v1 uses earlier **same-season actual-vs-our-own-forecast residuals**.

A prior match may enter regime state only after:

`prior kickoff + 3h <= current forecast as_of`

This is a hard PIT rule.

Signals tested:

- mean capacity-normalized residual;
- EWMA(0.50) residual;
- mean actual/expected ratio;
- shrink `n/(n+k)`, k = 2/4/6;
- correction cap +/-5% capacity.

Selection uses only 2022/23 + 2023/24 development folds. 2024/25–2025/26 are scored after selection is frozen.

### Result

| Horizon | Selected b2 v1 policy | Dev A | Dev B | Ref 2024/25 | Ref 2025/26 | Mean ref gain | Status |
|---|---|---:|---:|---:|---:|---:|---|
| T-30 | `NO_ADJUSTMENT` | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | no stable regime |
| T-14 | `NO_ADJUSTMENT` | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | no stable regime |
| T-7 | `ewma50-resid-k6-cap05` | +80.21 | +75.33 | -3.89 | +33.69 | +14.90 | mixed references / research-only |
| T-3 | `ewma50-resid-k2-cap05` | +65.63 | +120.91 | +31.46 | +32.86 | **+32.16** | material lead |
| T-1 | `ewma50-resid-k6-cap05` | +106.90 | +81.22 | +18.80 | +51.51 | **+35.15** | material lead |

T-3 and T-1 improve both development folds and both exposed reference seasons.

T-7 has strong development evidence but reference seasons disagree; it is not frozen as a stable b2 layer.

T-30/T-14 do not advance.

## Signal maturity finding

Development diagnostics show the same-season residual signal is much more reliable once the club has **3+ earlier completed home matches**.

Examples:

### T-3 development

2022/23:

- 1 prior: -281.94 MAE;
- 2 prior: -100.22;
- 3+ prior: **+109.27**.

2023/24:

- 1 prior: +185.66;
- 2 prior: -184.36;
- 3+ prior: **+147.69**.

### T-1 development

2022/23:

- 1 prior: -147.42;
- 2 prior: -64.29;
- 3+ prior: **+146.34**.

2023/24:

- 1 prior: +64.77;
- 2 prior: -158.21;
- 3+ prior: **+106.19**.

This is visible in development evidence, not only in exposed references.

## Immediate b2 next step

Run **Current-Season Residual Regime Stage 2 — signal-maturity activation robustness**.

Freeze the v1-selected signal source / k per advancing horizon and test only activation maturity:

- activate after 1 prior completed same-season home match;
- activate after 2;
- activate after 3.

Selection remains development-only on 2022/23 + 2023/24.

Primary objective:

> preserve the T-3/T-1 MAE uplift while avoiding low-sample current-season corrections that are unstable in development.

T-7 may be included as a research comparator, but mixed references prevent treating it as frozen b2 candidate without stronger evidence.

Do **not** advance to c2 until this b2 maturity question is resolved.

---

# c2 — Match context

Status: **NOT ACTIVE YET / AUDITED + FUTURE-FIXTURE V1 NOT PROVEN / NOT EXHAUSTED**.

Existing PIT-safe context already includes:

- opponent draw;
- pair history;
- PPG;
- GD/game;
- last-5 form;
- table position / gaps;
- top/bottom interactions;
- rest / congestion.

Future Fixture Context v1 was `NOT PROVEN` and must not be repeatedly retuned against the same exposed references.

Next candidate gaps after b2:

- match stakes / title-Europe-relegation relevance;
- sequence-aware winning/unbeaten/losing streaks;
- deterministic rivalry / derby / exceptional opponent draw;
- squad availability only if a reliable historical PIT source exists.

---

# Pre-Live v2 freeze point

After b2 + c2 are sufficiently evaluated, freeze exact per-horizon:

- base model ID;
- current-season regime policy where proven;
- match-context contract where proven;
- feature contract;
- training data/version;
- preprocessing;
- hyperparameters;
- calibration;
- seeds;
- artifacts / hashes;
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
- guarded sector / pricing decision support.

Target d2 architecture:

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
- conservative train-only synthetic: 2,261.5;
- stress train-only synthetic: 2,498.8;
- four-event chronological Prior: 452.8;
- raw Live: 2,103.7;
- frozen v8: 452.8 with PRIOR selected 16/16 rows.

Do not retune frozen v8 from this evidence.

Prospective scoring continues in parallel.

---

# Engineering governance

Full rules:

`ml/MODEL_ACCURACY_DEVELOPMENT_INSTRUCTIONS_V2.md`

Non-negotiable:

- MAE primary; tail/bias mandatory;
- event is independent evaluation unit;
- every feature/state must exist at forecast as-of;
- no random snapshot split;
- exact data/model/feature versions;
- committed code + CI + artifact + result doc + decision;
- hard reproduction gates where canonical values exist;
- exposed references cannot rescue development failures;
- no silent retuning;
- CI green != production promotion.

## Current development decision

**b2 Stage 2 signal-maturity activation robustness -> then complete b2 decision -> c2 -> freeze Pre-Live v2 -> d2**.

Production remains unchanged.