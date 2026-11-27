# Rolling72 December runtime options

**Read-only design, 27 November 2026.** No hosted calls or lane changes made.

## Recommendation

Create a separately named, finite source lane and paired PERS–DRIFT24 lane by cloning the reviewed v1 SQL contracts into new versioned files, then make explicit, reviewed identifier substitutions. Keep the active Nov/Dec lane and its immutable manifests untouched. This is lower risk than widening its cutoff: source activation and paired activation each freeze a single manifest, and the paired activation requires exact agreement with its source manifest, source SQL hash, and cutoffs.

The current code is **not parameterized for a second lane**. It hardcodes lane IDs, source-table references, table/function names, advisory-lock keys, ACLs, manifest checks and cron job names throughout both SQL files. There is no SQL/runtime generator. A generic string-replacement generator would add a new correctness-critical layer and is not the short-cut to use before the cutoff. Keep the clone mechanical and make the diff auditable.

Suggested IDs: `rolling72-mvp-research-dec2026-v1` and `rolling72-mvp-paired-drift24-dec2026-v1`. Freeze a finite December window with issue cutoff **2026-12-31 00:00 UTC** (31 Dec 01:00 Warsaw) and scoring cutoff **2027-01-03 06:00 UTC** (3 Jan 07:00 Warsaw), preserving the required 78-hour scoring grace. This captures late-December origins and permits +72 labels. Existing window remains `2026-12-01 00:00 UTC` / `2026-12-04 06:00 UTC`; do not repoint its cron or manifests.

## Concrete clone surface

- Source: copy `supabase/sql/rolling72_mvp_research_v1.sql` to a new versioned SQL file and give every private table, public RPC, trigger/helper, lane/version literal, lock namespace and grant/revoke a unique December identity. Keep forward-only admission v2 read-only; the new registration RPC may read its committed receipts, but its source snapshots, seals, opportunities and clocks must be new and post-activation.
- Paired: copy `supabase/sql/rolling72_mvp_paired_drift24_v1.sql`; rebind every source-table and source-lane reference to the December source objects, and use new private paired ledgers/RPCs/locks. Preserve the fixed PERS/DRIFT24 formula, shared-label selection, clocks, fallbacks, eligibility, and evaluator unchanged. Do not copy or import earlier seals, forecasts, labels, or outcomes.
- Add two new exact manifests with new SQL hashes and linked source manifest/hash; choose a finite fixture cap (100 is within existing contracts) and the fixed paired criteria. Add separate source and paired cron templates with unique job names, manifest/hash/deadline guards, and automatic expiry. Add isolated PG16 contract tests and workflow paths for both clones, exercising cross-lane isolation and the existing clock/label/ACL guarantees.
- Review a full identifier/reference inventory and diff; test fresh installs plus idempotent cron install, manifest mismatch, expiry cleanup and preservation of existing jobs. Release order: reviewed source SQL + tests, source migration/activation, source cron; then paired SQL + tests, paired activation, paired cron. Record actual activation and first successful issue/capture as separate evidence. No activation or hosted result is implied by this design.

## Feasibility against 2 December

There are **three weekdays including 27 November** before the 2 Dec cutoff (Fri 27, Mon 30, Tue 1; cutoff Wed 2). A local implementation and review is possible only as a tightly scoped clone with immediate ownership, no protocol changes, and fast independent review; it is not a safe promise from the present code alone. The duplicated SQL is substantial (source and paired functions plus separate PG16 suites), and both clones need hash-bound release artifacts and cron guards. Dec 2 hosted activation is **not established as feasible**: prior activation work recorded an approval-infrastructure initialization failure, and this task made no hosted calls. Treat the lane as not live until fresh, authorized deployment evidence exists.

The current verified new opportunities are two 5 Dec Roboticket fixtures, both from the same round; they cannot establish the formal 30-event/eight-club floor. The December window creates collection runway but does not guarantee the floor. Before admission, build a club-by-club schedule inventory across December rounds, verify canonical identities and direct public inventory, then retain refusals and late starts in the declared opportunity ledger. Late Dec 31 fixtures can still produce +72 labels by the proposed Jan 3 cutoff only if issuance occurs sufficiently early; actual labels remain subject to fresh source captures and the six-hour age rule. If the cloned lane cannot be reviewed/activated by Dec 2, do not extend the current lane or count its exposed origins as the new cohort; move the finite window and all cutoffs forward in a newly frozen manifest.

## Implementation checkpoint

The renderer verifies input SQL and manifest SHA-256s, replaces only the
reviewed lane/SQL/index identifiers, and binds a supplied decision window
with at least 78 hours of scoring grace. The December-only deadline above
is a pilot option, not the full 30-event/eight-club acceptance cohort.
Future continuation and any permitted pooling must be predeclared
before using outcomes. No window was frozen on Supabase.

The isolated PostgreSQL 16 integration installs old and new lanes side
by side, activates the rendered manifests, registers a committed test
receipt, captures a zero-inventory observation and issues both methods
at all three horizons. The old registry and predictions stay empty and
old function definitions remain unchanged. The test is synthetic. Hosted
DDL, reviewed launch schedules, admission and live issuance remain pending.
