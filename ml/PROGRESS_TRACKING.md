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

Current incumbent: **Structural Prior Runtime v1 / Global Model family**.

- 1,530 Ekstraklasa matches / five complete seasons;
- 7,650 PIT snapshots;
- T-30/T-14/T-7/T-3/T-1;
- canonical history SHA: `3c6b35142c6bd20a484f2aa758cd41284fd6f4c6db1353b138f81cf321161569`.

Estimator-only MAE challengers and post-hoc club calibration did not justify a runtime replacement.

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

Status: **FROZEN / GENUINE POST-FREEZE EVIDENCE ACTIVE**.

---

# 3. Roadmap tracking

| Roadmap item | Status | Decision / evidence |
|---|---|---|
| Evidence Lane — Long72 forecast-before-label | ✅ DONE / RUNNING | immutable hourly persistence + outcome-only scoring active |
| P1 — canonical forward/rolling validation | ✅ DONE | strict expanding-season + forward-event folds |
| P2 — MAE-native challenger tournament | ✅ DONE | no robust runtime replacement |
| P3 — `ΔMAE` uncertainty | ✅ DONE | estimator signals did not justify replacement |
| P4a — schedule-as-known / fixture spacing-density | ✅ INFRA DONE / DATA ACCUMULATING | PIT lookup + append-only Long72 sidecar operational |
| P4b — next-home opponent attractiveness | ✅ INFRA DONE / DATA ACCUMULATING | strict schedule + outcome knowledge gates; append-only sidecar operational |
| P5a — structural ↔ live convex shrinkage | ✅ DONE | full frozen P2 retains lowest strict forward-event MAE |
| P5 — structural + context + live combination | ⏸ DATA-BOUND | wait for genuine labeled P4 context evidence |
| P6 — live-ticket incremental value | ✅ DONE HISTORICALLY | +18.73% MAE point uplift; CI crosses zero; +917-seat bias guardrail |
| P7 — 72–168h learned model | ⏸ DATA-BOUND | `8/9` independent events >72h; 110 rows >72h |
| P8 — club calibration / shrinkage | ✅ DONE | small 0.15–0.38% point gains; all CIs cross zero; retain incumbent |
| Production activation | ⛔ NOT READY | `live_adjustment = 0` |

---

# 4. Closed R&D loops

## P2/P3 — estimator-only loop

Do not repeat without materially new information.

- T-30: retain incumbent;
- T-14: retain incumbent;
- T-7: point signal not temporally consistent;
- T-3: tiny point signal, uncertainty crosses zero widely;
- T-1: retain incumbent.

Conclusion: new PIT-safe information is more valuable than further estimator-only tuning.

## P5a — structural/live convex shrinkage

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

Decision: **retain frozen P2; no shrinkage replacement**.

## P8 — club calibration / shrinkage

Primary policy:

- rolling home-club median signed-error correction;
- conservative shrinkage `n/(n+80)`;
- strict forward order;
- tied kickoff fixtures cannot train each other;
- immutable OOS incumbent predictions from the MAE tournament artifact.

Result:

| Horizon | Incumbent MAE | Calibrated MAE | ΔMAE | Relative | 95% CI |
|---|---:|---:|---:|---:|---:|
| T-30 | 2094.98 | 2086.93 | -8.05 | -0.38% | [-20.47,+4.45] |
| T-14 | 1984.98 | 1977.95 | -7.03 | -0.35% | [-16.49,+2.35] |
| T-7 | 2016.68 | 2011.63 | -5.05 | -0.25% | [-17.12,+7.00] |
| T-3 | 1914.35 | 1911.45 | -2.90 | -0.15% | [-10.84,+4.84] |
| T-1 | 1912.17 | 1908.48 | -3.69 | -0.19% | [-11.43,+4.18] |

Additional guardrails:

- every 95% interval crosses zero;
- home-club improvement rate only ~46–54%;
- every horizon has season instability;
- away-opponent residual calibration is weaker.

Decision: **RETAIN INCUMBENT — NO ROBUST CLUB CALIBRATION GAIN**.

P8 is closed for simple post-hoc residual calibration. Reopen only with materially new evidence/mechanism.

---

# 5. P4a — schedule-as-known / fixture context

Operational:

- `private.fixture_schedule_batches_v1`;
- `private.fixture_schedule_rows_v1`;
- `public.capture_fixture_schedule_as_known_v1(...)`;
- immutable versioned schedule state;
- no historical final-schedule backfill.

First genuine schedule state:

`2026-10-21 20:21:39.668518+00`

PIT lookup:

- `public.fixture_context_as_known_v1(...)`;
- `public.fixture_context_for_ticket_event_as_known_v1(...)`.

Features:

- previous-home spacing;
- next-home spacing when known;
- team fixture density next 7/14/30d;
- home fixture density next 7/14/30d;
- previous/next home opponent identity.

Long72 append-only sidecar:

- `private.d2_long72_fixture_context_v1`;
- `public.capture_d2_long72_fixture_context_v1(...)`;
- automatic every 15 minutes.

Latest checkpoint:

- `16` reproducible Long72 forecasts;
- `16` fixture-context sidecar rows;
- `14 READY`;
- `2 NO_SCHEDULE_STATE_AS_OF`.

The two unavailable rows remain unavailable by design; no later schedule knowledge is substituted.

---

# 6. P4b — next-home opponent attractiveness

Operational:

- `public.opponent_attractiveness_as_known_v1(...)`;
- `public.next_home_opponent_attractiveness_for_ticket_event_as_known_v1(...)`;
- `private.d2_long72_next_opponent_attractiveness_v1`;
- automatic append-only capture every 15 minutes.

READY requires:

1. next home opponent known in a schedule state with `observed_at <= forecast_as_of_at`;
2. historical attendance outcome kickoff + created/updated/confirmed timestamps all no later than the same cutoff;
3. club history `>=8`;
4. opponent history `>=3`.

Current checkpoint:

- `16` sidecar rows;
- `0 READY`.

The active schedule states do not yet contain the later home fixture required for the feature. Missing knowledge remains fail-closed.

---

# 7. P6 — live incremental value

### 24–72h

- anchor MAE `3707.14`;
- frozen live/P2 MAE `3012.63`;
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

Guardrail: frozen live/P2 has `+917.05` event-balanced bias on the full development sample.

Conclusion: live inventory contains material incremental signal, but promotion still requires genuine prospective evidence.

---

# 8. Current data readiness

Long72:

- reproducible forecast rows: `16`;
- fixture-context sidecar rows: `16` (`14 READY`);
- next-opponent sidecar rows: `16` (`0 READY`);
- scored genuine Long72 events: `0` because active precommitted matches do not yet have final attendance.

Long168:

- `8` independent events >72h;
- `110` rows >72h;
- research-start threshold remains exactly `N>=9`.

Do not lower the threshold.

---

# 9. Immediate operating mode

All currently unblocked planned R&D loops are complete.

Continue automatically:

1. Long72 forecast-before-label persistence;
2. final24 prospective evidence;
3. schedule-as-known capture;
4. fixture-context sidecar;
5. next-opponent-attractiveness sidecar.

Trigger only when evidence becomes valid:

6. **P4 ablation** — after genuine labeled context events exist;
7. **P5 structural + context + live** — only after P4 produces a genuine context component;
8. **P7 Long168** — immediately when independent >72h event count reaches `9`.

Do not reopen estimator-only tuning, simple structural/live shrinkage, or post-hoc club calibration without materially new evidence.

Production remains unchanged.

## One-line handoff

> **P1/P2/P3/P5a/P6/P8 are closed; all P4 evidence infrastructure is operational and fail-closed. The remaining roadmap is genuinely data-bound: labeled context for P4/P5 and one more independent >72h event for P7.**
