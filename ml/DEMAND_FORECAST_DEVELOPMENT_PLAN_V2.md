# Beyond Ticketing — Demand Forecast Development Plan v2

Ostatnia aktualizacja: **2026-10-18**

Status: **CANONICAL ACCURACY ROADMAP**

Pełne zasady eksperymentów, walidacji i CI/CD:

`ml/MODEL_ACCURACY_DEVELOPMENT_INSTRUCTIONS_V2.md`

## Główny cel

> **Dopracować model maksymalnie teraz i obniżyć MAE tak daleko, jak pozwalają uczciwe, reprodukowalne dane i walidacja PIT-safe.**

Nie optymalizujemy developmentu pod zamykanie roadmapy. Failed challenger zamyka challenger, nie workstream. Reference holdouts nie służą do ratowania kandydatów, którzy nie przeszli wcześniej zamrożonego protokołu development.

## Architektura

### Pre-Live Model v2

`history + current-season regime + match context -> strongest pre-live forecast`

### Continuous Live Updater v2

`Pre-Live v2 + live trajectory + inventory + time-to-kickoff + reliability -> live delta / revised forecast`

## Kolejność

1. **a2 — Historical / Structural Prior optimization — ACTIVE**
2. **b2 — Current-season regime**
3. **c2 — Match context**
4. **Freeze Pre-Live v2**
5. **d2 — Continuous Live Updater**

Frozen C1 v8 prospective scoring trwa równolegle.

---

# 0. Production incumbent

Bundle:

`structural-prior-runtime-v1-frozen-2026-10-15-t1`

| Horizon | 2024/25 MAE | 2025/26 MAE |
|---|---:|---:|
| T-30 | 1,889.4 | 1,846.3 |
| T-14 | 1,748.5 | 1,870.4 |
| T-7 | 1,777.7 | 1,802.3 |
| T-3 | 1,661.7 | 1,775.1 |
| T-1 | 1,651.7 | 1,742.8 |

Evidence:

- 5 seasons;
- 1,530 matches;
- 7,650 PIT horizon rows;
- 100% verified capacity coverage.

Production remains:

`live_adjustment = 0`

---

# 1. a2 — Historical / Structural Prior optimization

Status: **ACTIVE / MODEL-GRID WORK COMPLETE / RESIDUAL-CLUB CALIBRATION NEXT**.

## Stage 1 — baseline optimization — COMPLETED

Evidence:

`ml/results/PRE_LIVE_BASELINE_OPTIMIZATION_V1_2026-10-18.md`

Run: `39156711796`

| Horizon | Stage-1 selected | Mean reference change | Interpretation |
|---|---|---:|---|
| T-30 | `ablate-rest_congestion` | +3.71 | tiny / unstable |
| T-14 | `recency-linear_075` | +11.19 | mixed |
| T-7 | `model-hist_absolute_31` | **+68.81** | material lead |
| T-3 | incumbent | 0.00 | incumbent |
| T-1 | `recency-linear_075` | -10.07 | not proven |

T-7 was the only material Stage-1 lead.

## T-7 Stages 2–5 — COMPLETED

Evidence:

- `ml/results/T7_HIST31_BLEND_ROBUSTNESS_V1_2026-10-18.md`;
- `ml/results/T7_ROBUST_ESTIMATOR_V1_2026-10-18.md`;
- `ml/results/T7_EXTERNAL_MODEL_FAMILY_V1_2026-10-18.md`;
- `ml/results/T7_FIXED_TEMPORAL_ROBUSTNESS_V1_2026-10-18.md`.

### Stage 2

Fixed blending `alpha 0/.25/.50/.75/1` selected full Hist31 (`alpha=1.0`). No partial-blend robustness evidence.

### Stage 3

Regularized HGB winner:

`hist31-leaf20-l2-1`

Exact config:

- HistGradientBoostingRegressor;
- absolute-error loss;
- lr 0.04;
- 300 iterations;
- 31 max leaf nodes;
- min samples leaf 20;
- L2 1.0;
- seed 42.

Mean reference:

- incumbent 1,789.98;
- candidate **1,712.38**;
- improvement **+77.60**.

### Stage 4

Pinned CatBoost / LightGBM / XGBoost candidates did not beat `hist31-leaf20-l2-1` on development. Do not broaden model zoo without a new hypothesis.

### Stage 5

Fixed config rolling audit, run `39159276055`:

| Season | Improvement vs incumbent | Bootstrap P(uplift > 0) |
|---|---:|---:|
| 2022/23 | +103.95 | 91.8% |
| 2023/24 | +159.48 | 99.08% |
| 2024/25 | +126.73 | 99.35% |
| 2025/26 | +28.48 | 76.04% |

- MAE improves 4/4 folds;
- mean fold improvement +104.66;
- median/p90 improve 4/4;
- bias closer zero 4/4;
- 47/72 club-season cells improve;
- tail remains material: max harmful regression +6,623.99;
- 2025/26 bootstrap CI crosses zero.

Decision:

> **Freeze `hist31-leaf20-l2-1` as historical T-7 Pre-Live candidate. Do not promote production. Stop micro-tuning T-7 on the same historical set.**

## Multi-fold unresolved-horizon tournament — COMPLETED

Evidence:

`ml/results/PRE_LIVE_UNRESOLVED_MULTIFOLD_V1_2026-10-18.md`

Run: `39159907426`

Artifact ID: `12148169124`

JSON SHA256:

`f7bf178bad293547f3e866dd312997e2415744b68d66f5d4ed5db9cc8b984b1a`

### Protocol

Development folds:

1. train 2021/22 -> validate 2022/23;
2. train 2021/22–2022/23 -> validate 2023/24.

Candidate must:

- be identifiable in at least two development folds;
- improve incumbent MAE in every identifiable fold.

Recency with one training season is explicitly non-identifiable. Numerical differences from fit/sample-weight plumbing do not count as recency evidence.

Only incumbent + development-frozen winner are scored on 2024/25–2025/26 references.

### T-30

No eligible non-incumbent.

Sign reversals include:

- sporting-form ablation +11.34 then -21.31;
- rest/congestion ablation -27.75 then +9.31;
- ExtraTrees leaf5 +20.07 then -57.99.

Decision: **incumbent retained**.

### T-14

No eligible non-incumbent.

Prior recency signal has only one identifiable development fold and cannot advance.

Sign reversals include:

- table-context ablation +12.37 then -67.56;
- sporting-form ablation +60.96 then -118.69.

Decision: **incumbent retained**.

### T-3

No eligible non-incumbent.

Examples:

- rest/congestion ablation +81.25 then -31.67;
- home-history ablation +48.09 then -2.90;
- Hist31 +34.59 then -26.26;
- ExtraTrees leaf5 +92.31 then -99.60.

Decision: **incumbent retained**.

### T-1

Development-eligible:

- `ablate-rest_congestion`;
- `ablate-capacity`.

Selected `ablate-rest_congestion`:

- 2022/23 +63.47;
- 2023/24 +11.97;
- mean +37.72.

Frozen references:

- 2024/25 **-38.36** — worse;
- 2025/26 +25.26;
- mean **-6.55** — worse.

Do not post-hoc select `ablate-capacity` from reference behavior.

Decision: **incumbent retained**.

## Current historical candidate state after model-grid work

| Horizon | Historical candidate |
|---|---|
| T-30 | current incumbent |
| T-14 | current incumbent |
| T-7 | **frozen `hist31-leaf20-l2-1`** |
| T-3 | current incumbent |
| T-1 | current incumbent |

No production runtime has changed.

## Next a2 — historical residual / club calibration

This is the remaining materially different historical hypothesis worth testing before declaring a2 sufficiently exhausted.

Question:

> After the correct rolling horizon model has made its PIT prediction, does a stable cross-season home-club residual remain that can improve future matches without memorizing clubs or leaking target-season outcomes?

### Required design

For every historical scored match and horizon:

`residual = actual attendance - rolling model prediction`

or normalized:

`residual_ratio = residual / capacity`

The model used to generate historical residuals must be the correct rolling historical candidate available under the experiment contract:

- T-30/T-14/T-3/T-1: current incumbent family;
- T-7: keep `hist31-leaf20-l2-1` estimator config frozen and treat calibration as a separate layer.

### Candidate calibration forms

Predeclare a small set such as:

- no calibration;
- home-club mean residual with shrinkage;
- home-club median residual with shrinkage;
- normalized residual mean/median;
- empirical-Bayes-style shrinkage toward league zero;
- bounded correction as a fraction of verified capacity.

Do not perform unrestricted per-club offsets.

### PIT / leakage rule

For a target match, club calibration may use only residuals from matches completed before that target forecast timestamp.

Target-season outcomes after that timestamp cannot enter the calibration state.

### Selection

Use rolling development folds and require consistent improvement, analogous to the unresolved-horizon multi-fold protocol.

Reference seasons cannot choose shrinkage/cap parameters.

### Mandatory diagnostics

- MAE / median / p90 / bias / WAPE;
- worst-event degradation;
- exact worst event;
- correction magnitude distribution;
- club-specific improvements/worsening;
- low-sample behavior;
- correction vs sample-size relationship;
- percentage of events receiving non-trivial calibration.

### a2 exit after calibration

If a robust calibration signal is found, freeze it separately per horizon and document its exact contract.

If not proven:

> **Treat a2 historical optimization as sufficiently exhausted for current data. Advance to b2 current-season regime instead of continuing arbitrary model-grid tuning.**

---

# 2. b2 — Current-season regime

Status: **PARTIALLY TESTED / NOT EXHAUSTED**.

Current Season Adjustment v1 tested raw current-season level vs historical norm and was not proven. That closes only that formulation.

Next after a2:

`residual = actual - expected`

`demand_ratio = actual / expected`

Test current-season-only regime signals:

- mean/median residual;
- EWMA;
- rolling r3/r5;
- robust residual;
- mean/median demand ratio;
- sample-size-aware / hierarchical shrinkage.

Important separation:

- a2 club calibration = persistent cross-season club residual;
- b2 = current-season regime shift.

Do not let 1–2 current-season matches create a large unrestricted correction.

---

# 3. c2 — Match context

Status: **AUDITED + ONE CHALLENGER TESTED / NOT EXHAUSTED**.

Already present PIT-safe:

- opponent draw / pair history;
- PPG;
- GD/game;
- last-5 form;
- table position/gaps;
- top/bottom interactions;
- rest/congestion.

Future Fixture Context v1 is `NOT PROVEN`; do not retune the same formulation on exposed references.

Next safe gaps:

- title/Europe/relegation stakes;
- direct-table-rival / points pressure;
- winning/unbeaten/losing streak sequence;
- rivalry / derby / exceptional opponent draw with deterministic mapping;
- squad availability only with reliable historical PIT timestamped data.

---

# 4. Freeze Pre-Live v2

After a2+b2+c2 freeze exact per horizon:

- model ID;
- feature contract;
- data version;
- training seasons/weights;
- preprocessing;
- hyperparameters;
- calibration;
- seed;
- artifact hash;
- benchmark scorecard;
- limitations.

Do not train d2 against a moving baseline.

---

# 5. d2 — Continuous Live Updater

Status: **NEW LEARNED d2 AFTER PRE-LIVE v2 FREEZE; infrastructure/prospective collection continue now**.

Use:

- earliest usable sales evidence;
- continuous time-to-kickoff;
- meaningful-snapshot refresh;
- trajectory / velocity / acceleration;
- release/coverage handling;
- sector/price-area evidence;
- reliability.

Preferred targets:

- delta vs Pre-Live;
- remaining demand;
- reliability-weighted blend.

T-30/T-14/T-7/T-3/T-1 remain quality checkpoints, not the only update moments.

Frozen C1 v8 remains separate comparator/prospective shadow.

---

# 6. C1 evidence boundary

- raw Live LOEO: 2,929.3;
- conservative synthetic: 2,261.5;
- stress synthetic: 2,498.8;
- four-event chronological Prior: 452.8;
- raw Live: 2,103.7;
- frozen v8: 452.8, PRIOR in 16/16 rows.

No confirmed prospective live MAE until independent completed prospective events are scored.

---

# 7. Mandatory scorecard / CI-CD

Every material experiment persists:

- exact source/data/artifact versions;
- feature definitions and as-of rules;
- train/dev/reference split;
- exclusions;
- preprocessing;
- weights/caps/shrinkage/thresholds;
- hyperparameters/seeds;
- PIT/leakage assertions;
- incumbent/challenger reproduction assertions;
- MAE, median AE, bias, WAPE, p90/tail;
- worst-event degradation and identity;
- event/club breakdowns where meaningful;
- machine-readable artifact;
- run/artifact IDs and hashes;
- explicit decision;
- canonical docs update.

No local-only result. No random snapshot split within event. No synthetic rows as independent evidence. No silent reference retuning. CI green != production promotion.

---

# 8. Immediate next task

**Implement historical residual / club calibration as the final major a2 hypothesis.**

Keep:

- T-7 estimator frozen;
- T-30/T-14/T-3/T-1 current incumbents as historical candidates;
- production unchanged;
- `live_adjustment = 0`.
