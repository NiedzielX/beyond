# Rolling72 P0-4c — first-point persistence issuance and due scoring

Date: 2026-11-23  
Status: READY FOR IMPLEMENTATION — root-reviewed clock/denominator/label contract; no code or activation  
Owner: SQL implementation and isolated PostgreSQL 16 tests assigned after P0-4b closes  
Parent: [MAE and investor MVP development](2026-11-22-rolling72-mae-and-investor-mvp-development.md), P0-4  
Source contract: [P0-4b runtime source lane](2026-11-23-rolling72-mvp-runtime-source-lane.md)  
Canonical strategy: [MAE Research Roadmap v6](../../ml/MAE_RESEARCH_ROADMAP_V6.md); operational state: [current execution plan](../../ml/EXECUTION_PLAN_CURRENT.md)

## Purpose and precommit provenance

P0-4c is the final persistence-and-scoring slice of the already planned P0-4 work. The 22-November parent plan specified a new independent PERS-only lane before the 23-November E5 outcomes: its first genuine receipt issues +24/+48/+72 persistence forecasts; each later receipt creates a new vintage; only later genuine observations score those issues. This spec makes that existing contract executable. The exposed E5 +24 results do not choose or alter the method, horizons, eligibility, score rule, or policy here. No fit, recipe search, refit, or production promotion is part of this task.

P0-4b supplies the forward-only admissions, source registry, committed-read seals, and immutable candidate denominator. P0-4c consumes those objects in its own lane and adds actual issue records, due labels, and scores. It does not change P0-4b or any frozen E5/B/v5/v3a/five-event object. All outputs concern public available inventory only; they are not sold tickets, demand, attendance, revenue, or causal price/promotion/ad effects. The approximately 1200-seat attendance-MAE goal and the fresh 30-event/8-club MAE review remain separate.

## Fixed method and lifecycle

- Lane/method: `rolling72-mvp-persistence-v1` / `PERS`; SQL/table prefix `rolling72_mvp_persistence_v1`. These exact names are pinned before implementation.
- Input: the exact `available_total` of one validated P0-4b seal, in the registered `available_total_seats` unit and bound to the same registered event/source identity.
- Fixed horizons: 24, 48, and 72 hours. No horizon selection, model fitting, feature engineering, or learned adjustment.
- For an eligible source receipt, create one immutable issue bundle containing exactly one row for each horizon. All three use the same actual `issued_at`; each `target_at = issued_at + horizon_hours`.
- For a target strictly before kickoff, the numeric forecast is the input `available_total`, including a true numeric zero. A target at or after kickoff is `OUTSIDE_KICKOFF`, with `prediction = null`. No issue row is omitted for an outside target.
- The first accepted post-activation source seal is a valid first forecast point. Do not require prior history, manufacture a slope, or drop the one-observation case.
- Issue `available_total` is the public inventory proxy. Store scope/membership/gap flags from the source seal and transition; a count or value change is not interpreted as sales, attendance, or causal effect.

### P0-4c activation boundary

Use a new immutable, singleton P0-4c lane/config row. It binds the exact P0-4b lane/version and reviewed source SQL identity, method, horizons, source-age limit, issue/scoring cutoffs, and P0-4c SQL hash. Activation time is database-generated only after validation and lock acquisition; no caller-supplied timestamp is accepted. Activation is idempotent only for the byte/value-identical manifest and otherwise fails closed.

For P0-4c issuance, eligible source seals must have `known_at >= p0_4c.activated_at`, be valid committed P0-4b receipts, and have their actual post-validation knowledge clock during the active issue window. Their measurement capture may precede model activation if their first genuine completed-read seal is after activation and remains fresh; no earlier issue is reconstructed. P0-4b candidates created before P0-4c activation remain visible as `PRE_ACTIVATION_EXCLUDED`; they are neither backfilled nor silently mixed into the active issue denominator. Candidates belonging to seals at or after P0-4c activation define the in-scope source-backed candidate population. Primary forecast coverage uses its SOURCE_ELIGIBLE candidates as denominator, including their later refusals and unattempted rows. Source-time OUTSIDE_KICKOFF candidates are retained in separate counts and never inflate numeric coverage. The P0-4c activation never admits historical snapshots or writes to a frozen lane.

Issue execution is permitted only while actual database time is `< issue_until`. The configured scoring cutoff must satisfy `scoring_until >= issue_until + 78 hours`; source capture continues after `issue_until` in P0-4b `LABEL_ONLY` mode through that scoring cutoff. No issuance occurs during the label-only grace period. An expired or absent activation yields an explicit refusal/status and no issue.

## SQL objects and service RPC contract

Implement one additive migration in `supabase/sql/rolling72_mvp_persistence_v1.sql` and an isolated contract suite in `tests/postgres/test_rolling72_mvp_persistence_v1.py`. P0-4b objects are read-only inputs. The migration may create only new P0-4c objects and functions; no edits to frozen SQL, old ledgers, source admissions, triggers, existing functions, or jobs.

Use a small set of append-only private tables, with exact names finalized once by the implementation:

1. `private.rolling72_mvp_persistence_v1_lane`: immutable manifest, source-lane binding, actual activation, issue/scoring cutoffs and policy hashes.
2. `private.rolling72_mvp_persistence_v1_issue_bundles`: one row per source seal successfully evaluated for issuance; unique source seal; actual issue/read clocks, source age, source digest and event identity.
3. `private.rolling72_mvp_persistence_v1_predictions`: exactly three rows per bundle (horizon 24/48/72), unique `(bundle_id,horizon_hours)`, candidate ID, actual target, status, nullable numeric PERS value, and source/scope provenance.
4. `private.rolling72_mvp_persistence_v1_issue_attempts`: one immutable terminal attempt per P0-4b candidate; status/reason, attempt clock, and optional bundle/prediction references. Enforce unique `candidate_id`. The candidate table itself remains the source-backed denominator; an absent attempt at a declared cutoff is reported as unattempted, not deleted or counted as a forecast.
5. `private.rolling72_mvp_persistence_v1_labels`: at most one accepted label per numeric prediction, unique prediction ID; source seal, actual total, source clocks, score clock/age, source identity/unit, and scope-transition flags.
6. `private.rolling72_mvp_persistence_v1_scores`: immutable PERS absolute/signed error per accepted label, or compute these as a stable read-only projection if that avoids duplicate stored facts. Do not create two independently mutable sources of score truth.
7. Append-only bounded run/attempt records sufficient to distinguish no work, refusals, retries, and operational errors without storing a second copy of raw source payloads.

Provide service-only RPCs, all `SECURITY DEFINER`, `SET search_path = ''`, fully qualified, bounded and deterministic:

```sql
public.activate_rolling72_mvp_persistence_v1(p_manifest_text text,p_manifest_sha256 text) returns jsonb
public.issue_rolling72_mvp_persistence_v1(p_limit integer default 25) returns jsonb
public.score_rolling72_mvp_persistence_v1(p_limit integer default 100) returns jsonb
public.get_rolling72_mvp_persistence_v1_status() returns jsonb
```

The manifest is validated against an exact allowlist and pinned constants. Caller parameters cannot set event metadata, input values, source/issue/target/label clocks, source age, eligibility, method, horizon, score, status, or raw payload. `p_limit` is bounded (issue: 1–25 source bundles; score: 1–100 target rows). Stable ordering and explicit row/advisory locks prevent overlapping invocations from duplicating work. Unique constraints remain the final idempotency guard. Same-manifest activation and retry of completed work return existing IDs/status; conflicting identity, manifest, digest, or content is a durable refusal or hard error, never a replacement.

The issue RPC reads the candidate, seal, registry and pinned lane in one consistent statement/snapshot, verifies all identities/hashes and source eligibility, and finishes calculating the PERS value. It then obtains a fresh actual `clock_timestamp()` for issuance and derives all three target coordinates from that clock. Target timestamp addition necessarily follows stamping the issue; no predicted value may use later information. It requires source `known_at <= issued_at` and `issued_at - captured_at <= 3600 seconds`. The source age limit is checked at actual issue time, not at source capture or candidate creation. The actual issue clock must follow the committed receipt read and completed calculation. It is never backdated to `known_at`, `captured_at`, candidate time, or a client timestamp.

For every consumed candidate, persist exactly one attempt result:

- `ISSUED`: bundle and the corresponding horizon prediction were committed. An outside-kickoff prediction row remains linked and has a null value.
- `REFUSED`: stable reason such as stale-at-issue, source identity/digest mismatch, invalid/uncommitted seal, not source eligible, target outside kickoff, or issue-window closed. A validation refusal for one candidate must not hide it from the denominator or cancel unrelated valid candidates.
- Transient transaction/runtime failure: commit no terminal refusal or partial bundle; leave the affected candidate unattempted and retryable. Do not represent an uncommitted attempt as an outcome.

A candidate whose P0-4b source-time status is `OUTSIDE_KICKOFF` is still consumed and represented in the shared three-horizon bundle when its source receipt is otherwise valid. Only that candidate's horizon is necessarily `OUTSIDE_KICKOFF`/null; the other horizons are evaluated independently from their own actual targets. One outside +72 candidate does not invalidate an otherwise eligible +24 candidate. For a `SOURCE_ELIGIBLE` candidate, delayed issuance can make one or more actual targets cross kickoff; compute each actual target from the shared issue clock and mark that horizon outside/null. Numeric forecast count includes only actual non-null pre-kickoff predictions. Candidate counts, refusals, unattempted candidates, outside rows, and numeric issues are always separately reported. Do not call this complete product polling or coverage.

## Label matcher and scorer

The score RPC reads only due numeric predictions from this new lane and later committed P0-4b seals. It uses an actual database score clock generated after reading the prediction and eligible source rows; no caller may provide a label, source receipt, score timestamp or outcome. For prediction (p), accept a label only from a genuine P0-4b seal satisfying all of:

- same registered `ticket_event_id`, P0-4b lane, source family (`roboticket/roboticket`), and unit (`available_total_seats`), with exact registry and source receipt bindings;
- source capture is strictly after actual `issued_at` and no later than actual `target_at`;
- source `known_at` is no later than the actual score clock;
- source capture age at the target is `target_at - captured_at <= 6 hours`;
- target is strictly before the registered kickoff;
- seal is valid, committed, and not mutated or ambiguous.

If multiple seals qualify, select the latest by strict `(captured_at, snapshot_id)` order. Select the latest eligible observation before applying identity/integrity checks; if that latest observation fails a required binding, record the failure and do not backtrack to an older value. A true zero is a valid numeric label. Missing, stale, invalid, uncommitted, wrong-event/source/unit, post-target, pre-issue, unknown-at-score, or after-kickoff observations are distinct non-label statuses. No label is fabricated from the origin value, a stale latest row, a future row, or an old/frozen ledger.

Persist the first accepted label per prediction exactly once. A later source correction, later receipt, retry, or repeat score call cannot replace it. Keep the actual source/scope flags with the label: current and prior seal IDs, `NO_PRIOR`/`COMPLETE`/`GAPPED`, sector-count delta, membership-change counts and relevant scope-unknown/change indicators. A sector membership/count change does not change the declared target: this scorer measures total available inventory in the same registered unit, not sales, sold seats, attendance, or a causal effect. A source/event/unit identity mismatch still blocks scoring.

Persist per-label signed error `prediction - actual_available_total` and absolute error. Per horizon, report event-balanced MAE and bias by averaging within each event first, then equally across events. With no accepted labels, label count is zero and MAE/bias are JSON `null`, never zero. Do not mix horizons or availability metrics with the separate attendance lane. Preserve pending/future, due-unscored, refusal, stale/missing/invalid, outside-kickoff and scored states in the bounded status response. A status cutoff must say when unattempted candidates or due predictions are considered outstanding; elapsed time alone does not turn an unknown scheduler window into a proven missed attempt.

## Immutability, grants and isolation

All P0-4c state is insert-only. Add mutation-rejecting triggers or equivalent database constraints/triggers for updates/deletes, including terminal refusals, bundles, predictions, labels and scores. A transaction may insert a bundle plus its three prediction rows and attempts atomically; it may not expose a partial committed triplet. Protect against same-seal/same-candidate concurrency with the stable lock order and unique constraints. Never reuse IDs or reset a lane.

Enable RLS on all new private tables. Revoke table and sequence access from `PUBLIC`, `anon`, `authenticated`, and `service_role`; service code reaches them only through the four intended RPCs. Revoke default function execution and grant the four RPCs only to `service_role`. Do not create public views that expose private payloads, grant service-role direct table access, use end-user supplied bearer values inside SQL, or call any other lane's write function. Do not create, edit or activate a cron job in this spec/implementation slice; an orchestrator may call bounded RPCs only after separate integration review. Keep `live_adjustment = 0`.

## Independent PostgreSQL 16 acceptance suite

Run against a dedicated isolated PG16 database, not hosted production. Compose the already-reviewed P0-4b migration as a test dependency if needed. Fixtures must be synthetic and explicitly test-only; they test clocks/constraints and do not claim to recreate hosted history. Do not modify either P0-4b SQL/tests from this task.

Acceptance tests must prove:

1. **Access/isolation:** no direct reads/writes to private tables or sequences for anon/authenticated/service role; only intended RPC execution for service role. P0-4b and frozen old-lane function/table hashes and counts are unchanged by applying the additive migration. No new P0-4c object reads or writes old ledgers.
2. **Activation:** exact manifest/hash/constant validation; no caller clocks; one activation; identical retry is idempotent; conflicting retry or unknown/missing key fails closed; issue/scoring cutoffs and `scoring_until >= issue_until + 78h` enforced.
3. **Fresh post-activation source:** a genuinely committed synthetic source seal after P0-4c activation is required. Pre-activation source/candidate is marked excluded and cannot issue. No bootstrap/history or direct caller payload can create an issue.
4. **First point and fixed triplet:** the first eligible source seal issues PERS with no prior receipt. One actual shared issue clock for exactly 24/48/72 rows; each target is actual `issued_at + h`; all numeric values equal the seal's `available_total`; zero remains numeric zero. Assert `issued_at >=` source `known_at`, committed-read completion and calculation completion and is strictly later than the source-read boundary. A delayed issue never rewrites/backdates the original source receipt.
5. **Freshness and cutoff:** receipt age exactly 3600 seconds is accepted if all other constraints hold; greater than 3600 seconds is refused and remains in the denominator. Issue calls after the strict `issue_until` boundary create no issue. A horizon whose actual target equals or exceeds kickoff is stored as `OUTSIDE_KICKOFF`/null; no outside value is counted numeric.
6. **Denominator and retry/concurrency:** every in-scope P0-4b candidate has exactly one terminal attempt or remains visibly unattempted; refused and outside candidates remain counted. Repeated RPC and concurrent calls cannot create duplicate attempts, bundles, horizons, forecasts, labels or scores. An injected transaction failure leaves no partial bundle or terminal refusal. Failure on one fixture/candidate does not erase successful work for others.
7. **Due label timing:** only a new committed post-issue seal with `captured_at > issued_at`, `captured_at <= target_at`, `known_at <= score_clock`, target age no more than six hours, valid event/source/unit binding and pre-kickoff target can score. Test exact timing boundaries; reject a pre-issue receipt, capture after target, >6h target age, post-kickoff target, uncommitted/current-transaction tuple, invalid/mutated digest, wrong fixture, wrong source family, wrong unit, or receipt known after score clock.
8. **Scope and immutability:** labels preserve real source and scope-transition flags, including changed sector count/membership; total-inventory target remains the numeric `available_total` when event/source/unit identity is valid. First accepted label wins; later valid or corrected receipts cannot change the label/score. A genuine zero label is scored as zero.
9. **Scoring semantics:** only PERS availability predictions appear; per-event averaging then equal event weighting is verified with unequal event row counts. Zero label count returns null MAE/bias, not zero. +24/+48/+72 remain separate; pending, due-unscored, refusal, outside and invalid-source states remain explicit.
10. **Label-only grace:** a post-`issue_until` P0-4b `LABEL_ONLY` seal can satisfy a due target label and can never create a new candidate or forecast. Capture/scoring are allowed only through the pinned `scoring_until`; after expiry no new score or label is accepted.

The implementation is ready for local approval only when the isolated suite passes and SQL review confirms the migration is additive, bounded, immutable, and service-only. Real hosted activation, scheduler wiring, UI integration and any public/MAE claim are separate decisions and evidence. A one- or two-match pilot proves plumbing only; the formal prospective MAE review still needs 30 new independent events across 8 clubs, future-only genuine labels, exact cohort accounting, and separate attendance evidence. No result in this increment claims the 1200-seat attendance goal or authorizes `live_adjustment`.

## Root review notes before implementation
The candidate is per horizon; a bundle has three independently classified
rows. Primary coverage denominator includes source-time eligible candidates,
with outside/preactivation counts reported separately. Issue clocks follow value
computation; targets are derived from that actual clock. Bias convention is
prediction minus actual, matching the existing scorecard/diagnosis.

Before scorer implementation, resolve latest-source refusal explicitly: selection
must inspect the newest in-scope observed source candidate/attempt, not silently
backtrack to an older READY seal when a later invalid/unsealed observation exists.
Unknown capture time on an execution failure must be reported as unknown; it
cannot justify selecting a convenient older label. Valid sealed source evidence
is checked against its immutable payload/hash, not rewritten to the current
mutable upstream snapshot. First accepted labels stay immutable.

The manifest will use exact bytes+SHA, matching P0-4b, with immutable source
manifest/SQL binding and fixed method/horizons/age policy. No deployment or
first issuance before this remaining label-selection contract is finalized.

### Latest-source label selection (root contract)
At a scoring read watermark, inspect this new source lane's actual attempts,
not only READY seals. For each snapshot, take the latest attempt known by that
watermark. Among observed captures strictly after issue and at/before target,
choose the greatest (captured_at,snapshot_id) before validating the outcome.
READY or identical NO_NEW_SOURCE may resolve to the unique immutable seal;
INVALID_SOURCE, skipped/stale, or a missing seal yields an explicit non-label
status. Do not backtrack to an older seal. Require the attempt content hash to
agree with the seal and recompute its immutable stored payload hash.
An execution failure with unknown capture time that is unresolved after the
latest trustworthy in-scope source knowledge makes source ordering UNKNOWN;
record that refusal rather than guessing an earlier label. A later accepted
label is never replaced by another attempt or upstream correction.
This rule applies uniformly before any outcomes from the new lane are observed.
