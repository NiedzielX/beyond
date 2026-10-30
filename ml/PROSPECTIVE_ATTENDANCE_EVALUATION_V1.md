# Beyond Ticketing — Prospective Attendance Evaluation v1

Status: **PRECOMMITTED BEFORE FIRST SCORED FROZEN-ENCODER / P9-v2 TARGET OUTCOME**

Precommit date: **2026-10-30**

Production impact: **none**

`live_adjustment = 0`

---

# 1. Purpose

This protocol freezes how genuinely prospective attendance challengers are evaluated after immutable predictions receive confirmed attendance outcomes.

It exists to prevent metric selection, horizon pooling or decision criteria from being changed after seeing early results.

This protocol does **not** define a business minimum meaningful improvement in seats. That threshold must be set independently of observed challenger results before any production-promotion decision.

---

# 2. Lanes remain separate

The following evidence must not be pooled into one challenger score:

1. `trajectory-frozen-encoder-ridge-ratio-head-v1`;
2. P9 prospective v1;
3. P9 Family Fallback v2;
4. Form5 prospective challenger v1.

Each lane has different eligibility and coverage mechanics. Missing predictions and fail-closed attempts are evidence about coverage, not zero-error forecasts.

---

# 3. Independent evaluation unit

The independent unit is the **ticket event / match**.

A model can have multiple prediction horizons for one event. Those rows are correlated observations and must not give that event extra weight in the overall result.

Therefore:

1. calculate absolute error for each immutable prediction row;
2. for an overall multi-horizon result, first average errors within each event;
3. then average the event-level values across events.

This is the primary **event-balanced MAE**.

Per-horizon MAE is reported separately and uses one row per event/horizon.

---

# 4. Primary metric

For each scored row:

`incumbent_AE = abs(actual_attendance - incumbent_p50)`

`challenger_AE = abs(actual_attendance - challenger_p50)`

`Delta_AE = challenger_AE - incumbent_AE`

For each event with multiple horizons:

`event_incumbent_AE = mean(incumbent_AE rows for event)`

`event_challenger_AE = mean(challenger_AE rows for event)`

`event_Delta_AE = event_challenger_AE - event_incumbent_AE`

Across events:

`incumbent_event_balanced_MAE = mean(event_incumbent_AE)`

`challenger_event_balanced_MAE = mean(event_challenger_AE)`

`Delta_MAE = challenger_event_balanced_MAE - incumbent_event_balanced_MAE`

Desired direction: **Delta_MAE < 0**.

---

# 5. Mandatory supporting metrics

For every lane report:

- independent scored event count;
- distinct club count;
- scored prediction-row count;
- prediction coverage separately from accuracy;
- incumbent event-balanced MAE;
- challenger event-balanced MAE;
- Delta MAE;
- event improvement rate: share of events with `event_Delta_AE < 0`;
- median event Delta AE;
- worst-event degradation: maximum positive event Delta AE;
- best-event improvement: minimum event Delta AE.

For trajectory and P9, also report results separately by frozen horizon.

Do not hide a weak horizon inside a pooled overall number.

---

# 6. Evidence review gate

Early results remain descriptive until the lane has at least:

- **8 independent scored events**; and
- **5 distinct clubs**.

Before both conditions are met, status is:

`PROSPECTIVE_COLLECTING`

After both conditions are met, status may become:

`EVIDENCE_REVIEW_READY`

This is only a minimum review gate. It is **not** an automatic production-promotion rule and does not imply statistical certainty.

Do not change the frozen model after the first 1–2 outcomes merely because Delta MAE is positive or negative.

---

# 7. Horizon reporting

## Frozen trajectory encoder

Report separately:

- P-7;
- P-3;
- P-1;
- event-balanced overall across all available frozen horizons.

An event with all three horizons still receives the same overall event weight as an event with one eligible horizon.

## P9 v2

Report separately:

- T-48;
- T-24;
- event-balanced overall across available fallback predictions.

P9 v1 and v2 remain separate. A v2 fallback row never replaces a v1 fail-closed attempt.

---

# 8. Missingness and fail-closed behavior

The following are not scored as predictions:

- `MISSED_WINDOW`;
- input-insufficient attempts;
- `PIT_SUPPORT_INSUFFICIENT`;
- fallback-support-insufficient attempts;
- checkpoints before operational activation that were not expected to run.

Coverage must be reported separately.

Never impute a challenger forecast after the target outcome is known merely to increase coverage.

---

# 9. Outcome eligibility

A row may be scored only when:

1. the prediction was persisted prospectively before the attendance outcome was known;
2. the attendance outcome is genuine and confirmed;
3. `attendance_confirmed_at > predicted_at`;
4. the stored prediction identity/lineage remains unchanged;
5. `production_change=false` for the research lane.

No manual target correction may be used to rescue a prospective row after the fact.

---

# 10. Decision discipline

When the review gate opens:

1. inspect the precommitted primary and supporting metrics;
2. inspect per-horizon behavior and coverage;
3. inspect worst-event degradation and event improvement rate;
4. compare against an independently defined business minimum meaningful effect;
5. make a separate reviewed decision whether to continue collecting, reject, iterate under a **new version**, or consider promotion.

Any model/feature/cap/alpha/horizon change after outcomes have been observed creates a new candidate version and a new prospective evidence stream.

Production remains OFF until a separate explicit promotion decision.
