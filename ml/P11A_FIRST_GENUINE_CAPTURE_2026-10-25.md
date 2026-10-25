# P11a — First Genuine PIT Odds Capture

Date: **2026-10-25**

Status: **GENUINE PIT DATA ACCUMULATING**

Production: **UNCHANGED** (`live_adjustment = 0`)

## Purpose

P11a adds a genuinely new point-in-time match-attractiveness / outcome-uncertainty signal through bookmaker 1X2 market consensus.

The purpose is not to predict attendance directly from closing odds. The purpose is to accumulate auditable pre-match market information exactly as it was known at forecast time.

## Runtime synchronization

The live Edge Function was synchronized from the corrected `main` source before the first genuine capture.

- function: `p11_odds_capture_v2`;
- corrected provider timestamp format: `YYYY-MM-DDTHH:MM:SSZ`;
- GitHub OIDC authorization remains restricted to `NiedzielX/beyond` on `refs/heads/main`;
- no fuzzy fixture matching;
- kickoff tolerance remains 5,400 seconds;
- started/in-play events remain rejected;
- target values are never read by capture.

After the capture and schedule activation the live runtime is **version 6** and its config contract reports scheduled capture enabled.

## First genuine capture

GitHub Actions run:

`40199626764`

Captured at:

`2026-10-25T13:46:04.688Z`

Provider:

`the-odds-api-v4`

Result:

- local candidate events: **3**;
- provider events returned: **2**;
- deterministically matched events: **2**;
- raw append-only bookmaker quote rows inserted: **34**;
- target values used: **false**;
- production change: **false**.

### Event 22 — Legia Warszawa vs Lech Poznań

- status: `CAPTURED`;
- provider event ID: `99069494a414da9e613df685edddefa0`;
- complete bookmaker quotes inserted: **18**;
- kickoff delta: **0 seconds**;
- capture batch: `c2bf550a-cb5c-49f3-9139-076f429e1858`;
- source payload SHA256: `adc595913223d1a5b3815353160f2a58a1caf600a36f0f9b3f466701aa284131`;
- all rows pre-match and captured before kickoff: **true**.

As-known de-vigged consensus at the first capture:

- home win probability: `0.4138058652`;
- draw probability: `0.2534063187`;
- away win probability: `0.3327878162`;
- favorite strength: `0.4138058652`;
- normalized outcome entropy: `0.9827731653`;
- mean bookmaker overround: `0.053969`;
- consensus bookmaker count: **15**.

### Event 6 — Lech Poznań vs Wisła Kraków

- status: `CAPTURED`;
- provider event ID: `800ce8e08945f17d3a51c46fb6c2b3cd`;
- complete bookmaker quotes inserted: **16**;
- kickoff delta: **0 seconds**;
- capture batch: `624b229e-f393-41b0-a587-d659f1d07a06`;
- source payload SHA256: `c7fb6d4de6b29a8bd1a2961ccf1ed011e7efa7bfd0dd3275f920868a84245a68`;
- all rows pre-match and captured before kickoff: **true**.

As-known de-vigged consensus at the first capture:

- home win probability: `0.5552463381`;
- draw probability: `0.2502877706`;
- away win probability: `0.1944658913`;
- favorite strength: `0.5552463381`;
- normalized outcome entropy: `0.9032610910`;
- mean bookmaker overround: `0.051434`;
- consensus bookmaker count: **15**.

### Event 23 — Śląsk Wrocław vs Wieczysta Kraków

- status: `NO_PROVIDER_MATCH`;
- no quote was inserted;
- no fuzzy or manual override was attempted.

This is the correct fail-closed behavior.

## Provider quota on first capture

- request cost: **1**;
- used: **1**;
- remaining: **499**.

## Readiness after first capture

`p11_market_odds_readiness_v2()`:

- status: `GENUINE_PIT_DATA_ACCUMULATING`;
- events with any genuine PIT 1X2: **2**;
- clubs with any genuine PIT 1X2: **2**;
- events with at least 3 bookmakers: **2**;
- events reaching 168h: **0**;
- events reaching 72h: **1**;
- events reaching 24h: **2**;
- model precommitted: **false**;
- target values used: **false**;
- production change: **false**.

## Scheduled accumulation

After the first capture passed audit, scheduled capture was enabled in GitHub Actions:

`17 */6 * * *`

This means one capture attempt every six hours. Push events run the contract/tests only; they do **not** call the provider.

The schedule remains protected by:

- main-only GitHub OIDC;
- provider secret presence check;
- deterministic verified-alias mapping;
- kickoff tolerance;
- pre-match-only inserts;
- append-only raw observations;
- target-free capture contract;
- `production_change=false`.

## Decision

1. Continue genuine append-only capture on the fixed six-hour schedule.
2. Audit horizon coverage rather than changing the cadence in response to outcomes.
3. Do not backfill closing odds into earlier PIT horizons.
4. Do not precommit or fit a P11a attendance model until genuine event/horizon coverage is adequate and the experiment is separately frozen.
5. Treat event 23's unmatched state as valid fail-closed evidence, not a reason to loosen matching.
6. Keep production unchanged.
