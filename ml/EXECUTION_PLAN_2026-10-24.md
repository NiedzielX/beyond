# Beyond Ticketing — MAE Execution Plan — refreshed 2026-10-25

Status: **ACTIVE DEVELOPMENT PLAN**

Canonical strategy: `ml/MAE_RESEARCH_ROADMAP_V4.md`.

This document records the current execution slice after the P7 Long168 gate opened and the ticketing-ingestion safety net was deployed. It does not activate production, lower research gates or reopen closed tuning loops.

## North star

> Minimize true out-of-sample attendance-forecast MAE at decision-relevant horizons using PIT-safe, reproducible evidence.

Production remains:

`live_adjustment = 0`

## Fresh readiness checkpoint — 2026-10-25

Read from `public.ml_research_readiness_v1()` before P7 execution:

- Long72 reproducible rows: `90`.
- Long72 genuine scored events: `2`; first-score trigger open.
- P7 Long168: `10/9` independent events and `139` rows >72h; gate OPEN and executed.
- P4a: `5` READY, `2` genuine labeled events, `2` distinct labeled previous-home-spacing values; gate CLOSED (`>=9` labels and `>=3` distinct required).
- Full P9 168h: `5/9` genuine completed reference curves; still DATA_BOUND.
- P9 T-72 / T-48 / T-24 readiness: `9 / 12 / 15` events.
- Production change: `false`.

## Ticketing ingestion safety net — LIVE

The earlier discovery/mapping gap could have caused loss of valuable booking-curve history. A permanent pre-mapping protection layer is now live.

### Controls

1. RoboTicket discovery uses same-element/direct-event identity rather than nearby-text heuristics.
2. Parking, VIP, Premium, conference, reserve-team and other obvious non-match products fail closed.
3. A known-football-club gate prevents other sports sharing the same storefront from entering the model-facing pipeline.
4. Discovery cadence is hourly instead of every six hours.
5. Genuine but not-yet-mapped match candidates are captured into a private raw buffer every 10 minutes.
6. Raw candidate observations are isolated from model-facing `public.snapshots`.
7. Original `captured_at` is preserved.
8. Once a verified fixture identity/kickoff exists, the event is promoted and eligible raw observations are backfilled into the normal snapshot lineage.
9. The normal collector remains active every 15 minutes.
10. Dashboard ingestion status refreshes every 10 minutes.
11. Beyond Ticketing Panel / Data Quality exposes tracked, buffered, excluded and gap states.

Safety rule:

> Candidate buffering preserves evidence only. A candidate cannot become model-facing until event identity and kickoff are verified.

The first live pass protected multiple newly discovered football events before normal mapping. Non-football GKS products were detected and kept out of model-facing snapshots. `Wisła Kraków – Cracovia` is currently tracked but source inventory is not yet exposed, so it remains an explicit `TRACKED_NO_SNAPSHOT` gap instead of receiving fabricated data.

## P7 Long168 — EXECUTED / ADVANCE RESEARCH

Frozen identity manifest:

- independent frozen events: `10`;
- rows: `139`;
- manifest SHA-256: `185a9fc90e646bd5fa1bbed3b50c625d65d127a2b2943501761bdfcb89f354ed`;
- target values present in freeze: `false`;
- model results opened before freeze: `false`.

Frozen T-7 anchor replay:

- status: `P7_T7_ANCHOR_REPLAY_READY`;
- anchor count: `10`;
- target-attendance invariance: `PASS`;
- anchor package SHA-256: `da22e25a940b9bb7ce0add3306348f6831f9def5463fafe498615353842553f5`.

Fixed precommitted tournament result:

- anchor event-balanced MAE: `7409.79`;
- best candidate: `gbr-l1-depth2-n50-lr003`;
- challenger event-balanced MAE: `6339.99`;
- ΔMAE vs anchor: `-1069.80` (`-14.44%`);
- event improvement rate: `0.80`;
- forward-fold improvement rate: `0.80`;
- forward test events: `5`;
- paired event-block bootstrap 95% interval for ΔMAE: `[-2566.13, +174.47]`;
- `P(ΔMAE < 0) = 0.9322`;
- worst event degradation: `+712.05` MAE;
- scorecard SHA-256: `f684570856e264dae288599a8e24dde6802f84669a43e304c1d900726aa94e45`.

Interpretation:

- internal P7 precommit decision: `ADVANCE_RESEARCH`;
- governance interpretation: `POINT_GAIN_UNCERTAINTY_LIMITED` because the uncertainty interval still crosses zero;
- this is meaningful positive research evidence, not production-readiness evidence;
- no candidate/hyperparameter retuning is allowed after observing this result;
- `production_change=false`, `production_activation_allowed=false`, `live_adjustment=0`.

## P9 / P9a — CURRENT PRIORITY AFTER P7

### P9a T-24/T-48 — target-free freeze audit now

P9a is representation/freeze infrastructure, not a trained learner.

Hard requirements remain:

- target values remain unopened;
- no model training;
- no future target snapshots;
- target cutoff uses only data already known by `as_of_at`;
- maximum cutoff-boundary staleness remains 6h;
- self references and future reference events remain excluded;
- incumbent lineage must be genuinely persisted, not reconstructed after labels;
- learner remains blocked pending a separate precommit and valid comparator sample.

The main P9a audit is being run after this plan refresh. Exact T-24/T-48 target/reference counts and manifest SHAs must come from the new run; do not reuse stale counts.

### Full P9 168h — remain data-bound

Full-window P9 remains at `5/9` genuine completed curves. Do not lower the gate or fit the first full-window residual learner early.

The ingestion safety net should improve future curve coverage by preserving observations from first discovery, even when verified mapping arrives later.

## P11a market odds v2 — GENUINE PIT DATA ACCUMULATING

Provider:

`the-odds-api-v4` / `soccer_poland_ekstraklasa` / pre-match `h2h`.

Fresh database readiness on 2026-10-25:

- status: `GENUINE_PIT_DATA_ACCUMULATING`;
- events with any genuine PIT 1X2: `2`;
- clubs with PIT 1X2: `2`;
- events with at least 3 bookmakers: `2`;
- events reaching 72h coverage: `1`;
- events reaching 24h coverage: `1`;
- events reaching 168h coverage: `0`;
- target values used: `false`;
- model precommitted: `false`;
- production change: `false`.

No P11/odds pg_cron job is currently active. Do not enable recurring capture merely because genuine rows exist. First audit the actual quote lineage, mapping and provider coverage; then enable recurring append-only capture only if that audit passes.

Scientific guardrails remain:

- append-only raw bookmaker quotes;
- actual capture timestamp is authoritative;
- provider update timestamp is metadata only;
- exact verified aliases + kickoff tolerance;
- ambiguous mappings fail closed;
- no closing-odds backfill into earlier PIT cutoffs;
- de-vig bookmaker quotes before consensus;
- `outcome_uncertainty != expected_match_quality`.

## P10 / P10b — CLOSED

Do not reopen without a materially new mechanism.

P10 v1:

- local HGB `2120.93`;
- pooled HGB `2057.46`;
- ΔMAE `-63.47`;
- `POINT_GAIN_UNCERTAINTY_LIMITED`.

P10b vs frozen Pre-Live v3:

- incumbent `1919.92`;
- pooled `2067.43`;
- challenger-incumbent ΔMAE `+147.51`;
- 95% CI `[+82.97,+210.67]`;
- 0/4 folds and 0/5 horizons improved;
- `NO_RESEARCH_GAIN`.

## P4a / Long72

P4a remains frozen/data-bound. Do not modify the fixed previous-home-spacing challenger before the gate opens.

Long72 remains immutable forecast-before-label evidence. Two genuine events are scored; continue prospective evidence collection without retuning the frozen package.

## Governance v2 — business threshold still required

`ROBUST_RESEARCH_ADVANCE` still requires a predeclared minimum practically meaningful MAE improvement derived from actual downstream decision costs, not from the challenger result.

P7's positive point estimate must therefore not be re-labeled robust merely because the observed uplift is large.

## Immediate development order

1. **P7 Long168: DONE for this frozen research tournament; advance research only, no production change.**
2. **Run/inspect P9a target-free T-24/T-48 audit now.**
3. Audit P11 genuine odds lineage/coverage; if valid, enable recurring append-only capture without opening a model ablation yet.
4. Keep full P9 168h data collection running toward 9 genuine completed curves.
5. Define the business-derived minimum meaningful MAE threshold.
6. Keep P4a and Long72 prospective evidence collection unchanged.
7. Keep ingestion safety-net monitoring active and fail closed on ambiguous/non-football candidates.

## Definition of done for the current slice

- ingestion safety net live and visible in panel;
- P7 frozen identities, anchor replay and fixed tournament complete;
- P7 result recorded without post-result retuning;
- P9a target-free audit rerun on current data;
- P11 genuine PIT rows audited before any schedule activation;
- no labels opened early;
- no hidden production activation;
- `live_adjustment=0` preserved.
