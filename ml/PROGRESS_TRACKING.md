# Beyond Ticketing — ML Progress Tracking

Last updated: **2026-10-25**

Status: **CANONICAL PLAN / STATUS / TRACKING SNAPSHOT**

Canonical strategy: `ml/MAE_RESEARCH_ROADMAP_V4.md`

Operational handoff: `ml/NEXT_SESSION_HANDOFF.md`

Current execution order: `ml/EXECUTION_PLAN_CURRENT.md`

## 1. North star

> **Minimize true out-of-sample attendance-forecast MAE at decision-relevant horizons with PIT-safe, reproducible evidence.**

Current phase: **representation-first, not tuning-first**.

Production remains:

`live_adjustment = 0`

---

## 2. Structural core

Current structural research champion family:

**Structural Prior Runtime v1 / frozen Pre-Live v3 research package**.

- 1,530 Ekstraklasa matches;
- five complete seasons;
- 7,650 PIT rows at T-30/T-14/T-7/T-3/T-1;
- canonical history SHA: `3c6b35142c6bd20a484f2aa758cd41284fd6f4c6db1353b138f81cf321161569`.

Historical seasons already inspected remain exposed R&D evidence.

Frozen Long72 package:

`d2-long72-stage2-p2-observation-maturity-2026-10-21-v1`

Historical development comparison:

- anchor MAE `3707.14`;
- frozen P2 MAE `3012.63`;
- point improvement `694.51 / 18.73%`;
- uncertainty interval crosses zero;
- P2 bias `+917.05`.

Status: **FROZEN / GENUINE POST-FREEZE EVIDENCE ACTIVE**.

---

## 3. Roadmap v4 status

| Item | Status | Current decision |
|---|---|---|
| Long72 forecast-before-label evidence | ✅ RUNNING | immutable persistence + outcome-only scoring |
| P1 temporal validation | ✅ DONE | canonical expanding/forward validation |
| P2 MAE-native tournament | ✅ DONE | no robust structural replacement |
| P3 `ΔMAE` uncertainty | ✅ DONE | estimator-only signal insufficient |
| **P4a previous-home spacing** | 🟡 PRECOMMITTED / 5 READY / 0 LABELS | wait for `>=9` labeled + `>=3` distinct labeled values |
| P4b next-home opponent | 🟡 DATA ACCUMULATING / 0 READY | inspect only when first genuine READY appears |
| P5a structural/live shrinkage | ✅ DONE | retain frozen P2 |
| P5 structural + context + live | ⏸ DATA-BOUND | only after context signal is established |
| P6 historical live incremental value | ✅ DONE HISTORICALLY | positive point signal not enough for promotion |
| **P7 Long168** | 🟠 **8/9 + DIAGNOSTIC REQUIRED** | event 6 expected in window but still not counted |
| P8 club calibration | ✅ DONE | no robust gain |
| **P9 full-168h Booking Curve** | 🟡 REPRESENTATION READY / **4/9** | collect genuine full-window curves; no learner yet |
| **P9a T-24/T-48 target-free freeze** | 🟡 **EXPORT + FREEZE HARNESS READY / LIVE EXPORT** | merge source, run main freeze audit, keep labels/model closed |
| **P10 pooled vs local HGB** | ✅ DONE | pooling effect real vs same local HGB |
| **P10b pooled vs Pre-Live v3** | ✅ DONE / `NO_RESEARCH_GAIN` | close fixed pooled-HGB replacement path |
| **P11a PIT market odds v2** | 🟡 **DB + EDGE CAPTURE INFRA LIVE / 0 GENUINE EVENTS** | merge source, configure secret, run one manual audited capture |
| Governance v2 | ✅ IMPLEMENTED | robust state blocked until business meaningful-MAE threshold exists |
| Production | ⛔ NOT READY | `live_adjustment = 0` |

---

## 4. Fresh live readiness — 2026-10-25 10:18 UTC

Canonical source:

`public.ml_research_readiness_v1()`

### Long72

- reproducible rows: **90**;
- genuine scored events: **0**;
- latest reproducible `as_of_at`: `2026-10-24T16:20:02.672Z`.

### P7 Long168

- rows >72h: `110`;
- independent events >72h: **8**;
- threshold: `9`;
- start trigger: **false**.

Event 6 — Lech Poznań vs Wisła Kraków, kickoff `2026-10-31 16:30Z` — should have crossed T-168 on 2026-10-24, but canonical readiness still reports 8/9 on 2026-10-25.

This is a **diagnostic item**, not an assumed unlock.

Check event 6 snapshots, `72 < h <= 168` eligibility, requested snapshot/as-of identity selection, exporter/readiness freshness and exclusions. Execute P7 only after canonical readiness itself says 9/9.

### P4a

- sidecar rows: `90`;
- READY rows: `88`;
- independent READY events: **5** — IDs `10,16,21,22,23`;
- genuine labeled READY events: **0**;
- primary feature `previous_home_match_days`;
- target-free values `13,36,15,14,15`;
- distinct values `4`;
- gate `>=9 labeled + >=3 distinct labeled values` — closed.

### P4b

- sidecar rows: `90`;
- READY rows: `0`.

### P9 full-window coverage

Completed genuine references:

- 168h: **4 events / 4 clubs**;
- 72h: **7 events / 5 clubs**;
- 48h: **10 events / 6 clubs**;
- 24h: **13 events / 8 clubs**.

`P9_BOOKING_CURVE_168_START = false`.

---

## 5. P9a T-24/T-48 target-free freeze

Active branch source:

`ml/p9-p11-execution-2026-10-24`

Files:

- `ml/p9a_booking_curve_freeze_v1.py`;
- `ml/test_p9a_booking_curve_freeze_v1.py`;
- `supabase/sql/p9a_booking_curve_freeze_v1.sql`;
- `supabase/functions/p9a_booking_curve_export_v1/index.ts`;
- `.github/workflows/p9a-booking-curve-freeze-v1.yml`.

Live Supabase:

- `public.export_p9a_booking_curve_inputs_v1(integer)`;
- `public.export_p9a_booking_curve_labels_v1(bigint[])` — label-only path, keep closed until explicitly allowed;
- Edge Function `p9a_booking_curve_export_v1` ACTIVE v1.

Target-free export checked 2026-10-25:

### T-24

- target events: **18**;
- reference catalog: **19**;
- `target_values_used=false`;
- `post_cutoff_target_snapshots_exported=false`;
- `production_change=false`.

### T-48

- target events: **15**;
- reference catalog: **19**;
- `target_values_used=false`;
- `post_cutoff_target_snapshots_exported=false`;
- `production_change=false`.

The harness is intentionally **freeze-only**:

- exact target/ref/snapshot/incumbent identities are frozen;
- target fields are rejected;
- target snapshots after cutoff are rejected;
- self-event references are excluded;
- reference event must be completed before target cutoff;
- incumbent forecast must already have been persisted before target cutoff;
- deterministic manifest SHA is produced;
- model training is forbidden in this stage.

Next action after branch reconciliation:

1. run/verify main T-24/T-48 target-free freeze audit;
2. persist/check manifest SHAs;
3. require `target_values_opened=false` and `model_training_performed=false`;
4. keep labels/learner blocked until a separate learner/comparator precommit.

Do not confuse P9a near-horizon freeze tooling with opening the full-168h P9 learner, which remains 4/9 data-bound.

---

## 6. P10 / P10b frozen closeout

### P10 v1 — pooled vs same local HGB

Canonical result:

`ml/results/P10_POOLED_HORIZON_V1_2026-10-23.md`

- local MAE `2120.93`;
- pooled MAE `2057.46`;
- `ΔMAE=-63.47`;
- relative improvement `~2.99%`;
- 95% paired CI `[-106.29,-23.20]`;
- event improvement `59.12%`;
- folds improved `3/3`;
- horizons improved `5/5`;
- governance `POINT_GAIN_UNCERTAINTY_LIMITED`.

### P10b — pooled vs frozen Pre-Live v3

Canonical result:

`ml/results/P10B_POOLED_VS_PRELIVE_V3_V1_2026-10-23.md`

- Pre-Live v3 MAE `1919.92`;
- pooled MAE `2067.43`;
- challenger-incumbent `ΔMAE=+147.51`;
- relative degradation `+7.68%`;
- 95% CI `[+82.97,+210.67]`;
- event improvement `43.69%`;
- folds improved `0/4`;
- horizons improved `0/5`;
- governance `NO_RESEARCH_GAIN`.

Decision: do not retune the fixed pooled-HGB architecture. Future pooling requires a materially new mechanism and new precommit.

---

## 7. P11a market odds v2

Active branch source:

`ml/p9-p11-execution-2026-10-24`

Files:

- `supabase/sql/p11_market_odds_capture_v2.sql`;
- `supabase/functions/p11_odds_capture_v2/index.ts`;
- `supabase/functions/p11_odds_capture_v2/provider.ts`;
- `supabase/functions/p11_odds_capture_v2/provider_test.ts`;
- `.github/workflows/p11-odds-capture-v2.yml`.

Live Supabase:

- raw bookmaker-level v2 table and capture/as-known/readiness RPCs live;
- Edge Function `p11_odds_capture_v2` ACTIVE v2;
- genuine raw rows **0**;
- no automatic schedule enabled.

Provider target:

`the-odds-api-v4`

Sport key:

`soccer_poland_ekstraklasa`

Market:

pre-match `h2h` / 1X2.

Architecture:

- bookmaker-level append-only rows;
- provider/capture-batch lineage;
- actual capture timestamp;
- raw decimal odds;
- source payload SHA;
- verified alias + kickoff mapping;
- ambiguous fixtures fail closed;
- de-vig each bookmaker first;
- median probability consensus, then renormalize;
- as-known lookup uses only batches known by requested cutoff and before kickoff.

Semantic guard:

`outcome_uncertainty != expected_match_quality`

Readiness 2026-10-25:

- provider selected true;
- genuine PIT events `0`;
- model precommitted false;
- status `CAPTURE_CONTRACT_READY_NO_GENUINE_OBSERVATIONS_YET`.

Required secret:

`THE_ODDS_API_KEY`

Configure/verify in Supabase secrets; never commit it.

First capture must be manual and audited before any schedule is enabled. No closing-odds backfill.

---

## 8. Governance v2

Implementation:

- `ml/research_advance_governance_v2.py`;
- `ml/test_research_advance_governance_v2.py`.

Statuses:

- `NO_RESEARCH_GAIN`;
- `POINT_GAIN_UNCERTAINTY_LIMITED`;
- `ROBUST_RESEARCH_ADVANCE`.

Robust advancement requires positive MAE gain, stability, PIT/lineage/reproducibility, a predeclared business-derived minimum meaningful MAE improvement and adequate precision.

Until the business threshold exists, the strongest positive state allowed is `POINT_GAIN_UNCERTAINTY_LIMITED`.

---

## 9. Immediate work order

1. **Diagnose P7 event 6** — understand why canonical readiness remains 8/9.
2. **Reconcile/merge active branch** preserving both P9a and P11a v2 implementations.
3. **Run/verify P9a main target-free T-24/T-48 freeze audit**; keep labels/model closed.
4. **Configure/verify `THE_ODDS_API_KEY`**.
5. **Run one manual P11a v2 capture**, audit mapping/quotes/lineage/consensus; keep schedule off.
6. **Keep full-168h P9 collecting** toward 9 genuine reference events.
7. **Derive business minimum meaningful MAE threshold** independently of model scorecards.
8. **Keep P4a/Long72 frozen evidence collection unchanged**.

---

## 10. Closed loops

Do not reopen without materially new evidence or mechanism:

- estimator-only tuning;
- repeated uncertainty analysis on same sample;
- simple structural/live shrinkage;
- historical Long72 incremental-value loop;
- simple post-hoc club/opponent calibration;
- fixed P10/P10b pooled-HGB replacement;
- blind model/weight sweeps.

The old ChatGPT Beyond readiness automations are intentionally disabled and must not be enabled implicitly.