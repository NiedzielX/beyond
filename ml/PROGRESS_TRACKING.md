# Beyond Ticketing — ML Progress Tracking

Last updated: **2026-10-22**

Status: **CANONICAL PLAN / STATUS / TRACKING SNAPSHOT**

Canonical strategy: `ml/MAE_RESEARCH_ROADMAP_V3.md`

## 1. North star

> **Minimize true out-of-sample attendance-forecast MAE at decision-relevant horizons with PIT-safe, reproducible evidence.**

Production remains unchanged:

`live_adjustment = 0`

---

# 2. Current model state

## Global historical / structural core

Current production/research incumbent: **Structural Prior Runtime v1 / Global Model family**

- 1,530 Ekstraklasa matches / five complete seasons;
- 7,650 PIT snapshots;
- T-30/T-14/T-7/T-3/T-1;
- committed canonical history SHA: `3c6b35142c6bd20a484f2aa758cd41284fd6f4c6db1353b138f81cf321161569`.

Estimator-only MAE challengers did not produce a robust replacement. The incumbent remains unchanged after forward-fold tournament + paired fixture-block uncertainty.

## Final24 frozen evidence lane

`Frozen Pre-Live v2 + P2 reliability * frozen ridge-a10 delta`

Status: **FROZEN / PROSPECTIVE VALIDATION ACTIVE**

## Pre-Live v3

`pre-live-v3-historical-candidate-2026-10-21-v1`

Historical 20-cell mean MAE:

`1934.04 -> 1924.64`, improvement `+9.39 / +0.49%`.

Status: **FROZEN RESEARCH CANDIDATE**

## Early-live Long72

Package:

`d2-long72-stage2-p2-observation-maturity-2026-10-21-v1`

Historical development:

- anchor MAE `3707.14`;
- package MAE `3012.63`;
- uplift `+694.51 / +18.73%`.

Status: **FROZEN / GENUINE POST-FREEZE EVIDENCE ACTIVE**

True forecast-before-label infrastructure is operational. First reproducible pre-outcome events: 10 and 16. Official scorecard excludes manual bootstrap rows and scores only reproducible pre-outcome forecasts.

---

# 3. Roadmap tracking

| Roadmap item | Status | Current decision / evidence |
|---|---|---|
| Evidence Lane — Long72 forecast-before-label | ✅ DONE / RUNNING | immutable hourly persistence + outcome-only scoring active |
| P1 — canonical forward/rolling validation | ✅ DONE | `temporal_validation_v1.py`; strict expanding-season + forward-event folds |
| P2 — MAE-native challenger tournament | ✅ DONE | no robust runtime replacement; only tiny T-3 point signal |
| P3 — `ΔMAE` uncertainty | ✅ DONE | T-3 signal not distinguishable from zero; incumbent retained |
| P4 — PIT-safe next-fixture / cannibalization | 🔄 ACTIVE | forward schedule-as-known store deployed; feature materialization/ablation next |
| P5 — forecast combination | ⏳ NEXT | mean/median/fixed convex/MAE-optimized convex; wait for materially different context forecast |
| P6 — live-ticket incremental value | ⏳ NEXT | formal structural-only vs structural+live residual experiment not yet run |
| P7 — 72–168h learned model | ⏸ DATA GROWING | exactly `8/9` independent events >72h; 110 rows >72h |
| P8 — club calibration / shrinkage | ⏳ LATER | lower priority; only if improvement survives forward evaluation |
| Production activation | ⛔ NOT READY | `live_adjustment = 0` |

---

# 4. P2 — MAE-native tournament result

Canonical input: 1,530 matches / 7,650 PIT rows.

Strict expanding-season folds:

1. 2021/22 + 2022/23 -> 2023/24;
2. through 2023/24 -> 2024/25;
3. through 2024/25 -> 2025/26.

Predeclared challengers:

- incumbent runtime;
- `quantile-linear-a0005`;
- `quantile-linear-a002`;
- `gbr-l1-depth2`.

Outcome:

- T-30: retain incumbent;
- T-14: retain incumbent;
- T-7: challenger mean delta about `-20.76` seats but only `1/3` fold wins -> reject by selector;
- T-3: `quantile-linear-a002` mean-fold delta about `-4.33` seats, `2/3` fold wins -> advance only to uncertainty diagnostic;
- T-1: retain incumbent.

No frozen runtime changed.

---

# 5. P3 — uncertainty result

Paired fixture-block bootstrap, 5,000 resamples, stratified by temporal fold.

T-3 `quantile-linear-a002`:

- event-level `ΔMAE = -5.16` seats;
- 95% interval `[-88.84, +80.55]`;
- `P(ΔMAE < 0) = 0.534`;
- event improvement rate `45.56%`;
- decision: **RETAIN INCUMBENT — EFFECT NOT DISTINGUISHABLE FROM ZERO**.

T-7 diagnostic:

- `ΔMAE = -21.16` seats;
- 95% interval `[-114.01, +73.77]`;
- `P(ΔMAE < 0) = 0.6782`;
- fold wins `1/3`;
- decision: **RETAIN INCUMBENT — TEMPORAL CONSISTENCY FAILED**.

Conclusion: estimator-only tuning is closed for this candidate family. R&D shifts to new PIT-safe information/context.

---

# 6. P4 — fixture substitution / cannibalization

Status: **ACTIVE**.

Safety decision:

Do not backfill historical next-fixture context from today's final schedule and call it PIT-safe. Historical reschedules could leak future information.

Forward schedule-as-known infrastructure is deployed in Supabase:

- `private.fixture_schedule_batches_v1`;
- `private.fixture_schedule_rows_v1`;
- `public.capture_fixture_schedule_as_known_v1(...)`;
- forward-only capture: `observed_at` must be close to `now()`;
- unchanged schedule states are fingerprint-deduplicated;
- historical backfill is explicitly disallowed.

Current captured state:

- `3` schedule batches;
- `351` versioned schedule rows.

Next P4 implementation:

1. commit/deploy the schedule-as-known migration source in repo;
2. implement PIT lookup using only schedule batch `observed_at <= as_of_at`;
3. materialize first safe feature family:
   - `next_home_match_days`;
   - `previous_home_match_days`;
   - `fixture_density_7d`;
   - `fixture_density_14d`;
   - `fixture_density_30d`;
4. add next-opponent attractiveness separately from a PIT-safe opponent-demand source;
5. run controlled ablation against the unchanged incumbent using the canonical temporal contract;
6. advance only if future/forward MAE improves.

---

# 7. 72–168h readiness

Latest audit:

- `8` independent events with valid observations >72h;
- `110` rows >72h;
- observed range above 72h: approximately `72.17h–166.12h`;
- predeclared research-start threshold remains `N>=9`.

Therefore P7 **has not started**. Do not move the threshold. At the ninth independent event: freeze exact identities first, then open the predeclared 72–168h challenger cycle.

---

# 8. Immediate work order

1. **finish P4 schedule-as-known repo/feature contract**;
2. **materialize PIT-safe fixture-spacing/density features**;
3. **run P4 controlled ablation against incumbent**;
4. if P4 creates a materially different useful forecast, **run P5 forecast-combination tournament**;
5. run **P6 structural-only vs structural+live incremental-value experiment**;
6. keep final24 + Long72 prospective evidence collecting automatically;
7. continuously monitor P7 readiness; trigger only when independent >72h event count reaches `9`;
8. keep P8 lower priority;
9. keep production unchanged.

## One-line handoff

> **Validation, estimator tournament and uncertainty are complete. They did not justify a model replacement. The active MAE opportunity is now new PIT-safe information: fixture substitution/cannibalization first, then combinations and incremental live-ticket value.**
