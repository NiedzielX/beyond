# Beyond Ticketing — ML Progress Tracking

Last updated: **2026-11-04**

Status: **CANONICAL TRACKING SNAPSHOT**

Canonical MAE strategy: `ml/MAE_RESEARCH_ROADMAP_V6.md`

Canonical execution plan: `ml/EXECUTION_PLAN_CURRENT.md`

Production: `live_adjustment = 0`

Important: operational counters below are dated snapshots unless explicitly refreshed from live DB.

---

## User-requested daily-path MVP — 2026-11-03 update

The latest user instruction requires **genuine observed prefix → predictions for every remaining day**, updated daily. Terminal attendance alone is insufficient for this product deliverable. The parallel error-driven attendance research programme below remains canonical; the new inventory-path lane has its own observable target, baseline and metrics and does not replace attendance evidence or its 550-seat contract. Partner transactions are unavailable for MVP and are not a prerequisite.

Implementation: [`DAILY_INVENTORY_PATH_IMPLEMENTATION_V1.md`](DAILY_INVENTORY_PATH_IMPLEMENTATION_V1.md). Deployment/recovery: [`DAILY_INVENTORY_PATH_DEPLOYMENT_V1.md`](DAILY_INVENTORY_PATH_DEPLOYMENT_V1.md). Formal lane precommit: [`DAILY_INVENTORY_PATH_PRECOMMIT_V1.md`](DAILY_INVENTORY_PATH_PRECOMMIT_V1.md).

Current operational counters, watcher health and deadlines belong in `NEXT_SESSION_HANDOFF.md` and the live runtime status command. Verified milestones:one frozen daily-path model; genuine post-freeze local captures and private backup/restore; hosted panel TypeScript/build; isolated PostgreSQL16persistence and typed panel-feed contract tests(run41810511980). These test milestones do not prove the undeployed SQL/Edge/scheduled workflow in live Supabase. No private partner transactions, production activation or old-model retuning is required.

The attendance history read on2026-11-03 ended at2026-10-25. The six tracked fixtures onOctober30–November2 had no confirmed outcomes in `ticket_event_outcomes`; zero attendance scores are therefore not evidence of zero error. Keep this source-ingestion blocker separate from daily inventory-target scoring.

---

# 1. North Star

> **Minimize true prospective event-balanced attendance-forecast MAE using PIT-safe, reproducible evidence.**

---

# 2. MAE research programme status

| Work package | Status | Current decision |
|---|---|---|
| MAE-01 — Incumbent error decomposition | ✅ HISTORICAL DIAGNOSTIC COMPLETE |603events; all10frozen MAEs reproduced; see `MAE01_INCUMBENT_ERROR_AUDIT_RESULT_V1.md`; hosted checks passed in run41711896063 |
| MAE-02 — Structural baseline benchmark | ✅ BOUNDED AUDIT COMPLETE | weighting-only variant rejected; simple anchors worse; frozen Pre-Live v3 research anchor reconciled; see `MAE02_SEAT_WEIGHTED_MEDIAN_RESULT_V1.md` |
| MAE-03 — Context residual model | 🟡 AUDITED / DATA_BOUND | form/standings/opponent/fixture/odds; squad only with trustworthy PIT-safe source |
| MAE-04 — Engineered trajectory benchmark | ⚪ QUEUED | velocity/acceleration/deltas/plateau/surge/density/similarity |
| MAE-05 — Horizon-specific correction | ⚪ QUEUED | test whether early vs late horizons need distinct residual logic |
| MAE-06 — Demand-regime / club heterogeneity | ⚪ QUEUED | investigate low/normal/near-sellout and club bias without brittle per-club models |
| MAE-07 — Controlled ablations | ⚪ QUEUED | structural vs context vs trajectory vs combined on same events |
| MAE-08 — Ensemble / calibrated blend | ⚪ QUEUED | only after independently useful signals show complementary error |
| Sequence-model expansion | ⏸ CONDITIONAL | proceed only if simpler trajectory evidence justifies representation complexity |

Research method:

`measure error -> classify residual failure -> state hypothesis -> add one information family/mechanism -> event-grouped PIT-safe test -> update scoreboard -> freeze/reject -> repeat`

---

# 3. Existing frozen / collecting evidence

Latest detailed machine-state values in the prior snapshot were from **2026-10-30**. Query live DB before using them as current counts.

| Item | Recorded status | Current decision |
|---|---|---|
| P7 prospective | 🟢 COLLECTING | collect/score only |
| P9 prospective v1 | 🟢 COLLECTING | correct fail-closed; protect genuine windows |
| P9 Family Fallback v2 | 🟢 COLLECTING | separate evidence only |
| Form5 prospective | 🟢 COLLECTING | genuine outcomes only |
| Long72 | 🟡 FROZEN | keep frozen evidence separate |
| P11 odds | 🟡 COLLECTING | useful future context family when PIT-safe coverage supports testing |
| P4a | 🟡 COLLECTING | gate remains evidence-driven |
| Daily trajectory infrastructure | ✅ DONE | PIT dataset + immutable evidence backend |
| Lane A v1 | ❌ REJECTED | MAE 4153.34 vs 2594.54 incumbent |
| Lane B v1 | ❌ DO NOT ADVANCE | MAE 2595.40; near-zero correction |
| Lane B v2 | ❌ MECHANISM NOT SUPPORTED | MAE 4792.42; harmful over-correction |
| Supervised tuning on exposed cohort | 🛑 STOPPED | no post-hoc repair |
| SSP trajectory v1 | ✅ REPRESENTATION_SUPPORTED | target-free representation result only |
| SSP encoder | ✅ FROZEN | immutable v1 artifact |
| Frozen attendance head v1 | ✅ FIT ONCE / FROZEN | Ridge alpha 10, cap +/-10% |
| Frozen encoder prospective shadow | 🟢 COLLECTING | P-7/P-3/P-1; production off |
| Business meaningful Delta MAE threshold | ✅ FROZEN FOR ACTIVE COMPARISON | `Delta MAE <= -550 seats` plus risk guards |

---

# 4. Closed supervised trajectory evidence

## Lane A v1

- incumbent MAE: 2594.54;
- Lane A MAE: 4153.34;
- Delta: +1558.80;
- decision: `REJECT_AS_CANDIDATE_RETAIN_AS_BENCHMARK`.

## Lane B v1

- Lane B MAE: 2595.40;
- Delta: +0.87;
- near-zero corrections;
- decision: `DO_NOT_ADVANCE`.

## Lane B v2

- Lane B v2 MAE: 4792.42;
- Delta: +2197.88;
- harmful over-corrections;
- decision: `MECHANISM_NOT_SUPPORTED`.

Conclusion:

> **Do not keep tuning supervised correction mechanics on the same exposed 10-event cohort.**

This conclusion does not prohibit new separately versioned research questions under Roadmap v6.

---

# 5. SSP v1 result

Precommit:

`ml/TRAJECTORY_SELF_SUPERVISED_PRETRAIN_V1.md`

Result:

`ml/results/trajectory_self_supervised_24h_delta_v1_result.json`

Frozen target-free sample:

- 26 usable events / 12 clubs;
- 3565 usable ~24h pairs;
- 21 train events / 3397 pairs;
- 5 validation events / 168 pairs.

Result:

- zero-change event-balanced MAE: **0.0917223592**;
- model event-balanced MAE: **0.0628961688**;
- Delta: **-0.0288261905**;
- improved validation events: **5/5**;
- attendance labels used: false;
- structural prior used: false.

Decision:

`REPRESENTATION_SUPPORTED`

Encoder artifact:

`ml/artifacts/trajectory_self_supervised_encoder_v1.json`

Do not interpret this as attendance accuracy evidence.

---

# 6. Frozen encoder attendance head v1

Candidate ID:

`trajectory-frozen-encoder-ridge-ratio-head-v1`

Frozen head artifact:

`ml/artifacts/trajectory_frozen_encoder_attendance_head_v1.json`

Protocol:

- frozen 8-d SSP encoder embedding;
- Ridge alpha 10;
- residual-ratio target;
- +/-10% correction cap;
- exact 10-event / 19-row exposed fit cohort;
- no historical candidate selection;
- no historical MAE-based tuning;
- P-7 / P-3 / P-1 prospective only.

The candidate remains frozen. New Roadmap v6 experiments must use new versions/lanes rather than modifying this artifact.

---

# 7. Current data/source semantics to preserve

Public inventory is a demand/inventory proxy, not confirmed sales or attendance.

P-60 is a collection horizon, not a requirement for fabricated full history.

Never forward-fill or interpolate merely to create model input.

Hidden/unknown inventory is never zero.

Known source findings remain fail-closed:

- Motor historical inactive-stage zeroes remain historical and are not rewritten;
- Korona hidden availability remains unknown, not zero;
- Widzew structural prior is resolved; source inventory semantics remain separate;
- Wisła Kraków VAO diagnostic observed **6,870 `occ=0` seats but 0 public-selectable seats under rights semantics**; do not promote those seats without confirmed rights.

---

# 8. Mandatory MAE experiment scoreboard

Every serious Roadmap v6 experiment must register:

| Field | Required |
|---|---|
| Experiment/version ID | yes |
| Hypothesis | yes |
| Incumbent/version | yes |
| Independent events | yes |
| Distinct clubs | yes |
| Coverage | yes |
| Incumbent event-balanced MAE | yes |
| Challenger event-balanced MAE | yes |
| Delta MAE | yes |
| Event improvement rate | yes |
| Median event Delta AE | yes |
| P90 AE / worst-event degradation | yes |
| Signed bias | yes |
| Per-horizon MAE when relevant | yes |
| PIT audit status | yes |
| Decision | yes |

Human-readable registry:

`ml/MAE_EXPERIMENT_SCOREBOARD.md`

---

# 9. Immediate order

1. Read `ml/MAE_RESEARCH_ROADMAP_V6.md`.
2. Query `public.prospective_decision_summary_v1(10)` for fresh live state.
3. Protect an immutable legal cutoff only if one is currently at risk.
4. Never backfill a missed prospective row.
5. Keep frozen prospective candidates unchanged while evidence accumulates.
6. MAE-01 historical diagnostic is reproduced; MAE-02 weighting audit rejected the variant; MAE-03 context audit is complete and data-bound; collect genuine variable context and validate prepared daily-path SQL in an isolated DB, preserving existing C2 rejection and Pre-Live v3 anchor.
7. Use the decomposition to choose the next falsifiable PIT-safe hypothesis instead of guessing a feature.
8. Follow MAE-02 through MAE-08 in evidence-driven order, skipping/reordering only when the preceding evidence clearly justifies it.
9. Update `ml/MAE_EXPERIMENT_SCOREBOARD.md` after every serious challenger.
10. Keep production review-gated and OFF.

## Daily-path diagnostic findings before first outcomes —2026-11-04

Exact coefficient audit:`DAILY_PATH_COEFFICIENT_AUDIT_2026-11-04.md`. All120relative-value-history coefficients are0;57issued points reconcile exactly to latest level/scale plus negative global/observation-pattern terms and clipping. No future accuracy claim, v1retuning or new learner. Separately versioned research should test a restrained genuine-prefix-change mechanism against persistence after its own precommit.

Prefix-regime diagnostics passed8hosted tests(run41816697000), preserve the full-cohort primary denominator and do not drop all-zero cases. Prepared source-statev2passed actualSQL→features integration(run41816696989),20SQL+13adaptercases; project deployment remains blocked.

The separately precommitted fixed24-hour drift comparator was implemented/frozen at11:06:27UTC(SHA332f6fd37bc2a09ce665668ef3c9c23d8d34ec3613f18435ec729d95d3bb43cf). Thirteen tests passed in hosted309-check run41818376777. Actual no-due cycle:0new attempts/points, nullMAE, verified private backup and byte-identical originalv1inputs. Bounded sidecar collecting only new legal post-freeze issues; no old-prediction backfill or fitted-model replacement. That first snapshot preceded a legal issue. First fail-closed drift capture is now proven in `FROZEN_WINDOW_GUARDIAN_EVIDENCE_2026-11-04.md`; READYforecasts and genuine drift labels remain pending.

At11:20UTCthe full guardian→encoderworkflow→success→expected DBattempt chain was proven for Korona603/P-3(run41819915267,DBattempt11:19:48UTC,MODEL_INPUT_INSUFFICIENT). Encoder9/5/0; P9v1 6/0/0,P9v2 5/3/0. Source contracts and historical misses unchanged. Separate localv1captured its8thattempt; drift watcher captured its1stlegal fail-closed attempt with verified backup. No READYdrift forecast/score yet. Evidence:`FROZEN_WINDOW_GUARDIAN_EVIDENCE_2026-11-04.md`.

## C1 same-time audit completed —2026-11-04 12:20UTC

`C1_LIVE_MATCHED_AUDIT_RESULT_V1.md`: all11events /44exact C1-time representatives retained. C1policyMAE4121.45, D2P2MAE5157.52; do not promote D2from the old later-time event5comparison. C1numerical replay matches,900old training cells verified; frozen D2development and original event5goldens reproduce. Wisła/Górnikactual prior metadata have zero season home history; source queue18history checks+6missing outcomes, no guessed labels. External source revalidation blocked. Separate one-factor9→20training-support experiment is precommitted in `C1_TRAINING_EXPANSION_PRECOMMIT_V1.md` before fitting; oldv8and all prospective gates unchanged. All20become training, never fresh holdout. New future evidence required.

### C1 training-support challenger actually frozen —12:27UTC

See `C1_TRAINING_EXPANSION_RESULT_V1.md`. New separate20event/74rowpackage frozen once12:26:39UTC, estimatorSHA04dbdf1e5b8846782194f2ca1e833078a10238d1c9ca151b8391a869449027ba; original30features/Ridge10/policy unchanged. No training-MAEclaim. Current DBinference12:27returns0eligiblecandidates/0predictions/0scores; MAEnull. Privatefreeze/input/lineagebackupbyteverified. Prepared separate bounded collector untilNov6 20:30UTC; startup proof pending at this entry. FirsteligiblewindowNov5 17:00, later than oldworkersdeadline. Candidate needs genuinefuturepairedforecasts and30newscored events/8clubs. No oldmodel/score/gateway/productionwrites.
