# Beyond Ticketing — Demand Forecast Development Plan v2

Ostatnia aktualizacja: **2026-10-18**

Status: **CANONICAL ACCURACY ROADMAP**

Pełne zasady eksperymentów, walidacji i CI/CD:

`ml/MODEL_ACCURACY_DEVELOPMENT_INSTRUCTIONS_V2.md`

## Główny cel

> **Dopracować model maksymalnie teraz i obniżyć MAE tak daleko, jak pozwalają uczciwe, reprodukowalne dane i walidacja PIT-safe.**

Nie optymalizujemy developmentu pod zamykanie roadmapy. Failed challenger zamyka challenger, nie workstream. Niższe mean MAE nie wystarcza do promocji, jeśli challenger ma materialny tail risk, bias lub niestabilność.

## Docelowa architektura

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

`a2 -> b2 -> c2 -> freeze Pre-Live v2 -> d2`

Frozen C1 v8 prospective scoring trwa równolegle.

---

# 0. Production incumbent

Current Structural Prior bundle:

`structural-prior-runtime-v1-frozen-2026-10-15-t1`

| Horizon | 2024/25 MAE | 2025/26 MAE |
|---|---:|---:|
| T-30 | 1,889.4 | 1,846.3 |
| T-14 | 1,748.5 | 1,870.4 |
| T-7 | 1,777.7 | 1,802.3 |
| T-3 | 1,661.7 | 1,775.1 |
| T-1 | 1,651.7 | 1,742.8 |

Evidence base:

- 5 seasons;
- 1,530 matches;
- 7,650 PIT horizon rows;
- verified capacity coverage 100%.

Production remains:

`live_adjustment = 0`

The current PIT feature store already includes substantial a/b/c information: historical demand, current-season demand, opponent/pair history, sporting form, table context, calendar/timing and rest/congestion. New work must add information or materially improve representation/modeling rather than duplicate existing fields.

---

# 1. a2 — Historical / Structural Prior optimization

Status: **ACTIVE / T-7 STAGES 1–5 COMPLETE / T-7 HISTORICAL CANDIDATE FROZEN / OTHER HORIZONS NEXT**.

Goal:

> **Build the strongest reproducible pre-live baseline before b2/c2 and before the new learned live layer.**

## Stage 1 — Pre-Live Baseline Optimization v1 — COMPLETED

Evidence:

`ml/results/PRE_LIVE_BASELINE_OPTIMIZATION_V1_2026-10-18.md`

Run: `39156711796`

Protocol:

- train 2021/22 + 2022/23;
- select on 2023/24 by MAE;
- after selection score unchanged on rolling 2024/25 and 2025/26 references;
- only incumbent + development-selected candidate on references;
- exact incumbent assertions;
- one change at a time;
- full MAE/tail scorecard;
- no automatic promotion.

Result:

| Horizon | Dev-selected candidate | Mean incumbent MAE | Mean selected MAE | Improvement | Decision |
|---|---|---:|---:|---:|---|
| T-30 | `ablate-rest_congestion` | 1,867.82 | 1,864.11 | +3.71 | retain incumbent |
| T-14 | `recency-linear_075` | 1,809.45 | 1,798.25 | +11.19 | mixed; retain incumbent |
| T-7 | `model-hist_absolute_31` | 1,789.98 | 1,721.18 | **+68.81** | material lead |
| T-3 | incumbent | 1,718.39 | 1,718.39 | 0.00 | retain incumbent |
| T-1 | `recency-linear_075` | 1,697.28 | 1,707.36 | -10.07 | retain incumbent |

T-7 Hist31 stage-1 lead:

- development +97.36 MAE;
- 2024/25 +105.55;
- 2025/26 +32.06;
- mean reference +68.81;
- worst degradations +3,685.74 / +4,233.11.

Conclusion: T-7 was the only material Stage-1 opportunity.

## Stage 2 — T-7 fixed blend robustness — COMPLETED

Evidence:

`ml/results/T7_HIST31_BLEND_ROBUSTNESS_V1_2026-10-18.md`

Run: `39157403710`

Predeclared alpha:

`0 / .25 / .50 / .75 / 1.0`

Blend:

`prediction = (1-alpha) * incumbent + alpha * Hist31`

Selection:

- 2023/24 development MAE only;
- exact tie -> lower alpha;
- references cannot choose alpha.

Development selected:

`alpha = 1.00`

Signal:

`FULL_HIST31_SELECTED_NO_BLEND_ROBUSTNESS_GAIN`

Conclusion:

- fixed blending is only a linear MAE/tail trade-off;
- development wants full Hist31;
- choosing smaller alpha from reference behavior would be holdout retuning;
- no production change.

## Stage 3 — T-7 Robust Estimator v1 — COMPLETED

Evidence:

`ml/results/T7_ROBUST_ESTIMATOR_V1_2026-10-18.md`

Run: `39157926927`

Only estimator regularization changed; baseline/features/target/weights/splits stayed fixed.

Development winner:

`hist31-leaf20-l2-1`

Exact config:

- HistGradientBoostingRegressor;
- `loss=absolute_error`;
- learning rate 0.04;
- 300 iterations;
- max leaf nodes 31;
- `min_samples_leaf=20`;
- L2 1.0;
- seed 42.

Only material change from stage-1 Hist31:

`min_samples_leaf: 10 -> 20`

### Development

- incumbent: 2,476.82;
- selected: **2,317.34**;
- improvement: **+159.48**;
- median AE: 1,103.63;
- bias: -31.75.

### 2024/25

- incumbent: 1,777.69;
- selected: **1,650.97**;
- improvement: **+126.73**;
- median AE: 926.00;
- p90 AE: 4,396.22;
- bias: +13.05;
- worst degradation: **+4,094.16** on `Śląsk Wrocław – Legia`.

### 2025/26

- incumbent: 1,802.28;
- selected: **1,773.80**;
- improvement: **+28.48**;
- median AE: 1,051.76;
- p90 AE: 3,753.08;
- bias: -5.43;
- worst degradation: **+3,700.56** on `Lechia Gdańsk – Legia`.

Aggregate:

- incumbent mean reference MAE: 1,789.98;
- selected: **1,712.38**;
- improvement: **+77.60**;
- improves both references: true;
- tail fully solved: false.

Signal:

`REGULARIZED_WINNER_POSITIVE_MEAN_TAIL_NOT_SOLVED`

## Stage 4 — materially different T-7 estimator families — COMPLETED

Evidence:

`ml/results/T7_EXTERNAL_MODEL_FAMILY_V1_2026-10-18.md`

Run: `39158519963`

Artifact ID: `12147987319`

Pinned runtime included:

- CatBoost 1.2.10;
- LightGBM 4.7.0;
- XGBoost 3.4.1.

Frozen dimensions:

- T-7;
- `baseline_season`;
- current T-7 base feature contract;
- incumbent preprocessing;
- capacity-normalized residual target;
- uniform season weights;
- seed 42;
- same train/dev/reference split.

Development ranking:

| Rank | Candidate | Family | MAE | Improvement vs incumbent |
|---:|---|---|---:|---:|
| 1 | **`hist31-leaf20-l2-1`** | HGB | **2,317.34** | **+159.48** |
| 2 | `lightgbm-l1-leaves15-l2-5` | LightGBM | 2,323.57 | +153.24 |
| 3 | `lightgbm-l1-leaves31-l2-5` | LightGBM | 2,369.53 | +107.29 |
| 4 | `catboost-mae-depth4-l2-5` | CatBoost | 2,387.27 | +89.54 |
| 5 | `catboost-mae-depth6-l2-5` | CatBoost | 2,417.66 | +59.16 |
| 6 | `xgboost-l1-depth3-l2-5` | XGBoost | 2,445.52 | +31.29 |
| 7 | `xgboost-l1-depth2-l2-5` | XGBoost | 2,446.41 | +30.40 |

The internal HGB remained the development winner. Reference scoring therefore reproduced Stage 3:

- 2024/25: 1,650.97, +126.73;
- 2025/26: 1,773.80, +28.48;
- mean reference MAE: **1,712.38**;
- mean improvement: **+77.60**.

Decision:

- tested CatBoost/LightGBM/XGBoost variants do not beat Stage-3 HGB on development;
- the LightGBM runner-up cannot be rescued post hoc by reference behavior;
- stop broadening the T-7 estimator zoo without a materially new hypothesis;
- advance the fixed HGB config to temporal robustness.

## Stage 5 — fixed-config broader T-7 temporal robustness — COMPLETED

Evidence:

`ml/results/T7_FIXED_TEMPORAL_ROBUSTNESS_V1_2026-10-18.md`

Run: `39159276055`

Artifact ID: `12148660037`

Artifact ZIP SHA256:

`a8d975d63f8387a14ecb7c7dac0a2da6d1c96b1cc4af1d4d267a2dd70b0c7f2b`

Result JSON SHA256:

`0e3f6720be56dabe358cea00b3ad5edf896e4dc7f71940cb89b400f287621d54`

Fixed candidate:

`hist31-leaf20-l2-1`

No tuning or model selection occurred in Stage 5.

Rolling folds:

| Test season | Evidence role | Incumbent MAE | Challenger MAE | Improvement | Bootstrap P(uplift > 0) | Worst degradation |
|---|---|---:|---:|---:|---:|---:|
| 2022/23 | additional pre-selection historical fold | 2,088.94 | **1,984.99** | **+103.95** | 91.8% | +6,623.99 |
| 2023/24 | development selection season | 2,476.82 | **2,317.34** | **+159.48** | 99.08% | +4,335.66 |
| 2024/25 | exposed reference | 1,777.69 | **1,650.97** | **+126.73** | 99.35% | +4,094.16 |
| 2025/26 | exposed reference | 1,802.28 | **1,773.80** | **+28.48** | 76.04% | +3,700.56 |

Aggregate:

- positive MAE improvement: **4/4 folds**;
- mean fold improvement: **+104.66 MAE**;
- median fold improvement: +115.34;
- minimum fold improvement: +28.48;
- median AE improves in all four folds;
- p90 AE improves in all four folds;
- bias moves closer to zero in all four folds;
- reportable club-season cells improved: **47/72 = 65.28%**.

Remaining risk:

- 2022/23 has a +6,623.99 worst single-event degradation;
- 2025/26 bootstrap CI crosses zero despite positive point MAE improvement;
- event improvement rate is ~53–55%, so benefit is magnitude-driven rather than universal;
- 25/72 reportable club-season cells are not improved.

### Explicit T-7 freeze decision

`hist31-leaf20-l2-1` is the **frozen historical T-7 candidate for Pre-Live v2**.

Freeze means:

- stop T-7 estimator/hyperparameter tuning on the current historical reference set;
- preserve the exact configuration for later b2/c2 integration and future evidence;
- reopen only with genuinely new data or a materially new hypothesis;
- no production replacement from retrospective evidence alone.

Production T-7 remains:

`structural-prior-runtime-v1-t7-gbr-base`

## Remaining a2 — unresolved horizons

Next active target:

- T-30;
- T-14;
- T-3;
- T-1.

Stage-1 evidence is too weak/unstable to justify a champion change:

- T-30: tiny +3.71 mean reference ablation signal;
- T-14: +11.19 mean reference recency signal but mixed seasons;
- T-3: incumbent wins development;
- T-1: development-selected recency degrades mean references by -10.07.

### Required next protocol — multi-fold unresolved-horizon tournament

Improve the selection protocol before adding more complexity.

Use development-era rolling folds where technically valid:

1. train 2021/22 -> validate 2022/23;
2. train 2021/22–2022/23 -> validate 2023/24.

Candidate advancement rules must be predeclared before reference scoring. Preferred default:

- candidate must improve incumbent MAE in **both** development folds to advance;
- rank eligible candidates on mean development MAE improvement;
- include tail/bias diagnostics as mandatory sanity checks;
- deterministic tie-break;
- freeze one candidate per horizon before 2024/25–2025/26 scoring;
- if no candidate clears the development consistency requirement, retain incumbent without looking to references for rescue.

Candidate families should begin with the already-implemented, attributable Stage-1 hypotheses rather than an open-ended model search:

- incumbent;
- feature-group ablations;
- explicit recency weighting;
- the small internal model-family set already defined in Stage 1.

A materially new family may be added later only with explicit rationale and pinned dependencies.

### Residual / club calibration

Still justified later in a2:

- test stable PIT-safe club residual structure;
- shrink low sample sizes;
- avoid memorization;
- evaluate out-of-sample;
- report club and tail behavior.

## Exit condition a2

a2 ends only when:

- feature-group contribution evidence exists;
- sensible recency policies were tested;
- justified model families were compared;
- material leads have robustness/tail analysis;
- per-horizon historical candidate decisions are explicit;
- every production champion change goes through explicit freeze/promotion;
- all artifacts/results/docs are persisted.

---

# 2. b2 — Current-season regime

Status: **PARTIALLY TESTED / NOT EXHAUSTED**.

Current Season Adjustment v1 tested raw current-season level vs historical norm and was not proven. That closes only that formulation.

Next after a2 historical candidates are settled:

## Residual regime index

Use historical PIT incumbent/candidate prediction for prior completed home matches:

`residual = actual - expected`

`demand_ratio = actual / expected`

Test predeclared signals:

- mean / median residual;
- EWMA;
- rolling r3/r5;
- robust residual;
- mean/median demand ratio.

## Reliability / shrinkage

Potential hierarchy:

`club current season -> club historical residual -> league current season -> zero`

Signal strength must depend on sample size. Do not let 1–2 matches cause a large unrestricted correction.

## Season-stage diagnostics

Measure usefulness after:

- 2 home matches;
- 3–5;
- 6+;
- later season.

Exit b2 only after residual-regime, shrinkage and sample-size diagnostics are fully scored.

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

Future Fixture Context v1 tested next-home timing / attractiveness / cannibalization and was `NOT PROVEN`. Do not retune that same formulation on exposed references.

Next candidate gaps:

## Match stakes

- title-race relevance;
- European qualification relevance;
- relegation relevance;
- direct-table-rival signal;
- points-gap pressure;
- late-season importance.

## Sequence-aware form

- winning streak;
- unbeaten streak;
- losing streak;
- recent points acceleration/deceleration;
- home-only streak if justified.

## Rivalry / exceptional draw

Only deterministic maintainable mapping:

- derby;
- rivalry;
- exceptional national opponent draw;
- opponent demand percentile.

No attendance-informed hand labeling.

## Squad context

Only with reliable historical PIT source and known availability timestamp:

- injuries;
- suspensions;
- expected XI;
- key-player availability.

No final/current-state backfill.

---

# 4. Freeze Pre-Live v2

After a2+b2+c2 freeze exact per-horizon:

- model ID;
- feature-contract ID;
- data version;
- training seasons / weights;
- hyperparameters;
- preprocessing;
- calibration;
- seed;
- artifact hash;
- benchmark scorecard;
- limitations.

Do not train learned d2 correction against a moving baseline.

---

# 5. d2 — Continuous Live Updater

Status: **NEW LEARNED d2 AFTER PRE-LIVE v2 FREEZE; live infrastructure/prospective collection continue now**.

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

Frozen C1 v8 remains comparator/prospective shadow and is not retuned into d2.

---

# 6. Current C1 evidence boundary

- raw Live LOEO: 2,929.3;
- conservative synthetic: 2,261.5;
- stress synthetic: 2,498.8;
- four-event chronological Prior: 452.8;
- raw Live: 2,103.7;
- frozen v8: 452.8, PRIOR in 16/16 rows.

Production remains:

`live_adjustment = 0`

No confirmed prospective live MAE until independent prospective completed events are scored.

---

# 7. Mandatory accuracy scorecard

Every material challenger reports at minimum:

- MAE;
- median AE;
- bias;
- WAPE where meaningful;
- p90 AE / tail metric;
- worst-event degradation vs incumbent;
- exact worst-event identity;
- share events improved;
- per-horizon / per-season result;
- per-club where sample permits;
- event count / row count.

Live additionally:

- window MAE;
- latest-row MAE;
- revision rate;
- maximum harmful revision;
- live-use/blend rate;
- conditional quality by observation count / time-to-kickoff.

---

# 8. CI/CD — non-negotiable

Every material experiment:

`code -> tests/checks -> CI -> artifact -> metrics -> result doc -> decision -> canonical docs update`

Persist exact:

- source/data/artifact versions;
- feature definitions;
- as-of rules;
- train/dev/holdout;
- exclusions;
- preprocessing;
- weights/caps/shrinkage/thresholds;
- hyperparameters;
- seeds;
- PIT/leakage assertions;
- incumbent benchmark assertions;
- machine-readable artifact;
- run/artifact IDs and hashes;
- explicit decision.

No local-only canonical result. No random snapshot split within event. No synthetic rows as independent evidence. No silent holdout retuning. CI green != production promotion.

---

# 9. Immediate next task

**Implement a multi-fold unresolved-horizon tournament for T-30 / T-14 / T-3 / T-1.**

Keep:

- T-7 `hist31-leaf20-l2-1` frozen as the historical Pre-Live candidate;
- production runtimes unchanged;
- `live_adjustment = 0`;
- development-only candidate selection before exposed-reference scoring.
