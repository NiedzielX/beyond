# Beyond Supabase write outage

Observed on 28 November around 14:19 Warsaw in project
`adchzwqboeekhokapxqi`. The project remained readable. PostgreSQL reported
`default_transaction_read_only=on` from its configuration file,
`transaction_read_only=on`, and `pg_is_in_recovery()=false`. The
`pg_net` worker was present. No `pg_cron` worker was visible.

The latest successful global cron job started at 22:36 Warsaw on
27 November. Existing collector job 2 last ran at 22:35, December source
job 46 at 22:23, and December paired job 47 at 22:27. All checked job
definitions remained active. A single controlled dispatch of the
existing collector command was rejected before enqueue with SQLSTATE
`25006`. Supabase Edge logs showed no later Roboticket invocation.

## Pilot impact

Each fixture had 23 raw observations by the outage. The 22:35
observations were the newest. The last sealed observations came from
22:20 and the last forecast bundles were issued at 22:27, all on
27 November Warsaw time. Both fixtures had 22 numeric common pairs on
each horizon and zero accepted labels at the 14:15 read. All 132 pairs
used PERS because no 24-hour anchor was available at issue.

The first +24 h targets are due at approximately 17:12 Warsaw on
28 November. A valid latest observation for those targets must be at
most six hours old and captured at or before the target. The unprocessed
22:35 observation from the previous evening is older than six hours.
Later source recovery can supply only eligible actual captures.

## Capacity and recovery decisions

Supabase reports the organization on Free. The PostgreSQL database
total is 1,643,968,179 bytes (1.53 GiB). This excludes some physical disk
usage, such as WAL. The measured state is managed read-only. The exact
physical disk usage percentage has not been verified.
[Supabase database and disk documentation](https://supabase.com/docs/guides/platform/database-size#free-plan-behavior)

| Largest relations | PostgreSQL reported size |
| --- | --- |
| `private.rolling72_managed_attempts_v3a` | 353 MB |
| `private.rolling72_lad_attempts_v5` | 279 MB |
| `public.sector_price_area_observations_v1` | 253 MB |
| `public.ticket_price_observations_v1` | 155 MB |
| `public.sector_inventory` | 142 MB |
| `private.rolling72_forward_baselines_b_attempts_v1` | 114 MB |

Supabase documents upgrading the existing organization to Pro for an
8 GB disk or reclaiming sufficient capacity. Before any cleanup, verify
actual disk metrics and make and test a recoverable archive outside the
saturated disk. Review exact candidate rows and references against
frozen forecast and score evidence. Raw inventory and immutable evidence
need a separate retention decision. Large bulk writes can increase WAL
under pressure. Capacity restoration, any paid change, and any cleanup
remain pending authorization.

After restoring read/write mode, verify the existing scheduled collector,
source seals, and paired issue and scoring jobs with a fresh capture from
both fixtures. Record the gap in coverage. Keep the original forecasts
and their target clocks.
