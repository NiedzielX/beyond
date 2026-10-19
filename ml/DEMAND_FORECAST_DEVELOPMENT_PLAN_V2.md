# Beyond Ticketing — Demand Forecast Development Plan v2

Ostatnia aktualizacja: **2026-10-19**

Status: **CANONICAL ACCURACY ROADMAP**

Pełne zasady:

`ml/MODEL_ACCURACY_DEVELOPMENT_INSTRUCTIONS_V2.md`

Aktywny prospective contract:

`ml/D2_PROSPECTIVE_ACCUMULATION_V1.md`

## Główny cel

> **Dopracować model maksymalnie i obniżyć MAE tak daleko, jak pozwalają uczciwe, reprodukowalne dane i walidacja PIT-safe.**

Failed challenger zamyka challenger, nie cały workstream. Exposed holdout nie może być później używany jako unseen validation po tuningu.

## Architektura

Frozen pre-live:

`history + proven current-season regime -> Frozen Pre-Live v2`

Frozen live:

`Frozen Pre-Live v2 + P2 reliability * frozen Ridge delta -> d2 forecast`

## Aktualna kolejność

1. **a2 Historical optimization — COMPLETE / CLOSED FOR CURRENT DATA**
2. **b2 Current-season regime — COMPLETE / FROZEN**
3. **c2 Historical context — COMPLETE FOR CURRENT DATA / NO EXTENSION**
4. **Pre-Live v2 — FROZEN + SEALED**
5. **d2 Stage 0 — COMPLETE**
6. **d2 Stage 1 — COMPLETE / `ridge-a10` FROZEN**
7. **d2 Stage 2 — COMPLETE / `P2-observation-maturity` FROZEN**
8. **Event 5 chronological holdout — COMPLETE**
9. **Prospective accumulation — ACTIVE NOW**
10. **New challenger/retraining cycle — only if repeated prospective evidence justifies it**
11. **Production promotion — evidence-gated, later**

Production remains:

`live_adjustment = 0`

---

# 1. Historical layers — closed for current exposed data

## a2

Final historical bases:

- T-30 Structural Prior;
- T-14 Structural Prior;
- T-7 `hist31-leaf20-l2-1`;
- T-3 Structural Prior;
- T-1 Structural Prior.

T-7 fixed rolling audit improves 4/4 folds, mean `+104.66 MAE`.

The completed a2 investigation already covered ablation, recency, internal/external model families including CatBoost/LightGBM/XGBoost, temporal robustness, unresolved-horizon multi-fold checks and persistent club calibration.

## b2

Frozen policies:

- T-30 `NO_ADJUSTMENT`;
- T-14 `NO_ADJUSTMENT`;
- T-7 `ewma50-resid-k6-cap05-min3`;
- T-3 `ewma50-resid-k2-cap05-min3`;
- T-1 `ewma50-resid-k6-cap05-min3`.

Historical four-fold mean gains:

- T-7 `+51.47`;
- T-3 `+70.44`;
- T-1 `+69.54`.

Event 5 adds a prospective warning that T-1 b2 may sometimes move a high-demand event in the wrong direction. Do not retune from one event.

## c2

Frozen historical contract:

`NO_CONTEXT_ALL_HORIZONS`

Future-only rivalry, verified absences and media/hype remain prospective research when valid PIT data exists.

---

# 2. Frozen Pre-Live v2

Freeze ID:

`pre-live-v2-historical-candidate-2026-10-18-v1`

Reference mean MAE:

| Horizon | MAE |
|---|---:|
| T-30 | 1,867.82 |
| T-14 | 1,809.45 |
| T-7 | 1,691.40 |
| T-3 | 1,682.63 |
| T-1 | 1,661.52 |

No prospective scorer may silently mutate this anchor.

---

# 3. Frozen d2 Stage 1

Expert:

`ridge-a10`

Development set:

`9 events / 30 rows`

Development latest MAE:

`3320.39` vs Frozen-v2 `4128.01`

Development window MAE:

`3619.19`

Worst latest-event degradation:

`4326.90`

Chronos-2 and Chronos-Bolt-small did not improve plain Ridge, therefore:

`TSFM_STAGE1 = NOT_PROVEN_VS_RIDGE`

No same-data fine-tuning of Chronos/Lag-Llama/NeuralProphet.

---

# 4. Frozen d2 Stage 2

Package:

`d2-stage2-p2-observation-maturity-2026-10-19-v1`

Selected policy:

`P2-observation-maturity`

Frozen reliability:

- obs1 `0.25`;
- obs2 `0.60`;
- obs3+ `1.00`;
- time cap >18h `0.75`;
- >12h <=18h `0.90`;
- <=12h `1.00`.

Development metrics:

- latest MAE `3240.99`;
- latest uplift vs Frozen `887.02 / 21.49%`;
- window MAE `3657.65`;
- worst degradation `1081.72`;
- worst degradation reduced by `75%` vs raw Ridge.

Do not retune P2 from future individual events.

---

# 5. Event 5 chronological holdout — COMPLETE

Canonical result:

`ml/results/D2_EVENT5_HOLDOUT_V1_2026-10-19.md`

Event:

Lech Poznań vs Korona Kielce, actual `37,407`.

| Layer | Latest error | Window MAE |
|---|---:|---:|
| Structural T-1 base | 7,669.07 | n/a |
| Frozen Pre-Live v2 | 9,832.52 | 9,832.52 |
| Raw Ridge | **6,652.81** | **6,170.35** |
| P2 | **6,652.81** | 7,263.16 |
| Persisted C1 v8 policy | 7,669.07 | 7,669.07* |

`*` slightly different sampling contract for the window metric.

Key findings:

1. d2 materially improved a severe Frozen-v2 miss;
2. d2 latest beat persisted C1 v8 policy by `1,016.26 seats`;
3. P2 early conservatism reduced useful early Ridge corrections on this event but matched Ridge at the mature final row;
4. b2 moved the pre-live anchor down by `2,163.45 seats`, worsening its error by the same amount versus Structural T-1 base.

Decision:

`HOLDOUT_COMPLETE_KEEP_D2_FROZEN_PROSPECTIVE_ACCUMULATION`

---

# 6. Prospective accumulation — ACTIVE NOW

Contract:

`ml/D2_PROSPECTIVE_ACCUMULATION_V1.md`

Every new eligible completed event must be scored append-only without retraining.

Persist separately:

1. Structural T-1 base;
2. Frozen Pre-Live v2 / b2;
3. raw frozen Ridge;
4. frozen P2;
5. genuine persisted pre-outcome C1 comparator where available.

Track per event:

- latest AE;
- trajectory/window MAE;
- b2 incremental contribution;
- Ridge incremental contribution;
- P2 incremental contribution;
- correction direction/magnitude;
- reliability trajectory;
- data-quality warnings.

Track cumulatively:

- mean/median latest AE;
- window MAE;
- bias;
- p90/worst event;
- event improvement rate;
- component contribution distributions.

## Hypotheses to monitor

### H1 — b2 negative overreaction

Potential hypothesis:

`same-season residual regime may overreact negatively on some high-demand Lech matches`

Status:

`NOT PROVEN — ONE PROSPECTIVE SIGNAL`

### H2 — P2 early conservatism cost

Potential hypothesis:

`P2 may sacrifice useful early correction on some events while reducing tail risk overall`

Status:

`NOT PROVEN AS A SYSTEMATIC PROBLEM — ONE HOLDOUT OBSERVATION`

Do not tune either hypothesis now.

---

# 7. New challenger / retraining gate

A new cycle starts only when:

1. materially more independent prospective events exist;
2. a repeated interpretable failure is visible;
3. the new hypothesis is declared before tuning;
4. the current frozen package remains benchmark;
5. a new train/development/forward split is declared;
6. exposed prospective events are labeled honestly.

No gradual event-by-event mutation of the frozen package.

---

# 8. Production promotion gate

Production promotion requires materially more independent prospective events than the single event-5 holdout.

Require:

- positive aggregate latest/window uplift;
- acceptable tail risk;
- no unresolved systematic component failure;
- reproducible frozen package;
- explicit reviewed decision.

Until then:

`live_adjustment = 0`
