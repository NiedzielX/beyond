# Beyond Ticketing — ML Progress Tracking

Last updated: **2026-10-25**

Status: **CANONICAL PLAN / STATUS / TRACKING SNAPSHOT**

Canonical strategy: `ml/MAE_RESEARCH_ROADMAP_V4.md`

Operational handoff: `ml/NEXT_SESSION_HANDOFF.md`

Current execution order: `ml/EXECUTION_PLAN_CURRENT.md`

## 1. North star

> **Minimize true out-of-sample attendance-forecast MAE at decision-relevant horizons with PIT-safe, reproducible evidence.**

Current phase: **representation-first, not tuning-first**.

Production remains unchanged:

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

### Frozen Long72 package

`d2-long72-stage2-p2-observation-maturity-2026-10-21-v1`

Historical development comparison:

- anchor MAE `3707.14`;
- frozen P2 MAE `3012.63`;
- point improvement `694.51 / 18.73%`;
- event-block interval crosses zero;
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
| **P7 Long168** | 🟠 **8/9 + DIAGNOSTIC REQUIRED** | event 6 expected in window but still not counted; diagnose before execution |
| P8 club calibration | ✅ DONE | no robust gain |
| **P9 Booking Curve** | 🟡 REPRESENTATION READY / **4/9 @168h** | collect genuine full-window curves; no learner yet |
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
- latest reproducible `as_of_at`: `2026-10-24T16:20:02.672Z`;
- first genuine score trigger: false.

### P7 Long168

- rows >72h: `110`;
- independent events >72h: **8**;
- threshold: `9`;
- start trigger: **false**.

Important:

Event 6 — Lech Poznań vs Wisła Kraków, kickoff `2026-10-31 16:30Z` — should have crossed T-168 on 2026-10-24, but canonical readiness still reports 8/9 on 2026-10-25.

This is now a **diagnostic item**, not an assumed unlock.

Check:

1. event 6 snapshots after T-168;
2. `72 < h <= 168` exporter eligibility;
3. requested snapshot/as-of identity selection;
4. readiness/export freshness and any exclusion rule.

Only if readiness itself becomes 9/9 may the frozen P7 executor run.

### P4a fixture context

- sidecar rows: `90`;
- READY rows: `88`;
- independent READY events: **5**;
- event IDs: `10,16,21,22,23`;
- genuine labeled READY events: **0**.

Primary feature:

`previous_home_match_days`

Target-free values:

`13,36,15,14,15`

- non-null `5/5`;
- distinct values `4`;
- labeled gate still `0/9`.

`next_home_match_days` remains a separate sparse feature, not P4a v1.

Fixture-density family remains inactive until genuine variance appears.

### P4b

- sidecar rows: `90`;
- READY rows: `0`.

### P9 booking curve

Completed genuine reference coverage:

- `168h`: **4 events / 4 clubs**;
- `72h`: **7 events / 5 clubs**;
- `48h`: **10 events / 6 clubs**;
- `24h`: **13 events / 8 clubs**.

Status:

`DATA_BOUND`

`P9_BOOKING_CURVE_168_START = false`

No learnable P9 model is precommitted yet.

---

## 5. P10 / P10b frozen closeout

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

Interpretation:

Cross-horizon pooling contains real information relative to the same weaker local-HGB architecture.

### P10b — pooled vs actual frozen champion

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

Decision:

**Do not retune the fixed pooled-HGB architecture after seeing this result.** A future pooling experiment needs a materially different mechanism and a new precommit.

---

## 6. P9 booking-curve / trajectory-shape workstream

Canonical implementation:

- `ml/p9_booking_curve_v1.py`;
- `ml/test_p9_booking_curve_v1.py`;
- `supabase/sql/p9_booking_curve_readiness_v1.sql`;
- `ml/results/P9_BOOKING_CURVE_PRECOMMIT_V1_2026-10-23.md`.

Target representation:

`visible PIT snapshots -> normalized trajectory -> historical curve similarity -> pickup distribution -> remaining-demand estimate -> structural residual challenger`

Canonical grid:

`168,144,120,96,72,60,48,36,24,18,12,6` hours before kickoff.

Hard rules:

- no target snapshot after `as_of_at`;
- no target-future canonical point;
- interpolation only between already-visible target observations;
- no self-event reference;
- reference event completed before target cutoff;
- public inventory is a demand proxy, not confirmed paid sales.

Do not fit/select the first learnable P9 residual model before the full-168h gate. At 9 genuine completed full-window references, freeze the learner contract before opening model-result comparisons.

---

## 7. P11 match attractiveness / commercial context

Priority order:

1. PIT market odds / outcome uncertainty / stakes / rivalry;
2. price / promotion;
3. lineup / star strength / verified absences;
4. weather / attention later.

### P11a v2 — current implementation

Active development branch:

`ml/p9-p11-execution-2026-10-24`

Source files:

- `supabase/sql/p11_market_odds_capture_v2.sql`;
- `supabase/functions/p11_odds_capture_v2/index.ts`;
- `supabase/functions/p11_odds_capture_v2/provider.ts`;
- `supabase/functions/p11_odds_capture_v2/provider_test.ts`;
- `.github/workflows/p11-odds-capture-v2.yml`.

Live Supabase state is temporarily ahead of `main`:

- `private.p11_market_odds_observations_v2` live;
- capture/input/as-known/readiness RPCs live;
- Edge Function `p11_odds_capture_v2` **ACTIVE v2**;
- genuine raw rows: **0**;
- no automatic schedule enabled.

Provider target:

`the-odds-api-v4`

Sport key:

`soccer_poland_ekstraklasa`

Market:

pre-match `h2h` / 1X2 only.

Raw capture design:

- bookmaker-level rows preserved append-only;
- provider event ID and capture batch UUID;
- actual `captured_at`;
- provider update/commence timestamps;
- raw home/draw/away decimal odds;
- source payload SHA-256;
- canonical home/away club keys;
- mapping method and kickoff delta.

Mapping fails closed unless verified aliases match and kickoff is within 5,400 seconds; ambiguous provider events are rejected.

As-known consensus:

1. latest capture batch known by requested cutoff;
2. pre-kickoff only;
3. de-vig each bookmaker independently;
4. median probabilities across bookmakers;
5. renormalize to 1;
6. expose home/draw/away, favorite probability and normalized outcome entropy.

Semantic guard:

`outcome_uncertainty != expected_match_quality`

Expected match quality needs a separate signal/precommit.

Readiness on 2026-10-25 10:19 UTC:

- provider selected: true;
- genuine PIT events: `0`;
- clubs: `0`;
- events with >=3 bookmakers: `0`;
- model precommitted: false;
- status `CAPTURE_CONTRACT_READY_NO_GENUINE_OBSERVATIONS_YET`.

Required secret:

`THE_ODDS_API_KEY`

It must be configured/verified in Supabase Edge Function secrets. Never store it in repo.

First capture must be manual and audited before any schedule is enabled.

Never backfill closing odds into historical cutoffs.

---

## 8. Governance v2

Implementation:

- `ml/research_advance_governance_v2.py`;
- `ml/test_research_advance_governance_v2.py`.

Statuses:

- `NO_RESEARCH_GAIN`;
- `POINT_GAIN_UNCERTAINTY_LIMITED`;
- `ROBUST_RESEARCH_ADVANCE`.

Robust advancement requires:

1. positive MAE point gain;
2. event/fold stability;
3. PIT + lineage + reproducibility pass;
4. predeclared business-derived minimum meaningful MAE improvement;
5. observed gain at least that large;
6. adequate precision, by default a block-bootstrap `ΔMAE` interval fully below zero.

Until the business threshold exists, the strongest positive state allowed is:

`POINT_GAIN_UNCERTAINTY_LIMITED`

Do not derive the threshold from the same model results it will judge.

---

## 9. Immediate work order

1. **P7 event 6 diagnostic** — understand why canonical readiness remains 8/9.
2. **Reconcile/merge active P11 v2 branch** to `main`; preserve the already-live implementation.
3. **Configure/verify `THE_ODDS_API_KEY`** in Supabase Edge Function secrets.
4. **Run one manual P11 v2 capture**, audit mapping/quotes/lineage/consensus; keep schedule off.
5. **Keep P9 collecting** toward 9 full-168h references; harden only representation/lineage before the gate.
6. **Derive business minimum meaningful MAE threshold** independently of model scorecards.
7. **Keep P4a/Long72 frozen evidence collection unchanged**.

---

## 10. Closed loops

Do not reopen without materially new evidence or mechanism:

- estimator-only tuning;
- repeated estimator uncertainty analysis on same sample;
- simple structural/live shrinkage;
- historical Long72 incremental-value loop;
- simple post-hoc club/opponent calibration;
- fixed P10/P10b pooled-HGB replacement;
- blind model/weight sweeps.

P9 and P11 remain valid because they add new representation/information rather than another blind tuning loop.

The old ChatGPT Beyond readiness automations are intentionally disabled and must not be enabled implicitly.