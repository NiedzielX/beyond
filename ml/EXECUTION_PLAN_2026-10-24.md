# Beyond Ticketing — MAE Execution Plan — 2026-10-24

Status: **ACTIVE DEVELOPMENT PLAN**

Canonical strategy remains `ml/MAE_RESEARCH_ROADMAP_V4.md`.

This file records the next execution slice after P10/P10b closeout. It does not change frozen P4a/P7 contracts, does not lower the full P9 168h gate, and does not activate production.

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
- Existing retrospective P9 reference-curve coverage at 72h / 48h / 24h: `7 / 10 / 13` completed events.
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

### 2. P9 booking curve — SPLIT P9a SHORT-HORIZON FROM FULL P9 168h

The canonical P9 precommit already separates two questions and must be interpreted literally:

#### P9a — 24–48h short-horizon R&D: develop now

Existing retrospective reference-curve readiness is sufficient to continue **development** at short horizons. This is not permission to use future target snapshots or to claim a learned MAE uplift.

A new audit on 2026-10-24 exposed mandatory safeguards before any P9a learner:

1. **Target eligibility must be cutoff-safe.** A T-24/T-48 target cannot be selected because its trajectory later turned out to be dense between the cutoff and T-6. Representation eligibility must use only snapshots already captured by the target `as_of_at`.
2. **Incumbent lineage must be real.** Older short-horizon events do not have comparable persisted pre-live anchors. Do not recreate an incumbent after labels and present it as prospective/frozen evidence.
3. **The target cutoff boundary cannot interpolate through future target data.** If there is no exact T-24/T-48 snapshot, use only the latest already-known pre-cutoff snapshot and only when it is <=6h stale. Otherwise the cutoff point remains missing.
4. **Reference export must be linear in the stored data, not target × reference duplication.** Full historical reference trajectories are exported once as a flat catalog; the freeze harness constructs each target's strict prior-only pool with `reference kickoff < target_as_of_at` and self exclusion.

The first nested-reference export design was intentionally rejected after a live audit exhausted PostgreSQL temporary workspace. No evidence rows were mutated. The live RPC was replaced with the flat-catalog contract before any learner/label access.

Flat export live audit after replacement:

- T-24 raw targets: `16`;
- T-48 raw targets: `13`;
- reference catalog: `17` historical events;
- post-cutoff target snapshot violations: `0` at both cutoffs;
- targets with any genuinely persisted pre-cutoff incumbent row: `6` at T-24 and `4` at T-48.

These are **raw target-free export counts**, not learnable/evaluation sample claims. Canonical 12h interpolation quality, 6h boundary freshness, minimum overlap and strict-prior references are enforced by the deterministic Python freeze harness.

Implemented P9a freeze infrastructure:

- `public.export_p9a_booking_curve_inputs_v1(24|48)` — target-free flat export;
- `public.export_p9a_booking_curve_labels_v1(bigint[])` — separate labels RPC, not used by the freeze workflow;
- `ml/p9a_booking_curve_freeze_v1.py` — deterministic identity/reference/lineage freeze;
- hard fail on post-cutoff target snapshots, label fields and post-cutoff incumbents;
- future and self reference events cannot enter a target's pool;
- fixed K=5 nearest historical curves after eligibility;
- target/reference snapshot identities persisted in lineage SHA;
- model training remains blocked pending a separate learner precommit and valid comparator sample;
- `p9a_booking_curve_export_v1` Edge Function deployed ACTIVE and protected by main-only GitHub OIDC;
- `.github/workflows/p9a-booking-curve-freeze-v1.yml` opens no labels and runs no learner.

A learnable P9a residual candidate may be frozen only after the target-free main audit proves enough `comparator_ready` strict-forward events. If it does not, keep P9a representation-ready but model-blocked rather than manufacturing an anchor.

#### Full P9 — 168h: remain data-bound

Full 168h P9 remains blocked at `4/9` reference curves. Do not lower that gate, weaken the 12h interpolation-quality rule, or treat P9a evidence as evidence for T-168.

The first full-P9 learner still requires a separate precommit after the 168h gate is reached.

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

1. Complete PR CI for P11 and P9a contracts.
2. Run the P9a target-free main audit for T-24/T-48 after merge and inspect exact `freeze_ready` / `comparator_ready` identities before any learner precommit.
3. Configure `THE_ODDS_API_KEY` as an Edge Function secret before any real P11 capture.
4. Run one explicit main-branch P11 capture and inspect mapping/coverage before enabling a schedule.
5. Re-read canonical readiness when P7 is expected to reach 9/9; never execute from the clock alone.
6. Precommit a P11 model only after genuine PIT coverage/variance audit.
7. Define the business-derived minimum meaningful MAE threshold separately from model results.

## Definition of done for this development slice

- execution plan saved and internally consistent with the canonical P9 precommit;
- P11a provider adapter + parser + fixture matcher + tests committed;
- append-only raw quote + as-known consensus contract live;
- P11a capture fail-closed on ambiguous mappings;
- Edge Function deployed but not silently scheduled;
- synthetic P11 contract verification leaves zero persisted evidence rows;
- P9a target-free flat export + freeze/lineage tooling committed and tested;
- no target is selected using post-cutoff snapshots;
- target boundary never uses a future target snapshot;
- no incumbent is reconstructed post-label and misrepresented as frozen evidence;
- full P9 168h and P7 gates remain unchanged;
- PR against `main` passes CI;
- production remains unchanged.
