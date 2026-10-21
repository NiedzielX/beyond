# Beyond Ticketing — d2 Long-Horizon Live v1 Plan

Last updated: **2026-10-21**

Status: **ACTIVE TRACK-B R&D / DATA CONTRACT FIRST / NO PRODUCTION CHANGE**

Parent evidence:

- `ml/results/D2_V3_STAGE0_ANCHOR_EQUIVALENCE_V1_2026-10-21.md`;
- `ml/results/PRE_LIVE_V3_HISTORICAL_FREEZE_V1_2026-10-21.md`.

## Why this workstream exists

The current d2 problem uses only the final 24 hours before kickoff and anchors all live rows on T-1.

The v2-v3 Stage-0 audit proved:

`V3_FINAL24_ANCHOR_EXACTLY_EQUIVALENT_TO_V2`

Therefore retraining the same final-24h problem under a new name would not be a material model change.

The next useful question is different:

> **Can live ticket trajectory improve attendance forecasting earlier than 24 hours, where the new Pre-Live v3 T-7 anchor can actually matter?**

## Data-readiness audit — 2026-10-21

Current Supabase snapshot history contains:

- 12,521 raw snapshot rows across 24 mapped ticket events;
- 15 events with outcome labels in the broader snapshot table;
- 14 labeled, capacity-resolved Ekstraklasa events eligible under the current C1 event/export rules.

For those 14 C1-eligible labeled Ekstraklasa events, using the same 6h bucket sampling and the existing PIT function `get_live_trajectory_features_v1_1_asof`:

- 13/14 have valid rows beyond 24h;
- 10/14 have valid rows beyond 48h;
- 8/14 have valid rows in 72–168h;
- several events have 24–28 valid 6h-bucket rows inside the final 168h.

Examples with near-full 7-day coverage:

- event 1 Lech–Raków;
- event 3 Lech–Jagiellonia;
- event 4 Lech–Radomiak;
- event 5 Lech–Korona;
- event 15 GKS Katowice–Pogoń;
- event 18 Cracovia–Legia;
- event 19 Zagłębie Lubin–Jagiellonia.

Event 11 Górnik–Piast reaches about 90h.

The limiting factor is currently the export contract, not raw data retention.

## Data integrity

The earlier snapshots are not reconstructed from final state.

The proposed export must use:

- source snapshot `captured_at`;
- point-in-time event kickoff stored/known at the request time where applicable;
- verified stadium capacity under the same C1 eligibility rules;
- `get_live_trajectory_features_v1_1_asof`;
- `point_in_time_validated = true`;
- non-null source feature snapshot;
- no outcome value inside live features.

Outcome is used only as the supervised target after the PIT live row is constructed.

## Additive export contract

Do **not** modify:

`v7-final24 -> export_c1_alpha_v7_final24_rows_v1`

Create an additive research export:

`v8-long168 -> export_d2_long_horizon_168_rows_v1`

Sampling:

- maximum window: 168h before kickoff;
- cadence: 6h;
- latest available source snapshot in each event x 6h bucket;
- same eligible-event and verified-capacity rules as v7-final24;
- same live PIT feature function.

The payload must include:

- `ticket_event_id`;
- `requested_snapshot_id`;
- `requested_as_of_at`;
- `hours_to_kickoff`;
- `bucket_6h`;
- PIT `features` JSON;
- per-event coverage summary where practical;
- top-level event/row counts and window/cadence metadata.

Research export remains service-role/OIDC protected through the existing main-only training gateway.

## Coverage rule

Do not pretend all events have a complete T-7 trajectory.

For every event persist:

- earliest valid hours-to-kickoff;
- latest valid hours-to-kickoff;
- count of valid 6h buckets;
- coverage by windows:
  - 0–24h;
  - 24–48h;
  - 48–72h;
  - 72–168h.

Missing earlier history is data availability, not zero demand.

## Evidence boundary

The original frozen final-24h development set remains:

`1,3,4,8,9,12,13,14,17`

Newer labeled events already exposed in previous diagnostics/readiness work include:

`5,11,15,18,19`

These labels are no longer unseen.

A long-horizon experiment must predeclare a chronological split and label every event as development/reference/exposed before model fitting.

No random snapshot split.

Independent unit:

`event`

## Stage A — coverage and baseline audit

Before fitting a live correction model:

1. export all valid long-horizon rows;
2. freeze event/as-of identities and coverage statistics;
3. determine the honest earliest modeling window supported by event count;
4. evaluate Pre-Live v2 and v3 anchor behavior at relevant checkpoints;
5. define the anchor-transition rule before opening model results.

Candidate initial modeling windows to compare:

- final 48h;
- final 72h;
- final 168h.

The selection must balance earlier coverage against independent event count.

## Anchor-transition question

Unlike final-24h, a long-horizon live model crosses more than one Pre-Live checkpoint.

The anchor rule must be predeclared and reproducible.

Candidate approaches for a later experiment:

1. **checkpoint hold:** use the latest available frozen Pre-Live checkpoint at/as-of the live row;
2. **piecewise transition:** move from T-7 toward T-3/T-1 only when the next checkpoint becomes valid;
3. another deterministic PIT-safe mapping justified before evaluation.

Do not interpolate using future checkpoint predictions that were not available at the row as-of time.

## Stage B — first long-horizon live benchmark

Only after Stage A freezes the data and anchor rule.

Minimum baselines:

- Pre-Live anchor only / zero live correction;
- transparent inventory trajectory extrapolation;
- existing final-24h Ridge applied only where its old contract is valid, as a reference rather than automatic long-horizon model.

Any learned model must use event-level chronological/LOEO discipline and event-balanced metrics.

Primary KPI:

`MAE`

Also report:

- median AE;
- bias;
- p90/worst event;
- event improvement rate;
- revision magnitude;
- performance by hours-to-kickoff band;
- coverage/missingness.

## What not to do

- do not mutate `v7-final24`;
- do not relabel exposed events as unseen;
- do not random-split snapshots;
- do not forward-fill from future observations;
- do not infer actual attendance from inventory;
- do not automatically reuse final-24h Ridge/P2 outside its validated window;
- do not activate production.

## Immediate work order

1. add/deploy `export_d2_long_horizon_168_rows_v1`;
2. add gateway route `v8-long168` without changing existing routes;
3. verify service-role/main-only access and payload counts;
4. persist a machine-readable long-horizon coverage audit;
5. freeze the data contract and chronological evidence split;
6. only then start modeling.

## Production boundary

Always:

- Track-A v2/Ridge/P2 unchanged;
- v3 research-only;
- long-horizon work research-only;
- production `live_adjustment = 0`.
