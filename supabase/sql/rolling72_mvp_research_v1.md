# Rolling72 source runtime v1

This is a separate, initially inactive source lane. It registers fixtures already
admitted through Roboticket admission v2 and records committed inventory reads,
first-point seals, scope transitions, and source-horizon candidates. It creates
no forecasts, scores, cron jobs or production adjustments.

The source target is public availability in seats. It does not establish paid
sales, attendance, or an intervention's revenue effect.

## Boundaries

- Private append-only registry, run/attempt, seal and candidate tables have RLS
  and no direct client/service-role grants. Only the public service-role RPCs
  perform writes. UPDATE, DELETE and TRUNCATE are rejected by ledger triggers.
- Registration reads the existing immutable admission receipt and verified event
  identity. It cannot create admission, supply metadata, or transfer evidence
  from another forecasting lane.
- A capture reads one complete source bundle with actual start/completion clocks.
  Tuple transaction status and the RPC's entry snapshot exclude uncommitted,
  self-written and later-committing source versions. This proves read visibility,
  not the upstream provider's original commit time.
- The source-content digest excludes read clocks; each attempt separately binds
  its actual clocks. An identical retry preserves original seal/candidate IDs.
  Changed accepted source rows cannot rewrite an earlier seal.
- Capture is bounded to 25 snapshot attempts, oldest first. Missing, stale,
  invalid, no-new and refused states stay explicit. A real observed zero remains
  numeric zero. Scope membership and intervening unsealed snapshots are retained.
- A first point needs no prior history. Equal capture timestamps retain distinct
  source IDs and real knowledge clocks; elapsed time zero never creates a rate.
- Candidate coordinates are provisional source-known-at +24/48/72h. They are
  not issued forecasts. A later forecasting implementation must use its actual
  issue clock and preserve refusals/unattempted candidates in coverage counts.
- New candidates stop at the frozen issue deadline. Label-only source capture
  continues through the scoring deadline, at least 78 hours later.

## RPCs and activation

activate_rolling72_mvp_research_v1(text,text) accepts the exact manifest bytes
and their SHA-256. It sets the activation clock itself and pins these ten keys:
lane_id, version, source_family, unit, max_source_age_seconds,
max_batch, max_fixtures, issue_until, scoring_until, sql_sha256.
The fixed values are rolling72-mvp-research-v1 for lane/version,
roboticket/roboticket, available_total_seats, 3600 seconds and batch 25.
Fixture cap is 1–1000. Freeze the exact reviewed SQL hash before activation.

Then use register_rolling72_mvp_research_v1(bigint[]) with 1–20 committed
admission receipt IDs and capture_rolling72_mvp_research_v1(integer) with a
limit of 1–25. get_rolling72_mvp_research_v1_status() exposes operator counts,
separately from automatic capture. No scheduler or activation is installed by
this proposal.

Dependencies are the existing Roboticket admission-v2 contract and its public
source tables. Their available integer fields define the seat-count unit;
the current snapshots schema has no unit column. The included admission SQL and
synthetic fixture helper are dependencies of the isolated test, preserved from
the existing admission implementation.

## Verification

The PostgreSQL 16 suite uses a disposable loopback database and synthetic source
data. It tests transaction visibility, first point/zero, identity and source
integrity, retries, scope/gaps, expiry, concurrency, immutable ledgers and ACLs.
CI uses no Supabase credentials and does not contact a hosted project.

Run only with ROLLING72_MVP_RESEARCH_TEST_DSN pointing at the dedicated
127.0.0.1:55440/rolling72_mvp_research_test database:

    python -m unittest discover -s tests/postgres -p 'test_rolling72_mvp_research_v1.py' -v

Passing synthetic contracts is not genuine source collection, forecasting,
prospective MAE improvement, or a completed investor MVP.
