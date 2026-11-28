# Rolling72 December deployment preflight

## Hosted readback

Supabase project `adchzwqboeekhokapxqi`, 27 November at 16:25 Warsaw.
The additive migration `rolling72_december_lanes_v1` installed the two
isolated schemas from the source and paired SQL hashes below. Both lane
manifest tables and the December cron namespace were empty after installation.
All 14 new private tables have RLS enabled. All eight public RPCs grant
execution to `service_role` and deny it to `anon` and `authenticated`.
The schedules and command hashes of old jobs 17, 43, 44 and 45 matched the
preflight. Their latest scheduled checks succeeded.
The 16:30 follow-up still showed zero December manifests and jobs. The
previous comparator had 115 issue bundles and 19 shared +24 h labels from
one fixture. Both policies had MAE 136.53 available seats. There were zero
shared +48 h and +72 h labels.

## Reviewed launch candidate

```sh
python -m ml.rolling72_december_bundle_v1 /tmp/beyond-december-launch \
  --issue-until 2026-12-31T00:00:00Z \
  --scoring-until 2027-01-03T06:00:00Z --max-fixtures 100 --with-schedules
```

Issuance closes 31 December at 01:00 Warsaw. Scoring closes 3 January at
07:00 Warsaw. The capture job runs at minutes 08, 23, 38, 53 and the paired
job at 12, 27, 42, 57. The paired schedule was moved off the exact minutes
of active job 45. The old and new lanes have separate runtime locks, so
long-running jobs can still overlap. Jobs self-unschedule after scoring.
The fixture cap is a capacity ceiling. Each fixture still needs a verified
admission receipt and explicit registration. This initial pilot has two
candidate fixtures.

| File | SHA-256 |
| --- | --- |
| source.sql | `443416d944c920ca1b2ebf878c231e41decfdd851a80af97e9005b973cc43358` |
| paired.sql | `41a148ef621a3b84203093234d40b8864efea8a2ae349a3d39c4bec3d28be677` |
| source_manifest.json | `043bc5fe4d9de8f8b68f107535f67db9623913f4822b2e0a92b059e8f0be6e27` |
| paired_manifest.json | `f0ecb61f229fdebc4881ce9e259a57a1923444615a9109166e4459b591e01699` |
| source_cron.sql | `a344a3b22d1f651c3b6be080821b6eadcbf2a9eb5dbc4759e184cd1939cd66e2` |
| paired_cron.sql | `de930b901d49224f3ec55c7cb3a501103cf43b9c81e47217bf9d722d6a06cf7e` |
| launch.sql | `8c170ac24039bb8b92ec54290020299fb32683c79ec862831ff1fc0145b6ef71` |

The disposable PostgreSQL 16.16 integration suite passed both tests.
The atomic launch rolled back both activations and the first cron install
when the second installer was made to fail. A repeated successful launch
left one job of each kind and preserved the old job. The synthetic source
capture still issued both policies at all three horizons.

## Admission and first observation

The two 5 December fixtures match the active club domains, exact aliases
and hosted round-17 schedule. Neither has a v2 receipt or registered ticket
event. The hosted `roboticket_collect_additional` v9 loads future Roboticket
ticket events for active clubs and selects full snapshots for Cracovia and
GKS Katowice. Its current price-only set contains Lech alone.

After the launch is authorized, refresh both direct sources and runtime
checks within the 10-minute gate described in
`ml/ROLLING72_DEC05_INTAKE_EVIDENCE_2026-11-27.md`. Commit v2 admissions,
then explicitly register the committed receipt IDs in the December lane
in a separate transaction. Register ahead of the next collector tick.
Verify an independently committed post-registration observation, a
December seal, and the paired forecasts in that order. Historical
candidate buffers (824 Cracovia rows and 691 GKS rows at preflight) remain
excluded. Use actual observations for the full match cycle. A +72 h
target must be before its fixture kickoff, so the earlier admission
deadline of practical relevance is 2 December at 14:45 Warsaw.

This pilot measures visible inventory proxy on two fixtures. The
prospective accuracy gate remains 30 new fixtures from at least eight
home clubs, at least 10% lower +72 h MAE with the whole 95% paired
interval below zero, and no +24/+48 h point MAE regression.
