# Beyond Ticketing — Model Accuracy Development Instructions v2

Last updated: **2026-10-19**

Status: **CANONICAL DEVELOPMENT INSTRUCTION**

This file defines how Beyond forecasting development must be conducted.

The objective is not to move through workstreams quickly. The objective is:

> **Reduce forecasting error as far as possible with honest, reproducible, point-in-time-safe evidence before treating the model as mature.**

MAE is the primary development KPI. Tail risk, bias, event independence and prospective evidence remain mandatory safety constraints.

---

## 1. Core architecture

Beyond forecasting is developed as two connected layers.

### Layer 1 — Frozen Pre-Live v2

Conceptually:

`history + current-season regime + historically proven context -> pre-live forecast`

Current historical contract:

- a2 historical optimization frozen;
- b2 same-season residual regime frozen where proven;
- c2 historical extension = `NO_CONTEXT_ALL_HORIZONS`.

Freeze ID:

`pre-live-v2-historical-candidate-2026-10-18-v1`

### Layer 2 — d2 Continuous Live Updater

Current learned expert after Stage 1:

`ridge-a10`

Current target architecture:

`final_forecast(t) = frozen_pre_live_v2(t) + reliability(t) * ridge_delta(t)`

The live layer must learn trustworthy incremental revision relative to the immutable frozen Pre-Live v2 anchor.

---

## 2. Current canonical status

Sequence:

`a2 CLOSED -> b2 CLOSED -> c2 historical CLOSED -> Pre-Live v2 FROZEN -> d2 Stage 0 DONE -> d2 Stage 1 DONE -> d2 Stage 2 ACTIVE`

### a2

Status:

`CLOSED FOR CURRENT HISTORICAL DATA`

Current historical base:

- T-30 Structural Prior;
- T-14 Structural Prior;
- T-7 `hist31-leaf20-l2-1`;
- T-3 Structural Prior;
- T-1 Structural Prior.

T-7 fixed audit improves all 4 rolling folds, mean `+104.66 MAE`.

Do not restart the same a2 grids on the same exposed historical references without materially new data or a materially new hypothesis.

### b2

Status:

`CLOSED FOR CURRENT HISTORICAL DATA / FROZEN INTO PRE-LIVE V2`

Critical PIT rule:

`prior kickoff + 3h <= current forecast as_of`

Frozen non-zero policies:

- T-7 `ewma50-resid-k6-cap05-min3`;
- T-3 `ewma50-resid-k2-cap05-min3`;
- T-1 `ewma50-resid-k6-cap05-min3`.

All activate only after at least 3 earlier completed same-season home matches.

Do not retune b2 against the same exposed references.

### c2 historical

Status:

`SUFFICIENTLY EVALUATED / NO HISTORICAL CONTEXT EXTENSION`

Historical contract:

`NO_CONTEXT_ALL_HORIZONS`

Forward-only rivalry, verified absences, media/hype and similar signals remain prospective research because complete PIT history does not exist.

### Frozen Pre-Live v2

Status:

`SEALED / REPRODUCIBLE / HISTORICAL CANDIDATE ONLY`

Reference mean historical MAE:

- T-30 `1867.82`;
- T-14 `1809.45`;
- T-7 `1691.40`;
- T-3 `1682.63`;
- T-1 `1661.52`.

Freeze reproduces 20/20 horizon-season MAE cells at tolerance `1e-9`.

### d2 Stage 0

Status:

`FROZEN_V2_EXACT_COMPATIBILITY_READY`

Development lineage:

- 9 events;
- 30 final-24h rows;
- exact Frozen-v2 anchor.

### d2 Stage 1

Status:

`COMPLETED / ridge-a10 RESEARCH LEAD`

Canonical result:

`ml/results/D2_STAGE1_MODEL_TOURNAMENT_V1_2026-10-19.md`

Key metrics:

- Frozen-v2 latest MAE `4128.01`;
- Ridge latest MAE `3320.39`;
- improvement `+807.62 seats / 19.56%`;
- Frozen-v2 event-balanced window MAE `4128.01`;
- Ridge window MAE `3619.19`;
- window improvement `+508.83 / 12.33%`;
- latest event improvement rate `66.7%`;
- worst latest-event degradation `+4326.90 seats`.

### d2 Stage 2

Status:

`ACTIVE — RELIABILITY / TAIL-RISK GATING`

Canonical contract:

`ml/D2_STAGE2_RELIABILITY_GATING_V1.md`

Stage 2 freezes Ridge and learns/governs reliability. It is not an open-ended model tournament.

---

## 3. Historical workstream reopening rule

Historical a2/b2/c2 may be reopened only if at least one is true:

- materially new historical data becomes available;
- a materially new hypothesis exists that was not already tested;
- genuine prospective evidence reveals a systematic failure mode that justifies a new challenger;
- previously unavailable PIT-safe context becomes reconstructable without leakage.

Do not reopen old grids because later stages are difficult or because an exposed result can be post-hoc improved.

---

## 4. a2 historical optimization contract

A complete historical optimization investigation may include:

- feature-group ablation;
- season-recency weighting;
- model-family challengers;
- horizon-specific optimization;
- club calibration/hierarchy;
- calibrated ensemble where independently justified.

Allowed model families include where technically appropriate:

- HistGradientBoosting / GradientBoosting;
- ExtraTrees / RandomForest;
- CatBoost;
- LightGBM;
- XGBoost;
- regularized linear/GAM-style models;
- validated ensembles.

Every dependency must be pinned in CI.

Current a2 is closed for the current dataset.

---

## 5. b2 current-season contract

Goal:

> Detect whether the current season is systematically running above or below the model's own prior expectation.

Use same-season residual evidence only when prior matches were genuinely completed by the current forecast as-of.

Low-sample regime signals require shrinkage/maturity gating.

Current frozen b2 supports activation only after at least 3 earlier completed same-season home matches at T-7/T-3/T-1.

Current b2 is historical candidate evidence, not production promotion.

---

## 6. c2 context contract

Goal:

> Explain why a specific match should differ from the club/season baseline.

Do not duplicate existing opponent/pair/form/table/congestion features without evidence.

Historical sequence/stakes extensions were tested and did not survive the frozen protocol.

Never backfill injuries, absences, rivalry, media or hype using later/final-state knowledge.

Forward-only context remains prospective where historical PIT truth is unavailable.

---

## 7. Pre-Live v2 freeze contract

Any frozen pre-live candidate must persist:

- feature contract;
- model family and hyperparameters;
- training protocol;
- weighting/calibration;
- data versions;
- source/artifact hashes;
- per-horizon model IDs;
- exact benchmark cells;
- known limitations.

Current freeze:

`pre-live-v2-historical-candidate-2026-10-18-v1`

Do not silently mutate it during d2 work.

Any material change requires a new explicit freeze version.

---

## 8. d2 Stage-1 expert contract

Stage-1 research lead:

`ridge-a10`

Frozen Stage-1 contract:

- target = `target_live_delta_occupancy`;
- `Ridge(alpha=10.0)`;
- median imputation within training fold;
- missing indicators;
- standardization;
- event-balanced sample weights;
- event-level LOEO;
- raw live correction clipped to +/-10pp occupancy.

Do not retune these during Stage 2.

Changing Ridge alpha, feature set, preprocessing, target or cap creates a new model challenger/version outside the Stage-2 policy comparison.

---

## 9. Time-series foundation models

Stage 1 tested:

- `amazon/chronos-2`;
- `amazon/chronos-bolt-small`.

Both used causal `available_share_of_capacity` trajectories only.

Final attendance never entered TSFM context.

Results:

- Ridge latest MAE `3320.39`;
- Ridge + Chronos-2 `3428.25`;
- Ridge + Bolt-small `3428.08`.

Decision:

`TSFM_STAGE1 = NOT_PROVEN_VS_RIDGE`

Do not fine-tune Chronos or add Lag-Llama / NeuralProphet on the same frozen 9-event development lineage.

A failed TSFM challenger closes this challenger family for current evidence, not d2 itself.

Reopen only with materially more independent trajectories or a materially new predeclared hypothesis.

---

## 10. d2 Stage 2 reliability contract

Goal:

> **Preserve a meaningful share of Ridge's average MAE uplift while materially reducing the +4326.90-seat worst-event degradation.**

Preferred architecture:

`final = frozen_v2 + reliability * ridge_delta`

where:

`0 <= reliability <= 1`

### 10.1 Immutable development boundary

Events:

`[1, 3, 4, 8, 9, 12, 13, 14, 17]`

Rows:

`30`

Independent unit:

`event`

Primary validation:

`LOEO`

New completed event 5 is excluded from Stage-2 selection.

### 10.2 Allowed reliability signals

Only PIT-safe evidence available at exact forecast time, including:

- observation count;
- observation span;
- time to kickoff;
- trajectory stability / volatility;
- velocity;
- acceleration;
- disagreement between Ridge and Frozen v2;
- absolute proposed correction size;
- release/replenishment flag;
- coverage-change flag;
- unexplained inventory increase flag;
- data-gap flag;
- signal/feature-quality state;
- sector coverage quality when already available PIT-safe.

### 10.3 Compact predeclared policy family

At minimum compare:

- `P0` Frozen-v2 only;
- `P1` raw Ridge;
- `P2` observation-maturity gating;
- `P3` disagreement/correction-magnitude shrinkage;
- `P4` data-quality gating;
- `P5` compact combined reliability policy.

Do not create a large threshold zoo.

### 10.4 Advancement criteria

A Stage-2 policy may advance only if it:

- improves latest-row MAE vs Frozen v2;
- improves event-balanced window MAE vs Frozen v2;
- retains meaningful raw-Ridge uplift;
- materially reduces raw-Ridge worst-event degradation;
- does not introduce unacceptable bias;
- remains stable under event-level LOEO;
- is fully versioned/reproducible;
- is selected before event 5 is opened.

If none passes, retain Ridge as research lead but do not promote.

---

## 11. Reserved chronological holdout rule

Reserved event:

- ticket event ID `5`;
- Lech Poznań vs Korona Kielce;
- kickoff `2026-10-18T15:30:00Z`;
- actual attendance `37,407`;
- capacity `43,269`;
- 4 final-24h live rows.

This outcome was not used for Stage-1 selection.

Mandatory rule:

> **Do not use event 5 to select Stage-2 features, thresholds, weights or policy. Freeze Stage 2 first. Then score event 5 once.**

After freeze compare:

1. Frozen Pre-Live v2;
2. raw frozen Ridge;
3. frozen Stage-2 governed Ridge;
4. frozen C1 v8 where compatible.

No retuning after opening the holdout.

A holdout validates a frozen decision; it does not become tuning data retroactively.

---

## 12. Event independence and PIT safety

Training rows may be `event x as_of_timestamp`, but the independent evaluation unit is the event.

Rules:

- all snapshots from one event remain in one fold;
- no random snapshot train/test split;
- use event-balanced weighting or equivalent;
- no future snapshot information;
- every feature/state must exist at exact as-of;
- releases/coverage changes are not automatically demand;
- public inventory is a proxy, not confirmed paid sales.

---

## 13. Accuracy scorecard

Primary metric:

- MAE.

For every serious challenger/policy report at minimum:

- latest-row MAE;
- event-balanced trajectory-window MAE;
- median AE;
- bias;
- event improvement rate;
- worst-event degradation;
- tail metric/p90 where meaningful;
- revision activation rate;
- mean/max revision magnitude;
- performance by observation count/time-to-kickoff;
- event count and row count.

For Stage 2 also report:

- retained share of raw Ridge uplift;
- reduction in worst-event degradation versus raw Ridge.

A lower global mean MAE with unacceptable tail risk is not sufficient.

---

## 14. CI/CD and reproducibility — NON-NEGOTIABLE

Every material experiment must have:

1. committed source code;
2. executable CI workflow;
3. pinned runtime dependencies and external model revisions where relevant;
4. syntax/import validation;
5. deterministic seeds where applicable;
6. explicit input data/artifact versions;
7. explicit train/development/holdout split;
8. PIT assertions;
9. incumbent benchmark assertions;
10. machine-readable result artifact;
11. run/artifact IDs and hashes;
12. committed human-readable result in `ml/results/`;
13. explicit decision;
14. canonical docs updated in the same cycle;
15. no production activation without explicit promotion.

Document exact:

- feature definitions;
- as-of rules;
- missing-value behavior;
- imputation/normalization;
- caps/clipping;
- weights/shrinkage;
- thresholds;
- hyperparameters;
- random seed;
- train/development/holdout events;
- exclusions and reason;
- model/policy ID;
- feature-contract/data/benchmark versions;
- evidence limitations.

If any material element changes, create a new challenger/version.

---

## 15. No silent retuning

Do not change thresholds, features, models, hyperparameters or gates after looking at the same holdout and continue calling that holdout unseen validation.

Exposed evidence remains regression evidence but must be labeled honestly.

Event 5 must not be used for Stage-2 selection.

Future completed events should remain prospective scoring evidence until an explicit separately versioned retraining cycle is declared.

---

## 16. Interpretation rule

Mandatory:

> **A failed challenger closes the challenger, not the whole workstream.**

Examples:

- failed Current Season Adjustment v1 did not close b2;
- failed Future Fixture Context v1 did not close c2;
- Chronos losing to Ridge does not close d2;
- one bad prospective event does not automatically invalidate the entire live workstream;
- one good holdout does not prove production readiness.

---

## 17. Production safety

Production remains:

`live_adjustment = 0`

CI green != production promotion.

Production promotion requires materially more genuinely prospective independent events, stable uplift, acceptable tail risk, a frozen reproducible package and an explicit reviewed promotion decision.

---

## 18. Immediate work order

1. Freeze Stage-1 `ridge-a10` exactly as selected.
2. Build Stage-2 reliability/tail-risk policies only on the original 9-event/30-row development set.
3. Keep policy family compact: P0-P5 from `ml/D2_STAGE2_RELIABILITY_GATING_V1.md`.
4. Select using both average MAE and tail-risk reduction.
5. Persist code, CI, machine-readable artifact, hashes and result doc.
6. Freeze the chosen Stage-2 policy before opening event 5.
7. Score Lech–Korona event 5 once against Frozen v2, raw Ridge, governed Ridge and C1 v8 where compatible.
8. Do not retune after opening event 5.
9. Continue append-only prospective scoring on later completed events.
10. Keep C1 v8, Pre-Live v2 and production unchanged unless a separate explicit promotion/version process occurs.

---

## 19. One-line instruction for every new AI / engineering session

> **Pre-Live v2 and Stage-1 `ridge-a10` are frozen research components. Build d2 Stage-2 reliability/tail-risk governance only on the original 9-event/30-row development lineage; do not use Lech–Korona event 5 for tuning. Freeze Stage 2 first, score event 5 once as chronological holdout, keep prospective evidence append-only, and keep production/C1 v8 unchanged.**
