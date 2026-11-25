# P0-4d: protected PERS feed and investor panel

24 November 2026. Parent: P0-4b/P0-4c and canonical MAE roadmap v6.
Root owns integration, capability gate, Edge routing and release. One backend
writer owns the new read-only feed and its tests; one panel writer owns the
typed client, panel and relay; independent reviewer checks clocks and access.

## Contract

Add `public.get_rolling72_mvp_persistence_feed_v1(bigint,text,bigint,integer,bigint)`
with the same parameter order/names as the existing investor feed. Only
`rolling72-mvp-persistence-v1` is accepted. Existing source/PERS/frozen SQL and
old feed/authorization functions remain unchanged. Service-only SECURITY
DEFINER, empty search_path, UTC, bounded limit1–200 and validated positive IDs.
No source capture, issue, score or mutations during feed reads.

Use `rolling72-investor-feed-v1` response shape and the existing availability
target contract `public_available_total_with_scope_events_v1`: same public
total with explicit scope flags, separate lane/cohort. PERS is exposed as
method `persistence`, never combined with E5/B metrics. Return source seals as
observations; seal IDs are receipt IDs within this lane. Captured and known
times remain distinct. Origin is exactly the bundle's input seal. Its visible
prefix requires captured_at<=origin captured_at AND known_at<=issued_at.
Labels may become known later and are separate from this prefix. The v1 wire
does not repeat a per-issue `input_prefix` array: clients assemble the visible
prefix from the independently paginated top-level observations using both
clock filters. This keeps response size bounded while preserving the temporal
contract.

Fixture metadata comes from the registered source binding; compare current
metadata without rewriting issued identity. Bundle IDs, actual issue/target
clocks, values, null outside targets, provenance, real labels and per-method
errors must map exactly to PERS ledgers. No dummy parent experiment: lineage
parent IDs/hash may be null. Scenario fields state price/promotion/advertising
unknown and public-pool interpretation limited; never assert a causal effect.

Independent descending issue/seal cursors, limit+1 pagination, empty and partial
states. Global scorecards cover the full registered PERS lane independent of
the selected fixture/page, map get_status denominators honestly: full
source-backed eligible opportunities, refusals and unattempted count; null MAE
with zero labels. No expensive frozen full-history joins or repeated full-lane
score aggregation for each issue row.

## Capability and panel

New private grants and service-only authorizer for exact fixture27049 and PERS,
expiry no later than29November01:15UTC. Store only an existing owner's code
SHA256, never raw code; existing E5/B grants are untouched. New Edge
`rolling72_pilot_feed_v2` routes PERS to the new grant/feed and existing E5/B to
their existing grant/feed. Validate fixture/lane pairs, request parameters,
grant expiry and response scope; fixed project origin, bounded timeout,
no-store, redacted errors and no credentials in logs. No broad public access.

Panel's same-origin relay points to fixed v2 Edge; frontend adds Jagiellonia
and PERS with contextual valid lane options. Preserve existing E5/B behavior,
microsecond checks, one-origin three-future-point chart, selected vintage,
late-label distinction, pagination, five-minute visible polling, abort/races,
stale-state retention and memory-only access code. No Supabase secrets or
arbitrary upstream URLs in browser. No manufactured forecasts or zero scores.

## Acceptance

Isolated PG16 contract tests: exact clocks/values, first point and zero/null,
labels and future-prefix exclusion, cursor independence, global denominators,
no writes/frozen body changes, ACLs and malformed/out-of-scope input.
Client/relay/Edge tests and browser scenarios for new PERS and E5/B regressions.
Independent review before hosted deployment or publication. Hosted bodies,
grants and actual protected browser chain verified separately; code/CI alone
does not prove Vercel page access, automatic new vintage or reduced MAE.

No model fitting, old outcome-based tuning, historical backfill, production
adjustment, paid plan/account change, or change to frozen experiment contracts.
