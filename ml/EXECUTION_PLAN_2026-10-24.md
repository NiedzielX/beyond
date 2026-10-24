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

A new audit on 2026-10-24 exposed two additional safeguards that are now mandatory before any P9a learner:

1. **Target eligibility must be cutoff-safe.** A T-24/T-48 target cannot be selected because its trajectory later turned out to be dense between the cutoff and T-6. Representation eligibility must use only snapshots already captured by the target `as_of_at`.
2. **Incumbent lineage must be real.** Older short-horizon events do not have comparable persisted pre-live anchors. Do not recreate an incumbent after labels and present it as prospective/frozen evidence.

Pre-cutoff-only exploratory availability from raw snapshots:

- T-24 target representation: `10` events / `8` clubs;
- T-48 target representation: `7` events / `6` clubs.

These counts are an engineering/readiness audit, not a model sample claim. The deterministic P9a freeze harness must re-derive exact eligible identities from target-visible snapshots and persist their SHA.

Development allowed now:

- target-free raw snapshot export;
- deterministic T-24/T-48 target representation freeze;
- prior-completed-event-only reference pools;
- target/reference snapshot identity lineage;
- target-future mutation/invariance tests;
- reference-pool SHA / freeze manifest;
- separate labels export after freeze;
- incumbent coverage audit.

A learnable P9a residual candidate may be frozen only after those artifacts prove that a valid incumbent comparison exists for enough strict-forward evaluation events. If it does not, keep P9a representation-ready but model-blocked rather than manufacturing an anchor.

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

1. Complete PR CI for P11 provider adapter / Edge Function contract.
2. Implement P9a target-free export + deterministic freeze/lineage audit now.
3. Audit persisted-incumbent coverage before freezing any P9a learner.
4. Configure `THE_ODDS_API_KEY` as an Edge Function secret before any real P11 capture.
5. Run one explicit main-branch P11 capture and inspect mapping/coverage before enabling a schedule.
6. Re-read canonical readiness when P7 is expected to reach 9/9; never execute from the clock alone.
7. Precommit a P11 model only after genuine PIT coverage/variance audit.
8. Define the business-derived minimum meaningful MAE threshold separately from model results.

## Definition of done for this development slice

- execution plan saved and internally consistent with the canonical P9 precommit;
- P11a provider adapter + parser + fixture matcher + tests committed;
- append-only raw quote + as-known consensus contract live;
- P11a capture fail-closed on ambiguous mappings;
- Edge Function deployed but not silently scheduled;
- synthetic P11 contract verification leaves zero persisted evidence rows;
- P9a target-free freeze/lineage tooling committed and tested;
- no target is selected using post-cutoff snapshots;
- no incumbent is reconstructed post-label and misrepresented as frozen evidence;
- full P9 168h and P7 gates remain unchanged;
- PR against `main` passes CI;
- production remains unchanged.
