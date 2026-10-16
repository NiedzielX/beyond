# E0 Dashboard Surface v1 — Live Verification

Date: **2026-10-16**  
Status: **backend ready / sanitized cache live / Step 5 backend complete**

## Purpose

Expose E0 sector status and no-action projection to `NiedzielX/BeyondTicketingPanel` without allowing browser clients to execute the heavy service-role trajectory functions directly.

## Architecture decision

The first public-RPC attempt intentionally failed under `anon` because the wrapper referenced a helper in the non-exposed `private` schema.

We did **not** grant `USAGE` on `private` to browser roles.

Instead the final architecture is:

`service-role heavy E0 functions -> sanitized current cache -> RLS-protected browser SELECT`

This also avoids running ~1 second of sector-history computation on every dashboard request.

## Public read caches

### `public.dashboard_sector_decision_current_v1`

Current sanitized sector rows with:

- event identity;
- sector;
- source/as-of time;
- current and reference public availability;
- gap in seats and normalized gap;
- `UNDERPERFORMING / ON_TRACK / OUTPERFORMING / INSUFFICIENT_SIGNAL`;
- status reason;
- trend state;
- projected public availability at kickoff if trajectory continues;
- projected public sell-through proxy;
- projection confidence/reason;
- explicit price-data state;
- policy/version metadata;
- cache refresh timestamp.

### `public.dashboard_sector_summary_current_v1`

Current event-level summary with:

- sector counts by status;
- projection coverage ratio;
- sum of known projected public availability across sectors that have a valid projection;
- top underperforming sector;
- top underperforming gap in seats;
- its projected public availability at kickoff;
- explicit price-data and pricing-recommendation state.

The aggregate public-availability projection is **not attendance** and may have incomplete sector coverage.

## Price semantics

Until a real price source is connected:

- `price_data_status = PRICE_DATA_MISSING`;
- `current_price = null`;
- `currency = null`;
- `pricing_recommendation_status = PENDING_PRICE_DATA`.

The dashboard must not fabricate a price or show a price recommendation before Step 6.

## Security

Both cache tables:

- have RLS enabled;
- have explicit SELECT policies for `anon` and `authenticated`;
- expose only sanitized decision-support fields;
- grant mutations only to `service_role`;
- do not expose raw/private model metadata.

The heavy direct E0 RPC wrappers and private helper functions are service-role-only after cache activation.

Supabase security advisor after deployment shows no new E0-specific security warning. Remaining warnings predate this change.

## Materializer

Function:

`public.refresh_dashboard_sector_decision_v1()`

Service-role only.

Refresh behavior:

1. replaces current detail and summary cache;
2. evaluates future events that have snapshots;
3. runs current `sector-decision-v1` logic;
4. writes sanitized sector rows;
5. derives event summaries/top underperformer;
6. retains explicit `PRICE_DATA_MISSING` semantics.

First verified refresh:

- detail rows: **348**;
- event summary rows: **13**;
- price state: `PRICE_DATA_MISSING`.

## Scheduler

pg_cron job:

`e0-sector-dashboard-v1`

Schedule:

`12,27,42,57 * * * *`

The job is active and runs:

`select public.refresh_dashboard_sector_decision_v1();`

This cadence follows the current collector cycle and avoids introducing another external scheduler.

## Anonymous read verification

The cache was queried under `SET LOCAL ROLE anon` successfully.

The browser role can read both summary and detail rows through RLS and cannot invoke the underlying heavy/service functions.

## Example — Pogoń Szczecin vs Radomiak Radom

Current event-level cache:

- sector count: **38**;
- underperforming: **14**;
- on track: **11**;
- outperforming: **11**;
- insufficient signal: **2**;
- projection coverage: **94.7%**;
- top underperformer: **D5**;
- D5 gap: approximately **+214 public seats** versus proportional event progress;
- D5 projected public availability at kickoff: approximately **565**;
- price data: `PRICE_DATA_MISSING`.

Selected detail rows include:

- D5 — current 674 / reference 821 / gap +213.67 / UNDERPERFORMING / projected 565.25;
- C7 — current 303 / reference 305 / gap +131.99 / UNDERPERFORMING / projected 290.21;
- C21 — current 222 / reference 225 / gap +95.84 / UNDERPERFORMING / projected 202.81.

## Advisor verification

Security advisor:

- no new E0 warning;
- remaining public SECURITY DEFINER warnings are pre-existing functions unrelated to E0.

Performance advisor:

- no new E0 unindexed-FK warning;
- remaining findings are pre-existing.

## Decision

**Step 5 backend is complete.**

Next actions:

1. wire `BeyondTicketingPanel` Event Detail to the two sanitized cache tables;
2. render `Sector Performance & Pricing` summary + sector table;
3. keep price cells explicitly unavailable until Step 6;
4. audit real price data sources immediately after the dashboard block is wired.
