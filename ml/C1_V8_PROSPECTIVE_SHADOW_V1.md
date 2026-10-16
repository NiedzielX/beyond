# C1 v8 Prospective Shadow v1

Last updated: **2026-10-16**  
Status: **LIVE / EXPERIMENTAL_SHADOW / production forecast unchanged**

## Purpose

This pipeline validates the frozen C1 v2+v8 package on genuinely future events without contaminating production forecasts or reconstructing decisions after outcomes become known.

Production remains:

`live_adjustment = 0`

The shadow path exists only to answer:

> Does the already-frozen v8 expert-reliability policy continue to improve on the Structural Prior when evaluated prospectively on events whose outcomes were not known when the package was frozen?

## Frozen package

Package version:

`c1-shadow-v8-frozen-2026-10-16-n9`

Live expert:

`c1-v2-live-ridge-directocc-compact-generic-a10`

Policy:

`c1-alpha-reliability-policy-v8-fixed-10pp-positive-slope-20pp-single`

Feature contract:

`live-trajectory-v1.1+c1-v2-compact-direct-occupancy`

Structural Prior dependency:

`structural-prior-runtime-v1-frozen-2026-10-15-t1`

Frozen artifact:

`ml/artifacts/c1_shadow_v8/c1_v2_live_expert_v1.joblib`

Artifact SHA256:

`df31af5effcda2d2f1e58265c7e954cc04edf0e90b48501403eb4e4afd94edf2`

Training contract SHA256:

`0a3edde223d8b6e64652f3fc8f79228998ac0d93a90fdaa9fc48311f98dee304`

Artifact commit:

`9bcf8fe83f85ee7e47a555e975352b8438ea4e3d`

Training events are frozen to:

`[1, 3, 4, 8, 9, 12, 13, 14, 17]`

Training evidence:

- 9 independent completed events;
- 30 regularized PIT-valid final-24h rows;
- direct-occupancy target;
- event-balanced weights;
- 30 frozen v2 compact features.

Scheduled inference **must never fit** this model.

## Frozen v8 policy

At each PIT point:

### One available live observation

Use LIVE only when:

`abs(prior occupancy - live occupancy) >= 0.20`

Otherwise use PRIOR.

### Two or more available live observations

Use LIVE only when both hold:

- absolute disagreement >= `0.10`; and
- live-prediction slope, calculated only from observations available up to the current point, is `> 0`.

Otherwise use PRIOR.

Do not change the 10 pp / 20 pp thresholds or the positive-slope condition while the prospective validation window is running.

## Development evidence — not prospective validation

The frozen rule was designed after the v7 diagnostic on the original 9 events.

Development replay:

- Structural Prior: **3,968.7 MAE**;
- frozen v2 Live: **2,929.3 MAE**;
- v8 representative-window MAE: **2,713.3**;
- v8 latest-row MAE: **1,998.1**;
- prior/live oracle: **1,867.9**;
- worst event degradation vs Prior: approximately **203**.

These values justify prospective testing but are **not** fresh promotion evidence.

## Prospective inference flow

Scheduler:

`.github/workflows/c1-shadow-v8-inference.yml`

Cadence:

`9,24,39,54 * * * *`

This intentionally follows:

- Structural Prior materializer: `5,20,35,50`;
- Live Forecast Orchestrator: `7,22,37,52`.

Runtime entrypoint:

`ml/demand_engine/run_c1_shadow_v8.py`

The scheduled path:

1. obtains GitHub OIDC token with audience `beyond-c1-shadow-v8`;
2. fetches forward-only candidates from `c1_shadow_v8_gateway_v1`;
3. accepts only naturally available, PIT-valid `T-1` Structural Prior candidates inside final 24h;
4. reconstructs at most four final-24h 6-hour representatives using only snapshots available by the run time;
5. loads and hash-verifies the frozen v2 artifact;
6. predicts live P50 for the representatives;
7. applies the frozen v8 policy using only the history available up to the current representative;
8. persists the current decision before the outcome exists;
9. scores any events whose outcomes have subsequently arrived.

If no naturally due T-1 candidate exists, the correct result is zero predictions and zero writes.

## Forward-only input contract

RPC:

`public.get_c1_shadow_v8_inputs_v1(timestamptz)`

Important rules:

- requested time must be within 15 minutes of `now()`;
- kickoff must be in the future and within 24h;
- Structural Prior must resolve `ready / T-1`;
- Structural Prior must be PIT-validated;
- live rows must be PIT-validated;
- only latest snapshot per event x 6h bucket is used;
- only buckets 0–3 are eligible;
- no future snapshot is allowed.

Do not query with a future timestamp merely to exercise the path.

## Pre-outcome evidence

Private table:

`private.c1_shadow_v8_predictions_v1`

This is append-only prospective evidence.

Key fields:

- event / source prior / source snapshot;
- `as_of_at` and `run_requested_at`;
- kickoff / hours-to-kickoff / capacity;
- Structural Prior P50;
- frozen v2 Live P50;
- prior/live disagreement;
- number of live representatives to date;
- live slope to date;
- selected expert;
- v8 policy prediction;
- reason code;
- package/model/policy/feature-contract IDs;
- artifact SHA;
- audit metadata.

Idempotency:

`ticket_event_id + as_of_at + package_version`

Writer RPC:

`public.insert_c1_shadow_v8_predictions_v1(jsonb,timestamptz)`

It rejects:

- already-known outcomes;
- future or non-PIT rows;
- snapshot/as-of mismatch;
- missing/non-T1/non-PIT Structural Prior;
- source-prior mismatch;
- Structural Prior P50/capacity mismatch;
- wrong package or policy ID;
- invalid selected expert;
- policy prediction inconsistent with selected expert.

No backfill of the original development events is allowed.

## Post-outcome scoring

Private table:

`private.c1_shadow_v8_event_scores_v1`

Scoring RPC:

`public.score_c1_shadow_v8_completed_events_v1(timestamptz)`

The scorer uses **only predictions already persisted before the outcome existed**.

It does not reconstruct a missing historical v8 decision after the result becomes known.

Metrics:

- latest-row Prior MAE;
- latest-row frozen v2 Live MAE;
- latest-row v8 policy MAE;
- representative-window Prior MAE;
- representative-window frozen v2 Live MAE;
- representative-window v8 policy MAE;
- per-event improvement flags and audit metadata.

For the representative-window metric, the scorer uses the latest persisted pre-outcome decision in each 6-hour bucket.

Outcome corrections do not overwrite prior score rows. A changed outcome version creates a new score version using `outcome_version_at`.

## Current prospective state

At initial deployment on 2026-10-16:

- frozen package: **available**;
- scheduled load-only inference: **live**;
- append-only prediction store: **live**;
- post-outcome scorer: **live**;
- prospective prediction rows: **0**;
- prospective scored events: **0**.

This is intentional. The first naturally eligible events were still resolved at T-3 during deployment, so no T-1 evidence was fabricated.

The first valid operational checkpoint is:

> **the first non-zero frozen v8 pre-outcome decision written after a genuine T-1 Structural Prior becomes naturally due.**

The second valid checkpoint is:

> **the first score produced after that event completes and its actual attendance is confirmed.**

## Governance during prospective validation

Do not:

- retune v8 thresholds;
- refit the frozen v2 artifact automatically;
- add completed prospective events into the package silently;
- backfill missing predictions after outcomes are known;
- use future timestamps to create T-1 evidence early;
- rewrite old prediction rows;
- present development replay as prospective validation;
- write v8 into production `final_p50`;
- change production `live_adjustment` from 0.

Any future package retrain requires an explicit new version, frozen artifact, manifest, training-event set and governance decision.

## Promotion direction

The 20-independent-completed-match rule remains a later promotion gate.

Promotion requires, at minimum:

- enough genuinely prospective independent events;
- v8 policy uplift versus Structural Prior;
- acceptable degradation/tail risk;
- frozen package and immutable pre-outcome evidence;
- human review;
- explicit promotion decision.

No automatic production promotion exists.

## Operational commands / ownership

Primary workflow:

`.github/workflows/c1-shadow-v8-inference.yml`

Artifact freezer:

`.github/workflows/c1-shadow-v8-artifacts.yml`

Edge gateway:

`supabase/functions/c1_shadow_v8_gateway_v1/index.ts`

DB migrations:

- `supabase/sql/c1_shadow_v8_prospective_evidence_v1.sql`;
- `supabase/sql/c1_shadow_v8_prospective_evidence_v1_resolver_fix.sql`;
- `supabase/sql/c1_shadow_v8_scoring_v1.sql`.

Evidence owner status:

`EXPERIMENTAL_SHADOW`

Production owner status:

`Structural Prior / live_adjustment = 0`
