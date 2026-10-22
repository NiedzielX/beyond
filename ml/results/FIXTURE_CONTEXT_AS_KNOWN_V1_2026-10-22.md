# Fixture Context As-Known v1 — 2026-10-22

## Purpose

Implement P4 fixture substitution / cannibalization context without historical schedule leakage.

The key integrity rule is:

> A feature lookup may use only a schedule state whose `observed_at <= forecast as_of_at`.

Today's final schedule is never backfilled into historical model rows and labelled PIT-safe.

## Forward schedule evidence

Source: `public.sporting_league_matches_shadow`.

Immutable evidence tables:

- `private.fixture_schedule_batches_v1`;
- `private.fixture_schedule_rows_v1`.

Capture RPC:

- `public.capture_fixture_schedule_as_known_v1(...)`.

Runtime cadence currently active in Supabase:

- cron: `14 */6 * * *`;
- command: `select public.capture_fixture_schedule_as_known_v1();`.

At implementation checkpoint:

- 3 immutable schedule batches;
- 351 versioned schedule rows;
- first schedule state observed `2026-10-21 20:21:39.668518+00`;
- historical backfill explicitly forbidden.

## PIT-safe feature lookup

New RPCs:

- `public.fixture_context_as_known_v1(home, away, event_date, as_of_at)`;
- `public.fixture_context_for_ticket_event_as_known_v1(ticket_event_id, as_of_at)`.

The lookup first resolves the latest schedule batch known at `as_of_at`, then derives only from that immutable batch.

Current v1 features:

- `previous_home_match_days`;
- `next_home_match_days`;
- `team_fixture_density_next_7d`;
- `team_fixture_density_next_14d`;
- `team_fixture_density_next_30d`;
- `home_fixture_density_next_7d`;
- `home_fixture_density_next_14d`;
- `home_fixture_density_next_30d`;
- previous/next home opponent identity for later PIT-safe attractiveness joins.

`next_home_opponent_canonical` is an identity only. No attractiveness score is inferred from future outcomes.

## Live verification

Ticket event 10 — Pogoń Szczecin vs Radomiak Radom, forecast `as_of_at=2026-10-22 07:20:01.949+00`:

- status `READY`;
- schedule batch `3` observed `2026-10-22 06:14:00.096106+00`;
- previous home match distance `13` days;
- team fixtures next 7/14/30d = `1/1/1`;
- home fixtures next 7/14/30d = `0/0/0`.

Ticket event 16 — Wisła Kraków vs Raków Częstochowa, same forecast timestamp:

- status `READY`;
- schedule batch `3`;
- previous home match distance `36` days;
- team fixtures next 7/14/30d = `1/1/1`;
- home fixtures next 7/14/30d = `0/0/0`.

Leakage guard verification:

- event 10 at `2026-10-21 19:50:01.657+00`, before the first schedule capture, returns `NO_SCHEDULE_STATE_AS_OF`;
- the system does **not** reconstruct that row using a later schedule batch.

## Research limitation

A controlled historical P4 ablation cannot yet be called PIT-safe because schedule version history does not exist before `2026-10-21 20:21:39.668518+00`.

Therefore:

1. forward P4 evidence collection starts now;
2. no historical final-schedule backfill is allowed;
3. P4 model selection waits for genuine schedule-as-known labels/evidence;
4. MAE R&D does not stop while P4 evidence accumulates — other roadmap items may run in parallel.

## Production boundary

Research/evidence infrastructure only.

- no frozen package changed;
- no Structural Prior runtime changed;
- no production forecast changed;
- `live_adjustment = 0` remains unchanged.
