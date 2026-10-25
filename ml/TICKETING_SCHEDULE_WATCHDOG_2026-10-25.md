# Ticketing Schedule Watchdog — 2026-10-25

Status: **LIVE**

Production model: **UNCHANGED** (`live_adjustment = 0`)

## Purpose

Source discovery alone is not sufficient to protect early booking curves.

A ticketing platform can expose a match late, change its markup, hide the main event while exposing ancillary products, or simply not open the sale yet. If monitoring starts only when the ticketing source discovers an event, an early T-168/T-72 booking window can be lost without any explicit failure.

The watchdog therefore checks coverage in the reverse direction:

`known upcoming league fixture -> onboarded home ticketing source -> canonical event or protected candidate`

A missing downstream event becomes an explicit operational alert before the booking curve is silently lost.

## Live database contract

Fixture coverage view:

`public.dashboard_ticketing_fixture_coverage_v1`

Shared panel table:

`public.dashboard_ticketing_ingestion_status_v1`

Multi-source refresh:

`private.refresh_dashboard_ticketing_ingestion_status_v2()`

Current dashboard payload version:

`dashboard-ticketing-ingestion-status-v2.1`

Refresh cadence:

`9,19,29,39,49,59 * * * *`

Cron:

`ticketing_ingestion_dashboard_10m`

## Coverage logic

For every upcoming fixture in the next 28 days from the sporting schedule:

1. resolve home and away club keys using the verified structural alias universe;
2. identify the active home ticketing source family — RoboTicket or Stellis;
3. look for a canonical `ticket_event` for the same home/away pair within +/-4 calendar days of the sporting placeholder date;
4. if no canonical event exists, look for a safe Stellis candidate with the same resolved home/away keys;
5. for RoboTicket, look for either a verified schedule mapping or a recent match candidate whose normalized product identity contains both home and away club aliases;
6. classify the fixture.

Coverage states:

- `TRACKED`
- `BUFFERING_OR_DISCOVERED`
- `SCHEDULE_GAP`
- `SOURCE_NOT_ONBOARDED`
- `IDENTITY_UNRESOLVED`

Only genuine uncovered upcoming fixtures become panel alerts.

## Why kickoff is not invented

The sporting shadow can still carry a generic round-weekend date before final scheduling.

For a `SCHEDULE_GAP` row:

- the fixture date is shown in `issue_reason`;
- `kickoff_at` remains null until the ticketing/verified source supplies an exact time;
- the watchdog never fabricates a kickoff from the placeholder schedule date.

## Fresh gap state after deployment

After a fresh RoboTicket discovery, Stellis collect and candidate-buffer run, the following five gaps remained genuine:

1. **Górnik Zabrze – Legia Warszawa** — round 13 schedule fixture; RoboTicket currently exposes a parking product for Legia but no safe first-team match event.
2. **Jagiellonia Białystok – GKS Katowice** — round 14 schedule fixture; no safe ticketing candidate yet.
3. **Motor Lublin – Wisła Płock** — round 14 schedule fixture; no corresponding Stellis candidate yet.
4. **Śląsk Wrocław – Piast Gliwice** — round 14 schedule fixture; no safe RoboTicket candidate yet.
5. **Widzew Łódź – Pogoń Szczecin** — round 14 schedule fixture; no corresponding Stellis event yet.

These are now visible in the panel as:

`SCHEDULE_GAP`

The absence of a source event is no longer silent.

## Example of a correctly suppressed alert

**Wieczysta Kraków – Jagiellonia Białystok** is present in the sporting schedule but is **not** a gap.

RoboTicket discovery safely resolves the home/away pair and the private buffer already protects a genuine inventory curve.

Latest manual buffer check:

- event ID: `1359`;
- visible available inventory: **3,958**;
- sectors: 7;
- football identity gate: passed;
- candidate snapshot already recent, so no duplicate insert was needed.

The watchdog therefore classifies it as covered by a protected candidate rather than creating a false alert.

## False-positive protection

The same buffer run rejected unrelated products/events including hockey because two known football club identities were not present.

This is required: schedule protection must not increase data volume by contaminating the football dataset.

## Panel behavior

The Beyond panel now treats `SCHEDULE_GAP` as a first-class actionable status.

The ingestion coverage component shows:

- tracked events;
- protected raw curves;
- schedule gaps;
- all remaining actionable ingestion issues.

`SCHEDULE_GAP` is rendered as a danger state and counted separately.

The panel no longer hardcodes every source as RoboTicket; it shows RoboTicket, Stellis, or the schedule watchdog source context.

Panel commit:

`2b3e8bb201cfda3e1543434cd2ea41b2201759b0`

Dashboard CI run:

`40222368344`

Result:

**SUCCESS**

## Guardrails

- schedule presence is not treated as ticket inventory;
- no kickoff time is invented from a placeholder date;
- no historical booking curve is fabricated;
- no unrelated sport/product is accepted merely to remove an alert;
- ambiguous fixture/source identity remains visible rather than auto-promoted;
- acquisition/watchdog logic does not read attendance targets;
- no model parameter changes;
- no production activation;
- `live_adjustment = 0`.

## Operational meaning

The ingestion system now has three protection layers:

`fixture watchdog -> source discovery/private buffer -> canonical ticket_event/model-facing snapshots`

This closes the failure mode that caused the 2026-10-25 concern: a known future match can no longer disappear from monitoring merely because the ticketing source has not yet produced a canonical event.
