# Rolling72 post-break Stellis source gate — design

**Status:** design only; no source activation, event admission, hosted write, or change to the frozen lane. Reconcile the spring calendar and review a separate provider contract before collecting post-break cohort data.

## Intended eight-club sourcing roster

Keep the existing active Roboticket roster distinct from the proposed Stellis additions:

| Source family | Home clubs |
|---|---|
| Roboticket (5 active lane clubs) | Cracovia (`cracovia`), GKS Katowice (`gkskatowice`), Raków Częstochowa (`rakow`), Śląsk Wrocław (`slaskwroclaw`), Wisła Kraków (`wislakrakow`) |
| Stellis (3 proposed additions) | Piast Gliwice (`piastgliwice`), Motor Lublin (`motorlublin`), Widzew Łódź (`widzewlodz`) |

These are eight distinct clubs. The Stellis clubs are tangible source candidates, not yet eligible fixtures or cohort admissions. The October source-coverage map documents `stellis_collect_v3` and these active stores; fresh hosted reads on 27 November show verified Stellis events and snapshots for all three:

- Piast–Jagiellonia, source event `50502`, ticket event `25668`: 1,128 snapshots, latest capture 16:13:02 UTC.
- Motor–Lech, source event `50505`, ticket event `25667`: 2,852 snapshots, latest capture 16:13:02 UTC.
- Widzew–Zagłębie, source event `11601`, ticket event `24781`: 1,178 snapshots, latest capture 16:13:02 UTC.

Each was mapped with `stellis-visible-availability-v2.2+active-stage-guard+latest-raw+league-pair-window` and `mapping_confidence=verified`. These examples establish present connector operation only. The checked TheSportsDB fixture shadow ends at 17 December 2026 and contains no spring fixtures, so exact post-break home fixtures and kickoff identities remain unverified. The active Stellis candidates also include Motor–Widzew (event `51202`) and Piast–Zagłębie (`50720`) in `awaiting_fixture`; neither is an admission.

## Fail-closed admission requirements

Before an event can enter a separate Stellis prospective lane, retain and review the original source observation and require all of the following:

1. **Event identity:** source club slug and configured store domain, provider event ID, exact public event URL, raw event title, home and away labels, normalized club keys, and source kickoff. Reconcile to the official league and home-club fixture schedules; require one unique first-team Ekstraklasa home/away pairing within the established date window. Reject cup, friendly, stadium tour, away-sector-only, season-pass, or ambiguous listings.
2. **Visibility and completeness:** explicitly distinguish visible aggregate availability from hidden, unknown, sold, or unavailable data. A visible count must be numeric, nonnegative, event-wide or drawn from a documented complete inventory pool, and supported by the collector's recognized source variant. Keep `available_total=null`/unknown when hidden or incomplete; never turn absence, parse failure, or `sold_total` into zero availability. Preserve raw sector/pool completeness indicators and exclusions so the accepted aggregate can be reproduced.
3. **Capture clocks:** preserve request start/finish and server response date where available, `captured_at` in UTC from the actual completed read, source kickoff as observed in that same response, and collector/version lineage. Reject future, stale, or retrospectively copied clocks. Start prospective collection only after the separate lane is activated; historical snapshots cannot fill missed origins or target labels.
4. **Raw evidence and lineage:** persist the exact decoded source payload (or immutable raw-body reference plus SHA-256), status, request/final URL, byte count, capture time, source event ID, parser/adapter version, visibility state, completeness result, mapping result, and promotion linkage in private raw evidence. Keep raw source identity separate from canonical fixture identity and preserve every parse/mapping refusal.
5. **Canonical promotion:** only the latest valid observation may promote after identity, league-membership, kickoff, visibility, freshness, and completeness gates pass. A later invalid/hidden read must not permit backtracking to an older convenient visible value. Never promote an unknown inventory state as a measured zero.

The current Stellis contract already retains `club_slug`, `external_event_id`, `captured_at`, event/home/away labels and keys, kickoff, `availability_exposed`, totals, source URL/version, and raw metadata. The design gate requires reviewing that metadata for raw-payload integrity, response/request clocks, and complete-pool proof before relying on a value for +72 evaluation.

## Lane and evaluation boundary

Do not add Stellis events to, rewrite, or extend the frozen Roboticket lane or its admission receipts. Establish a separately versioned post-break manifest, lane ID, activation time, issue/scoring deadlines, immutable source contract, and per-event admission receipt. Keep its observations, forecasts, refusals, and labels isolated from the current Roboticket window and frozen fixtures.

For any future 30-fixture/eight-club evaluation, declare provider/source family on every event and report coverage, refusals, missing labels, +72 MAE, bias, and paired comparisons by provider and club. A pooled primary estimate is permitted only if both adapters prove the same event-wide available-seat target, equivalent capture/issue clocks, complete-pool semantics, and scoring rules before outcomes are seen. Otherwise report provider-specific estimates and do not claim the combined 30/8 gate passed. Reject unsupported providers and source states at intake; do not substitute hidden Stellis inventory, club aggregate sales, or attendance data for a public-inventory label.

The stable-pair policy has a stronger feature requirement. A usable aggregate
can support an availability benchmark but cannot establish continuity of
sector and price-area identities. Before counting Stellis matches in a
formal stable-pair comparison, require complete, repeatable pair-level
source evidence with preserved identifiers. If that evidence is unavailable,
evaluate the aggregate source separately under its own predeclared policy.

**Observed extent (targeted read-only check, 27 November 2026 16:23:45 UTC):**
all three cited events are currently aggregate-only. Their newest raw records
use `stellis-react-events-v3`, report `show_available_tickets_count=true`,
`has_active_stage=true`, and a numeric event-level `available_total` (Piast
4,187; Motor 2,098; Widzew 716 at 16:23:02 UTC). The collector extracts
`availableTicketsCount`; it does not emit sector or price-area rows. For each
ticket event, `snapshots.sector_count` is null on every row, and there are zero
rows in `public.sector_price_area_observations_v1` and
`public.ticket_price_observations_v1`: zero sector-source IDs, price-area IDs,
sector × price-area identities, numeric sector-availability quantities, or
numeric price observations. The Stellis raw metadata also has no sector,
price, or sector/price-row collection. Thus these three clubs are currently
**ineligible for the stable-pair comparison**. They may only be considered in
a separately predeclared aggregate-availability analysis after the common
target/clock/completeness contract is accepted; they cannot be counted toward
stable-pair support by virtue of event-level totals or snapshot volume.

The checked-in collector/ingestion contract supports this finding:
`supabase/functions/stellis_collect_v3/index.ts` parses the React event fields
into one event row (`availableTicketsCount` as `available_total`, plus
`soldTicketsCount` and event metadata); it has no sector or price-area row
extraction. `supabase/sql/stellis_ingestion_v1.sql` stores that same event-level
total in private raw observations and promotes it to `snapshots` with
`sector_count=null`. The verified Piast, Motor, and Widzew evidence is therefore
an aggregate count, not native sector × price-area identities or quantities.
The bounded live metadata check above found no child rows for these examples;
no broader source crawl was used for this conclusion.

Club-aggregate sales/refund/pool/membership/scan/final-attendance feeds are a separate target pilot under `ROLLING_72H_CLUB_PILOT_DATA_V1.md`. No accepted club feed is evidenced. Such feeds cannot substitute for availability observations or contribute to this cohort's availability +72 labels.

## Observed blockers and next gate

- The schedule shadow has no post-break fixtures; attach current official league and home-club fixture proof before any admission.
- Motor and Piast have current numeric public aggregates on verified December fixtures, while Widzew has a current numeric aggregate on its Nov 28 fixture. These support adapter readiness, not spring eligibility.
- The three example events have no stored numeric sector × price-area observations or stable pair identities; they cannot count in a stable-pair feature comparison without a new supported parser and prospective pair-level evidence.
- Korona's fresh candidate was `hidden_availability` with null available count; its only canonical snapshots were stale (last 26 October). Radomiak had no canonical event/snapshots and its fresh candidate was also `hidden_availability`. Do not count either as a fourth/fifth Stellis club without new evidence and an accepted visibility contract.
- Current technical audit records zero accepted club aggregate feeds. Sales and final attendance require separate provenance, reconciliation, missingness, and scoring gates.

Next step: after the spring fixtures are officially scheduled, reconcile one bounded fixture batch for Piast, Motor, and Widzew against their club calendars and fresh Stellis event listings; review raw completeness and actual capture clocks; then freeze and separately review the source-specific lane manifest. Until those checks pass, readiness remains **three supported club sources, zero verified post-break admissions**.
