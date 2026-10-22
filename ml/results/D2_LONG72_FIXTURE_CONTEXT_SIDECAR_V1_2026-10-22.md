# D2 Long72 Fixture Context Sidecar v1 — 2026-10-22

## Goal

Attach PIT-safe fixture-spacing/density context to each immutable reproducible Long72 forward prediction **without changing the forecast itself**.

This prepares P4 context ablations for future labeled events while preserving the existing frozen Long72 package.

## Evidence contract

For prediction `p` at `p.as_of_at`, context may use only an immutable schedule batch with:

`schedule_batch.observed_at <= p.as_of_at`

If no such schedule state existed, the sidecar records a fail-closed status. It never fills the historical row from a later schedule capture.

## Runtime objects

Table:

`private.d2_long72_fixture_context_v1`

Capture RPC:

`public.capture_d2_long72_fixture_context_v1(...)`

Scheduler:

- job: `d2_long72_fixture_context_sidecar_v1_15m`;
- cadence: `7,22,37,52 * * * *`;
- job id at deployment: `29`.

The job runs after/around the hourly Long72 forecast workflow and inserts only missing sidecar rows.

## Append-only rules

- one sidecar row per `forward_prediction_id`;
- UPDATE/DELETE rejected by trigger;
- only reproducible Long72 rows are eligible;
- manual bootstrap rows are excluded;
- context payload includes exact schedule batch lineage;
- production forecast is never revised from this table.

## Initial materialization

At deployment:

- reproducible Long72 prediction rows available: `12`;
- inserted sidecar rows: `12`;
- `READY`: `10`;
- `NO_SCHEDULE_STATE_AS_OF`: `2`.

The two unavailable rows are the first forecasts for events 10 and 16 at approximately `2026-10-21 19:50 UTC`, before the first genuine schedule state was captured at `2026-10-21 20:21:39 UTC`.

They remain unavailable by design.

The next 10 rows are PIT-valid and resolve against schedule batches 1–3.

Examples:

### Event 10 — Pogoń Szczecin vs Radomiak Radom

Post-capture rows show:

- previous home match distance: `13` days;
- team fixture density next 7d: `1`;
- exact schedule batch id preserved.

### Event 16 — Wisła Kraków vs Raków Częstochowa

Post-capture rows show:

- previous home match distance: `36` days;
- team fixture density next 7d: `1`;
- exact schedule batch id preserved.

At these captured schedule states `next_home_match_days` is null for both events. This is preserved as observed rather than inferred from later schedule knowledge.

## What this unlocks

When final attendance arrives, P4 can compare forecast residuals against fixture context that was genuinely known at each forecast timestamp.

Future ablation candidates can include:

- previous-home spacing;
- next-home spacing when available;
- team fixture density 7/14/30d;
- home fixture density 7/14/30d;
- later: PIT-safe next-opponent attractiveness joined from an observed source.

## What it does not unlock yet

It does **not** create historical schedule-version evidence before the first capture timestamp.

Therefore:

- no historical final-schedule backfill;
- no claim that P4 has historical causal/forward validation yet;
- no context model selection until enough labeled forward context observations exist.

## Production boundary

- frozen P2 unchanged;
- Structural Prior unchanged;
- no production activation;
- `live_adjustment = 0`.
