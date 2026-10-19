# Beyond Ticketing — Demand Forecast Development Plan v2

Ostatnia aktualizacja: **2026-10-19**

Status: **CANONICAL ACCURACY ROADMAP**

Pełne zasady eksperymentów, walidacji i CI/CD:

`ml/MODEL_ACCURACY_DEVELOPMENT_INSTRUCTIONS_V2.md`

## Główny cel

> **Dopracować model maksymalnie i obniżyć MAE tak daleko, jak pozwalają uczciwe, reprodukowalne dane i walidacja PIT-safe.**

Failed challenger zamyka challenger, nie cały workstream. Nowy holdout służy do walidacji zamrożonej decyzji, a nie do retroaktywnego tuningu.

## Architektura

### Frozen Pre-Live v2

`history + proven current-season regime -> frozen pre-live anchor`

Historical c2:

`NO_CONTEXT_ALL_HORIZONS`

### d2 Continuous Live Updater

Po Stage 1 aktualny kierunek to:

`frozen Pre-Live v2 + reliability * frozen Ridge live delta -> revised forecast`

## Aktualna kolejność

1. **a2 — Historical optimization — COMPLETE**
2. **b2 — Current-season regime — COMPLETE**
3. **c2 — Historical context — COMPLETE FOR CURRENT DATA / NO EXTENSION**
4. **Pre-Live v2 historical candidate — FROZEN + SEALED**
5. **d2 Stage 0 — Frozen-v2 replay compatibility — COMPLETE**
6. **d2 Stage 1 — learned live-residual tournament — COMPLETE**
7. **d2 Stage 2 — reliability / tail-risk gating — ACTIVE NOW**
8. **Event 5 Lech–Korona chronological holdout — AFTER STAGE-2 FREEZE**
9. **Prospective accumulation — ongoing after holdout**
10. **Production promotion — evidence-gated, later**

Frozen C1 v8 scoring trwa równolegle i pozostaje niezmieniony.

---

# 0. Production boundary

Production bundle:

`structural-prior-runtime-v1-frozen-2026-10-15-t1`

Production remains:

`live_adjustment = 0`

Research candidates do not automatically replace production runtime.

---

# 1. a2 — Historical optimization

Status: **COMPLETE FOR CURRENT DATA**.

Frozen historical base:

| Horizon | a2 base |
|---|---|
| T-30 | Structural Prior incumbent |
| T-14 | Structural Prior incumbent |
| T-7 | `hist31-leaf20-l2-1` |
| T-3 | Structural Prior incumbent |
| T-1 | Structural Prior incumbent |

T-7 fixed rolling audit improves 4/4 folds, mean **+104.66 MAE**.

Persistent cross-season calibration was tested and rejected.

Rule:

> Do not reopen a2 on the same exposed seasons without materially new data or a materially new hypothesis.

---

# 2. b2 — Current-season regime

Status: **COMPLETE FOR CURRENT HISTORICAL DATA / FROZEN INTO PRE-LIVE V2**.

Frozen b2:

| Horizon | b2 layer |
|---|---|
| T-30 | `NO_ADJUSTMENT` |
| T-14 | `NO_ADJUSTMENT` |
| T-7 | `ewma50-resid-k6-cap05-min3` |
| T-3 | `ewma50-resid-k2-cap05-min3` |
| T-1 | `ewma50-resid-k6-cap05-min3` |

All non-zero policies activate only after at least 3 earlier completed same-season home matches.

Final fixed four-fold mean gains:

- T-7: **+51.47 MAE**;
- T-3: **+70.44**;
- T-1: **+69.54**.

Rule:

> No further b2 tuning against the same historical references.

---

# 3. c2 — Historical context

Status: **SUFFICIENTLY EVALUATED / NO HISTORICAL CONTEXT EXTENSION**.

Historical contract:

`NO_CONTEXT_ALL_HORIZONS`

Forward-only context remains prospective research/shadow:

- rivalry/derby;
- verified absences;
- media attention;
- search/social/hype when valid PIT sources exist.

Do not reconstruct those historically from later knowledge.

---

# 4. Frozen Pre-Live v2

Freeze ID:

`pre-live-v2-historical-candidate-2026-10-18-v1`

Historical reference mean MAE:

| Horizon | MAE |
|---|---:|
| T-30 | 1,867.82 |
| T-14 | 1,809.45 |
| T-7 | **1,691.40** |
| T-3 | **1,682.63** |
| T-1 | **1,661.52** |

No d2 model may silently mutate this anchor.

---

# 5. d2 Stage 0 — COMPLETE

Stage-0 contract replays the frozen C1 live lineage against exact Frozen Pre-Live v2.

Frozen development lineage:

- 9 events;
- 30 final-24h rows;
- exact anchor lineage on every row.

Status:

`FROZEN_V2_EXACT_COMPATIBILITY_READY`

---

# 6. d2 Stage 1 — COMPLETE

Canonical result:

`ml/results/D2_STAGE1_MODEL_TOURNAMENT_V1_2026-10-19.md`

Research lead:

`ridge-a10`

Selection protocol:

- exact frozen 9-event / 30-row development set;
- event-level LOEO;
- event-balanced weights;
- no random row split;
- exact Frozen-v2 anchor;
- no production write.

## Stage-1 scorecard

| Candidate | Latest MAE | Latest uplift vs Frozen v2 | Window MAE | Window uplift |
|---|---:|---:|---:|---:|
| Frozen v2 | 4,128.01 | 0.00 | 4,128.01 | 0.00 |
| Inventory extrapolation | 3,869.68 | +258.33 | 3,701.05 | +426.97 |
| **Ridge `alpha=10`** | **3,320.39** | **+807.62** | **3,619.19** | **+508.83** |
| Ridge + Chronos-2 | 3,428.25 | +699.76 | 3,645.19 | +482.82 |
| Ridge + Bolt-small | 3,428.08 | +699.93 | 3,658.58 | +469.43 |

Ridge relative latest-row improvement:

**19.56%**

Ridge relative event-balanced window improvement:

**12.33%**

Latest event improvement rate:

**66.7%**

Critical risk:

**worst latest-event degradation = +4,326.90 seats**

Decision:

> `ridge-a10` advances as research lead. Raw Ridge does not advance to production or unrestricted prospective activation because tail risk remains too high.

Canonical run:

`39256585339`

Artifact ID:

`12187853899`

Artifact ZIP SHA256:

`c494ba609f3c9ee376e8285a9af975cc78d813337bd219fbaf94c7a9a336c6de`

---

# 7. TSFM / Chronos decision

Stage 1 tested zero-shot:

- Chronos-2;
- Chronos-Bolt-small.

They forecast only causal public inventory trajectory, not final attendance directly.

Both improve Frozen v2 when added to Ridge, but both lose to plain Ridge.

Decision:

`TSFM_STAGE1 = NOT_PROVEN_VS_RIDGE`

Do not fine-tune Chronos or add Lag-Llama / NeuralProphet on the same 9-event development set.

Reopen the family only with materially more independent trajectory events or a materially new predeclared hypothesis.

---

# 8. d2 Stage 2 — ACTIVE NOW

Canonical contract:

`ml/D2_STAGE2_RELIABILITY_GATING_V1.md`

## Objective

Stage 2 does **not** search for another prediction model.

It freezes Stage-1 `ridge-a10` and answers:

> **When should Ridge be trusted, shrunk, or ignored in favor of Frozen Pre-Live v2?**

Preferred architecture:

`final = frozen_v2 + reliability * ridge_delta`

with:

`0 <= reliability <= 1`

## Frozen Stage-1 expert

Do not change during Stage 2:

- Ridge `alpha=10`;
- Stage-1 feature contract;
- preprocessing;
- event-balanced weighting;
- target;
- +/-10pp occupancy correction cap.

A change to Ridge itself creates a new model challenger and is not Stage-2 policy tuning.

## Compact Stage-2 policy family

Predeclared comparison:

1. `P0` Frozen-v2 only;
2. `P1` raw Ridge;
3. `P2` observation-maturity gate;
4. `P3` disagreement/correction-magnitude shrinkage;
5. `P4` data-quality gate;
6. `P5` compact combined reliability policy.

Do not create a large threshold zoo.

## Reliability inputs

Use only PIT-safe live signals such as:

- valid observation count;
- observation span;
- hours to kickoff;
- trajectory stability;
- velocity / acceleration;
- disagreement between Ridge and Frozen v2;
- proposed correction size;
- release/replenishment flags;
- coverage-change flags;
- unexplained inventory increases;
- data-gap / feature-quality state.

## Stage-2 selection objective

A policy should:

1. improve latest and window MAE vs Frozen v2;
2. retain a meaningful share of raw Ridge uplift;
3. materially reduce raw Ridge worst-event degradation;
4. avoid systematic bias;
5. remain stable under event-level LOEO;
6. remain simple enough to reproduce and explain.

Development remains restricted to the original 9 events / 30 rows.

---

# 9. Reserved event-5 holdout

New append-only completed event:

- ID `5`;
- Lech Poznań vs Korona Kielce;
- kickoff `2026-10-18T15:30:00Z`;
- actual attendance `37,407`;
- capacity `43,269`;
- 4 live rows.

It was **not** used for Stage-1 selection.

It must **not** be used for Stage-2 policy selection.

Only after Stage 2 is frozen, score once:

1. Frozen Pre-Live v2;
2. frozen raw Ridge;
3. frozen Stage-2 governed Ridge;
4. frozen C1 v8 where compatible.

No retuning after opening event 5.

---

# 10. Prospective accumulation after event 5

After scoring event 5:

- persist the result regardless of outcome;
- continue append-only scoring for every new eligible event;
- keep model/policy frozen during the prospective evidence window;
- do not silently retrain on new outcomes;
- start a separately versioned retraining cycle only when justified by enough new independent events.

---

# 11. Promotion boundary

Historical/LOEO development uplift is insufficient for production promotion.

Production promotion requires:

- materially more genuinely prospective independent completed events;
- positive uplift vs the correct frozen baseline;
- acceptable worst-event/tail risk;
- frozen reproducible model/policy package;
- full CI evidence;
- explicit human-reviewed promotion.

Production remains:

`live_adjustment = 0`
