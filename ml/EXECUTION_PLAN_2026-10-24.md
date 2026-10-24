# Beyond Ticketing — MAE Execution Plan — 2026-10-24

Status: **ACTIVE DEVELOPMENT PLAN**

Canonical strategy remains `ml/MAE_RESEARCH_ROADMAP_V4.md`.

This file records the next execution slice after P10/P10b closeout. It does not change any frozen P4a/P7/P9 scientific gate and does not activate production.

## North star

> Minimize true out-of-sample attendance-forecast MAE at decision-relevant horizons using PIT-safe, reproducible evidence.

Production remains:

`live_adjustment = 0`

## Fresh readiness checkpoint

Read from `public.ml_research_readiness_v1()` on **2026-10-24 09:41:41 UTC / 11:41 Europe/Warsaw**.

- Long72 reproducible rows: `81`.
- Long72 genuine scored events: `0`.
- P7 Long168: `8/9` independent events >72h — gate still closed.
- P4a: `5` READY independent events, `0` genuine labels — gate still closed.
- P9 full 168h reference curves: `4/9` — gate still closed.
- P9 72h / 48h / 24h coverage: `7 / 10 / 13` completed events.
- P4b next-opponent READY rows: `0`.
- Production change: `false`.

Expected P7 timing remains approximately **2026-10-24 18:30 Europe/Warsaw** for event 6 to enter the <=168h window. The clock is not an execution condition; always re-read readiness before execution.

## Closed research path

P10/P10b are closed for the fixed pooled-HGB architecture.

- P10 proved a real pooling effect against the same weaker local HGB.
- P10b lost materially to frozen Pre-Live v3.
- Do not retune P10/P10b after observing those results.

## Development order

### 1. P11a genuine PIT odds capture — START NOW

Primary provider candidate for v1 integration: **The Odds API v4**.

Reasons for the v1 adapter choice:

- explicit Polish Ekstraklasa coverage (`soccer_poland_ekstraklasa`);
- pre-match `h2h`/1X2 data;
- ISO timestamps and market-level update timestamps;
- provider terms explicitly allow storage, analytics and statistical/ML model training, while prohibiting raw-feed resale;
- simple REST integration suitable for append-only PIT collection.

Important boundary:

Provider integration is infrastructure, not model evidence. No historical closing-odds backfill may be used to impersonate earlier PIT observations.

Implementation slice:

1. provider-neutral fixture matching contract;
2. deterministic team-name normalization / explicit alias map;
3. capture only pre-match 1X2 observations;
4. aggregate bookmaker observations into one deterministic market snapshot only after preserving source lineage;
5. append into the existing private P11a table through a controlled service-role path;
6. hash raw provider event payload for lineage;
7. fail closed on ambiguous event mapping;
8. record provider event id, bookmaker count and mapping evidence;
9. no in-play capture in v1;
10. no model ablation before genuine PIT coverage exists.

### 2. P9 booking-curve — KEEP COLLECTING, HARDEN HARNESS

The representation is ready, but the learnable 168h model stays blocked at `4/9`.

Development allowed now:

- representation tests;
- target-future leakage tests;
- reference-pool lineage audit;
- readiness/coverage reporting;
- deterministic freeze-manifest tooling.

Forbidden now:

- opening/tuning a learnable P9 residual model before the 168h gate and a separate learner precommit.

### 3. P7 — EXECUTE ONLY WHEN CANONICAL GATE OPENS

At `9/9`:

`readiness -> freeze exact identities -> verify frozen T7 replay -> attach labels -> strict forward tournament -> paired event-block uncertainty -> research decision`

Do not redesign P7 after gate opening.

### 4. Governance v2 — BUSINESS THRESHOLD

Existing code intentionally prevents `ROBUST_RESEARCH_ADVANCE` without a predeclared minimum practically meaningful MAE improvement.

Next non-model task:

- derive that threshold from actual downstream decisions and asymmetric error costs;
- do not derive it from observed challenger score distributions.

## P11a v1 scientific guardrails

- independent unit remains `ticket_event`;
- capture timestamp must be actual ingestion time;
- provider update timestamp is metadata, never substituted for capture time;
- only observations captured before kickoff are eligible;
- odds must be de-vigged before model feature use;
- 1X2 outcome uncertainty is not called expected match quality;
- expected match quality, if added later, must be a distinct signal/precommit;
- no outcome/attendance target is needed to build the capture/readiness layer;
- provider/API failures must not mutate existing observations;
- no overwrite of historical observations;
- production remains off.

## Definition of done for this development slice

- execution plan saved in repo;
- P11a provider adapter + parser + fixture matcher + tests committed;
- append-only capture function created but not silently activated without required API secret;
- P11a capture is fail-closed on ambiguous mappings;
- P9/P7 gates remain untouched;
- canonical docs updated after implementation results;
- PR opened against `main` after tests/audit.
