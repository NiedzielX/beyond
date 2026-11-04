# Beyond Ticketing — MAE Experiment Scoreboard

Last updated: **2026-11-04**

Status: **CANONICAL HUMAN-READABLE MAE EXPERIMENT REGISTRY**

Canonical research strategy: `ml/MAE_RESEARCH_ROADMAP_V6.md`

---

# 1. Purpose

This file records comparable MAE experiments so that model selection is driven by reproducible evidence rather than narrative memory.

One row should represent one materially distinct experiment/version.

Do not overwrite a failed experiment. Record the result and decision.

---

# 2. Headline scoreboard

| Experiment ID | Hypothesis | Incumbent | Events | Clubs | Coverage | Incumbent MAE | Challenger MAE | Delta MAE | Improvement rate | Median Delta AE | P90 / worst degradation | Signed bias | PIT audit | Decision |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|
| structural-incumbent-frozen-reference | frozen reference on exposed 10-event trajectory cohort | — | 10 | — | — | 2594.54 | 2594.54 | 0.00 | — | — | — | — | recorded | incumbent reference |
| trajectory-lane-a-ridge-v1 | engineered trajectory residual Ridge improves structural incumbent | structural incumbent | 10 | — | — | 2594.54 | 4153.34 | +1558.80 | — | — | — | — | recorded | REJECTED |
| trajectory-lane-b-gru-raw-v1 | GRU raw-seat residual improves structural incumbent | structural incumbent | 10 | — | — | 2594.54 | 2595.40 | +0.87 | — | — | — | — | recorded | DO NOT ADVANCE |
| trajectory-lane-b-gru-ratio-v2 | GRU residual-ratio mechanism improves structural incumbent | structural incumbent | 10 | — | — | 2594.54 | 4792.42 | +2197.88 | — | — | — | — | recorded | MECHANISM NOT SUPPORTED |

Notes:

- the 10-event cohort above is exposed and must not be reused for post-hoc tuning and then treated as fresh evidence;
- fill missing historical guardrail fields only from reproducible existing results, never from guesses;
- target-free SSP representation results belong in representation evidence, not in attendance MAE rows unless an attendance challenger is actually evaluated.

---

# 3. Roadmap v6 experiment queue

| Work package | Planned experiment | Status | Entry criterion | Exit criterion |
|---|---|---|---|---|
| MAE-01 | incumbent error decomposition v1 | HISTORICAL DIAGNOSTIC COMPLETE | reproducible incumbent predictions + outcomes | ranked error segments + failure taxonomy + next hypothesis |
| MAE-02 | structural baseline benchmark v1 | WEIGHTING REJECTED; ANCHOR RECONCILED | MAE-01 identifies structural error opportunities | strongest honest PIT-safe structural research anchor selected/frozen |
| MAE-03 | context residual benchmark v1 | AUDITED / DATA_BOUND | timestamped PIT-safe context available | incremental context Delta MAE measured vs same-event anchor |
| MAE-04 | engineered trajectory benchmark v2 | QUEUED | genuine trajectory coverage sufficient | incremental trajectory Delta MAE measured with ablations |
| MAE-05 | horizon-specific residual v1 | QUEUED | enough events across useful horizons | horizon curve shows whether separate correction is justified |
| MAE-06 | club/regime heterogeneity v1 | QUEUED | MAE-01/02 show systematic heterogeneous error | global vs club/regime-aware comparison completed |
| MAE-07 | context/trajectory ablation v1 | QUEUED | individual signal families measured | source of combined gain identified |
| MAE-08 | calibrated ensemble v1 | QUEUED | at least two independently useful, complementary challengers | blend beats strongest simpler challenger on same events |
| sequence-next | compact sequence challenger | CONDITIONAL | engineered trajectory shows signal + plausible representation gap | beats simple trajectory benchmark under same event-grouped validation |

---

# 4. Required detail block for every new experiment

Copy this block below for each new serious experiment.

## `<experiment-id>`

**Work package:** MAE-XX  
**Status:** PLANNED / RUNNING / FROZEN / REJECTED / SUPPORTED / PROSPECTIVE_SHADOW  
**Hypothesis:**  
**Incumbent/version:**  
**Challenger/version:**  
**Dataset/version:**  
**Cutoff/horizon contract:**  
**Independent events:**  
**Distinct clubs:**  
**Coverage:**  
**PIT audit:** PASS / FAIL / PENDING  

### Result

- Incumbent event-balanced MAE:
- Challenger event-balanced MAE:
- Delta MAE:
- Event improvement rate:
- Median event Delta AE:
- P90 AE / worst-event degradation:
- Signed bias:
- Per-horizon MAE:
- Best-event improvement:
- Worst-event degradation:

### Interpretation

State what the result supports and what it does **not** support.

### Decision

`REJECT / RETAIN_AS_BENCHMARK / SUPPORT_SIGNAL / PRECOMMIT_NEXT_VERSION / FREEZE_FOR_PROSPECTIVE_SHADOW / INSUFFICIENT_EVIDENCE`

### Next hypothesis

State one next question derived from the observed residual error. Do not list arbitrary feature ideas.

---

# 5. Evaluation rules

1. Event/fixture is the independent unit.
2. Compare incumbent and challenger on the same eligible events.
3. Use PIT-safe features only.
4. Keep all rows/prefixes from one event in the same fold.
5. Primary selector is event-balanced MAE.
6. Multiple horizons from one event do not increase independent-event count.
7. Do not repair failed results post hoc on exposed outer outcomes.
8. Historical/grouped research is not prospective evidence.
9. Any promoted challenger requires a new precommit/freeze before genuine prospective scoring.
10. Production activation remains a separate explicit review.

---

# 6. Active frozen prospective reference

The currently frozen trajectory attendance candidate remains separate from Roadmap v6 research:

`trajectory-frozen-encoder-ridge-ratio-head-v1`

Its current prospective decision must be made only from its immutable future evidence stream and the precommitted evaluator/business guards.

For that active comparison the business-resolution scale remains:

`Delta MAE <= -550 seats`

Do not tune Roadmap v6 experiments toward this exact number and do not rewrite the frozen candidate based on early outcomes.

---

# 7. Separate public-inventory daily-path experiment

This section uses **future public inventory**, not attendance. Never pool its MAE with the attendance headline table. Latest user product instruction requires the remaining daily path; partner transactions are unavailable for MVP.

## daily-inventory-direct-median-v1

- Hypothesis: a small lead-conditioned predictor using the complete genuine observed prefix improves future-day inventory MAE over persistence.
- Precommit: `DAILY_INVENTORY_PATH_PRECOMMIT_V1.md`; fit once on16completed events /1,239rows, cutoff2026-11-03T00:00Z.
- Frozen artifact: `artifacts/daily_inventory_path_v1.json`, SHA1137e257494583374f768622feca343f2dd7d634ef2446198703f8c27fbd9525.
- Diagnostic70/30 temporal split: **INSUFFICIENT_EVIDENCE**, only4training events with labels known by the first test issue; minimum5retained. No validation MAE improvement claimed.
- Recorded local prospective state at20:01UTC:7attempts /4events with predictions /57future daily points /0scores. These are not57independent events. First targets mature2026-11-04T17:00Z.
- Baseline MAE, challenger MAE, Delta, improvement rate, median/tail/bias: **pending genuine future observations**, not zero.
- PIT status: dedicated leakage/window/hash/idempotency tests pass; source active/visible flags are missing from public snapshot exports and measurement changes fail closed. No independent external PIT audit claimed.
- Decision: **FROZEN / LOCAL_POST_FREEZE_PROSPECTIVE_COLLECTING**. Private Storage recovery verified; SQL/gateway/scheduled GitHub job prepared, not deployed/enabled.
- Metrics: equal-event paired path MAE and per-lead +1/+3/+7, with matured/pending coverage separated. Attendance thresholds are unchanged and do not automatically apply here.
- Next evidence: score the already-issued points against subsequent genuine inventory observations; classify residual error without retuning v1.

## mae01-incumbent-error-decomposition-v1

- Status: historical diagnostic complete; hosted reproduction passed in run41711896063. Protocol/result: `MAE01_INCUMBENT_ERROR_AUDIT_PROTOCOL_V1.md`, `MAE01_INCUMBENT_ERROR_AUDIT_RESULT_V1.md`.
- Evidence:603events /3,010horizon rows;599common-five-horizon events. All10frozen benchmark MAEs reproduced. Frozen source/artifact hashes verified unchanged.
- Incumbent historical equal-event MAE1,773.89; bias+14.59; median AE1,129.28; P90 AE4,195.79. No challenger or new Delta MAE. Separate from the exposed10-event trajectory cohort and from future daily-inventory errors.
- Lech contributes17.41%of total error and remains high-error in both seasons. Four largest-contributing clubs account for43.57%of error on19.73%of events. Constant club offsets are not supported by changing bias.
- PIT audit: existing feature-store timing and fixed season separation checks pass; archived publication times/capacity knowledge are not independently proven. Outcome-conditioned fill bins are descriptive only.
- Decision: RETAIN_AS_DIAGNOSTIC; proceed to separately versioned MAE-02 raw-seat-objective audit. No serving-artifact changes, prospective promotion or claim of new independent validation.

## structural-seat-weighted-median-v1

- Work package:MAE-02. Status:REJECTED; weighted old-holdout fitting not performed. Precommit/result:`MAE02_SEAT_WEIGHTED_MEDIAN_PRECOMMIT_V1.md`,`MAE02_SEAT_WEIGHTED_MEDIAN_RESULT_V1.md`.
- Previously exposed2023/24development, trained2021/22–2022/23;297events /18clubs /594pairedT-3/T-1rows;100%paired coverage within existing eligibility. Same features, estimator parameters and decode; normalized capacity weighting only.
- Equal-event MAE:incumbent2,329.81;challenger2,459.68;Delta+129.88. Improvement42.76%;medianDeltaAE+12.95;P90 5,305.57→5,551.76;worst degradation+4,974.83;bias−183.43→+265.61. Per-horizonDelta:T-3+155.01,T-1+104.75.
- PIT checks:fixed train/test separation, exact incumbent development reproduction, unchanged incumbent predictions and frozen hashes pass. Archived publication-time limits remain; this is not fresh validation.
- Decision:REJECT_FOR_PROSPECTIVE. No new variant or Lech-only rescue. All4fixed simple PIT summaries underperform incumbent on this development sample.
- Existing research anchor:retain frozen Pre-Live v3 contract; its recorded historical seal and source/evidence hashes are verified, not newly executed prospective validation. Existing C2sequence/stakes extension remains rejected; do not rerun its grid.
- Next:target-free audit of new genuine fixture/market/price context and labeled coverage. P4a frozen support gate remains9events; current5does not permit fitting.

## mae03-context-evidence-audit-v1

- Status:DATA_BOUND; no model fit or target attendance values opened. Result:`MAE03_CONTEXT_EVIDENCE_AUDIT_RESULT_V1.md`.
- Existing stored snapshots121;70prospective-window-valid,51retrospective excluded.62baseline-timed rows;11distinct paired events across checkpoints.37isolated feature/source/baseline/checkpoint groups;35insufficient event support,1constant,1insufficient grouped variance.
- NGrams media attentionT-24h:10events /10clubs /1distinct value(0). NGrams accelerationT-24h:4events /4clubs /3values. T-6hmedia has only1nonzero event and cannot supply every held-out event/club training fold; no checkpoint rescue.
- Decision:NO_NEW_CONTEXT_FIT. Existing Hype gates reconfirmed; no new MAE or model promotion claim. Existing P4a9-event gate unchanged(current5). Continue genuine collection and separate daily-path SQL validation.

## Daily-path preparation / diagnostic registry —2026-11-04

These are not new MAE challenger results.

- Prefix-regime diagnosticv1:8hosted tests passed(run41816697000). Full eligible primary evaluator unchanged; zero-only, constant-positive and varying groups are descriptive, with reconciled primary contributions and overlapping-vintage event warning. Actual0scores means allMAEsnull.
- Exact coefficient auditv1:57issued points reconstructed within9.10e-13places; all120relative-value-history weights0. No target values, refit or accuracy evaluation. See`DAILY_PATH_COEFFICIENT_AUDIT_2026-11-04.md`. Decision:retain frozenv1evidence, explicitly qualify its learned-mechanism limitation; next separately precommit a restrained genuine-prefix-change comparator rather than tunev1.
- Source-stateinformationv2:isolatedSQL→featurecontract passed(run41816696989;20SQL+13adaptertests); seven fixed fields/masks, known-at guards, zero/hidden separation and exact input whitelist. No learner orMAE, no live deployment. Decision:PREPARED_INFORMATION_CONTRACT; admin deployment binding remains the blocker.

## daily-inventory-genuine-24h-drift-v1

Separate public-inventory research comparator. Precommit:`DAILY_INVENTORY_DRIFT_COMPARATOR_PRECOMMIT_V1.md`. Hypothesis:actual recent daily inventory change adds signal beyond persistence; fixed rule, no fit/search. Originalv1relative-value coefficients were0, as diagnosed before first outcomes.

- Frozen2026-11-04T11:06:27Z; artifactSHA332f6fd37bc2a09ce665668ef3c9c23d8d34ec3613f18435ec729d95d3bb43cf. Predictor source and precommit hashes remain fixed.
- Thirteen hosted tests passed(run41818376777,total309Pythonchecks). Rule/lifecycle correctness only; synthetic fixture errors are not model accuracy.
- Actual first no-due cycle completed, original source/model bytes unchanged and private read-back verified.0attempts/points/scores at freeze; no eligible post-freeze source issue yet. These counts are not a failed prospective window.
- Independent scored events/clubs0; prediction/error coverage and baseline/challengerMAE,Delta,improvement,median/tail/bias/per-lead errors pending genuine future targets. No accuracy claim.
- PIT/source limitations inherited from actualv1public prefix; active/visible metadata absent, no independent raw immutability certification. OldNov3points cannot become new drift evidence.
- Decision:FROZEN_RULE / BOUNDED_LOCAL_COLLECTING. First review after8independent genuine+1events/5clubs; separate primary same-target event-balanced metrics against persistence. No production promotion, attendance change or modelv1repair.

Drift operational update11:20UTC:first legal new issue captured automatically11:19:58UTC,1attempt/0points/0scores,INSUFFICIENT_PREFIX_SPAN,privatebackupverified. This is genuine coverage evidence, not a forecast/MAE. Originalv1now8attempts/57points/0scores; no metric cohort changed. READYdrift forecast and new target labels remain pending.

## Existing persisted live evaluations —2026-11-04T11:42UTC

Do not describe every live model as unscored just because the newer prospective summary has0scores. The deployed public view`dashboard_c1_shadow_v8_status_v1`returns C1v8package`c1-shadow-v8-frozen-2026-10-16-n9`:101prediction rows,17events,11scored events,last score2026-10-25. Latest-row priorMAE4314.722244,raw live7127.992602,policy4121.454326; representative-window policyMAE4971.620552(vs prior4314.722244). These are actual persisted live-shadow scores, not Pre-Live historical validation.

Main-panel`forecast_observations`latest version`beyond-demand-engine-v1-structural-prior-shadow`:latest-per-event panel-ruleMAE4314.727273,11scored events,24forecast events,1313rows,alllive_adjustment0. Latest evaluated forecasts pass kickoff/confirmation-time checks. Two manually seeded D2Long72rows appear in the raw table but are excluded by the official Long72quality contract; do not present their panel aggregate as official prospective scoring. Other older tiny version cohorts must not be pooled or compared as identical validation.

## c1-objective-geometry-audit-v1 —2026-11-04

Target-free contract audit, not a new predictor or accuracy result.20frozen training events/74rows; equal-event mass3.7verified; capacities15004–43708give8.4861small/large-capacity squared-occupancy loss ratio for the same person error. No target columns parsed, fit/inference/trainingMAE or new DeltaMAE. ExistingC1L1trees/clubvariants and structuralweighting rejection preserved. Result:`C1_OBJECTIVE_GEOMETRY_AUDIT_RESULT_V1.md`. Decision:OBJECTIVE_CONTRACT_DOCUMENTED; exact separate median-linear precommit still required beforefit; futureevidenceonly. Sixunitchecks pass.

## c1-live-seat-median-v1-frozen-2026-11-04-n20

**Work package:** MAE-04 / live-objective supplement. **Status:** FROZEN / BOUNDED_LOCAL_COLLECTING. **Hypothesis:** direct-person conditional median improves future event errors over expanded occupancy Ridge using identical information. **Incumbents:** original9C1, expanded20Ridge and shared prior, with raw/governed metrics separate. **Training:**20exposed events/74rows/11clubs, same30features/exact fitted preprocessor, no fresh validation from those20. **Protocol:** final24genuine current paired captures; first30newscored events/8clubs,10000eventbootstrap seed42 and distinct raw/product gates. **Prospective result:**0predictions/0scores, all MAE/bias/tail/improvement/coverage-result fields null, not zero error. No promotion. Fit13:44:30UTC; worker17:19verified. Full manifest/evidence:`C1_SEAT_MEDIAN_RESULT_V1.md`, precommit:`C1_SEAT_MEDIAN_PRECOMMIT_V1.md`.

## Existing prospective scores after delayed genuine outcomes —17:19UTC

These are dated cohort expansions, not newly trained experiments or comparable all-model tournaments. Details, source timing and immutable evidence:`VERIFIED_ATTENDANCE_IMPORT_RESULT_2026-11-04.md`.

| Frozen lane/target | Independent events | Incumbent MAE | Challenger MAE | Paired delta | Decision |
|---|---:|---:|---:|---:|---|
| C1v8 attendance, latest row |16|3303.287177 prior|3428.290290 governed|+125.003114|Collect; unchanged model; old11event score retained |
| Frozen encoder attendance |3|923.271989|1529.709219|+606.437230|Early worse; no promotion/retuning |
| P9v2 attendance |2|1248.354372|1984.717101|+736.362730|Early worse; keep v1separate |
| Dailyv1available_total at+1day |2|326.500000|258.941674|−67.558326|Early only;1/2improve; availability is not attendance |

Expanded20Ridge still0future scores/nullMAE. Do not replace dated historical closed experiment results or reuse these completed old fixtures to validate either Nov4freeze. Partial source-import status/event445block remains explicit.

## Structural attendance source-contract integration —2026-11-04

Input integrity work, not a new learner/MAE result: exact-count raw export, per-cutoff source/revision filtering, unchanged frozen-predictor integration and bounded private source archive. Actual current inspection0forecasts/no-ready target; synthetic predictor parity is correctness only. Separate as-of lookup preserves genuinely earlier source values and leaves missing earlier archives missing. No new prospective candidate activated and no production/old-score change. Details:`STRUCTURAL_KNOWN_AT_INPUT_INTEGRATION_V1.md`.

## Outcome coverage completed —18:32UTC

Current originalC1v8:17scored of17forecast events,101rows; priorMAE3131.157876, policy3248.807865, raw6241.964642, window policy3913.558409. New17thlabel3396is composite-verified against exact official fixture identity and primary attendance; no schedule shift. Old11/16event metrics are preserved; this is cohort growth, not model improvement. Frozen encoder now4events,1623.917287vs1051.043479; P9v2 unchanged2events,1984.717101vs1248.354372. No gates opened or model/parameter changes. Full evidence:`OUTCOME445_COMPOSITE_VERIFICATION_RESULT_V1.md`.
