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

Estimator-only MAE challengers did not produce a robust replacement. The incumbent remains unchanged.

## Frozen Long72 package

`d2-long72-stage2-p2-observation-maturity-2026-10-21-v1`

Historical P6 comparison:

- structural anchor MAE `3707.14`;
- frozen P2 MAE `3012.63`;
- `ΔMAE = -694.51` / `18.73%` improvement;
- 95% event-block interval `[-1549.89,+148.05]`;
- `P(ΔMAE<0)=0.9500`;
- structural bias `-242.63`;
- frozen P2 bias `+917.05`.

Status: **FROZEN / GENUINE POST-FREEZE EVIDENCE ACTIVE**

---

# 3. Roadmap tracking

| Roadmap item | Status | Current decision / evidence |
|---|---|---|
| Evidence Lane — Long72 forecast-before-label | ✅ DONE / RUNNING | immutable hourly persistence + outcome-only scoring active |
| P1 — canonical forward/rolling validation | ✅ DONE | strict expanding-season + forward-event folds |
| P2 — MAE-native challenger tournament | ✅ DONE | no robust runtime replacement |
| P3 — `ΔMAE` uncertainty | ✅ DONE | estimator signals did not justify replacement |
| P4a — schedule-as-known / fixture spacing-density | ✅ INFRA DONE / DATA ACCUMULATING | PIT lookup + append-only Long72 sidecar operational |
| P4b — next-home opponent attractiveness | ✅ INFRA DONE / DATA ACCUMULATING | strict schedule + outcome knowledge gates; append-only sidecar operational |
| P5a — structural ↔ live convex shrinkage | ✅ DONE | full frozen P2 retains lowest strict forward-event MAE |
| P5 — structural + context + live combination | ⏸ WAITING FOR P4 LABELED EVIDENCE | start only when context component is genuinely label-ready |
| P6 — live-ticket incremental value | ✅ DONE HISTORICALLY | +18.73% MAE point uplift; CI crosses zero; +917-seat bias guardrail |
| P7 — 72–168h learned model | ⏸ DATA GROWING | exactly `8/9` independent events >72h; 110 rows >72h |
| P8 — club calibration / shrinkage | ⏳ LATER | only if forward evaluation shows generalizable gain |
| Production activation | ⛔ NOT READY | `live_adjustment = 0` |

---

# 4. Closed R&D loops

## P2/P3 estimator loop

Do not repeat without a materially new hypothesis.

- T-30: retain incumbent;
- T-14: retain incumbent;
- T-7: point signal not temporally consistent;
- T-3: tiny point signal, uncertainty crosses zero widely;
- T-1: retain incumbent.

Conclusion: new PIT-safe information is higher priority than more estimator-only tuning.

## P5a structural/live convex shrinkage

`blend(w) = anchor + w * (P2 - anchor)`

Strict forward-event MAE:

| Candidate | MAE |
|---|---:|
| anchor / `w=0` | 3180.22 |
| `w=.25` | 2974.89 |
| `w=.50` | 2776.51 |
| `w=.75` | 2614.46 |
| **frozen P2 / `w=1`** | **2472.30** |
| train-selected weight | 2564.22 |

Train-selected shrinkage is `+91.92` seats worse than full P2.

Decision: **retain frozen P2; no shrinkage replacement.**

---

# 5. P4a — fixture substitution / schedule-as-known

## Schedule evidence

Operational:

- `private.fixture_schedule_batches_v1`;
- `private.fixture_schedule_rows_v1`;
- `public.capture_fixture_schedule_as_known_v1(...)`;
- cron `fixture_schedule_as_known_v1_6h`;
- immutable batches;
- no historical schedule backfill.

First genuine schedule state:

`2026-10-21 20:21:39.668518+00`

PIT lookup:

- `public.fixture_context_as_known_v1(...)`;
- `public.fixture_context_for_ticket_event_as_known_v1(...)`.

Current feature family:

- previous-home spacing;
- next-home spacing when known;
- team fixture density next 7/14/30d;
- home fixture density next 7/14/30d;
- previous/next home opponent identity.

## Long72 fixture-context sidecar

Operational:

- `private.d2_long72_fixture_context_v1`;
- `public.capture_d2_long72_fixture_context_v1(...)`;
- cron `7,22,37,52 * * * *`;
- append-only one-to-one sidecar per reproducible forecast.

Latest checkpoint:

- 12 reproducible Long72 predictions;
- 12 fixture-context sidecar rows;
- 10 `READY`;
- 2 `NO_SCHEDULE_STATE_AS_OF` from forecasts before the first schedule capture.

No later schedule knowledge is substituted into those two rows.

---

# 6. P4b — next-home opponent attractiveness

Operational PIT lookup:

- `public.opponent_attractiveness_as_known_v1(...)`;
- `public.next_home_opponent_attractiveness_for_ticket_event_as_known_v1(...)`.

Append-only Long72 sidecar:

- `private.d2_long72_next_opponent_attractiveness_v1`;
- `public.capture_d2_long72_next_opponent_attractiveness_v1(...)`;
- cron `9,24,39,54 * * * *`.

Readiness requires both:

1. next home opponent known in a schedule batch with `observed_at <= forecast_as_of_at`;
2. attendance history system-known by the same cutoff: kickoff + outcome created/updated/confirmed timestamps all no later than `forecast_as_of_at`.

Attractiveness metric:

`opponent_uplift_pct = (opponent_median_attendance / club_median_attendance - 1) * 100`

with readiness gates:

- club history `>=8`;
- opponent history `>=3`.

Initial sidecar checkpoint:

- 12 rows processed;
- 2 `FIXTURE_CONTEXT_NO_SCHEDULE_STATE_AS_OF`;
- 10 `NO_NEXT_HOME_MATCH_IN_SCHEDULE_STATE`;
- 0 `READY`.

This is deliberate fail-closed evidence behavior. Current captured schedules do not yet expose the later home fixture required to score the feature for events 10/16.

Do **not** replace these missing values with later schedule knowledge or a hand-authored opponent score.

---

# 7. P6 — live incremental value

Formal historical exposed comparison:

### 24–72h

- `ΔMAE = -694.51`;
- relative improvement `18.73%`;
- event improvement rate `61.54%`;
- 95% interval `[-1549.89,+148.05]`;
- `P(ΔMAE<0)=0.9500`.

### 24–48h

- `ΔMAE = -954.58`;
- relative improvement `25.75%`;
- 95% interval `[-2001.66,+13.10]`.

### 48–72h

- `ΔMAE = -664.71`;
- relative improvement `14.47%`;
- 95% interval `[-1463.31,+241.98]`.

Guardrail: frozen live/P2 has `+917.05` event-balanced bias on the full development set.

Conclusion: live inventory contains material incremental signal, but genuine prospective evidence remains required before promotion.

---

# 8. Current prospective/data readiness

Long72 latest checkpoint:

- reproducible forecast rows: `12`;
- fixture-context sidecar rows: `12` (`10 READY`);
- next-opponent sidecar rows: `12` (`0 READY`);
- scored genuine Long72 events: `0` because current precommitted events have no final attendance yet.

Long168 latest audit:

- `8` independent events >72h;
- `110` rows >72h;
- predeclared research-start floor remains exactly `N>=9`.

Do not lower the threshold.

---

# 9. Immediate work order

1. **keep Long72 forecast, schedule-as-known, fixture-context and next-opponent sidecars collecting automatically**;
2. monitor for the first `READY` next-opponent rows as later home fixtures become genuinely known;
3. once labeled P4 events accumulate, run controlled schedule/context ablations;
4. only then run P5 `structural + context + live` combinations;
5. continue final24 + Long72 genuine prospective evidence automatically;
6. trigger P7 immediately at the ninth independent >72h event;
7. keep P8 lower priority;
8. keep production unchanged.

## One-line handoff

> **All currently unblocked P4 evidence infrastructure is operational and fail-closed. Estimator tuning, historical live-value testing and simple structural/live shrinkage are closed. The next model-selection step requires genuine labeled context evidence; Long168 remains 8/9.**
