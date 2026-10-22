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

Formal P6 event-block uncertainty:

- `ΔMAE = -694.51` seats;
- 95% interval `[-1549.89, +148.05]`;
- `P(ΔMAE < 0) = 0.9500`;
- anchor bias `-242.63`;
- live/P2 bias `+917.05`.

Interpretation: **material historical incremental live value, but N=13 remains uncertainty-limited and positively biased.**

Status: **FROZEN / GENUINE POST-FREEZE EVIDENCE ACTIVE**

True forecast-before-label infrastructure is operational. Manual bootstrap rows remain audit-only and excluded from the official scorecard.

---

# 3. Roadmap tracking

| Roadmap item | Status | Current decision / evidence |
|---|---|---|
| Evidence Lane — Long72 forecast-before-label | ✅ DONE / RUNNING | immutable hourly persistence + outcome-only scoring active |
| P1 — canonical forward/rolling validation | ✅ DONE | strict expanding-season + forward-event folds |
| P2 — MAE-native challenger tournament | ✅ DONE | no robust runtime replacement |
| P3 — `ΔMAE` uncertainty | ✅ DONE | estimator signals did not justify replacement |
| P4 — PIT-safe next-fixture / cannibalization | 🟡 **INFRA DONE / DATA ACCUMULATING** | schedule-as-known + PIT lookup + Long72 append-only context sidecar operational |
| P5a — structural ↔ live convex shrinkage | ✅ DONE | full frozen P2 retains lowest strict forward-event MAE; no shrinkage replacement |
| P5 — structural + context + live combination | ⏸ WAITING FOR P4 EVIDENCE | start once genuine context component is label-ready |
| P6 — live-ticket incremental value | ✅ DONE HISTORICALLY | +18.73% MAE point uplift; CI crosses zero; +917-seat bias guardrail |
| P7 — 72–168h learned model | ⏸ DATA GROWING | exactly `8/9` independent events >72h; 110 rows >72h |
| P8 — club calibration / shrinkage | ⏳ LATER | only if forward evaluation shows generalizable gain |
| Production activation | ⛔ NOT READY | `live_adjustment = 0` |

---

# 4. P2/P3 — estimator tournament closed

Canonical input: 1,530 matches / 7,650 PIT rows.

Strict expanding-season folds:

1. 2021/22 + 2022/23 -> 2023/24;
2. through 2023/24 -> 2024/25;
3. through 2024/25 -> 2025/26.

Result:

- T-30: retain incumbent;
- T-14: retain incumbent;
- T-7: candidate point delta about `-20.76`, but only `1/3` fold wins;
- T-3: candidate point delta about `-4.33`, but paired uncertainty crosses zero widely;
- T-1: retain incumbent.

Conclusion: **do not spend the next cycle on more estimator-only tuning.** New PIT-safe information is the higher-value MAE path.

---

# 5. P4 — fixture substitution / cannibalization

## Schedule-as-known contract

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

- `previous_home_match_days`;
- `next_home_match_days`;
- team fixture density next 7/14/30 days;
- home fixture density next 7/14/30 days;
- previous/next home opponent identity for later attractiveness joins.

Fail-closed behavior is verified: a forecast timestamp before the first captured schedule state returns `NO_SCHEDULE_STATE_AS_OF` rather than using a later schedule.

## Long72 fixture-context sidecar

Operational in Supabase:

- `private.d2_long72_fixture_context_v1`;
- `public.capture_d2_long72_fixture_context_v1(...)`;
- cron `d2_long72_fixture_context_sidecar_v1_15m` at `7,22,37,52 * * * *`;
- one immutable sidecar row per reproducible Long72 prediction;
- production forecast is untouched.

Initial capture:

- 12 reproducible Long72 prediction rows processed;
- 10 `READY` context rows;
- 2 pre-schedule-capture rows permanently recorded as `NO_SCHEDULE_STATE_AS_OF`.

This means future labels can be joined to context that was genuinely known at forecast time without reconstructing context from the future.

## P4 limitation

A truthful historical schedule-version ablation before `2026-10-21 20:21:39+00` is impossible because no historical schedule state was captured then.

Therefore P4 is **not blocked operationally**, but model selection is **data accumulating**. Do not manufacture historical PIT evidence from today's final schedule.

---

# 6. P5a — structural/live convex shrinkage

Frozen blend family:

`blend(w) = anchor + w * (P2 - anchor)`

with `w ∈ {0,.25,.50,.75,1}` plus a train-only selected weight.

Strict forward-event evaluation:

| Candidate | Event-balanced MAE |
|---|---:|
| anchor / `w=0` | 3180.22 |
| `w=.25` | 2974.89 |
| `w=.50` | 2776.51 |
| `w=.75` | 2614.46 |
| **frozen P2 / `w=1`** | **2472.30** |
| train-selected weight | 2564.22 |

Train-selected shrinkage is `+91.92` seats worse than full P2. Its paired event-block interval versus P2 is `[-126.79,+324.24]`.

Decision: **retain frozen P2; no shrinkage replacement.**

P5 remains open only for genuinely different information, especially `structural + context + live`.

---

# 7. P6 — live incremental value

Formal historical exposed comparison:

### 24–72h

- anchor MAE `3707.14`;
- frozen live/P2 MAE `3012.63`;
- `ΔMAE = -694.51`;
- relative improvement `18.73%`;
- event improvement rate `61.54%`;
- 95% paired event-block interval `[-1549.89,+148.05]`;
- `P(ΔMAE<0)=0.9500`.

### 24–48h

- `ΔMAE = -954.58`;
- relative improvement `25.75%`;
- 95% interval `[-2001.66,+13.10]`.

### 48–72h

- `ΔMAE = -664.71`;
- relative improvement `14.47%`;
- 95% interval `[-1463.31,+241.98]`.

Important guardrail:

- anchor event-balanced bias `-242.63`;
- frozen live/P2 bias `+917.05`.

Conclusion: live inventory contains valuable information beyond the structural anchor, but genuine prospective evidence is still required and the positive bias must remain visible in any future challenger evaluation.

---

# 8. 72–168h readiness

Latest audit:

- `8` independent events with valid observations >72h;
- `110` rows >72h;
- observed range approximately `72.17h–166.12h`;
- predeclared research-start floor remains exactly `N>=9`.

P7 has **not started**. Do not move the threshold. At the ninth independent event: freeze exact identities first, then open the separate 72–168h challenger cycle.

---

# 9. Immediate work order

1. **keep P4 schedule-as-known + Long72 context sidecar collecting automatically**;
2. **add next-opponent attractiveness only through a PIT-safe observed source; never recompute historical values from final outcomes**;
3. once enough labeled P4 context exists, run controlled context ablations;
4. then run the remaining P5 `structural + context + live` combination tournament;
5. continue final24 + Long72 genuine prospective evidence automatically;
6. trigger P7 immediately when independent >72h event coverage reaches `9`;
7. keep P8 lower priority;
8. keep production unchanged.

## One-line handoff

> **Estimator R&D, uncertainty, historical live incremental value and simple structural/live shrinkage are complete. P4 forward context evidence is now being captured automatically beside every Long72 prediction; the next model-selection opportunity is genuine context + live once those labels exist, while Long168 remains 8/9.**
