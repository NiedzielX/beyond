# Beyond Ticketing — Demand Forecast Development Plan v2

Ostatnia aktualizacja: **2026-10-18**

Status: **CANONICAL ACCURACY ROADMAP**

Pełne zasady eksperymentów, walidacji i CI/CD:

`ml/MODEL_ACCURACY_DEVELOPMENT_INSTRUCTIONS_V2.md`

## Główny cel

> **Dopracować model maksymalnie i obniżyć MAE tak daleko, jak pozwalają uczciwe, reprodukowalne dane i walidacja PIT-safe.**

Failed challenger zamyka challenger, nie workstream. Exposed references nie służą do ratowania kandydatów, którzy nie przeszli zamrożonego protokołu development.

## Architektura

### Frozen Pre-Live v2 historical candidate

`history + proven current-season regime -> frozen pre-live anchor`

Historical c2:

`NO_CONTEXT_ALL_HORIZONS`

Forward-only context remains prospective shadow.

### d2 Continuous Live Updater

`frozen Pre-Live v2 + live trajectory + inventory + time-to-kickoff + reliability -> live delta / revised P50`

## Aktualna kolejność

1. **a2 — Historical optimization — COMPLETE**
2. **b2 — Current-season regime — COMPLETE**
3. **c2 — Historical match context — SUFFICIENTLY EVALUATED / NO EXTENSION**
4. **Pre-Live v2 historical candidate — FROZEN + SEALED**
5. **d2 — Continuous Live Updater — ACTIVE**

Frozen C1 v8 prospective scoring trwa równolegle i nie jest automatycznie retunowany.

---

# 0. Production boundary

Production bundle:

`structural-prior-runtime-v1-frozen-2026-10-15-t1`

Production remains:

`live_adjustment = 0`

Historical research candidates do not automatically replace production runtime.

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

No stable replacement was proven for T-30/T-14/T-3/T-1 under stricter multi-fold selection.

Persistent cross-season club calibration was tested under two fixed formulations and rejected.

Rule:

> Do not reopen a2 feature/model/recency/calibration grids on the same exposed seasons without materially new data or a materially new hypothesis.

---

# 2. b2 — Current-season regime

Status: **COMPLETE FOR CURRENT HISTORICAL DATA / FROZEN INTO PRE-LIVE V2**.

Successful formulation:

`same-season actual - our own earlier Pre-Live expectation`

Critical PIT rule:

`prior home match kickoff + 3h <= current forecast as_of`

Frozen b2 policy:

| Horizon | b2 layer |
|---|---|
| T-30 | `NO_ADJUSTMENT` |
| T-14 | `NO_ADJUSTMENT` |
| T-7 | `ewma50-resid-k6-cap05-min3` |
| T-3 | `ewma50-resid-k2-cap05-min3` |
| T-1 | `ewma50-resid-k6-cap05-min3` |

Activation requires at least **3 earlier completed same-season home matches**.

Final fixed temporal audit:

| Horizon | Mean 4-fold MAE improvement | Minimum fold improvement |
|---|---:|---:|
| T-7 | **+51.47** | +7.15 |
| T-3 | **+70.44** | +21.18 |
| T-1 | **+69.54** | +24.66 |

Known risk:

- max harmful event regression: +2,760.55 seats;
- club-level uplift is heterogeneous;
- correction cap remains +/-5% verified capacity.

Rule:

> No further b2 tuning against the same historical references.

---

# 3. c2 — Historical match context

Status: **SUFFICIENTLY EVALUATED FOR CURRENT DATA / NO HISTORICAL CONTEXT EXTENSION**.

Canonical result:

`ml/results/CONTEXT_EXTENSION_V2_2026-10-18.md`

Incremental baseline was the frozen a2+b2 stack.

Context Extension v2 tested:

- PIT-safe winning/unbeaten/losing sequences;
- recent points acceleration;
- home-specific sequence signals;
- current-table stakes/pressure;
- sequence + stakes.

Result:

- T-30/T-14/T-7/T-3 -> `NO_CONTEXT` on development;
- T-1 -> development selected `sequence_stakes`, but references worsened by **36.97 MAE** on average.

Historical c2 contract:

`NO_CONTEXT_ALL_HORIZONS`

Forward-only context remains prospective research/shadow:

- rivalry/derby registry;
- verified absences;
- media attention / mention acceleration;
- future search/social/hype signals when valid sources exist.

Do not reconstruct those features historically from later knowledge.

---

# 4. Pre-Live v2 historical freeze

Status: **COMPLETE / SEALED**.

Freeze ID:

`pre-live-v2-historical-candidate-2026-10-18-v1`

Canonical manifest:

`ml/artifacts/pre_live_v2_historical_candidate_v1/manifest.json`

Manifest SHA256:

`44c911d1ac8b1bf6870ed31e1a636b9b8374d8c8da2d57ba3b4fb5b4aaba4d3c`

Result:

`ml/results/PRE_LIVE_V2_HISTORICAL_FREEZE_V1_2026-10-18.md`

Seal run:

`39166115174`

Artifact ID:

`12150457295`

Artifact ZIP SHA256:

`c2b7440ae84a96c474992ecbb07c4bb43f319a9e021fc370a82f439b6edd5dd1`

Freeze gate:

- 20/20 exact horizon-season MAE cells reproduce at `1e-9`;
- committed manifest is byte-for-byte identical to freshly generated manifest;
- source/evidence hashes are persisted;
- production remains unchanged.

Frozen contract:

| Horizon | Historical base | b2 | c2 | Reference mean MAE |
|---|---|---|---|---:|
| T-30 | `structural-prior-runtime-v1-t30-extra-full` | none | none | 1,867.82 |
| T-14 | `structural-prior-runtime-v1-t14-hist-base` | none | none | 1,809.45 |
| T-7 | `hist31-leaf20-l2-1` | `ewma50-resid-k6-cap05-min3` | none | **1,691.40** |
| T-3 | `structural-prior-runtime-v1-t3-hist-full` | `ewma50-resid-k2-cap05-min3` | none | **1,682.63** |
| T-1 | `structural-prior-runtime-v1-t1-hist-full` | `ewma50-resid-k6-cap05-min3` | none | **1,661.52** |

No d2 learned model should mutate or silently refit this anchor.

---

# 5. d2 — Continuous Live Updater

Status: **ACTIVE NOW**.

## Objective

Learn the incremental live correction to the frozen Pre-Live v2 candidate:

`live_delta = actual_attendance - frozen_pre_live_v2_p50`

Compare with capacity-normalized target:

`live_delta_occ = actual/capacity - frozen_pre_live_v2_p50/capacity`

Final candidate:

`d2_p50 = clip(frozen_pre_live_v2_p50 + predicted_live_delta, 0, capacity)`

## Modelling shape

Start with **one continuous updater** using continuous time-to-kickoff.

Do not split the small live evidence into five tiny T-30/T-14/T-7/T-3/T-1 models unless later evidence proves that splitting helps.

The named horizons remain evaluation checkpoints, not separate model boundaries.

## Training unit and independence

Rows:

`event x as_of_timestamp`

Independent validation unit:

`event`

Rules:

- all snapshots from one event stay in one fold;
- LOEO is primary while N events is small;
- use event-balanced weighting and/or regularized cadence;
- no random row-level train/test split;
- no future snapshots;
- source Pre-Live forecast must identify the frozen v2 lineage.

## Frozen anchor requirement

Primary d2 leaderboard must use:

`pre-live-v2-historical-candidate-2026-10-18-v1`

If a monitored event cannot receive that exact anchor because it is outside model domain or historical replay is unavailable:

- label the fallback explicitly;
- do not silently substitute legacy forecast;
- exclude incompatible fallback rows from the primary frozen-v2 leaderboard where necessary.

## Initial d2 features

Reuse existing PIT-safe C1/live infrastructure before adding new feature families.

### Anchor / time

- frozen Pre-Live v2 P50;
- expected occupancy;
- capacity;
- continuous hours/days to kickoff;
- checkpoint labels only as diagnostics.

### Inventory / trajectory

- normalized availability/inventory;
- observed progress;
- expected progress;
- trajectory gap;
- 6h / 24h / 72h / 7d velocity where available;
- acceleration;
- latest change rate;
- signal readiness/confidence.

### Sector aggregates

- underperforming/outperforming sector share;
- worst/median sector gap;
- sector-gap dispersion;
- sector velocity dispersion;
- remaining availability concentration;
- release/replenishment activity;
- coverage changes.

### Price evidence

Use Roboticket price observations only when PIT-valid and coverage semantics are explicit. Missing price coverage is not a zero-demand signal.

## d2 first tournament

Primary baselines:

1. frozen Pre-Live v2 / zero live correction;
2. training-fold bias-only correction;
3. simple trajectory extrapolation.

Focused learned candidates:

- Ridge;
- Huber / robust linear;
- HistGradientBoosting with strong regularization;
- optionally one shallow tree ensemble if sample size supports it.

Do not start with a large model zoo.

## Primary validation

LOEO across independent completed live events.

Report per held-out event and aggregate:

- frozen Pre-Live v2 MAE;
- d2 MAE;
- absolute MAE uplift;
- relative MAE uplift;
- median AE;
- bias;
- event improvement rate;
- worst-event degradation;
- occupancy error;
- performance by time-to-kickoff window;
- model revision magnitude.

Do not count multiple timestamps from the same held-out event as independent successes.

## C1 v8 relationship

Frozen package:

`c1-shadow-v8-frozen-2026-10-16-n9`

C1 v8 remains `EXPERIMENTAL_SHADOW` and continues prospective scoring unchanged.

Use C1 infrastructure and evidence as:

- a data pipeline to reuse;
- a frozen benchmark/expert;
- a source of lessons about small-N live reliability.

Do not silently modify v8 thresholds/artifact while developing d2.

## d2 Stage 1 deliverables

1. frozen-v2 compatible live replay dataset;
2. exact PIT audit and event lineage;
3. event-balanced continuous live feature table;
4. small predeclared model tournament;
5. LOEO scorecard vs frozen Pre-Live v2;
6. tail/revision diagnostics;
7. machine-readable artifact + result doc;
8. explicit decision whether a learned d2 candidate is strong enough for prospective shadow.

## Promotion boundary

Historical/LOEO uplift alone does not modify production.

Prospective shadow with immutable pre-outcome predictions remains required before any production promotion.

Production stays:

`live_adjustment = 0`
