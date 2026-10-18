# Beyond Ticketing — Demand Forecast Development Plan v2

Ostatnia aktualizacja: **2026-10-18**

Status: **CANONICAL ACCURACY ROADMAP**

Pełne zasady eksperymentów, walidacji i CI/CD:

`ml/MODEL_ACCURACY_DEVELOPMENT_INSTRUCTIONS_V2.md`

## Główny cel

> **Dopracować model maksymalnie teraz i obniżyć MAE tak daleko, jak pozwalają uczciwe, reprodukowalne dane i walidacja PIT-safe.**

Failed challenger zamyka challenger, nie workstream. Exposed references nie służą do ratowania kandydatów, którzy nie przeszli zamrożonego protokołu development.

## Architektura

### Pre-Live Model v2

`history + current-season regime + match context -> strongest pre-live forecast`

### Continuous Live Updater v2

`Pre-Live v2 + live trajectory + inventory + time-to-kickoff + reliability -> live delta / revised forecast`

## Aktualna kolejność

1. **a2 — Historical / Structural Prior optimization — COMPLETE FOR CURRENT DATA**
2. **b2 — Current-season regime — COMPLETE FOR CURRENT DATA**
3. **c2 — Match context — ACTIVE**
4. **Freeze Pre-Live v2**
5. **d2 — Continuous Live Updater**

Frozen C1 v8 prospective scoring trwa równolegle.

---

# 0. Production boundary

Production bundle:

`structural-prior-runtime-v1-frozen-2026-10-15-t1`

| Horizon | 2024/25 MAE | 2025/26 MAE |
|---|---:|---:|
| T-30 | 1,889.4 | 1,846.3 |
| T-14 | 1,748.5 | 1,870.4 |
| T-7 | 1,777.7 | 1,802.3 |
| T-3 | 1,661.7 | 1,775.1 |
| T-1 | 1,651.7 | 1,742.8 |

Production remains:

`live_adjustment = 0`

Historical research candidates do not automatically replace this runtime.

---

# 1. a2 — Historical optimization

Status: **COMPLETE FOR CURRENT DATA**.

Main evidence:

- `ml/results/PRE_LIVE_BASELINE_OPTIMIZATION_V1_2026-10-18.md`;
- `ml/results/T7_ROBUST_ESTIMATOR_V1_2026-10-18.md`;
- `ml/results/T7_EXTERNAL_MODEL_FAMILY_V1_2026-10-18.md`;
- `ml/results/T7_FIXED_TEMPORAL_ROBUSTNESS_V1_2026-10-18.md`;
- `ml/results/PRE_LIVE_UNRESOLVED_MULTIFOLD_V1_2026-10-18.md`;
- `ml/results/PERSISTENT_CLUB_CALIBRATION_V1_2026-10-18.md`.

Frozen historical base:

| Horizon | a2 historical base |
|---|---|
| T-30 | Structural Prior incumbent |
| T-14 | Structural Prior incumbent |
| T-7 | **`hist31-leaf20-l2-1`** |
| T-3 | Structural Prior incumbent |
| T-1 | Structural Prior incumbent |

T-7 fixed rolling audit improves 4/4 folds, mean **+104.66 MAE**.

No stable replacement was proven for T-30/T-14/T-3/T-1 under the stricter multi-fold protocol.

Persistent cross-season club calibration was tested under two materially different fixed formulations and not proven.

### a2 rule from now on

Do not reopen feature/model/recency/calibration grids on the same exposed seasons without:

- materially new data; or
- a materially new hypothesis that is not equivalent to already-tested work.

---

# 2. b2 — Current-season regime

Status: **COMPLETE FOR CURRENT DATA**.

## Old formulation

Raw current-season attendance vs historical norm was not proven.

## Successful residual-regime formulation

Evidence:

- `ml/results/CURRENT_SEASON_RESIDUAL_REGIME_V1_2026-10-18.md`;
- `ml/results/CURRENT_SEASON_REGIME_MATURITY_STAGE2_V1_2026-10-18.md`;
- `ml/results/CURRENT_SEASON_REGIME_FIXED_TEMPORAL_AUDIT_V1_2026-10-18.md`.

Critical idea:

`current-season actual - our own earlier Pre-Live expectation`

Critical PIT rule:

`prior home match kickoff + 3h <= current forecast as_of`

No uncompleted outcome can enter state.

Frozen historical b2 policy:

| Horizon | b2 layer |
|---|---|
| T-30 | `NO_ADJUSTMENT` |
| T-14 | `NO_ADJUSTMENT` |
| T-7 | `ewma50-resid-k6-cap05-min3` |
| T-3 | `ewma50-resid-k2-cap05-min3` |
| T-1 | `ewma50-resid-k6-cap05-min3` |

Activation:

- requires at least **3 earlier completed same-season home matches**;
- correction remains capped at +/-5% verified capacity.

## Fixed temporal audit

Run:

`39162448305`

All fixed candidates improve all 4 rolling folds.

| Horizon | Mean 4-fold MAE improvement | Min fold improvement | Mean active share |
|---|---:|---:|---:|
| T-7 | **+51.47** | +7.15 | 78.4% |
| T-3 | **+70.44** | +21.18 | 79.1% |
| T-1 | **+69.54** | +24.66 | 79.4% |

Risk boundary:

- max harmful event regression: +2,760.55 seats;
- club-season cells improved: ~60–64%;
- event improvement rate may be below 50%;
- gains come from magnitude, not universal per-match wins.

Decision:

> **Freeze b2 historical candidates. No further tuning on the same references.**

---

# 3. c2 — Match context

Status: **ACTIVE**.

The baseline to beat is now the frozen historical a2+b2 stack, not the old production-only Structural Prior.

## Current Pre-Live stack before c2

| Horizon | a2 base | b2 layer |
|---|---|---|
| T-30 | incumbent | none |
| T-14 | incumbent | none |
| T-7 | `hist31-leaf20-l2-1` | `ewma50-resid-k6-cap05-min3` |
| T-3 | incumbent | `ewma50-resid-k2-cap05-min3` |
| T-1 | incumbent | `ewma50-resid-k6-cap05-min3` |

## Existing PIT-safe context already inside Structural Prior

Do not duplicate these without a materially better representation:

- opponent draw;
- pair history;
- home/away PPG;
- GD per game;
- last-5 points / GD;
- table position / gaps;
- top/bottom interactions;
- rest / congestion.

`Future Fixture Context v1` is `NOT PROVEN`. Do not retune the same future-fixture/cannibalization contract on the same exposed references.

## c2 Stage 1 — match stakes + sequence-aware form

Immediate experiment:

**C2 Context Extension v2**.

### A. Match-stakes / table-pressure candidates

PIT-safe only:

- title-race relevance using points/table state known at as-of;
- European qualification pressure;
- relegation pressure;
- direct-table-rival / small position or points-gap interaction;
- late-season importance interactions.

Do not use final table positions, final point totals or future results.

### B. Sequence-aware form candidates

Add information not represented by current last-5 sums:

- current winning streak length;
- unbeaten streak length;
- losing streak length;
- home-only winning/unbeaten streak where sample allows;
- recent points acceleration/deceleration (e.g. last-3 vs prior-3), computed PIT;
- optionally result-sequence entropy/volatility if predeclared and interpretable.

### C. Evaluation architecture

c2 must measure **incremental value over the current a2+b2 stack**.

Preferred first implementation:

1. produce frozen a2+b2 prediction for every historical PIT row;
2. construct PIT-safe context state at each as-of;
3. train a bounded context-residual challenger on earlier seasons;
4. select candidate contract on development folds only;
5. score unchanged on exposed references;
6. persist exact context definitions and as-of assertions.

Avoid rebuilding a weaker baseline and claiming context uplift against it.

### D. Selection protocol

Use rolling development folds analogous to b2:

1. train through 2021/22 -> evaluate 2022/23;
2. train through 2022/23 -> evaluate 2023/24.

A context challenger must improve both development folds before reference scoring matters.

References:

- 2024/25;
- 2025/26.

References cannot choose thresholds/features.

### E. Mandatory diagnostics

- MAE / median AE / p90 / bias / WAPE;
- worst-event degradation;
- exact worst/best events;
- club breakdown;
- season/horizon breakdown;
- feature availability/missingness at as-of;
- correction magnitude and active share;
- contribution by stakes vs sequence-aware groups;
- late-season vs early-season performance;
- top-table / relegation-zone conditional diagnostics.

### F. c2 next after Stage 1

If match-stakes or sequence-aware form is proven, run fixed robustness and freeze.

Then consider:

- deterministic rivalry/derby/exceptional opponent draw;
- squad availability only with trustworthy historical PIT timestamps.

If no reliable historical PIT squad feed exists, record blocker; do not fake/backfill current knowledge into history.

---

# 4. Freeze Pre-Live v2

After c2 is sufficiently evaluated, freeze exact per horizon:

- a2 base model ID;
- b2 regime policy;
- c2 context policy where proven;
- feature/state contracts;
- training data and versions;
- preprocessing;
- hyperparameters;
- seeds;
- artifact hashes;
- scorecards;
- known limitations.

No d2 learned model should train against a moving baseline.

---

# 5. d2 — Continuous Live Updater

Status: **AFTER PRE-LIVE v2 FREEZE; data/prospective infrastructure continues now**.

Target:

`frozen Pre-Live v2 + live trajectory + inventory + time-to-kickoff + reliability -> live delta / remaining demand / governed revision`

Use continuous time, earliest usable sales evidence, velocity/acceleration, release/coverage state and sector/price-area evidence.

T-30/T-14/T-7/T-3/T-1 remain evaluation checkpoints, not the only model-update moments.

Production remains unchanged until explicit promotion governance is satisfied.
