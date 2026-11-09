# Future fixture coverage — read-only audit

Date: 2026-11-09. Status: IMPLEMENTED — one actual bounded metadata read and aggregate report complete.

The current rolling72 v2 weights, precommit, registry and paired ledger are frozen. This audit complements [the canonical plan](../../../ml/EXECUTION_PLAN_CURRENT.md) and [v2 precommit](../../../ml/artifacts/rolling72_v2/precommit.json); it does not change any experiment or start forecasts.

Inspect the original pinned identity registry, then make at most one bounded read-only `ticket_events` request for fixtures whose kickoff is after the actual request-start clock. Select known metadata columns only, order by kickoff/id, request exact count, and cap at100 rows. Refuse incomplete/truncated counts. No snapshot/history requests, SQL writes, model fits, production change, worker renewal or registry replacement. Preserve original response bytes and actual retrieval receipt privately outside Git; publish only aggregate findings without credentials or private API addresses.

Compare current metadata identities with the pinned registry, retaining aliases and incomplete/conflicting identity cases. Distinguish metadata lead-time coverage from usable snapshot prefixes and issued forecasts. A new ID alone is neither a new independent fixture nor verified fresh evaluation evidence.

Acceptance: report actual query success/failure, exact completeness evidence, current fixture/club counts, supported providers, new versus pinned identities and remaining24/48/72h pre-kickoff metadata windows. Recommend an independently versioned future registry-admission route that keeps the same frozen model weights and requires actual knowledge clocks, immutable snapshot ownership and identity/alias checks. Do not implement v3 or weaken review gates. Defaults remain `production_change=false`, `live_adjustment=0`.


Actual evidence: HTTP200/0-2of3/1124bytes at19:50:43UTC, exact count complete; three current future fixtures/three clubs, zero new IDs or identities, no metadata changes. [Report](../../../ml/FUTURE_FIXTURE_COVERAGE_AUDIT_2026-11-09.md). No source/model/worker/registry mutation or activation. Upstream discovery diagnosis is a separate next audit.
