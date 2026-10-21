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

- 1,530 Ekstraklasa matches / five complete seasons;
- 7,650 PIT snapshots;
- horizons T-30/T-14/T-7/T-3/T-1;
- architecture: `club-history baseline + global residual correction`.

Historical later-season evidence shows roughly 16–24% MAE improvement versus the baseline across all five horizons. 2024/25 and 2025/26 are exposed research evidence for future iterations.

## Track A — final24 frozen evidence lane

`Frozen Pre-Live v2 + P2 reliability * frozen ridge-a10 delta`

Status: **FROZEN / PROSPECTIVE VALIDATION ACTIVE**

## Track B — Pre-Live v3

`pre-live-v3-historical-candidate-2026-10-21-v1`

Historical 20-cell mean MAE:

`1934.04 -> 1924.64`, improvement `+9.39 / +0.49%`.

Status: **FROZEN RESEARCH CANDIDATE**

## Track B — early-live long72

Package:

`d2-long72-stage2-p2-observation-maturity-2026-10-21-v1`

Historical development:

- anchor MAE `3707.14`;
- package MAE `3012.63`;
- uplift `+694.51 / +18.73%`;
- event improvement rate `61.54%`;
- worst event degradation `1488.34`;
- bias `+917.05`.

Status: **FROZEN / GENUINE POST-FREEZE EVIDENCE ACTIVE**

True forecast-before-label infrastructure is now operational. See:

`ml/results/D2_LONG72_FORWARD_PROSPECTIVE_V1_2026-10-21.md`

First reproducible prospective events:

- event 10 — Pogoń Szczecin vs Radomiak Radom;
- event 16 — Wisła Kraków vs Raków Częstochowa.

Successful main run:

- run `39667034428`;
- artifact `12376893783`;
- digest `sha256:feca43332445e974652e0ad2e1b59f3f7595d52ff8dea9b3cbbef35f771c594a`.

Both events are still pre-outcome, so prospective MAE is intentionally unavailable.

---

# 3. Operating model

## Lane A — Evidence / validation

Running continuously:

- final24 append-only scoring;
- hourly long72 pre-outcome materialization;
- immutable prediction persistence;
- outcome-only append scoring after attendance exists;
- event-balanced MAE / band / bias / tail diagnostics;
- explicit evidence classes.

Manual bootstrap predictions are retained for audit but excluded from the official Long72 scorecard. Only reproducible pipeline rows are scoreable.

## Lane B — MAE R&D

Does not wait for Lane A.

Current sequence:

1. ✅ canonical rolling / forward validation;
2. 🔄 MAE-native challenger tournament;
3. `ΔMAE` uncertainty;
4. PIT-safe next-fixture / cannibalization features;
5. forecast combination;
6. live-ticket incremental correction over the strongest structural model;
7. 72–168h learned model at `N>=9`;
8. club calibration / shrinkage only if it generalizes.

---

# 4. Milestone tracker

| Milestone | Status | Decision / output |
|---|---|---|
| Global historical multi-club core | ✅ DONE | Global Model v2.1 family established |
| Season-blocked PIT benchmark | ✅ DONE | later-season exposed evidence |
| Pre-Live v2 freeze | ✅ DONE | Track-A anchor frozen |
| final24 d2 Stage 1/2 | ✅ DONE | Ridge/P2 frozen |
| Pre-Live v3 freeze | ✅ DONE | v3 research anchor sealed |
| v2-v3 final24 equivalence | ✅ DONE | exact `0.0` seat delta |
| long-horizon export | ✅ DONE | additive `v8-long168` |
| long72 data + Stage 1/2 | ✅ DONE | inventory/P2 frozen |
| long72 true prospective plumbing | ✅ DONE | forecast-before-label + immutable score path |
| first long72 prospective forecasts | ✅ DONE | events 10 and 16 precommitted before outcome |
| canonical rolling/forward validator | ✅ DONE | reusable temporal-validation-v1 + fold SHA |
| MAE-native challenger tournament | 🔄 ACTIVE NEXT | compare median/quantile challengers vs current MAE incumbents |
| `ΔMAE` uncertainty | 🟡 NEXT | event/fixture-block intervals |
| next-fixture / cannibalization context | 🟡 NEXT | PIT-safe feature family |
| forecast combination tournament | 🟡 NEXT | mean/median/convex before stacker |
| live-ticket uplift over strong structural model | 🟡 NEXT | residual incremental-value test |
| 72–168h learned model | ⏸ DATA GROWING | 8/9 independent events at last audit |
| production activation | ⛔ NOT READY | historical uplift != promotion evidence |

---

# 5. Canonical validation contract

`ml/temporal_validation_v1.py`

For historical/global challengers:

- expanding / rolling groups;
- strict `train_end < test_start`;
- no future-season rows in earlier training folds;
- exact fold identities persisted with deterministic SHA;
- per-horizon/fold/club reporting;
- random row split is not headline evidence.

For live challengers:

- event is the independent unit;
- forward-event folds ordered by kickoff;
- tied kickoff events cannot train each other;
- LOEO may remain diagnostic only.

Common diagnostics now include:

- MAE;
- median AE;
- P90 AE;
- bias;
- RMSE;
- event-balanced MAE where trajectory density differs.

---

# 6. MAE-native challenger work

Important correction to the research framing:

Global Model v2.1 incumbents are already partly MAE-aligned:

- HistGradientBoosting uses `loss="absolute_error"`;
- XGBoost uses `objective="reg:absoluteerror"`.

Therefore the next tournament is **not** a simple MSE -> MAE conversion.

The compact challenger set should test genuinely different median/L1 estimators, including:

- regularized linear median / `QuantileRegressor(q=0.50)`;
- alternative robust median residual estimator(s);
- current HistGBR/XGB absolute-error incumbents as controls.

Primary selector: MAE over the new time-respecting fold contract.

---

# 7. Long72 evidence contract

For every new eligible event preserve before final attendance is used:

1. event / kickoff;
2. source snapshot / `as_of_at`;
3. frozen T-3 Structural Prior;
4. frozen b2 replay state;
5. raw inventory extrapolation;
6. governed Stage-1 forecast;
7. P2 observation index / reliability / final forecast;
8. package / manifest / code lineage.

After the match:

- attach final attendance;
- score only existing reproducible forecasts;
- never reconstruct a missing forecast from the future;
- append score evidence.

---

# 8. 72–168h

Last audited readiness: `8` independent events beyond 72h.

Predeclared research-start floor: `N>=9`.

At `N>=9`: freeze identities first, define PIT-safe T-7 transition, then open a separate challenger cycle. `N=9` starts research; it does not prove adequacy.

---

# 9. Immediate work order

1. **run the MAE-native global residual challenger tournament using temporal-validation-v1**;
2. **add event/fixture-block uncertainty for `ΔMAE`**;
3. **materialize PIT-safe next-fixture / cannibalization features**;
4. run controlled context ablations;
5. run simple forecast-combination tournament;
6. measure live-ticket incremental uplift over the strongest structural forecast;
7. keep final24 + long72 prospective collection running automatically;
8. trigger long168 research when `N>=9`;
9. keep production unchanged.

## One-line handoff

> **Prospective Long72 and canonical temporal validation are operational. Active modelling now moves to a genuinely new MAE-native challenger tournament; frozen evidence collection continues automatically in parallel.**
