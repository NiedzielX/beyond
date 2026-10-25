# Ticketing Source Coverage Expansion — 2026-10-25

Status: **LIVE / MULTI-SOURCE COLLECTION ACTIVE**

Production model: **UNCHANGED** (`live_adjustment = 0`)

## Why this exists

The 2026-10-25 ingestion audit showed two separate issues:

1. newly discovered RoboTicket matches could remain outside canonical `ticket_events` for too long;
2. a materially larger attendance dataset was being left on the table because several Ekstraklasa home clubs use a different ticketing platform family.

The first issue is handled by the RoboTicket safety net. The second is now addressed by adding a second source family: **Stellis / Liferay ticketing**.

This is a data-acquisition expansion only. No model weights, validation rules, frozen challengers or production forecasts were changed.

## Current multi-source architecture

### RoboTicket

Canonical controls:

- live discovery: `roboticket-discovery-v8`;
- discovery cadence: hourly;
- unmapped genuine-match buffer: every 10 minutes;
- candidate raw snapshots remain private until verified promotion;
- same-element eventId/label identity;
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

### Stellis

#### Korona Kielce vs Radomiak Radom

- canonical ticket event: **603**;
- source event ID: `48701`;
- status: `TRACKED`;
- model-facing snapshots at audit time: **2**;
- first observed aggregate availability: **5,294**;
- mapping: `stellis-visible-availability-v2.1+latest-raw+league-pair-window`.

#### Piast Gliwice vs Korona Kielce

- source event ID: `48823`;
- source kickoff: 2026-11-20T17:00:00Z;
- public aggregate availability observed: **4,409**;
- status: `BUFFERING_AWAITING_KICKOFF` in the shared dashboard vocabulary;
- raw curve protected privately;
- promotion waits for a unique league fixture identity in the sporting shadow.

#### Radomiak Radom vs Śląsk Wrocław

- source event ID: `48101`;
- source kickoff: 2026-11-02T17:00:00Z;
- source currently declares aggregate availability hidden for the active source contract;
- status: `MATCH_DISCOVERED_NO_BUFFER`;
- no fake zero or reconstructed inventory is created.

#### Motor Lublin vs Raków Częstochowa

- source event ID: `48812`;
- raw inventory observations are protected;
- league fixture confirmation is not currently sufficient for promotion;
- status: `BUFFERING_AWAITING_KICKOFF`;
- no model-facing snapshot until the league gate passes.

#### Widzew Łódź

No active ticket event was exposed by the source during the audit. The source remains onboarded and will be checked by the same 10-minute collector.

## Shared dashboard / panel contract

`private.refresh_dashboard_ticketing_ingestion_status_v1()` now publishes **Roboticket + Stellis** into the same panel-facing table:

`public.dashboard_ticketing_ingestion_status_v1`

Current dashboard contract version:

`dashboard-ticketing-ingestion-status-v2`

Existing panel code does not need a second source-specific API. It continues to render the same status vocabulary, including:

- `TRACKED`;
- `TRACKED_NO_SNAPSHOT`;
- `BUFFERING_AWAITING_KICKOFF`;
- `MATCH_DISCOVERED_NO_BUFFER`;
- `NON_MATCH_EXCLUDED`;
- `NON_FOOTBALL_EXCLUDED`;
- `UNKNOWN_EXCLUDED`.

The panel therefore shows both canonical events and protected pre-promotion gaps through one operational view.

## Why this materially improves the dataset

Previously, source coverage was effectively biased toward RoboTicket-hosted home fixtures. A club using another ticketing platform could be absent even though its public sale inventory was available.

With the Stellis family onboarded, five additional home-club sources are continuously monitored. Not every source exposes the same level of inventory detail, but the important behavior is now systematic:

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

Keep both source families collecting and let genuine early-window observations accumulate. Continue the precommitted P7 prospective lane and existing P9/P11 accumulation without changing scientific gates.
