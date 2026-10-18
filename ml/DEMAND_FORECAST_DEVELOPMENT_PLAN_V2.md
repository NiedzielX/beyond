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

Status: **ACTIVE / STAGES 1–3 COMPLETE / STAGE 4 NEXT**.

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

Conclusion: T-7 is the only material stage-1 opportunity.

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

Ten predeclared candidates included:

- exact stage-1 Hist31;
- HGB with fewer leaf nodes;
- HGB with larger `min_samples_leaf`;
- stronger HGB L2;
- shallow GradientBoosting with absolute-error loss.

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

### Aggregate

- incumbent mean reference MAE: 1,789.98;
- selected: **1,712.38**;
- improvement: **+77.60**;
- improves both references: true;
- tail improves vs stage-1 Hist31 on both references: false.

Signal:

`REGULARIZED_WINNER_POSITIVE_MEAN_TAIL_NOT_SOLVED`

This is the **lowest T-7 mean reference MAE found so far**.

Decision:

- production T-7 incumbent remains unchanged;
- `hist31-leaf20-l2-1` becomes strongest current MAE challenger;
- no post-hoc selection of another stage-3 candidate from reference behavior;
- stop micro-tuning the same exposed HGB grid.

## Stage 4 — materially different T-7 estimator family — NEXT

Question:

> Can a materially different tabular learner beat or match `hist31-leaf20-l2-1` on development while producing a better reference MAE/tail profile under the same fixed feature/baseline contract?

Keep fixed:

- horizon T-7;
- baseline `baseline_season`;
- T-7 base feature contract;
- capacity-normalized residual target;
- uniform season weights unless explicitly isolated in a separate experiment;
- same development/reference split;
- development-only selection;
- exact incumbent benchmark assertions;
- full scorecard.

Priority model families, only with pinned reproducible runtime:

- CatBoost;
- LightGBM;
- XGBoost;
- another materially different learner only if rationale is explicit.

The current `hist31-leaf20-l2-1` must be included as the strongest internal benchmark challenger alongside the production incumbent.

Candidate count must remain small and predeclared. No open-ended hyperparameter search.

After one development winner is frozen, score only it + production incumbent on references.

Required output:

- MAE;
- median AE;
- p90 AE;
- bias;
- WAPE;
- event improvement rate;
- worst-event degradation;
- exact worst event;
- revision magnitude vs incumbent;
- per-reference result;
- full dependency/runtime versions.

## Stage 5 — fixed-config broader temporal robustness — REQUIRED BEFORE T-7 FREEZE

Any serious T-7 champion candidate after Stage 4 must be evaluated with a fixed configuration across additional valid chronological historical folds/seasons.

This is retrospective robustness evidence, not fresh prospective validation.

Rules:

- candidate config fixed before audit;
- no per-fold hyperparameter reselection;
- no reference-derived threshold tuning;
- explicitly label folds previously used for development/training;
- event-level and tail diagnostics mandatory.

Goal:

> establish whether the T-7 gain is broad and stable enough to justify an explicit champion freeze/promotion decision.

## Remaining a2 after T-7

### Other horizons

- T-30: tiny/unstable ablation signal; incumbent retained.
- T-14: mild mixed recency signal; incumbent retained; no exposed-reference decay tuning.
- T-3: incumbent wins development.
- T-1: recency challenger fails mean references.

Further work is allowed only when it introduces a justified new hypothesis, not repeated tuning of already exposed weak ideas.

### Residual / club calibration

Still justified after model-family work:

- test stable PIT-safe club residual structure;
- shrink low sample sizes;
- avoid memorization;
- evaluate out-of-sample;
- report per-club and tail behavior.

## Exit condition a2

a2 ends only when:

- feature-group contribution evidence exists;
- sensible recency policies were tested;
- justified model families were compared;
- material leads have robustness/tail analysis;
- per-horizon champion decisions are explicit;
- every champion change goes through explicit freeze/promotion;
- all artifacts/results/docs are persisted.

---

# 2. b2 — Current-season regime

Status: **PARTIALLY TESTED / NOT EXHAUSTED**.

Current Season Adjustment v1 tested raw current-season level vs historical norm and was not proven. That closes only that formulation.

Next after a2 freeze:

## Residual regime index

Use historical PIT incumbent prediction for prior completed home matches:

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

**Implement Stage 4: materially different T-7 estimator family comparison.**

Keep production T-7 unchanged.

Include `hist31-leaf20-l2-1` as the strongest internal benchmark challenger and compare it with a small, pinned, predeclared external tabular-model set under the same development-only selection protocol.
