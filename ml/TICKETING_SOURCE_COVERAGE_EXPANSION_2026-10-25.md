# Ticketing Source Coverage Expansion — 2026-10-25

Status: **LIVE / MULTI-SOURCE COLLECTION ACTIVE / 18 OF 18 CURRENT LEAGUE HOME CLUBS COVERED**

Production model: **UNCHANGED** (`live_adjustment = 0`)

## Why this exists

The 2026-10-25 ingestion audit showed two separate issues:

1. newly discovered RoboTicket matches could remain outside canonical `ticket_events` for too long;
2. a materially larger attendance dataset was being left on the table because several Ekstraklasa home clubs use a different ticketing platform family.

The first issue is handled by the RoboTicket safety net. The second is now addressed by adding a second source family: **Stellis / Liferay ticketing**.

This is a data-acquisition expansion only. No model weights, validation rules, frozen challengers or production forecasts were changed.

## Coverage result

An alias-resolved audit against the current 2026/27 Ekstraklasa home-club universe now gives:

- current league home clubs: **18**;
- covered by at least one active ticketing source: **18**;
- uncovered: **0**.

This resolves the earlier apparent 16/18 result, which was a slug-normalization artifact (`slask_wroclaw` vs `slaskwroclaw`, `wisla_krakow` vs `wislakrakow`). Coverage is verified through the football alias universe rather than direct slug equality.

Important: source coverage is not equivalent to visible inventory for every future fixture. If a source hides aggregate availability, has not yet published the event, or fixture identity is not sufficiently verified, the system remains fail closed and reports the gap rather than manufacturing data.

## Current multi-source architecture

### RoboTicket

Canonical controls:

- hardened same-element event/product identity;
- discovery cadence: hourly;
- unmapped genuine-match buffer: every 10 minutes;
- candidate raw snapshots remain private until verified promotion;
- football-universe gate;
- parking / VIP / premium / reserve / non-football products fail closed;
- verified kickoff -> automatic `ticket_events` promotion + original-PIT backfill.

### Stellis

Active source registry:

- Widzew Łódź — `bilety.widzew.com`;
- Radomiak Radom — `bilety.rksradomiak.pl`;
- Piast Gliwice — `bilety.piast-gliwice.eu`;
- Motor Lublin — `bilety.motorlublin.eu`;
- Korona Kielce — `bilety.korona-kielce.pl`.

Canonical collector:

`stellis_collect_v3`

Cadence:

`3,13,23,33,43,53 * * * *`

The older `stellis_collect_v1`, `stellis_collect_v2` and diagnostic probe functions are **not** scheduled.

## Stellis collection contract

The collector supports both known Stellis variants:

1. React/embedded-event JSON;
2. legacy server-rendered event cards.

The raw source contract can include:

- external event ID;
- event name;
- home / away club identity;
- source kickoff timestamp;
- public aggregate available-ticket count where the source exposes it;
- sold-ticket count where present;
- source/parser lineage.

All raw observations are stored before promotion in:

`private.stellis_raw_observations_v1`

Candidate state is stored in:

`public.stellis_event_candidates_v1`

## Promotion gate

A Stellis observation can become a model-facing `ticket_event` / `snapshot` only when all required gates pass:

1. event is a first-team football match;
2. home club resolves to the configured source club;
3. away club resolves uniquely in the verified football alias universe;
4. event is not explicitly a cup/friendly/non-league product;
5. source kickoff is known;
6. aggregate availability is explicitly model-safe for the source variant;
7. exactly one league home/away pair exists in the sporting shadow within +/-4 calendar days of the source kickoff.

The ticketing source supplies the exact kickoff. The sporting shadow is an identity / league-membership cross-check only because its date can still represent a generic round weekend before final scheduling.

No ambiguous fixture is promoted.

## Cup / non-league hardening

`Puchar Polski`, `Polish Cup`, friendly/towarzyski and equivalent explicit non-league signals are fail-closed.

The promotion function evaluates the **latest** raw observation per event before fixture matching. This prevents an older, less-specific raw row from overriding a later explicit cup classification.

Example verified on 2026-10-25:

`STS Puchar Polski Piast Gliwice - Górnik Zabrze`

Dashboard state:

`NON_MATCH_EXCLUDED`

No model-facing snapshot was created.

## Raw-observation dedup hardening

The ~9-minute dedup suppresses only an **unchanged state**.

A new raw row is persisted immediately when any of these change:

- availability visibility;
- `available_total`;
- `sold_total`;
- resolved home/away identity;
- kickoff timestamp.

This protects the exact transition when a sale/inventory state becomes available.

## Current genuine state

Fresh status at the 2026-10-25 audit:

### Canonical future events

- RoboTicket: **12 future events**, **11 with model-facing snapshots**;
- Stellis: **1 future event**, **1 with model-facing snapshots**;
- combined: **13 future canonical events**, **12 with snapshots**;
- one explicit `TRACKED_NO_SNAPSHOT`: Wisła Kraków vs Cracovia — mapped, but RoboTicket currently returns no readable sectors.

The source-side exception above is not treated as a missing event and is never converted to a fake zero.

### Protected pre-promotion evidence

The ingestion safety net preserves genuine raw observations before final mapping. Examples include future match candidates waiting for verified fixture identity or kickoff. A mapping delay therefore no longer destroys the early booking curve.

### Stellis examples

#### Korona Kielce vs Radomiak Radom

- canonical ticket event: **603**;
- source event ID: `48701`;
- status: `TRACKED`;
- model-facing snapshots present;
- mapping: `stellis-visible-availability-v2.1+latest-raw+league-pair-window`.

#### Piast Gliwice vs Korona Kielce

- source event ID: `48823`;
- public aggregate availability observed;
- raw curve protected while unique league fixture confirmation is pending;
- no model-facing snapshot until the league gate passes.

#### Radomiak Radom vs Śląsk Wrocław

- source event ID: `48101`;
- source currently hides aggregate availability for the active source contract;
- status remains an explicit ingestion gap;
- no fake zero or reconstructed inventory is created.

#### Motor Lublin vs Raków Częstochowa

- source event ID: `48812`;
- raw inventory observations are protected;
- league fixture confirmation remains a promotion gate;
- no model-facing snapshot until the gate passes.

#### Widzew Łódź

The source remains onboarded and is continuously monitored even when no active model-safe event is currently exposed.

## Shared dashboard / panel contract

`private.refresh_dashboard_ticketing_ingestion_status_v1()` publishes **RoboTicket + Stellis** into the same panel-facing table:

`public.dashboard_ticketing_ingestion_status_v1`

Current dashboard contract version:

`dashboard-ticketing-ingestion-status-v2`

Existing panel code renders one shared operational vocabulary, including:

- `TRACKED`;
- `TRACKED_NO_SNAPSHOT`;
- `BUFFERING_AWAITING_KICKOFF`;
- `MATCH_DISCOVERED_NO_BUFFER`;
- `NON_MATCH_EXCLUDED`;
- `NON_FOOTBALL_EXCLUDED`;
- `UNKNOWN_EXCLUDED`.

The panel also keeps recent completed matches visible, so completed fixtures do not appear to have disappeared simply because they are no longer future events.

## Why this materially improves the dataset

Previously, source coverage was effectively biased toward RoboTicket-hosted home fixtures. A club using another ticketing platform could be absent even though its public sale inventory was available.

The current architecture now covers **18/18 current league home clubs** across RoboTicket and Stellis. Not every source exposes the same level of inventory detail, but the important behavior is systematic:

`source appears -> event discovered -> raw evidence protected -> league identity verified -> model-facing snapshot promoted`

A mapping delay no longer automatically destroys the early booking curve.

## Guardrails

- no historical booking curve is invented;
- no source is backfilled from present-day inventory and labeled PIT;
- no cup/non-league event enters Ekstraklasa model data;
- no hidden/unknown availability becomes a fake zero;
- no ambiguous club/fixture mapping is promoted;
- no attendance target/outcome is read by acquisition or promotion;
- production model unchanged;
- `live_adjustment = 0`.

## Immediate next step

Keep both source families collecting across the full 18-club league universe. Continue the precommitted P7 prospective lane and existing P9/P11 accumulation without changing scientific gates.
