# Beyond Ticketing — ML Progress Tracking

Last updated: **2026-10-25 11:45 Europe/Warsaw**

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
| **P7 Long168** | 🟡 **8/9 / FROZEN UNTIL OUTCOME** | event 6 needs completed match + genuine attendance; T-168 snapshot alone is insufficient |
| P8 club calibration | ✅ DONE | no robust gain |
| **P9 full-168h Booking Curve** | 🟡 REPRESENTATION READY / **4/9** | collect genuine full-window curves; no learner yet |
| **P9a T-24/T-48 target-free freeze** | 🟡 **EXPORT + FREEZE HARNESS READY / LIVE EXPORT** | reconcile source, run main freeze audit, keep labels/model closed |
| **P10 pooled vs local HGB** | ✅ DONE | pooling effect real vs same local HGB |
| **P10b pooled vs Pre-Live v3** | ✅ DONE / `NO_RESEARCH_GAIN` | close fixed pooled-HGB replacement path |
| **P11a PIT market odds v2** | 🟠 **DB + EDGE ACTIVE v2 / 0 GENUINE EVENTS** | first genuine manual capture is immediate priority |
| Governance v2 | ✅ IMPLEMENTED | robust state blocked until business meaningful-MAE threshold exists |
| Production | ⛔ NOT READY | `live_adjustment = 0` |

---

## 4. Fresh live readiness — 2026-10-25 10:39 UTC

Canonical source:

`public.ml_research_readiness_v1()`

### Long72

- reproducible rows: **90**;
- genuine scored events: **0**;
- latest reproducible `as_of_at`: `2026-10-24T16:20:02.672Z`.

### P7 Long168

- rows >72h: `110`;
- independent eligible events: **8**;
- threshold: `9`;
- start trigger: **false**.

Resolved cause of the event-6 expectation mismatch:

- the frozen Long168 exporter requires a completed event;
- it requires genuine `actual_attendance`;
- therefore a valid T-168 snapshot alone does not make the event eligible.

Event 6 — Lech Poznań vs Wisła Kraków, kickoff `2026-10-31 16:30 UTC` — may become the ninth event only after the match is completed and genuine attendance is available upstream.

Decision: **leave P7 frozen**. Do not change the gate or exporter. Execute only when canonical readiness itself reports 9/9.

### P4a

- sidecar rows: `90`;
- READY rows: `88`;
- independent READY events: **5** — IDs `10,16,21,22,23`;
- genuine labeled READY events: **0**;
- primary feature `previous_home_match_days`;
- distinct target-free values: `4`;
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

`P9_BOOKING_CURVE_168_START=false`.

---

## 5. Branch / live reconciliation status

Canonical repo:

`NiedzielX/beyond`

Active implementation branch:

`ml/p9-p11-execution-2026-10-24`

Fresh comparison before reconciliation:

- active branch **32 commits ahead**;
- active branch **14 commits behind**;
- state: diverged.

Required policy:

- canonical docs/governance come from current `main`;
- P9a/P11a implementation files on the active branch must be preserved;
- do not force-push or recreate the implementation;
- reconcile before final active -> main merge.

---

## 6. P9a T-24/T-48 target-free freeze

Files to preserve:

- `ml/p9a_booking_curve_freeze_v1.py`;
- `ml/test_p9a_booking_curve_freeze_v1.py`;
- `supabase/sql/p9a_booking_curve_freeze_v1.sql`;
- `supabase/functions/p9a_booking_curve_export_v1/index.ts`;
- `.github/workflows/p9a-booking-curve-freeze-v1.yml`.

Live Supabase:

- `public.export_p9a_booking_curve_inputs_v1(integer)`;
- `public.export_p9a_booking_curve_labels_v1(bigint[])` — label-only path, keep closed until explicitly allowed;
- Edge Function `p9a_booking_curve_export_v1` ACTIVE v1.

Target-free export latest recorded state:

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

The harness is intentionally freeze-only:

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

## 7. P10 / P10b frozen closeout

### P10 v1 — pooled vs same local HGB

Canonical result:

`ml/results/P10_POOLED_HORIZON_V1_2026-10-23.md`

- local MAE `2120.93`;
- pooled MAE `2057.46`;
- `ΔMAE=-63.47`;
- relative improvement `~2.99%`;
- 95% paired CI `[-106.29,-23.20]`;
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
- folds improved `0/4`;
- horizons improved `0/5`;
- governance `NO_RESEARCH_GAIN`.

Decision: do not retune the fixed pooled-HGB architecture. Future pooling requires a materially new mechanism and new precommit.

---

## 8. P11a market odds v2

Files to preserve:

- `supabase/sql/p11_market_odds_capture_v2.sql`;
- `supabase/functions/p11_odds_capture_v2/index.ts`;
- `supabase/functions/p11_odds_capture_v2/provider.ts`;
- `supabase/functions/p11_odds_capture_v2/provider_test.ts`;
- `.github/workflows/p11-odds-capture-v2.yml`.

Live Supabase:

- raw bookmaker-level v2 table and capture/as-known/readiness RPCs live;
- Edge Function `p11_odds_capture_v2` **ACTIVE v2**;
- genuine raw rows: **0**;
- no automatic schedule enabled.

Important correction: **deployment is complete**. The next missing evidence step is the first genuine provider capture.

Provider:

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

Latest readiness:

- provider selected: true;
- genuine PIT events: `0`;
- events with >=3 bookmakers: `0`;
- model precommitted: false;
- status `CAPTURE_CONTRACT_READY_NO_GENUINE_OBSERVATIONS_YET`.

Current `p11_market_capture_inputs_v2(14)` candidates include:

- event 23 — Śląsk Wrocław vs Wieczysta Kraków — `2026-10-25 11:15 UTC`;
- event 21 — Jagiellonia Białystok vs Wisła Płock — `2026-10-25 13:45 UTC`;
- event 22 — Legia Warszawa vs Lech Poznań — `2026-10-25 16:30 UTC`;
- event 6 — Lech Poznań vs Wisła Kraków — `2026-10-31 16:30 UTC`.

Required secret:

`THE_ODDS_API_KEY`

Configure/verify in Supabase secrets; never commit it.

First capture must be manual and audited before any schedule is enabled. No closing-odds backfill.

---

## 9. Governance v2

Statuses:

- `NO_RESEARCH_GAIN`;
- `POINT_GAIN_UNCERTAINTY_LIMITED`;
- `ROBUST_RESEARCH_ADVANCE`.

Robust advancement requires positive MAE gain, stability, PIT/lineage/reproducibility, a predeclared business-derived minimum meaningful MAE improvement and adequate precision.

Until the business threshold exists, the strongest positive state allowed is `POINT_GAIN_UNCERTAINTY_LIMITED`.

---

## 10. Immediate work order

1. **Reconcile active branch with current main** while preserving P9a/P11a implementation.
2. **Merge P9a/P11a source and workflows to main** after CI/tests.
3. **Verify/configure `THE_ODDS_API_KEY`** in Supabase Edge Function secrets.
4. **Run one genuine manual P11a v2 capture** and audit mapping, quotes, quota, lineage, hashes and consensus; keep schedule off.
5. **Run/verify P9a main target-free T-24/T-48 freeze audit**; keep labels/model closed.
6. **Inspect Long72/P4a actual-attendance/outcome sync** because genuine labels remain zero.
7. **Keep full-168h P9 collecting** toward 9 genuine completed reference events.
8. **Keep P7 frozen at 8/9** until event 6 is completed and genuine attendance becomes available.
9. **Derive business minimum meaningful MAE threshold** independently of model scorecards.

---

## 11. Closed loops

Do not reopen without materially new evidence or mechanism:

- estimator-only tuning;
- repeated uncertainty analysis on same sample;
- simple structural/live shrinkage;
- historical Long72 incremental-value loop;
- simple post-hoc club/opponent calibration;
- fixed P10/P10b pooled-HGB replacement;
- blind model/weight sweeps.

The old ChatGPT Beyond readiness automations are intentionally disabled and must not be enabled implicitly.
