# Rolling72 December hosted launch

On 27 November, the user approved the exact two-manifest launch and
forward-only admission of Cracovia–Widzew and GKS Katowice–Legia after
a fresh source check. The authorized launch covered the finite window
documented in [the preflight](2026-11-27-december-hosted-preparation.md).

## Committed activation

Executed the reviewed atomic SQL, SHA-256
`8c170ac24039bb8b92ec54290020299fb32683c79ec862831ff1fc0145b6ef71`.
Supabase readback at 16:51 Warsaw confirmed source and paired manifests
active as of 16:51:00, with the exact hashes and deadlines in the
preflight. Existing jobs 2, 17, 43, 44 and 45 remained active. Jobs 17,
43, 44 and 45 preserved their preflight schedule and command hashes.

| New job | ID | Schedule |
| --- | --- | --- |
| `rolling72_december_source_v1_capture` | 46 | `8,23,38,53 * * * *` |
| `rolling72_december_pair_v1_tick` | 47 | `12,27,42,57 * * * *` |

First natural source tick ran at 16:53 Warsaw and succeeded in 0.235 s.
It ran before fixture admission.

## Verified admission and registration

Fresh ticket pages, independent schedule lookup and direct inventory
requests returned HTTP 200 between 16:52:34 and 16:52:41 Warsaw. The
deployed collector uses full snapshots for both active clubs. The
production parser accepted 6,609 visible seats across 25 sectors for
Cracovia and 1,763 across 14 for GKS. These probes were source-readiness
evidence only. The new forecast ledger uses source captures from the
normal post-registration collector.

The v2 admission request was validated by the existing builder and
submitted atomically (request SHA-256
`0860f430c8e92d7c423e2b8ee0cc98eea2d7d73502d4e1abb8770cf83ab8d5ea`).
The source registration call was made in a separate transaction. The
16:56:20 readback confirmed both registrations, with zero snapshots yet
and zero backfill. Legacy candidate buffer rows were excluded.

| Match on 5 December | Kickoff Warsaw | Roboticket offer | Ticket event | Receipt | Registered Warsaw |
| --- | --- | --- | --- | --- | --- |
| Cracovia–Widzew | 14:45 | 10896 | 28411 | 7 | 16:56:11.313 |
| GKS Katowice–Legia | 20:15 | 5772 | 28412 | 8 | 16:56:11.341 |

The first natural collector run after registration committed the
following snapshots on 27 November. These IDs and counts came from
`public.snapshots` and its price-area observations, independently of the
earlier direct-page probes.

| Ticket event | Snapshot | Captured Warsaw | Available seats | Sector rows | Sector/price rows |
| --- | --- | --- | --- | --- | --- |
| 28411 | 51091 | 17:05:02.619 | 6,608 | 25 | 25 |
| 28412 | 51092 | 17:05:02.785 | 1,760 | 14 | 14 |

Job 46 ran at 17:08:00 Warsaw, finished in 0.335 s and committed
seals 1 and 2. It created six `SOURCE_ELIGIBLE` opportunities
across the two events. All three provisional targets per event were
before kickoff.

## First scheduled forecasts

Job 47 issued the first paired bundles at 17:12:00 Warsaw. Post-commit
readback confirmed 12 numeric forecasts across two matches, two methods
and +24/+48/+72 h. Each exact target clock is the issue time plus its
horizon. Both bundles used `NO_24H_ANCHOR`, so DRIFT24 copied PERS for
these first observations.

| Ticket event | Bundle | Issued Warsaw | Capture to issue | First value at each horizon |
| --- | --- | --- | --- | --- |
| 28411 | 1 | 17:12:00.328 | 417.709 s | 6,608 |
| 28412 | 2 | 17:12:00.371 | 417.586 s | 1,760 |

The first target timestamps fall on 28, 29 and 30 November at 17:12
Warsaw. Labels recorded at first readback: zero. Any MAE must wait for
valid target observations. The targets measure visible inventory.

The [fixture coverage query](../../supabase/ops/rolling72_december_fixture_coverage_v1.sql)
returns three rows per registered fixture, including horizons without
issues or labels. It reports numeric pairs, target maturity and each
DRIFT24 fallback reason. Use it as a read-only operational check.

## Upcoming intake opportunities

The [official Ekstraklasa schedule](https://ekstraklasa.org/aktualnosci/terminarz-18-kolejki-oraz-terminy-meczow-zaleglych/)
shows three later home fixtures for clubs active in this Roboticket
source. At 17:02 Warsaw, none had an offer candidate or v2 receipt.
All three corresponding public listings returned HTTP 200 at 17:07,
and none showed its target offer. Source admission still requires
a direct ticket page and supported public inventory.

| Match | Kickoff Warsaw | Latest permissible boundary for +72 h, exclusive |
| --- | --- | --- |
| Śląsk–Górnik | 12 December 20:15 | 9 December 20:15 |
| Cracovia–Lech | 13 December 14:45 | 10 December 14:45 |
| GKS Katowice–Wisła | 13 December 17:30 | 10 December 17:30 |

The official calendar lists the winter break after the last postponed
fixtures on 16–17 December. The admitted December pilot and these potential
fixtures fall well short of the formal 30-match, eight-home-club threshold.
