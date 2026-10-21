# D2 Long72 Forward Prospective v1 — 2026-10-21

Status: **IMPLEMENTED / GENUINE POST-FREEZE EVIDENCE ACTIVE**

Production change: **none**

Frozen package:

`d2-long72-stage2-p2-observation-maturity-2026-10-21-v1`

## Purpose

Create genuine Long72 evidence in the correct causal order:

`forecast persisted before outcome -> outcome attached later -> score append-only`

The frozen Long72 package is not retrained or retuned.

## Implementation

Implemented and merged through PR #141 plus timestamp-lineage hotfix PR #142.

Main successful prospective run:

- workflow: `d2 Long72 Forward Prospective v1`;
- run ID: `39667034428`;
- head SHA: `c83c2a14060d6f064636349c0db16cc4fc2b4b68`;
- artifact ID: `12376893783`;
- artifact digest: `sha256:feca43332445e974652e0ad2e1b59f3f7595d52ff8dea9b3cbbef35f771c594a`;
- result: validation + OIDC + forward input + normalization + frozen materialization + immutable persistence + scoring + artifact upload all passed.

## Evidence contract

### Before outcome

Persist immutably:

- event ID / kickoff;
- source snapshot ID and `as_of_at`;
- frozen T-3 Structural Prior ID/P50;
- frozen b2 maturity state and correction;
- final anchor;
- raw inventory extrapolation;
- governed ±10pp Stage-1 correction;
- Stage-1 forecast;
- P2 observation index / reliability;
- frozen P2 forecast;
- package / manifest / code lineage.

The writer rejects events whose attendance outcome already exists.

### After outcome

The scorer only joins attendance to forecasts already stored before the label existed. It never reconstructs missing predictions after the result.

Representative score rows use the latest reproducible persisted forecast for each event × 6h bucket.

## First genuine prospective events

### Event 10 — Pogoń Szczecin vs Radomiak Radom

Automated reproducible checkpoint:

- snapshot ID: `20825`;
- `as_of_at`: `2026-10-21T19:50:01.657Z`;
- hours to kickoff: `67.666206`;
- verified capacity: `21163`;
- frozen T-3 Structural Prior: `18250.984984154635`;
- b2 prior same-season home matches: `5`;
- b2 correction: `-228.2599236881507` seats;
- final Long72 anchor: `18022.725060466484`;
- governed inventory correction: `+0.10` occupancy;
- Stage-1 inventory forecast: `20139.025060466483`;
- P2 observation index: `1`;
- P2 reliability: `0.25`;
- frozen P2 forecast: `18551.800060466485`.

Frozen b2 source lineage contains five earlier same-season Pogoń home matches completed before the T-3 cutoff. The earlier manual audit had looked only at tracked `ticket_events` and therefore understated this history; the automated replay correctly uses the canonical historical attendance layer.

### Event 16 — Wisła Kraków vs Raków Częstochowa

Automated reproducible checkpoint:

- snapshot ID: `20826`;
- `as_of_at`: `2026-10-21T19:50:02.358Z`;
- hours to kickoff: `70.416012`;
- verified capacity: `33130`;
- frozen T-3 Structural Prior: `15888.241360695727`;
- b2 prior same-season home matches: `0`;
- b2 correction: `0`;
- final Long72 anchor: `15888.241360695727`;
- governed inventory correction: `+0.10` occupancy;
- Stage-1 inventory forecast: `19201.241360695727`;
- P2 observation index: `1`;
- P2 reliability: `0.25`;
- frozen P2 forecast: `16716.491360695727`.

## Manual bootstrap rows

Two pre-outcome checkpoints were persisted manually before the automated workflow was complete. They are retained as immutable audit records.

They are **not scoreable official package evidence** because the manual Pogoń bootstrap used an incomplete current-season-history audit.

A follow-up score-quality rule excludes rows with `manual_first_checkpoint=true` from the official prospective scorecard. No evidence rows are deleted or rewritten.

## Current scoring state

At this checkpoint both events are still pre-outcome.

- prospective scored events: `0`;
- event MAE: not available yet;
- no forecast is reconstructed from the future;
- scorer returns null aggregate metrics until an attendance label becomes available.

## Infrastructure

Supabase:

- `private.d2_long72_forward_predictions_v1` — immutable pre-outcome predictions;
- `private.d2_long72_forward_event_scores_v1` — append-only post-outcome scores;
- `public.get_d2_long72_forward_inputs_v1` — forward-only PIT input;
- `public.insert_d2_long72_forward_predictions_v1` — strict package writer;
- `public.score_d2_long72_forward_completed_events_v1` — outcome-only scorer;
- Edge Function `d2_long72_forward_shadow_v1` — main-only GitHub OIDC gateway.

Repo:

- `ml/d2_long72_forward_materialize_v1.py`;
- `ml/d2_long72_forward_input_normalize_v1.py`;
- `ml/test_d2_long72_forward_materialize_v1.py`;
- `ml/test_d2_long72_forward_input_normalize_v1.py`;
- `.github/workflows/d2-long72-forward-prospective-v1.yml`;
- `supabase/sql/d2_long72_forward_prospective_v1.sql`;
- `supabase/sql/d2_long72_forward_score_quality_v1.sql`.

## Decision

`ADVANCE_PROSPECTIVE_EVIDENCE_COLLECTION`

Milestone 1 from the MAE roadmap is complete as infrastructure. The package remains frozen and hourly pre-outcome materialization continues automatically.

The next modelling work does **not** wait for outcomes: reusable temporal validation is already implemented, followed by the MAE-native challenger tournament.
