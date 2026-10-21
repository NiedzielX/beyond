# Beyond Ticketing — ML Progress Tracking

Last updated: **2026-10-21**

Status: **CANONICAL PLAN / STATUS / TRACKING SNAPSHOT**

Canonical strategy: `ml/MAE_RESEARCH_ROADMAP_V3.md`

## 1. North star

> **Minimize true out-of-sample attendance-forecast MAE at decision-relevant horizons with PIT-safe, reproducible evidence.**

Production remains unchanged:

`live_adjustment = 0`

---

# 2. Current model state

## Global historical / structural core

Current research champion family: **Global Model v2.1**

Data:

- 1,530 Ekstraklasa matches / five complete seasons;
- 7,650 PIT snapshots;
- horizons T-30/T-14/T-7/T-3/T-1.

Architecture:

`club-history baseline + global residual correction`

Historical later-season evidence shows roughly 16–24% MAE improvement versus the baseline across all five horizons. These seasons are now exposed research evidence for future iterations.

## Track A — final24 frozen evidence lane

Package:

`Frozen Pre-Live v2 + P2 reliability * frozen ridge-a10 delta`

Status: **FROZEN / PROSPECTIVE VALIDATION ACTIVE**

Do not mutate from new outcomes.

## Track B — Pre-Live v3

Freeze:

`pre-live-v3-historical-candidate-2026-10-21-v1`

Historical 20-cell mean MAE:

`1934.04 -> 1924.64`, improvement `+9.39 / +0.49%`.

Status: **FROZEN RESEARCH CANDIDATE**

## Track B — early-live long72

Package:

`d2-long72-stage2-p2-observation-maturity-2026-10-21-v1`

Scope:

`24 < hours_to_kickoff <= 72`

Composition:

- frozen T-3 checkpoint anchor;
- `inventory-linear-extrapolation` expert;
- correction cap `±0.10` occupancy;
- `P2-observation-maturity` reliability.

Historical development:

- anchor MAE `3707.14`;
- package MAE `3012.63`;
- uplift `+694.51 / +18.73%`;
- event improvement rate `61.54%`;
- worst event degradation `1488.34`;
- bias `+917.05`.

Status: **FROZEN HISTORICAL RESEARCH PACKAGE / PROSPECTIVE EVIDENCE ACTIVE**

---

# 3. Operating model

## Lane A — Evidence / validation

Goal: estimate true forward performance of frozen packages without contaminating them.

Active work:

- final24 append-only scoring;
- long72 two-phase persistence: forecast before label -> outcome join later;
- event-balanced MAE;
- 24–48h / 48–72h views;
- bias;
- P90 / worst-event degradation;
- event improvement rate;
- explicit evidence class.

## Lane B — MAE R&D

Goal: build challengers that can lower future MAE.

Priority:

1. forward / rolling validation;
2. MAE-native loss tournament;
3. `ΔMAE` uncertainty;
4. new PIT-safe context features;
5. forecast combination;
6. live-ticket incremental correction over the strongest structural model;
7. 72–168h learned model at `N>=9`;
8. club calibration / shrinkage only if it generalizes.

Lane B does not wait for Lane A.

---

# 4. Milestone tracker

| Milestone | Status | Decision / output |
|---|---|---|
| Global historical multi-club core | ✅ DONE | Global Model v2.1 family established |
| Season-blocked PIT benchmark | ✅ DONE | 2024/25 + 2025/26 later-season evidence |
| Pre-Live v2 freeze | ✅ DONE | Track-A anchor frozen |
| final24 d2 Stage 1 | ✅ DONE | `ridge-a10` selected |
| final24 d2 Stage 2 | ✅ DONE | `P2-observation-maturity` frozen |
| Pre-Live v3 freeze | ✅ DONE | v3 research anchor sealed |
| v2-v3 final24 equivalence | ✅ DONE | exact `0.0` seat delta |
| long-horizon export | ✅ DONE | additive `v8-long168` |
| long72 data + anchor freeze | ✅ DONE | 14 events / 130 rows |
| long72 Stage 1 | ✅ DONE | inventory extrapolation lead |
| long72 Stage 2 | ✅ DONE | P2 frozen |
| long72 true prospective plumbing | 🔄 ACTIVE | forecast before label + append-only score |
| canonical rolling/forward validator | 🟡 NEXT | required for all new challengers |
| MAE-native challenger tournament | 🟡 NEXT | q=0.5 / absolute-loss family |
| `ΔMAE` uncertainty | 🟡 NEXT | event/fixture-block intervals |
| next-fixture / cannibalization context | 🟡 NEXT | PIT-safe feature family |
| forecast combination tournament | 🟡 NEXT | mean/median/convex before stacker |
| live-ticket uplift over strong structural model | 🟡 NEXT | residual incremental-value test |
| 72–168h learned model | ⏸ DATA GROWING | 8/9 independent events at last audit |
| production activation | ⛔ NOT READY | historical uplift != promotion evidence |

---

# 5. Validation contract going forward

Historical/global challenger research must use time-respecting views.

Required:

- season-blocked or rolling/expanding-origin folds;
- no future-season rows in an earlier training fold;
- per-horizon reporting;
- persisted fold identities;
- no random row split as headline evidence.

Live-ticket challenger research requires:

- complete-event independence;
- LOEO as a diagnostic where useful;
- forward-event evaluation ordered by kickoff;
- no snapshot-level random split.

2024/25 and 2025/26 are already exposed to research and must never be rebranded as unseen for new variants.

---

# 6. MAE-first challenger backlog

## A. Loss alignment

Test against current residual incumbents:

- median / LAD regression;
- quantile regression `q=0.50`;
- tree boosting with absolute / quantile objective;
- robust residual linear models;
- current HistGBR/XGB controls.

Primary selector: time-respecting MAE.

## B. Context

Highest-priority new family:

- next home match timing;
- next opponent attractiveness;
- next-match importance;
- fixture density;
- previous-home proximity.

Then:

- verified absences;
- match importance / rivalry;
- forecast weather available at PIT;
- PIT-safe media/search/social attention.

All families require ablation against the same incumbent.

## C. Combination

Test in order:

1. mean;
2. median;
3. fixed convex blend;
4. MAE-optimized convex blend within train folds;
5. regularized stacker only if needed.

Component forecasts should represent different information sources, not cosmetic variants of the same model.

## D. Live inventory

Question to answer:

> Does PIT inventory reduce MAE **after** the strongest structural/global forecast has already explained historical demand?

Use residual corrections and reliability/shrinkage.

---

# 7. Long72 evidence contract

For each new eligible event preserve before final attendance is used:

1. event and kickoff identity;
2. frozen T-3 anchor;
3. raw inventory extrapolation;
4. frozen P2 reliability;
5. frozen P2 forecast;
6. `as_of_at` and source snapshot lineage;
7. package/code/data hashes.

After the match:

- attach final attendance;
- compute errors;
- never recompute the historical forecast;
- append to scorecard.

---

# 8. 72–168h

Last audited readiness: `8` independent events beyond 72h.

Predeclared start floor: `N>=9`.

When reached:

1. freeze exact event/as-of identities before model selection;
2. define PIT-safe T-7 anchor transition;
3. start with simple / strongly regularized models;
4. include MAE-native objectives;
5. use event-safe + forward-event validation;
6. create a separate challenger/package ID.

`N=9` starts research. It does not prove sufficiency.

---

# 9. Hard boundaries

Do not:

- mutate frozen packages;
- switch P2 -> P4 post hoc on opened evidence;
- reuse future checkpoints;
- call exposed historical holdouts unseen;
- optimize ensemble weights on final evaluation folds;
- use realized future context at a PIT cutoff;
- perform broad blind hyperparameter sweeps as the default strategy;
- stop R&D while prospective evidence accumulates;
- activate production from historical improvement alone.

---

# 10. Immediate work order

1. **finish long72 immutable forecast materialization + outcome scorer**;
2. **implement rolling/forward validation utilities**;
3. **run MAE-native residual challenger tournament**;
4. **add event/fixture-block `ΔMAE` uncertainty**;
5. **materialize next-fixture / cannibalization features**;
6. **run controlled context ablations**;
7. **run simple forecast-combination tournament**;
8. **measure live-ticket incremental uplift over strongest structural forecast**;
9. continue Track-A/long72 prospective scoring in parallel;
10. trigger long168 research when `N>=9`;
11. keep production unchanged.

## One-line handoff

> **Frozen packages collect evidence in the background. Active development is MAE-first challenger R&D, not waiting: forward validation, MAE-aligned losses, PIT-safe context, forecast combinations and incremental live corrections over the strongest global model.**
