# Beyond Ticketing — Trajectory Feature Contract v1

Frozen for development: **2026-10-28**

Status: **FROZEN DEVELOPMENT CONTRACT / RESEARCH-ONLY**

Contract ID:

`trajectory-feature-contract-v1`

Canonical strategy:

- `ml/MAE_RESEARCH_ROADMAP_V5.md`;
- `ml/TRAJECTORY_FORECASTING_PLAN_V1.md`;
- `ml/EXECUTION_PLAN_CURRENT.md`.

This contract defines the **shared information boundary** for the first Lane A vs Lane B trajectory comparison.

It is not a production activation contract and is not yet a prospective promotion precommit.

`live_adjustment = 0`

---

# 1. Human summary

The first comparison must answer one clean question:

> **Does an ordered sequence model learn useful trajectory information beyond a simpler model built from explicit trajectory features?**

To answer that honestly, Lane A and Lane B must see the same underlying event history and the same structural attendance anchor.

They may represent that history differently:

- Lane A receives a fixed scalar feature vector;
- Lane B receives the genuine ordered snapshot sequence plus a small shared global context.

Neither lane may receive extra odds, weather, hype, match-stakes or other context in v1.

This isolates the value of **trajectory representation itself**.

---

# 2. Shared target and anchor

Default supervised target for both lanes:

`attendance_residual = actual_attendance - structural_incumbent_p50`

Final challenger:

`challenger_p50 = structural_incumbent_p50 + predicted_residual`

The structural incumbent remains the anchor because it already carries historical/structural attendance information.

The trajectory experiment should prove incremental value rather than relearn the complete attendance problem from scratch.

Actual attendance is a training/scoring label only. It is never an inference feature.

---

# 3. Shared cutoff semantics

Daily cutoff:

`as_of_at(P-N) = kickoff_at - N * 24h`

Supported collection frame:

`P-60 ... P-1`

At a target cutoff, both lanes may use only information genuinely available by `as_of_at`.

No snapshot with:

`captured_at > as_of_at`

may enter the target representation.

A structural prior is eligible only if its target/request/generation lineage proves it genuinely existed by the cutoff.

---

# 4. Shared eligibility for the first Lane A vs Lane B comparison

To preserve an apples-to-apples comparison, an event/cutoff enters the primary shared evaluation cohort only when all are true:

1. target event is within the agreed competition/domain;
2. target cutoff is P-60...P-1;
3. no target attendance is visible during representation building;
4. a PIT-valid structural incumbent P50 genuinely exists by the cutoff;
5. canonical trajectory data contain at least **4 clean genuine snapshots** visible by the cutoff;
6. the genuine observation window spans at least **24 hours**;
7. canonical trajectory `signal_readiness = ready`;
8. all target snapshots satisfy PIT chronology;
9. the event belongs wholly to one evaluation fold.

Why use the existing readiness rule:

- the canonical feature store already defines `MIN_READY_SNAPSHOTS = 4`;
- it already defines `MIN_READY_OBSERVATION_HOURS = 24`;
- it already detects material data gaps and unexplained inventory increases;
- using the same gate avoids inventing a new quality definition only for the model tournament.

Rows failing the shared gate remain useful for collection/diagnostics but do not enter the primary Lane A vs Lane B comparison in v1.

Any later relaxed-support experiment requires a new versioned contract.

---

# 5. Features explicitly excluded from v1

Do not use these in either Lane A or Lane B v1:

- target actual attendance;
- future target inventory/snapshots;
- P11 odds;
- weather;
- media/hype;
- Sporting Match Stakes;
- timing-context rejected features;
- Form5 value;
- P4a spacing/context;
- future lineups/absences not genuinely known by cutoff;
- raw club ID/name as a learnable feature;
- ticket_event_id as a learnable feature;
- provider/source-domain identity as a learnable shortcut.

`club_slug` and `ticket_event_id` remain in lineage/grouping only.

This v1 contract deliberately asks whether **trajectory + structural anchor** adds signal.

---

# 6. Canonical source of trajectory semantics

Do not implement a second cleaning/quality definition.

Canonical feature store:

`ml/demand_engine/live_trajectory_feature_store.py`

Canonical daily cutoff wrapper:

`ml/demand_engine/daily_trajectory_dataset.py`

Inventory interpretation:

`demand_proxy_not_confirmed_sales`

Unknown/hidden inventory is never converted to zero.

---

# 7. Lane A — fixed scalar feature vector

Lane A uses engineered features already derivable PIT-safely from the canonical trajectory feature store.

## 7.1 Numeric trajectory features

Frozen v1 numeric list:

1. `days_to_event`;
2. `available_index`;
3. `available_share_of_capacity`;
4. `velocity_6h_pct_of_first_per_hour`;
5. `velocity_24h_pct_of_first_per_hour`;
6. `velocity_72h_pct_of_first_per_hour`;
7. `velocity_7d_pct_of_first_per_hour`;
8. `acceleration_6h_vs_24h`;
9. `acceleration_24h_vs_72h`;
10. `acceleration_72h_vs_7d`;
11. `snapshot_age_minutes`;
12. `clean_snapshot_count`;
13. `observation_window_hours`;
14. `max_visible_gap_hours`;
15. `structural_incumbent_p50`;
16. `structural_incumbent_p50_share_of_capacity` when verified capacity is available.

## 7.2 Categorical / boolean quality features

Frozen v1 quality list:

- `feature_quality`;
- `signal_readiness`;
- `data_gap_detected`;
- `release_activity_flag`;
- `sector_coverage_change_flag`;
- `unexplained_inventory_increase_flag`.

Even though primary shared eligibility requires `signal_readiness=ready`, the field remains persisted in manifests for auditability and for later diagnostic datasets.

## 7.3 Missing-value handling

Missing numeric trajectory values remain missing until model preprocessing.

For Lane A model development:

- numeric imputation statistics are learned from **training fold only**;
- missing-indicator columns are added for nullable numeric inputs;
- categorical encoding is fitted from training fold only;
- scaling/standardization is fitted from training fold only.

No global/full-dataset preprocessing fit is allowed.

---

# 8. Lane B — genuine variable-length sequence

Lane B must not receive a fake complete P-60 daily vector.

It receives the **ordered genuine clean snapshots visible at the cutoff**.

## 8.1 Snapshot cleaning

For the target event/cutoff:

1. use only `captured_at <= as_of_at`;
2. require `available_total >= 0` and non-null;
3. if multiple rows have the exact same timestamp, keep the highest `snapshot_id`, matching canonical feature-store semantics;
4. sort genuine observations chronologically;
5. for sequence v1, reduce scraper-frequency bias to at most **one observation per integer hour-to-kickoff bucket**, keeping the latest genuine observation within that bucket;
6. do not interpolate missing hours/days;
7. do not forward-fill missing hours/days.

The hourly bucket is representation compression only. It must never create an observation that did not exist.

## 8.2 Per-timestep model fields

Frozen v1 sequence fields:

1. `hours_to_kickoff`;
2. `available_index` relative to the first genuine sequence observation;
3. `available_share_of_capacity` when verified capacity is available;
4. `delta_hours_since_previous`;
5. `delta_available_index` since the previous genuine sequence observation.

Raw `available_total`, `snapshot_id` and `captured_at` remain in lineage but are not required as direct normalized model channels.

If the first genuine available value is zero, normalized `available_index` cannot be defined safely; the v1 sequence is `MODEL_INPUT_INSUFFICIENT` rather than inventing a denominator.

## 8.3 Sequence/global context

Lane B may additionally receive the following shared global context:

- `days_to_event`;
- `snapshot_age_minutes`;
- `clean_snapshot_count`;
- `observation_window_hours`;
- `max_visible_gap_hours`;
- `structural_incumbent_p50`;
- `structural_incumbent_p50_share_of_capacity` when available;
- explicit verified-capacity-available flag;
- sequence length.

## 8.4 Padding/masking

Batches may pad sequences for implementation convenience.

A padding mask/length is mandatory.

A padded numeric zero is **not** a genuine zero inventory observation.

The model must never infer sequence length from padded values alone.

---

# 9. Normalization rules

Normalization must be deterministic or learned from training folds only.

Safe deterministic examples:

- `days_to_event / 60`;
- `hours_to_kickoff / (60*24)`;
- `delta_hours_since_previous / 24`.

Any data-derived normalization statistics must be fit inside the training fold.

Do not calculate a full-dataset mean/std/quantile and then reuse it inside validation folds.

---

# 10. Capacity semantics

Verified stadium capacity may be used only when its lineage is accepted by the model dataset contract.

Capacity-derived fields are optional, not a reason to fabricate a value.

If capacity is unavailable:

- `available_share_of_capacity` remains missing;
- `structural_incumbent_p50_share_of_capacity` remains missing;
- an explicit capacity-available indicator is set false.

Do not infer capacity from target attendance or challenger output.

---

# 11. Structural incumbent semantics

Both Lane A and Lane B use exactly the same structural incumbent for the same event/cutoff.

Selection follows the canonical PIT rule implemented by the daily trajectory dataset contract.

The incumbent itself is not recomputed retrospectively after outcome exposure.

A target/cutoff without an eligible structural incumbent cannot enter the shared residual-model comparison.

---

# 12. Event grouping and fold rule

All rows and prefixes for one `ticket_event_id` belong to one fold.

Never split P-14 of an event into train and P-7 of the same event into validation/test.

The next artifact after this contract is a frozen shared fold registry used identically by Lane A and Lane B.

Primary development comparison must use the exact same eligible event/cutoff identities for both lanes.

---

# 13. Dataset manifest requirements

Every material Lane A/B run must persist/hash at least:

- contract ID/version;
- code Git SHA;
- eligible event IDs;
- event/cutoff identity list;
- fold assignment per event;
- feature names / sequence field names;
- canonical feature-store version;
- canonical daily-dataset version;
- structural-incumbent lineage/version;
- preprocessing configuration;
- target/label definition;
- explicit `target_values_used=false` for inference artifacts.

Any change to these semantics requires a new contract version.

---

# 14. Primary comparison

Lane A and Lane B must be judged on the same:

- events;
- daily cutoffs;
- fold registry;
- structural incumbent;
- attendance labels;
- scoring rules;
- horizon reporting.

The first question is not “which neural network wins?”.

It is:

> **Does the ordered sequence add incremental MAE reduction beyond an explicit engineered trajectory representation?**

---

# 15. Promotion boundary

This development contract may produce historical/grouped research evidence.

It does not activate production.

Before any candidate is used for genuine prospective daily shadow forecasts, freeze a separate candidate/precommit containing:

- exact model family/parameters;
- exact preprocessing;
- exact feature contract version;
- exact daily cutoff policy;
- exact immutable persistence identity;
- exact scoring/evidence rules.

`production_change = false`

---

# 16. Frozen decision

For the first trajectory comparison:

> **Use one shared PIT-safe trajectory information boundary. Lane A receives engineered scalar summaries; Lane B receives the genuine ordered variable-length snapshot sequence. Do not give either lane unrelated context, do not fabricate missing P-N observations, and do not let event prefixes cross folds.**
