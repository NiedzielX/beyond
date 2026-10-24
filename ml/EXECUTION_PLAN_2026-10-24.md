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

### 1. P11a genuine PIT odds capture — IMPLEMENTED / SECRET-BOUND

Provider selected for the v2 capture adapter: **The Odds API v4**.

Reasons:

- explicit Polish Ekstraklasa coverage (`soccer_poland_ekstraklasa`);
- pre-match `h2h`/1X2 data;
- ISO timestamps and market-level update timestamps;
- provider terms allow storage, analytics and statistical/ML model training while prohibiting raw-feed resale;
- simple REST integration suitable for append-only PIT collection.

Important boundary:

Provider integration is infrastructure, not model evidence. No historical closing-odds backfill may be used to impersonate earlier PIT observations.

Implemented v2 architecture:

1. target-free local capture input RPC;
2. deterministic team-name normalization backed by verified club aliases;
3. exact home/away club-key matching plus <=90-minute kickoff tolerance;
4. ambiguous or unresolved mappings fail closed;
5. pre-match `h2h`/1X2 only;
6. raw bookmaker-level quotes are preserved append-only;
7. provider event payload is SHA-256 hashed for lineage;
8. provider event id, bookmaker id, capture batch, provider update timestamp and mapping method are persisted;
9. database repeats club/kickoff/timing validation before accepting rows;
10. as-known consensus de-vigs each bookmaker first, takes medians across the latest batch, then renormalizes to sum to one;
11. `outcome_uncertainty` is normalized 1X2 entropy and is explicitly not labeled expected match quality;
12. GitHub OIDC main-only authorization protects the deployed capture function;
13. workflow has **no schedule** and capture requires explicit `workflow_dispatch`;
14. no P11 model ablation is precommitted yet.

Live verification on 2026-10-24:

- migration `p11_market_odds_capture_v2` applied successfully;
- `p11_market_capture_inputs_v2(14)` returns the current upcoming Ekstraklasa event set and aliases without targets;
- `p11_market_odds_readiness_v2()` = `CAPTURE_CONTRACT_READY_NO_GENUINE_OBSERVATIONS_YET`;
- `p11_market_context_as_known_v2(...)` returns `MISSING` before genuine capture;
- function ACLs expose v2 RPCs only to `postgres` and `service_role`;
- transactional rollback test inserted three synthetic bookmaker quotes and produced a valid de-vigged `READY` consensus;
- rollback verification confirmed `0` persisted synthetic rows;
- Edge Function `p11_odds_capture_v2` deployed ACTIVE, version 1;
- automated/scheduled capture remains OFF;
- genuine capture remains **secret-bound** until `THE_ODDS_API_KEY` is configured in Supabase Edge Function secrets.

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

## P11a scientific guardrails

- independent unit remains `ticket_event`;
- capture timestamp is actual ingestion time;
- provider update timestamp is metadata, never substituted for capture time;
- only observations captured before kickoff are eligible;
- odds are de-vigged before feature use;
- 1X2 outcome uncertainty is not called expected match quality;
- expected match quality, if added later, must be a distinct signal/precommit;
- no outcome/attendance target is needed to build capture/readiness;
- provider/API failures do not mutate existing observations;
- no overwrite of historical observations;
- production remains off.

## Next actions

1. Run PR CI for provider adapter / Edge Function contract.
2. Configure `THE_ODDS_API_KEY` as an Edge Function secret before any real capture.
3. Run one explicit main-branch capture and inspect mapping/coverage before enabling a schedule.
4. Only after successful genuine capture decide the sampling cadence based on quota and decision horizons.
5. Continue P9/P7 accumulation unchanged.
6. Re-read canonical readiness when P7 is expected to reach 9/9; never execute from the clock alone.
7. Precommit a P11 model only after genuine PIT coverage/variance audit.

## Definition of done for this development slice

- execution plan saved and updated in repo;
- P11a provider adapter + parser + fixture matcher + tests committed;
- append-only raw quote + as-known consensus contract live;
- P11a capture fail-closed on ambiguous mappings;
- Edge Function deployed but not silently scheduled;
- synthetic contract verification leaves zero persisted evidence rows;
- P9/P7 gates untouched;
- PR opened against `main` and CI green;
- genuine P11 data collection starts only after provider secret configuration.
