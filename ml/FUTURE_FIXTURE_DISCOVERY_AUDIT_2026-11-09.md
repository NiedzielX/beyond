# Future fixture discovery — verified admission bottleneck

**The source pipeline is not globally offline. New event admission is blocked even while candidate discovery and raw buffering continue.** The earlier [complete live coverage read](FUTURE_FIXTURE_COVERAGE_AUDIT_2026-11-09.md) found only3canonicalfuturefixtures. This follow-up inspected existing code first, then bounded actual metadata and Actions records. [Machine evidence](FUTURE_FIXTURE_DISCOVERY_AUDIT_2026-11-09.json); private original responses and actual receipts are under `/workspace/ops-runtime/2026-11-09-future-fixture-discovery-audit/`.

## Actual source state

At19:54–19:58UTC/20:54–20:58Warsaw, exact-count reads proved13activeRoboticketclubs and5activeStellisclubs. The cached admission table had97untracked rows whose kickoff is unknown or future:89candidate rows and8schedule gaps. Its actual `refreshed_at` was19:49UTC. Status counts were12`BUFFERING_AWAITING_KICKOFF`,1`MATCH_DISCOVERED_NO_BUFFER`,8`SCHEDULE_GAP`,38`UNKNOWN_EXCLUDED`,28`NON_MATCH_EXCLUDED`,10`NON_FOOTBALL_EXCLUDED`. These97rows are not97new eligible football fixtures.

Candidate metadata and cached raw-buffer timestamps are fresh for multiple clubs. Some rows with unknown canonical kickoff still refer to past dates in their labels; a freshly refreshed dashboard does not make the underlying fixture current. No expiry, exclusion, polling cadence or recorded observation was changed.

## Concrete Roboticket parser gap

For all six cases below, the actual metadata says discoveryv8, direct-pageHTTP200, no login redirect, `direct_page_match_identity`, and a direct-pageH1 containing a full future civil date/time. Nevertheless `metadata.discovered_kickoff_at` isNULL and candidate status is`discovered`.

| Candidate | Date/time text in direct-page H1 | Existing league pair/date | Cached raw-buffer latest |
|---|---|---|---|
|Cracovia10797|2026-11-21 14:45|same pair/date, source2490319|Nov9,19:47UTC|
|GKS Katowice5771|2026-11-22 14:45|same pair/date, source2490320|Nov9,19:47UTC|
|Lech11258|2026-11-29 14:45|same pair, league dateNov28, source2490330|Nov9,19:47UTC|
|Raków6593|2026-11-22 12:15, preceded by`niedziela,`|same pair/date, source2490321|Nov6,21:47UTC|
|Śląsk8781|2026-11-28 17:30|same pair/date, source2490325|Nov9,19:47UTC|
|Wisła Kraków11916|2026-11-28 20:15|same pair/date, source2490326|Nov9,19:47UTC|

These times are preserved source text, not newly verified UTCkickoffs. This audit retained the actual metadataJSON, not original sourceHTML. **No sourceHTMLSHA exists for this audit**, and reconstructing an HTML fixture from H1 must be described as derived test input rather than original page bytes. The six-row responseSHA is`12f6113a27fcd35f43f9075239055671c69a809c4649719ff942d7dfb80d3531`, retrieved19:56:58UTC.

Code locations in `supabase/functions/roboticket_discover_clubs/index.ts`:

- `extractKickoff`, lines78–81, recognises only ISOdate strings assigned to selected JS/JSONfields. It does not inspect the already extracted direct-pageH1. Missing timezone currently defaults to+01:00; a new interpretation must declare Europe/Warsaw and handle its calendar/DST rules explicitly.
- `probeEvent`, lines83–86, obtains identity/H1 and calls that parser; metadata line146 preserves H1/status andNULLkickoff.
- Lines148–150 require `event.probe.kickoffAt` before creating a verified-schedule payload. Thus the six cases never reach that path despite visible date/time text.
- **A timestamp fallback alone is insufficient:** lines149–150 split the entire identity string into home/away. For a dated H1, the away string retains the date/time and possibly weekday. A future pure parser must return separate clean participants, timestamp and raw provenance, with actual-case tests; do not append dated away-team names into the verified schedule.

## League data already exist, with limits

One bounded read of `sporting_league_matches_shadow` found exactly18future fixture rows forNov10–Dec7, all with source`fetched_at=2026-11-09T18:10:00.091546Z`. Exact home/away pairs exist for all six Roboticket cases. Five have matching source civil dates. **Lech's direct H1 saysNov29 while the league shadow saysNov28.** The audit cannot decide whether one provider has a placeholder or rescheduled date; preserve that conflict and do not silently force agreement. The league table supplies dates here, not a verified kickoff hour.

MotorLublin50505has fresh raw buffering and a parsedDec5kickoff, but its exact Motor–LechDec5league pair is absent from this bounded source range, consistent with the cached`league fixture confirmation pending`diagnosis. Radomiak50301is a separate availability blocker: current cached diagnostic says aggregate availability is hidden and raw count is0. Neither is solved by retuning ML.

The existing source-consumption routes are `private.roboticket_verified_schedule_v1`→`promote_roboticket_verified_candidates_v1`, and Stellis's unique league-pair/date-window gate. `public.process_thesportsdb_round_responses_v1` writes the league shadow from actual provider responses. The sporting-contextGitHubworkflow instead collects context for existing ticket events; it is not the fixture-discovery route.

## Execution proof and access boundary

Roboticket's hourly discovery and ten-minute candidate buffer, Stellis collection, and dashboard refresh are configured in SQL via Supabase`pg_cron`. Their actual cron job records were not accessible/read in this audit; SQL configuration alone is not execution proof. Fresh current DB candidate/buffer/refresh timestamps establish observed activity, without proving every configured job succeeded.

Actual recent main`Sporting Context Collector`runs42572730127,42528165820,42484631460,42452810231,42417567039areSUCCESS; latest visible run beganNovember9 at06:23UTC despite its configured six-hour cadence. Those successes do not prove league-fixture intake or source promotion. No workflow was dispatched.

The narrow `dashboard_ticketing_fixture_coverage_v1`read returnedHTTP403:`permission denied for function normalize_ticketing_name_v1`. This is a caller diagnostic access limitation, not evidence that owner/definer refresh or promotion stopped. No auth retry or privilege change was attempted. The separately permitted public league-metadata read supplied the18row evidence above.

## Next step, deferred to a new change specification

Build and test an isolated **read-only** parser that can recover clean participants and an explicit civil timestamp from actual direct-pageH1 metadata while retaining provenance, rejecting ambiguous/multiple/invalid dates, and distinguishing metadataJSONfrom originalHTML. Obtain actual direct-pageHTML/current independent schedule evidence before any automatic verified admission. Preserve Lech's date disagreement, Motor's missing league pair, inactive/hidden inventory, explicit league scope, timezone uncertainty and alias guards. Anchorlabelalone is insufficient.

This audit implements no parser, permission fix, schedule import, promotion, forecast, registry change or model search. Existing frozen v1/v2weights and lanes remain unchanged. A future registry-admission version must retain the same fitted weights and current30freshfixtures/8clubs review rule; repeated readings of two events cannot satisfy that gate. User's newly requested separately precommitted historical24/48/72h experiment now takes priority; this source fix is deferred.

Phase2used six bounded database metadata GETs and one GitHubActionsGET; zero snapshot/historyGETs, database writes, workflow dispatches or model fits. One of the six metadata reads was the denied diagnostic view. `production_change=false`, `live_adjustment=0`.
