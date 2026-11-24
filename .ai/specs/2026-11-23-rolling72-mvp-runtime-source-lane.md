# Rolling72 P0-4b — independent forward-only runtime source lane

Date: 2026-11-23
Status: LOCAL IMPLEMENTATION COMPLETE — PR229/CI PASS; hosted deployment/activation pending
Owner: integrator assigns disjoint SQL / PostgreSQL-test / offline-contract files
Parent: [MAE and investor MVP development](2026-11-22-rolling72-mae-and-investor-mvp-development.md), P0-4
Canonical strategy: [MAE Research Roadmap v6](../../ml/MAE_RESEARCH_ROADMAP_V6.md)

## Why this increment exists

P0-4a, `ml/rolling72_mvp_source_registry_v1.py`, validates caller-supplied admission, source identity, counts, hashes and clocks. Its own contract correctly says it is preparation-only: it does not execute admission or a source read, and cannot prove that source rows were committed and visible together. The remaining work is a real, separate runtime lane for newly admitted fixtures, not another offline packet validator.

The 23-November B error budget reports that changed-sector-count labels contain 89.15% / 96.12% / 92.09% of drift24 absolute error at +24/+48/+72. That retrospective concentration motivates preserving actual source membership and scope changes for future diagnosis. It does not show causality, make a future feature safe, establish independent validation, or justify a new model. Equal sector counts do not establish stable membership. E5 remains pending and separate. No attendance-MAE or revenue claim follows from this work.

## Bounded deliverable

Implement a new private lane, `rolling72-mvp-research-v1`, with its own registry, append-only source read attempts, immutable validated source receipts/seals, and immutable per-receipt/per-horizon opportunity rows. It dynamically registers only events already admitted by Roboticket forward-only admission v2. It captures committed source state by reading the parent admission/event, snapshot and all required child rows in one MVCC-consistent SQL statement, validates exact identity and reconciliation, hashes the read, and only then assigns the seal's `known_at` clock.

This slice does not modify, import into, or share writable tables/functions/jobs with the frozen five-event registries or E5/B/v5 lanes. It adds no model. The first valid receipt is retained as an explicit `NO_PRIOR` first point, not dropped for lack of history. It creates forecast-opportunity denominators for each eligible receipt × horizon even if issuance is not ready. Persistence issue creation and due-label scoring are P0-4c; if the implementation budget supports them separately, do not silently fold them into this contract or claim them complete here.

### Owned deliverables to assign

- New migration only: `supabase/sql/rolling72_mvp_research_v1.sql`.
- Isolated local PostgreSQL 16 contract suite only: `tests/postgres/test_rolling72_mvp_research_v1.py`.
- Optional offline parser/fixture contract only: `ml/rolling72_mvp_research_v1.py` and a matching focused test, if needed to bind JSON hashes and exercise the SQL response without a live DB.
- Integrator separately owns deployment, a bounded scheduled invocation, job expiry, and canonical status updates. Do not apply the migration, activate, create a cron job, or write hosted data as part of this specification task.

## Frozen boundaries and explicit non-goals

- Do not change `roboticket_forward_only_admission_v2.sql`, its triggers/gates, admission receipts, ticket-event rows or public source rows. Admission remains its own already-authorized step.
- Do not change frozen E5, B, v5, v3a, the five-event seal lane, any past forecast/label or prior receipt. No historical bootstrap, backfill, fixture transfer, compatibility view that writes to a frozen lane, or cross-lane ranking.
- Do not call an external source, use service credentials outside service-only SQL RPCs, update prices/promotions/ads, issue club outreach, or activate forecasting.
- `live_adjustment = 0`. Availability is a public availability proxy, not sold tickets, demand, attendance, revenue or causal intervention evidence. The ~1200-seat attendance-MAE goal remains separate.
- No use of `created_at`/identity sequence/default timestamps as evidence of source commit visibility. No caller-supplied time may define actual `known_at`, capture start/completion, activation, or expiry.
- No schema-cache workaround or changes to unrelated hosted functions, old triggers, models or schedules.

## Lane identity, activation and admission

Define one fixed lane/version: `rolling72-mvp-research-v1`. The activation RPC accepts exactly these ten manifest keys. Fixed horizons and history/target policies are pinned by the SQL hash, not caller-overridable fields:

```json
{
  "lane_id": "rolling72-mvp-research-v1",
  "version": "rolling72-mvp-research-v1",
  "source_family": "roboticket/roboticket",
  "unit": "available_total_seats",
  "max_source_age_seconds": 3600,
  "max_batch": 25,
  "max_fixtures": 100,
  "issue_until": "explicit UTC cutoff",
  "scoring_until": "explicit UTC cutoff no earlier than issue_until plus 78 hours",
  "sql_sha256": "exact reviewed SQL SHA256"
}
```

Before activation, the integrator freezes the exact manifest, SQL/code hashes, fixtures admitted for the initial bounded run, max capture batch and expiry. Runtime registry remains open to further explicitly admitted future fixtures while the lane is active, subject to a documented hard fixture cap and expiry. A lane that reaches its cap rejects additional registration visibly; never silently evict an earlier event. The SQL activation/registration/capture functions are `SECURITY DEFINER`, `SET search_path = ''`, fully qualify every object, use an explicit lock order, and are executable only by `service_role`. Private tables have RLS enabled and no direct grants to `PUBLIC`, `anon`, `authenticated`, or `service_role`; revoke default function execute grants and grant only the intended public RPC entry points to `service_role`.

Registration RPC contract:

```sql
public.register_rolling72_mvp_research_v1(p_admission_receipt_ids bigint[])
returns jsonb
```

It accepts 1–20 unique receipt IDs per call, processes in a stable sorted order, and returns one result per requested ID, including rejected identities with stable reason codes. It reads only the already committed `private.roboticket_admission_receipts_v2`, `public.ticket_events`, and required trusted club/source metadata. It never creates admission or edits an existing row. A registry row is insert-only and binds:

- admission receipt ID and its immutable receipt-row hash;
- `ticket_event_id`, club slug and Roboticket external event ID;
- provider/source domain, home/away/canonical identity, competition, match date and exact `kickoff_at`;
- admission `known_at` and pinned lane/version.

Accept only a unique v2 admission row whose evidence payload/hash fields satisfy the v2 contract, whose receipt is committed before registration's actual transaction snapshot, and whose ticket-event row agrees exactly with the admission identity and stored verified schedule metadata. Event must be still future at registration and within `issue_until`; historical, already kicked-off, ambiguous, unsupported-source or conflicting identities get a durable rejection/registration-attempt record and no registry row. Resolve same-event retries to the existing registry row only if every binding/hash matches exactly. A second admission receipt or conflicting identity for the same event fails closed; do not merge it. No caller may provide or override event metadata, identity, admission clock, lane, activation or expiry.

The existing Roboticket admission RPC locks fixture identities in lexical `club_slug:external_event_id` order. New functions that lock more than one event must use the same lexical ordering to avoid deadlock with that path. Never take locks on frozen lane keys.

## Runtime capture RPC and source binding

Capture RPC contract:

```sql
public.capture_rolling72_mvp_research_v1(p_limit integer default 25)
returns jsonb
```

`p_limit` is 1–25. Each call has an internally generated run ID and actual start/end times. It handles at most this many snapshot attempts in deterministic oldest-first order, returns explicit counts and per-snapshot stable status/reason, and isolates source-validation errors without aborting other work. It runs only while activated and before `scoring_until`. Do not accept user-provided snapshots, source payloads, rows, status, timestamps or hashes. Registration and creation of new source-horizon candidates stop at `issue_until`; after that, capture is limited to `LABEL_ONLY` reads for already registered fixtures, which can create immutable validated source seals but never issue candidates. The final six-hour-after-+72 scoring grace therefore continues to receive fresh source reads through `scoring_until`.

Process the oldest unconsumed source snapshots in deterministic `(captured_at, snapshot_id)` ascending order, with the batch limit applying to snapshot attempts, not fixtures. On every call, find snapshots for registered fixtures that are post-activation (`captured_at >= activated_at`) and do not yet have a successful receipt. Retryable incomplete reads remain eligible only within the one-hour rule below. An old/stale or otherwise permanently skipped snapshot gets an explicit immutable `SKIPPED_STALE`/reason attempt; keep processing later IDs in order within the same bounded batch. Do not select only the latest snapshot and imply that intervening observations were captured. At initial registration, do not bootstrap an old latest row as a new first point. The first qualifying source snapshot is captured by a subsequent runtime poll; its actual read clock is the earliest point of the lane's source knowledge. Each later committed snapshot is handled in order; recorded skips remain gaps. A poll with no new eligible snapshot writes an explicit `NO_NEW_SOURCE` collection-attempt result, not a fake receipt or issue.

Each source capture is a separate service RPC transaction from the transactions that wrote admission/snapshot data. The orchestrator must wait for the admission/source writer request to return successfully (and commit), then call registration/capture in a separate PostgREST RPC request/transaction. No batched SQL, shared explicit transaction, or caller write payload may combine source writes with registration/capture. In addition, the SQL functions/tests must reject admission or source tuple versions inserted by the current top-level transaction or one of its subtransactions; if the implementation cannot reliably distinguish those tuple versions, it must refuse the row rather than claim an independent committed-read boundary. A single MVCC SELECT proves only what was visible in that function's read snapshot; it does not establish the upstream transaction's original commit timestamp.

Validation must bind all of the following before a receipt can be `READY`:

1. Admission receipt remains byte/value identical to the registered row; ticket-event ID, provider, external ID, club, home/away/canonical keys, competition, civil match date and kickoff match the immutable registration. Preserve the repository's distinct ID namespaces: `public.snapshots.id` is the source snapshot ID; `snapshots.ticket_event_id` and `sector_price_area_observations_v1.ticket_event_id` are internal `public.ticket_events.id`; `snapshots.event_id` and (when populated) `public.sector_inventory.event_id` are the Roboticket external event ID. `sector_inventory.snapshot_id` binds its rows to the snapshot; it is not a substitute for the internal ticket-event FK. Validate each non-null field against the right registered key; do not compare external `event_id` to internal `ticket_event_id` or silently ignore a populated mismatch.
2. Source is exactly `roboticket`; unit is exactly `available_total_seats`; `captured_at` and all required source clocks are present and consistent. Snapshot capture must not be later than read completion or earlier than `read_completed_at - 3600 seconds`; kickoff metadata at capture agrees exactly with registration. A registered event whose kickoff has arrived yields explicit `OUTSIDE_KICKOFF` and receives no new opportunity/forecast.
3. `available_total` is a finite nonnegative integer, including true zero. Sector count and the required source children are present and reconcile exactly. Reject null/negative/fractional values, duplicate child identities, duplicate/unstable sector-source mappings, wrong parent/snapshot/capture, unscoped rows, ambiguous IDs, child-total mismatch, or snapshot-total mismatch. Missing/hidden is never zero. Retain explicit `INVALID_SOURCE`/reason and raw validated read payload only in the private attempt/seal tables.
4. Canonicalize child arrays using stable IDs before hashing. Persist two distinct digests. `source_content_sha256` covers stable admission/fixture identity and exact snapshot/child content with canonical child ordering, but excludes per-read start/completion/known clocks, attempt ID, validation outcome and any other retry-varying fields. It is the idempotency/mutation key. `attempt_binding_sha256` covers `source_content_sha256` plus the actual read clocks, attempt/run IDs, lane/version, validation outcome and reason; it is expected to differ on a later retry. Persist the raw private per-attempt JSON and both hashes so each can be reproduced. A later read with the same stable source content returns the original accepted receipt/seal and opportunity IDs, without changing their original clocks or creating another seal/opportunity, while appending a new attempt with its own binding hash. A different source-content hash for a snapshot that already has a `READY` seal is `SOURCE_ROW_MUTATED`; never update or reseal it. A different hash after only an incomplete/invalid attempt may be retried within the stated partial-read window, but the snapshot row itself must remain unchanged. Admission-binding changes always fail closed.

The whole source bundle is read in one statement/snapshot. Compute `source_content_sha256` from the stable selected content and registered identity. After full validation and this content-hash computation, take an actual database clock for `known_at`; require `known_at >= read_completed_at`, `known_at >= admission.known_at`, and `known_at >= captured_at`. Then compute `attempt_binding_sha256` over the content hash, `known_at`, attempt clocks/ID, lane/version and validation outcome. Do not use the attempt-binding digest for retry equality: real clock fields necessarily vary across reads. Do not infer `known_at` from a parent receipt's `known_at`, row `created_at`, source capture time or a client timestamp. If a concurrent source write committed after the statement snapshot, it is eligible only on a later capture call/transaction. The clock proves when this lane read/validated committed rows, not when the source provider or upstream writer originally committed them.

### Attempts, retries and immutable seals

Every poll of an eligible registered event appends a collection attempt with lane, fixture, attempt/run ID, start/complete/known clocks, selected snapshot ID if any, status and bounded reason code. Attempts are immutable. Missing source, no new snapshot, stale data, partial children, validation failure, and post-expiry are distinguishable. A missing/partial-child source read may be retried only while the same source is at most one hour old and before expiry; attempts remain intact. A successful receipt is unique per `(lane_id, ticket_event_id, snapshot_id)` and immutable. A retry with identical `source_content_sha256` but different read clocks appends only a new attempt and returns the original receipt ID/seal/opportunity IDs; it does not rewrite original clocks, make a second seal, or create another opportunity. A different content hash after a `READY` seal is a hard integrity conflict and cannot make a second accepted version of the same snapshot. A later genuine snapshot creates a new receipt. No delete/reseal/reset path is supplied.

On each first successful `READY` seal, compare only with the prior `READY` seal in strict `(captured_at,snapshot_id)` order in this new lane. The first point is persisted with `prior_status = NO_PRIOR`, null deltas/rates, zero prior/gap counts and no fabricated history. For later points, persist IDs/hashes/clocks of current and prior seals, elapsed capture time (zero on a capture-time tie), total delta, sector/price-area membership changes, added/removed availability and continuity status. Exact arithmetic invariant: `total_delta = common_sector_delta + added_available - removed_available`. Same-count membership changes are detected using stable sector source IDs, not sector count alone. Retain intervening failed/unsealed source opportunities as explicit gaps; if any exist, mark transition `GAPPED` and do not claim continuous change. Unchanged endpoints never prove unobserved continuity. The first increment need not compute slopes/features; it must preserve the data and exact clock/identity provenance needed for a later PIT-safe feature slice.

## Opportunity denominator and handoff to forecast slice

Do not use predictions as their own denominator. For each new `READY` source receipt whose actual post-validation `known_at` is strictly before `issue_until`, insert exactly one immutable **source-horizon candidate** row per `horizon_hours ∈ {24,48,72}`. It binds `receipt.known_at` as the observation/opportunity clock, `captured_at` as the external measurement clock, the horizon, and `provisional_target_at = known_at + h`. This provisional coordinate records what horizon was available from that source vintage; it is not a forecast target or `issued_at`. Mark its source-time eligibility according to whether the provisional target is strictly before registered kickoff, but do not call this measure forecast coverage. The source candidate table is unique on `(lane_id, receipt_id, horizon_hours)` and immutable; identical read retry returns the same IDs. A `READY` receipt with `known_at >= issue_until` is marked `LABEL_ONLY` and creates no source-horizon candidate; it can only provide a later genuine source state to the P0-4c label matcher.

Separately record every registered-fixture poll/check attempt, including `NO_NEW_SOURCE`, stale, invalid and post-kickoff; this is the source collection-operation denominator. The source-horizon candidate count is a source-backed candidate denominator, not a forecast-coverage denominator. Missing polling windows not actually attempted remain unknown unless a scheduler ledger proves them. Report separately: registered fixture count, collection calls/attempt outcomes, valid source receipt count, first-point count, all source-horizon candidates, source-time pre-kickoff candidates, outside-kickoff candidates, and later actual forecast issued/available counts. Zero denominators produce `null`, not 100%.

P0-4c (separate implementation ticket if not included) consumes each source-horizon candidate once and issues simple persistence `available_total` for +24/+48/+72 at first receipt and every later receipt. It must set `issued_at` from an actual database clock after it reads the committed source receipt and completes forecast computation; it must never backdate `issued_at` to `receipt.known_at` if the issue transaction happens later. `target_at = actual issued_at + horizon`. Store immutable actual issue rows linked to the source-horizon candidate, with actual status and reason. The forecast opportunity denominator is the immutable set of source-time eligible candidates (`provisional_target_at < kickoff_at`), including any later refusal/unattempted candidate so missed issuance cannot disappear. Numerator is only an actual numeric forecast whose `issued_at+h < kickoff_at`; delayed issue that crosses kickoff is `OUTSIDE_KICKOFF` and contributes no numeric forecast. For each metric, label it source-backed issuance coverage and report denominator, actual issue attempts, refusals, unattempted candidates, outside-kickoff attempts and numeric forecasts separately; do not imply complete product/source polling coverage. P0-4c also implements labels/scoring against later genuine receipts with `captured_at > actual issued_at`, `captured_at <= actual target_at`, `known_at <= scoring time`, maximum six-hour target age, strict pre-kickoff policy, and scope/identity comparability rules. A true zero label is numeric zero; missing/stale/invalid/changed scope remains a distinct status. P0-4b alone creates no forecast and no score; its report must state this plainly.

## Expiry, scheduling and safety

Every lane has immutable activation, `issue_until`, and explicit `scoring_until` pinned before activation; require `scoring_until >= issue_until + 72 hours + 6 hours` so the last allowed +72 issue can reach target and its six-hour label grace. Exact cutoffs are in UTC and are not extended in place; any successor is a new lane/version. Registration and new source-horizon candidates stop after `issue_until`. Capture continues in `LABEL_ONLY` mode for already registered fixtures through `scoring_until`, solely to preserve actual later source reads needed by due labels; no forecast or new opportunity is created in this phase. The integrator may add a new bounded five-minute scheduler only after migration review and explicit activation, only for this new RPC, and it must automatically unschedule at `scoring_until`. No old cron/job definition or capture trigger is changed. Each run respects the RPC's batch ceiling. A missed poll is a recorded gap only if the scheduler/run ledger proves the missed opportunity; it is never backfilled by selecting an old snapshot as though newly known.

The only writer entrypoints are service-only RPCs. Tables remain private/RLS enabled; no direct service-role table grants, browser key, caller payload, or public read RPC is added in this slice. Status output is bounded and sanitized: IDs, clocks, counts and stable enums/reasons only, no source body, secret, or personal data. Runtime failures append bounded attempts where possible and fail closed; one invalid fixture cannot corrupt another fixture's state.

## Required local PostgreSQL 16 acceptance

Run only in a dedicated isolated disposable test database, never a hosted or frozen lane. Tests must prove:

1. Migration applies cleanly, re-applies safely if the repository migration convention requires it, all new functions parse, and all frozen function/table/job definitions under the protected boundary remain unchanged.
2. Direct SELECT/INSERT/UPDATE/DELETE on private tables is denied to `PUBLIC`, `anon`, `authenticated`, and `service_role`; only intended RPC execute is granted to `service_role`; anonymous/authenticated calls fail.
3. Registration accepts a true existing v2 forward-only admission and exact event binding; same exact retry is idempotent. Reject duplicate requested IDs, duplicate/conflicting admission, mismatched receipt hashes/fields, wrong provider/source/canonical metadata, already-kicked-off admission, expired lane, unsupported source, cap overflow and caller attempts to substitute metadata.
4. Capture sees a snapshot/child bundle only when committed before the MVCC read. A transaction that has not committed is not observable. Explicitly insert admission/source rows and invoke registration/capture within the same top-level transaction, including via a savepoint/subtransaction; these rows must be rejected as self-written. Commit them, then call the RPC in a separate transaction and prove acceptance. Assert `read_started_at <= read_completed_at <= known_at`, `captured_at <= known_at`, admission-known-before-read, `known_at` is after complete validation, and parent `created_at`/future clock cannot change knowledge. Assert the source snapshot ID/internal ticket-event FK/external Roboticket ID mappings separately, including non-null inventory `event_id` binding.
5. Complete valid source rows produce one hash-verifiable `READY` seal and three horizon opportunities where pre-kickoff; real zero remains a READY zero. Missing/hidden/partial/null/negative/fractional/duplicate/unscoped/mismatched rows and wrong unit/source fail with explicit status and no eligible opportunity. Sector child/header/inventory totals and stable IDs reconcile exactly.
6. First valid receipt is `NO_PRIOR` with null deltas; a second valid receipt links the true prior by capture/knowledge order, detects same-count sector membership swap and satisfies the exact delta decomposition. Intervening failed receipt attempts mark the transition GAPPED. No old lane rows are read or written.
7. Identical source content read again under different real clocks has identical `source_content_sha256`, different `attempt_binding_sha256`, appends a new attempt, and returns the original receipt/seal/opportunity IDs with clocks unchanged. Mutation after READY fails; incomplete-child retry is allowed only under the bounded partial-read rule. UPDATE/DELETE against every new immutable ledger is rejected. Concurrent duplicate capture/register retries serialize safely; multi-event locking matches admission lexical order.
8. Poll attempts distinguish no-new, missing, stale, invalid, post-kickoff, issue-window, label-only and expiry. Source-horizon candidate counts, source-time eligible count, outside-kickoff count, zero denominator/null reports and separate collection-poll denominator are exact. P0-4b does not publish forecast coverage. In P0-4c tests, issue clocks are actual and not backdated; actual target uses `issued_at+h`; delayed/refused/unattempted candidate remains visible; a target crossing kickoff is outside kickoff and does not enter numeric forecast numerator. Label-only seals may be considered only by the exact later-receipt label matcher and never create issues. No caller supplies source, issue/target/known clocks or forges opportunities.
9. A batch with one malformed fixture and one valid fixture records the first failure but commits the second result without cross-fixture contamination. Expiry forbids registration/new candidates after `issue_until` and all capture after `scoring_until`; an already registered fixture can produce only label-only seals in the intervening score window. Manifest validation rejects `scoring_until < issue_until + 78 hours`.

Offline contract tests (if introduced) must exercise exact JSON field names, numeric-vs-boolean identity/count parsing, canonical row ordering/hash parity, first-point nulls, clock inequalities, duplicate/unknown payload fields and opportunities. They do not substitute for the PostgreSQL MVCC, permission or trigger tests.

## Release and completion claims

Implementation is locally complete only when the isolated PG16 tests and an independent SQL security/clock review pass and the new migration/function/code hashes are frozen. Hosted deployment, activation, registration, cron setup and actual runtime evidence are separate integration actions, each requiring explicit review and proof. Until those exist, status is `PREPARED/NOT_ACTIVATED`, never “collecting” or “live”.

P0-4b proves a real private forward-only source registry and committed-read seal path with honest collection/opportunity denominators. It does not prove forecast coverage, E5 quality, attendance accuracy, 30 independent fixtures/8 clubs, continuous polling, cause of sector changes, or revenue impact. P0-4c is required for actual persistence forecasts and due scoring. New independent MAE review still requires 30 new independent events across 8 clubs, future-only truth and a separate precommit. Production adjustment remains off.

## Integrator review23XI
Reviewed actual admission/source contracts and corrected stable-content retry
hashes versus per-read clock bindings, actual delayed issue clocks, source
internal/external ID roles, oldest-first bounded processing, same-transaction
visibility, and continued label-only capture through the +72 grace deadline.
Deadline decisions use actual post-validation clocks, including a call crossing
issue_until; caller timestamps cannot keep the issuance window open.
This is an implementation-ready specification, not a completed source lane.
Next writer owns only new rolling72_mvp_research_v1.sql; independent PG16 tests
use a dedicated new disposable DB. No hosted action while runtime is unhealthy.

## Concrete source-schema binding during implementation
The actual snapshots schema has no unit column. Unit is pinned as
available_total_seats by the manifest and the Roboticket table adapter's integer
available_total/available semantics, not claimed to be read from a nonexistent
source field. If a future snapshot includes an explicit unit, it must agree.
The adapter remains inventory-only and never asserts paid sales/attendance.
Capture caches whether any committed source exists and intermediate unsealed
source IDs in its single source-bundle SELECT. No data vs no eligible new source
are separate statuses. Transition knowledge gets its own actual computation
clock; receipt known_at remains the post-validation source knowledge clock.

Two genuine rows sharing captured_at are ordered deterministically by snapshot ID
and retain distinct actual knowledge clocks. A larger ID at the same capture
time may produce a READY seal with elapsed_capture_seconds=0, explicit
TIED_CAPTURE_TIME / UNAVAILABLE_ZERO_ELAPSED markers and no velocity. Snapshot
ID ordering does not prove physical measurement order. This preserves first-point
and later-row coverage without dividing by zero or inventing source timestamps.
Prior selection/gap intervals use the same total key; backwards keys fail closed.
This clarification affects only the new, not-yet-activated lane.

Whole-cycle guard: activation accepts an explicit finite issue cutoff without an
arbitrary 30-day upper bound. A first real observation at P-50 is eligible;
registration/capture do not require P-15 or the final72hours. Operator activation
still pins a concrete bounded lifetime and cannot extend it in place.

## Actual implementation result
SQL SHA911dc9a55159b8ec2e3acaf0bc41fb7d5380f860e6aec44bdc637ae1042a7270;
18PG16tests/integratorrerun/independentreviewPASS. DraftPR229 exacthead3852489,
CI45224037575SUCCESS. Newsourcehasnotbeenhosted/activated, no forecastscreated.
See ml/ROLLING_72H_MVP_SOURCE_RUNTIME_RESULT_2026-11-23.md andproofJSON.
Keepactiveuntilhostedfirstgenuinesourceacceptance. AdmissionofJagiellonia5520
blockedbyautomaticapprovalreview; explicituserapprovalneeded, no bypass/retry.
