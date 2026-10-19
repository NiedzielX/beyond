# Beyond Ticketing — Model Accuracy Development Instructions v2

Last updated: **2026-10-19**

Status: **CANONICAL DEVELOPMENT INSTRUCTION**

This file defines how Beyond forecasting development must be conducted.

The objective is not roadmap completion. It is:

> **Reduce forecasting error as far as possible with honest, reproducible, point-in-time-safe evidence before treating the model as mature.**

MAE is the primary development KPI. Tail risk, bias, event independence and prospective evidence remain mandatory constraints.

---

## 1. Canonical architecture

### Layer 1 — Frozen Pre-Live v2

Conceptually:

`historical demand + current-season regime + historically proven context -> pre-live forecast`

Current freeze:

`pre-live-v2-historical-candidate-2026-10-18-v1`

Historical c2 contract:

`NO_CONTEXT_ALL_HORIZONS`

### Layer 2 — frozen d2 live updater

Stage-1 expert:

`ridge-a10`

Stage-2 policy:

`P2-observation-maturity`

Frozen package:

`d2-stage2-p2-observation-maturity-2026-10-19-v1`

Architecture:

`final_forecast(t) = frozen_pre_live_v2(t) + reliability(t) * ridge_delta(t)`

The live layer revises a frozen pre-live anchor. It is not an unrelated second forecast against a moving baseline.

---

## 2. Current canonical status

Sequence:

`a2 CLOSED -> b2 CLOSED -> c2 historical CLOSED -> Pre-Live v2 FROZEN -> d2 Stage 0 DONE -> Stage 1 FROZEN -> Stage 2 FROZEN -> EVENT 5 HOLDOUT COMPLETE -> PROSPECTIVE ACCUMULATION ACTIVE`

### a2 — historical optimization

`CLOSED FOR CURRENT HISTORICAL DATA`

Completed investigation includes:

- feature-group ablation;
- season-recency weighting;
- internal estimator-family challengers;
- CatBoost / LightGBM / XGBoost external families at T-7;
- horizon-specific optimization;
- T-7 fixed temporal robustness;
- stronger multi-fold unresolved-horizon audits;
- persistent cross-season club calibration under fixed formulations.

Final historical bases:

- T-30 Structural Prior;
- T-14 Structural Prior;
- T-7 `hist31-leaf20-l2-1`;
- T-3 Structural Prior;
- T-1 Structural Prior.

T-7 improves 4/4 rolling folds, mean `+104.66 MAE`.

### b2 — current-season regime

`CLOSED FOR CURRENT HISTORICAL DATA / FROZEN INTO PRE-LIVE V2`

Critical PIT rule:

`prior kickoff + 3h <= current forecast as_of`

Frozen policies:

- T-30 `NO_ADJUSTMENT`;
- T-14 `NO_ADJUSTMENT`;
- T-7 `ewma50-resid-k6-cap05-min3`;
- T-3 `ewma50-resid-k2-cap05-min3`;
- T-1 `ewma50-resid-k6-cap05-min3`.

Non-zero b2 activates only after at least 3 earlier completed same-season home matches.

Historical fixed four-fold mean gains:

- T-7 `+51.47`;
- T-3 `+70.44`;
- T-1 `+69.54`.

Fresh prospective evidence now adds one warning: on event 5, T-1 b2 changed `29,737.93 -> 27,574.48`, worsening the final pre-live error by `2,163.45 seats`.

Status of that observation:

`PROSPECTIVE_FAILURE_SIGNAL_ONLY`

Do **not** retune or reopen b2 from one event.

### c2 — historical context

`SUFFICIENTLY EVALUATED / NO HISTORICAL EXTENSION`

Historical tests included sequence/streak and stakes/pressure context after the earlier future-fixture challenger.

No c2 extension survived the frozen protocol.

Forward-only rivalry, verified absences, media/hype/search/social remain prospective research when valid PIT sources exist.

Never backfill them from final-state knowledge.

### Frozen Pre-Live v2

`SEALED / REPRODUCIBLE / HISTORICAL CANDIDATE ONLY`

Reference mean MAE:

- T-30 `1867.82`;
- T-14 `1809.45`;
- T-7 `1691.40`;
- T-3 `1682.63`;
- T-1 `1661.52`.

Freeze reproduces 20/20 horizon-season cells at tolerance `1e-9`.

### d2 Stage 0

`FROZEN_V2_EXACT_COMPATIBILITY_READY`

Frozen development lineage:

- 9 events;
- 30 final-24h rows;
- exact Frozen-v2 anchor.

### d2 Stage 1

`COMPLETED / ridge-a10 FROZEN RESEARCH EXPERT`

Development:

- Frozen-v2 latest MAE `4128.01`;
- Ridge latest MAE `3320.39`;
- latest uplift `807.62 / 19.56%`;
- Ridge window MAE `3619.19`;
- window uplift `508.83 / 12.33%`;
- worst latest-event degradation `4326.90`.

### d2 Stage 2

`COMPLETED / P2-observation-maturity FROZEN`

Development:

- P2 latest MAE `3240.99`;
- uplift vs Frozen v2 `887.02 / 21.49%`;
- P2 window MAE `3657.65`;
- worst degradation `1081.72`;
- worst degradation reduction vs raw Ridge `75%`;
- retained raw-Ridge window uplift `92.44%`.

Only P2 passed all frozen Stage-2 advancement gates.

### Event 5 holdout

`COMPLETED_ONE_PASS_HOLDOUT`

Canonical result:

`ml/results/D2_EVENT5_HOLDOUT_V1_2026-10-19.md`

Errors:

- Structural T-1 base `7669.07`;
- Frozen-v2 `9832.52`;
- raw frozen Ridge latest `6652.81`;
- raw Ridge window `6170.35`;
- P2 latest `6652.81`;
- P2 window `7263.16`;
- persisted C1 v8 policy/latest `7669.07`.

Event 5 is now exposed and may never be treated as unseen validation again.

---

## 3. Historical workstream reopening rule

Do not reopen a2/b2/c2 because later stages are difficult or because an exposed event suggests a post-hoc fix.

Historical or frozen work may be reopened only when at least one is true:

- materially new independent data exists;
- a materially new hypothesis exists that was not already tested;
- repeated prospective evidence exposes a systematic failure mode;
- previously unavailable PIT-safe context becomes reconstructable without leakage.

Any reopening requires a new explicit candidate/version and a new declared evaluation boundary.

---

## 4. Historical optimization requirements

A complete a2-style investigation may include:

- feature-group ablation;
- season recency weighting;
- horizon-specific configurations;
- HistGradientBoosting / GradientBoosting;
- ExtraTrees / RandomForest;
- CatBoost;
- LightGBM;
- XGBoost;
- regularized linear / GAM-style baselines;
- independently validated ensembles;
- club calibration/hierarchy with low-sample shrinkage.

Do not assume the current champion family is theoretically optimal.

However, do not re-run the same exposed grids without new evidence.

Every dependency must be pinned in CI.

---

## 5. Current-season regime requirements

Goal:

> Detect whether the current season is systematically running above or below the model's own prior expectation.

Candidate signals may include:

- mean/median residual;
- actual/expected ratio;
- EWMA residual;
- rolling residuals;
- robust residual variants.

Low-sample evidence requires shrinkage and maturity gating.

Current frozen b2 is not to be changed during the prospective accumulation window.

Prospective component diagnostics must explicitly compare:

`Structural base -> Frozen Pre-Live v2/b2`

so wrong-direction b2 corrections remain visible instead of being hidden inside the final d2 score.

Potential hypothesis to monitor:

> **Negative same-season residual correction may overreact on some high-demand Lech matches.**

Event 5 alone does not prove this hypothesis.

---

## 6. Match-context requirements

Context must explain why a specific match differs from the club/season baseline without duplicating existing opponent/pair/form/table/congestion features.

Potential future sources include:

- rivalry/derby;
- verified injuries/suspensions;
- expected XI/key-player availability;
- media attention;
- search/social/hype.

Only PIT-valid sources are allowed.

No historical reconstruction using later/final-state information.

---

## 7. Frozen Pre-Live contract

Any frozen pre-live candidate must persist:

- feature contract;
- model family/hyperparameters;
- training protocol;
- weighting/calibration;
- data versions;
- artifact/source hashes;
- per-horizon IDs;
- benchmark cells;
- limitations.

The live layer must never silently mutate its anchor.

A material change requires a new freeze ID.

---

## 8. Frozen d2 Stage-1 expert contract

Expert:

`ridge-a10`

Contract:

- target `target_live_delta_occupancy`;
- Ridge `alpha=10.0`;
- numeric PIT-safe live features;
- median imputation within training fold;
- missing indicators;
- standardization;
- event-balanced weights;
- raw live correction clipped to +/-10pp occupancy.

Do not change any of these during prospective accumulation.

A change creates a new versioned model challenger.

---

## 9. Frozen P2 policy contract

Policy:

`P2-observation-maturity`

Observation reliability:

- observation 1 `0.25`;
- observation 2 `0.60`;
- observation 3+ `1.00`.

Time-to-kickoff cap:

- >18h `0.75`;
- >12h <=18h `0.90`;
- <=12h `1.00`.

Final:

`reliability = min(observation_weight, time_weight)`

Do not modify these weights from event-5 evidence.

Event 5 showed that P2 can sacrifice useful early correction on an event while still matching raw Ridge after maturity. Treat this as a prospective risk/return diagnostic, not a tuning cue.

---

## 10. TSFM / Chronos boundary

Stage 1 tested zero-shot:

- `amazon/chronos-2`;
- `amazon/chronos-bolt-small`.

Both forecast only causal public inventory trajectory.

Latest MAE:

- Ridge `3320.39`;
- Ridge + Chronos-2 `3428.25`;
- Ridge + Bolt-small `3428.08`.

Decision:

`TSFM_STAGE1 = NOT_PROVEN_VS_RIDGE`

Do not fine-tune Chronos or add Lag-Llama / NeuralProphet on the same exposed development/holdout set.

Reopen the family only with materially more independent trajectories or a materially new predeclared hypothesis.

---

## 11. Prospective accumulation contract — ACTIVE NOW

Canonical contract:

`ml/D2_PROSPECTIVE_ACCUMULATION_V1.md`

For every new eligible completed event:

1. score once under the frozen package;
2. persist the result regardless of direction;
3. do not train on the event in the same evidence cycle;
4. preserve component-level diagnostics.

Mandatory layers:

1. Structural T-1 base;
2. Frozen Pre-Live v2 / b2;
3. raw frozen Ridge;
4. frozen P2 governed Ridge;
5. persisted pre-outcome C1 comparator where available.

Mandatory event metrics:

- latest AE;
- trajectory/window MAE;
- incremental error change per layer;
- bias;
- max live revision;
- b2 correction direction/magnitude;
- P2 reliability trajectory;
- data-quality warnings.

Mandatory accumulated metrics:

- mean/median latest AE;
- event-balanced window MAE;
- bias;
- p90 latest AE;
- worst event degradation;
- improvement rate;
- cumulative contribution of b2, Ridge and P2;
- club diagnostics only when sample size permits.

---

## 12. Event independence / PIT safety

Training rows may be `event x as_of_timestamp`, but the independent evaluation unit is the event.

Rules:

- all snapshots from one event stay together;
- no random snapshot train/test split;
- no future snapshot information;
- no future match outcome information;
- public inventory is a proxy, not confirmed paid sales;
- ticket releases / coverage changes are not automatically demand;
- synthetic rows never count as independent evidence.

For prospective scoring, the event outcome may be used only after the forecast package has been frozen for that event.

---

## 13. Accuracy scorecard

Primary metric:

`MAE`

Every serious model/policy/prospective report should include where applicable:

- latest-row MAE;
- event-balanced trajectory-window MAE;
- median AE;
- bias;
- p90/tail error;
- worst-event degradation;
- event improvement rate;
- revision frequency;
- mean/max revision magnitude;
- behavior by observation count and time-to-kickoff;
- event/row counts.

For prospective accumulation also report component-level incremental contribution.

A lower mean MAE with unacceptable tail risk must be called out explicitly.

---

## 14. CI/CD — NON-NEGOTIABLE

Every material experiment or prospective scoring pipeline must have:

1. committed source code;
2. executable CI workflow;
3. pinned runtime dependencies and external model revisions where relevant;
4. syntax/import validation;
5. deterministic seeds where applicable;
6. explicit input data/artifact versions;
7. explicit train/development/holdout/prospective boundary;
8. PIT assertions;
9. incumbent/frozen benchmark assertions;
10. machine-readable JSON/CSV evidence;
11. run/artifact IDs and hashes;
12. human-readable result in `ml/results/` when a material event/stage closes;
13. explicit decision;
14. canonical docs updated in the same development cycle;
15. no production activation without explicit promotion.

Persist exact:

- feature definitions;
- source tables/files;
- as-of rules;
- missing/imputation/normalization behavior;
- clipping/caps;
- weights/shrinkage;
- thresholds;
- hyperparameters;
- random seed;
- train/development/holdout/prospective events;
- exclusions and rationale;
- model ID;
- policy ID;
- feature/data/benchmark versions;
- limitations.

If a material element changes, create a new version.

---

## 15. No silent retuning

Do not change a model, feature, threshold, policy or gate after seeing an event and continue calling that event unseen validation.

Event 5 is permanently exposed.

It may be used as:

- regression evidence;
- component failure evidence;
- motivation for a future predeclared hypothesis.

It may not be reused as fresh holdout evidence after tuning.

Future prospective events follow the same rule once scored.

---

## 16. Interpretation rule

Mandatory:

> **A failed challenger closes the challenger, not the whole workstream.**

Also mandatory:

> **One bad prospective event does not prove a failure mode, and one good prospective event does not prove production readiness.**

Examples:

- failed Current Season Adjustment v1 did not close b2;
- failed Future Fixture Context v1 did not close c2;
- Chronos losing to Ridge did not close d2;
- event 5 b2 degradation does not automatically reopen b2;
- event 5 d2 uplift does not automatically promote d2.

---

## 17. Reopening / retraining gate

A new candidate cycle may start only after:

1. materially more independent prospective events exist;
2. a repeated interpretable failure pattern is identified;
3. a new hypothesis is declared before tuning;
4. the frozen current package remains the benchmark;
5. a new train/development/forward-evidence boundary is declared;
6. exposed prospective events are labeled honestly.

Do not gradually mutate the frozen package event by event.

---

## 18. Production safety

Production remains:

`live_adjustment = 0`

CI green != production promotion.

Production promotion requires materially more genuinely prospective independent events, positive aggregate uplift, acceptable tail risk, no unresolved systematic failure, a frozen reproducible package and an explicit reviewed promotion decision.

---

## 19. Immediate work order

1. Keep `d2-stage2-p2-observation-maturity-2026-10-19-v1` frozen.
2. Do not retune from event 5.
3. Implement/operate append-only prospective scoring for every new eligible completed event.
4. Persist Structural base -> Frozen-v2/b2 -> raw Ridge -> P2 -> genuine persisted C1 comparator as separate layers.
5. Track the event-5 b2 wrong-direction signal prospectively without changing b2.
6. Track P2 early-conservatism cost versus tail-risk protection prospectively without changing P2.
7. Maintain cumulative prospective MAE/tail/component dashboards/evidence.
8. Open a separately versioned challenger only if materially more independent prospective evidence supports a specific hypothesis.
9. Keep C1 v8 and production unchanged.

---

## 20. One-line instruction for every new AI / engineering session

> **Event 5 is complete and exposed. Keep Pre-Live v2, `ridge-a10` and `P2-observation-maturity` frozen; score each new completed event append-only with separate Structural -> b2 -> Ridge -> P2 -> persisted C1 diagnostics; monitor the event-5 b2/P2 signals without tuning; only open a new versioned challenger after materially more independent prospective evidence. Production remains unchanged.**
