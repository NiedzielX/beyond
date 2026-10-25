# RoboTicket Ingestion Safety Net — 2026-10-25

Status: **LIVE / VERIFIED**

Production model: **UNCHANGED** (`live_adjustment = 0`)

## Why this was needed

A dashboard review on 2026-10-25 exposed a structural ingestion gap: RoboTicket discovery could find a new ticket product, but there was no sufficiently robust automatic path from:

`discovered product -> verified football match -> ticket_event -> normal collector`

This could make a newly opened home match disappear from the model-facing event list until it was manually mapped. Because booking-curve evidence is perishable, delayed mapping could permanently reduce the usable match base.

The old discovery parser also associated some labels with the wrong nearby `eventId`, which could confuse a real match with parking, VIP, premium or other products.

## What was NOT lost in round 12

The complete round was not lost.

Genuine pre-kickoff booking curves were preserved for 5 of the 9 round-12 fixtures that were hosted by onboarded clubs:

- Pogoń Szczecin – Radomiak Radom: 1,456 snapshots;
- Wisła Kraków – Raków Częstochowa: 731 snapshots;
- Śląsk Wrocław – Wieczysta Kraków: 1,047 snapshots;
- Jagiellonia Białystok – Wisła Płock: 1,057 snapshots;
- Legia Warszawa – Lech Poznań: 1,068 snapshots.

The four other round-12 matches were hosted by clubs that were not onboarded as ticketing sources. KGHM Zagłębie, Górnik, GKS Katowice and Cracovia were away teams in those fixtures, so their own ticket systems could not provide the host inventory curve.

## Root causes

### 1. Missing promotion path

Discovery persisted `roboticket_event_candidates`, but the normal additional-club collector consumed only already-created `ticket_events`.

A discovered match could therefore remain outside the normal collector indefinitely.

### 2. Loose discovery identity parsing

The previous parser could associate an `eventId` with text found in nearby HTML rather than the exact same link/element.

Observed examples included:

- GKS–Widzew: real match `5770`; `6003` is parking;
- Cracovia–Motor: real match `10599`; `10632` is VIP;
- Pogoń–Śląsk: real match `13532`; `13564` is parking;
- KGHM–Korona: real match `1986`;
- Wisła Płock–Piast: real match `3075`;
- Górnik–Wieczysta: real match `5215`.

### 3. Mixed products / disciplines

Some RoboTicket installations expose more than first-team football, including parking, hospitality, reserve teams and other sports. A broad "looks like a match" rule is not safe enough.

## Safety net now live

### A. Hardened discovery

Edge Function:

`roboticket_discover_clubs`

Current contract: `roboticket-discovery-v7`.

Rules:

- `eventId` and candidate label must come from the same HTML element/link;
- direct event-page identity may strengthen classification but a generic login/portal page cannot override explicit exclusions;
- parking, VIP, premium, vouchers, hospitality, conferences, reserve/U19/U17 and similar products fail closed;
- candidate metadata stores classification lineage and direct-page evidence;
- a verified kickoff can trigger schedule upsert/promotion only when identity evidence is sufficiently direct.

### B. Pre-mapping raw candidate buffer

Private tables:

- `private.roboticket_candidate_snapshots_v1`;
- `private.roboticket_verified_schedule_v1`.

Key principle:

> A real football match can begin accumulating raw inventory before its exact kickoff has been fully mapped into `ticket_events`.

This prevents delayed mapping from deleting the early booking curve.

Raw candidate observations stay isolated from `public.snapshots` and all model-facing training/evaluation data until the mapping is verified.

### C. Football-universe gate

Edge Function:

`roboticket_buffer_candidates_v1`

Current contract: `roboticket-candidate-buffer-collector-v2`.

A candidate is buffer-eligible only when:

1. discovery classifies it as a match;
2. it is recent;
3. it is not already tracked;
4. the label/identity resolves to at least two known football club keys;
5. the expected home club is among those keys.

This prevents other sports and non-football ticket products from contaminating the raw buffer.

### D. Verified promotion + PIT-preserving backfill

RPC:

`public.promote_roboticket_verified_candidates_v1()`

After verified schedule mapping:

- create/update the canonical `ticket_event`;
- mark the candidate `collecting`;
- move eligible private raw observations into the canonical model-facing tables;
- preserve the original `captured_at` values;
- keep provenance as candidate-buffer backfill.

No synthetic historical observation is created.

### E. Faster cadence

Discovery:

`roboticket_discovery_hourly` -> every hour at minute 02.

Unmapped candidate buffer:

`roboticket_candidate_buffer_10m` -> minutes 07,17,27,37,47,57.

Normal tracked-event collection continues on its existing cadence.

Practical implication: after a real match appears publicly, discovery delay should normally be <= ~1 hour and raw inventory capture <= ~10 minutes after classification, even if exact kickoff mapping is delayed.

## Current future-round recovery

The safety-net/recovery work created or activated tracking for the next rounds, including:

- KGHM Zagłębie Lubin – Korona Kielce;
- GKS Katowice – Widzew Łódź;
- Cracovia – Motor Lublin;
- Górnik Zabrze – Wieczysta Kraków;
- Wisła Płock – Piast Gliwice;
- Pogoń Szczecin – Śląsk Wrocław;
- Lech Poznań – Zagłębie Lubin;
- Legia Warszawa – Raków Częstochowa;
- Jagiellonia Białystok – Lech Poznań.

Fresh monitoring after recovery showed **11 future matches in normal TRACKED state**.

One explicit exception remains:

`Wisła Kraków – Cracovia` / ticket event 448 / RoboTicket event 11718.

It is already discovered and mapped, but RoboTicket currently returns **zero ticket sectors**, so the normal collector has no inventory observation to persist yet. It remains visible as `TRACKED_NO_SNAPSHOT` / "waiting for inventory" and is retried by the normal collector.

This is not the same failure mode as a missing event.

## Dashboard monitoring

Panel repository:

`NiedzielX/BeyondTicketingPanel`

Coverage is exposed in:

- Overview;
- Data Quality / ingestion monitoring.

The dashboard uses `public.dashboard_ticketing_ingestion_status_v1` and distinguishes:

- `TRACKED`;
- `TRACKED_NO_SNAPSHOT`;
- `COMPLETED_TRACKED`;
- `BUFFERING_AWAITING_KICKOFF`;
- `READY_TO_PROMOTE`;
- `MATCH_DISCOVERED_NO_BUFFER`;
- excluded non-match/non-football states.

Completed matches remain visible in historical coverage rather than disappearing after kickoff.

Client-facing dashboard relations are read-only; anon/authenticated access is SELECT-only.

## Contamination audit

Early parser testing produced some false-positive candidate-buffer observations before the football-universe gate was added.

These rows remained in the **private candidate buffer** and were not promoted into `public.snapshots`, so they did not contaminate training, validation or production predictions.

Do not promote or reinterpret them retrospectively.

## Required weekly / round health checks

Before each upcoming round is considered ingestion-safe:

1. every onboarded club's public RoboTicket source is reachable or has an explicit blocker;
2. every real discovered first-team football home match is either `TRACKED`, `BUFFERING_AWAITING_KICKOFF` or `READY_TO_PROMOTE`;
3. `MATCH_DISCOVERED_NO_BUFFER` must be treated as an operational alert;
4. `TRACKED_NO_SNAPSHOT` must be explained by source state, not silently ignored;
5. no parking/VIP/premium/reserve/non-football product enters `public.snapshots`;
6. completed tracked matches stay queryable historically;
7. raw candidate observations are promoted only after verified match/kickoff mapping;
8. the dashboard coverage table is refreshed and visible;
9. production ML remains independent of this ingestion monitoring logic.

## Scientific boundary

This safety net improves **data acquisition and preservation**, not model parameters.

It does not:

- change any frozen model;
- alter the P7/P9/P11 scientific contracts;
- fabricate historical booking curves;
- use future attendance labels;
- change production forecasts;
- change `live_adjustment`.
