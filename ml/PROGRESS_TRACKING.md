# Beyond Ticketing — ML Progress Tracking

Last updated: **2026-11-03**

Status: **CANONICAL TRACKING SNAPSHOT**

Canonical MAE strategy: `ml/MAE_RESEARCH_ROADMAP_V6.md`

Canonical execution plan: `ml/EXECUTION_PLAN_CURRENT.md`

Production: `live_adjustment = 0`

Important: operational counters below are dated snapshots unless explicitly refreshed from live DB.

---

## User-requested daily-path MVP — 2026-11-03 update

The latest user instruction requires **genuine observed prefix → predictions for every remaining day**, updated daily. Terminal attendance alone is insufficient for this product deliverable. The parallel error-driven attendance research programme below remains canonical; the new inventory-path lane has its own observable target, baseline and metrics and does not replace attendance evidence or its 550-seat contract. Partner transactions are unavailable for MVP and are not a prerequisite.

Implementation: [`DAILY_INVENTORY_PATH_IMPLEMENTATION_V1.md`](DAILY_INVENTORY_PATH_IMPLEMENTATION_V1.md). Deployment/recovery: [`DAILY_INVENTORY_PATH_DEPLOYMENT_V1.md`](DAILY_INVENTORY_PATH_DEPLOYMENT_V1.md). Formal lane precommit: [`DAILY_INVENTORY_PATH_PRECOMMIT_V1.md`](DAILY_INVENTORY_PATH_PRECOMMIT_V1.md).

Recorded at 20:01 UTC: 7 local immutable attempts / 57 future-day points / 0 scores, plus verified private Supabase Storage backup and full restore. A bounded host-dependent watcher runs through2026-11-04T17:15Z; its status is `/workspace/ops-runtime/2026-11-03-daily-path/latest-cycle.json`. Inspect it and `watcher.pid` before starting another process. First targets mature2026-11-04T17:00Z. Local/cloud inference is verified; new SQL/gateway/GitHub schedule remain prepared but not deployed/enabled. Panel parser/geometry are verified; full TypeScript check and production build passed in GitHub Actions on the companion panel PR. Local npm access remains blocked. Missing network/management-token requirements are saved as an environment draft, not applied. No private transaction access, production activation or old-model retuning is required.

The attendance history read on2026-11-03 ended at2026-10-25. The six tracked fixtures onOctober30–November2 had no confirmed outcomes in `ticket_event_outcomes`; zero attendance scores are therefore not evidence of zero error. Keep this source-ingestion blocker separate from daily inventory-target scoring.

---

# 1. North Star

> **Minimize true prospective event-balanced attendance-forecast MAE using PIT-safe, reproducible evidence.**

---

# 2. MAE research programme status

| Work package | Status | Current decision |
|---|---|---|
| MAE-01 — Incumbent error decomposition | ✅ HISTORICAL DIAGNOSTIC COMPLETE |603events; all10frozen MAEs reproduced; see `MAE01_INCUMBENT_ERROR_AUDIT_RESULT_V1.md`; hosted checks pending |
| MAE-02 — Structural baseline benchmark | 🟢 NEXT | isolate raw-seat objective weighting with existing medianT-3/T-1specifications; no frozen model mutation |
| MAE-03 — Context residual model | ⚪ QUEUED | form/standings/opponent/fixture/odds; squad only with trustworthy PIT-safe source |
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
6. MAE-01 historical diagnostic is reproduced; continue **MAE-02 structural objective audit** under a separate protocol/version.
7. Use the decomposition to choose the next falsifiable PIT-safe hypothesis instead of guessing a feature.
8. Follow MAE-02 through MAE-08 in evidence-driven order, skipping/reordering only when the preceding evidence clearly justifies it.
9. Update `ml/MAE_EXPERIMENT_SCOREBOARD.md` after every serious challenger.
10. Keep production review-gated and OFF.
