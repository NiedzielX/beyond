-- Beyond Ticketing — Sector Gap v1
--
-- Release/coverage-aware continuous gap layer on top of sector-trajectory-v1.
-- No UNDERPERFORMING / ON_TRACK / OUTPERFORMING status is assigned here yet.
--
-- Provisional quality policies:
-- - coverage is considered stable when the current sector was visible in at
--   least 80% of event snapshots over both the latest 6h and 24h windows;
-- - a material availability increase is flagged when the largest positive
--   24h jump is >= 5 seats AND >= 10% of the current reference availability.
--
-- These are E0 quality heuristics, not learned demand or elasticity models.

create or replace function public.get_sector_gap_v1_asof(
    p_ticket_event_id bigint,
    p_as_of_at timestamptz default now()
)
returns table (
    feature_version text,
    trajectory_feature_version text,
    baseline_version text,
    release_heuristic_version text,
    coverage_policy_version text,
    ticket_event_id bigint,
    sector text,
    source_snapshot_id bigint,
    as_of_at timestamptz,
    kickoff_at timestamptz,
    hours_to_kickoff numeric,
    current_available integer,
    reference_available integer,
    velocity_6h numeric,
    velocity_24h numeric,
    velocity_72h numeric,
    velocity_7d numeric,
    acceleration_6h_vs_24h numeric,
    public_sell_through_proxy numeric,
    sector_gap_available numeric,
    sector_gap_ratio numeric,
    snapshots_6h integer,
    sector_observations_6h integer,
    sector_presence_ratio_6h numeric,
    snapshots_24h integer,
    sector_observations_24h integer,
    sector_presence_ratio_24h numeric,
    max_positive_availability_delta_24h integer,
    max_positive_availability_delta_ratio_24h numeric,
    potential_release_activity_flag boolean,
    coverage_stable_flag boolean,
    availability_increase_24h_flag boolean,
    sector_appeared_within_24h_flag boolean,
    sector_coverage_gap_flag boolean,
    sector_coverage_change_flag boolean,
    data_gap_flag boolean,
    trajectory_readiness text,
    gap_reliability text,
    gap_usable_for_status boolean,
    point_in_time_validated boolean
)
language sql
stable
security invoker
set search_path = public
as $function$
with base as (
    select *
    from public.get_sector_trajectory_v1_asof(p_ticket_event_id,p_as_of_at)
), anchor as (
    select max(as_of_at) as as_of_at
    from base
), window_snapshots as (
    select
        count(*) filter (where s.captured_at>=a.as_of_at-interval '6 hours')::integer as snapshots_6h,
        count(*) filter (where s.captured_at>=a.as_of_at-interval '24 hours')::integer as snapshots_24h
    from public.snapshots s
    cross join anchor a
    where s.ticket_event_id=p_ticket_event_id
      and s.captured_at<=a.as_of_at
      and s.captured_at>=a.as_of_at-interval '24 hours'
), sector_presence as (
    select
        b.sector,
        count(distinct s.id) filter (
            where s.captured_at>=a.as_of_at-interval '6 hours'
              and si.id is not null
        )::integer as sector_observations_6h,
        count(distinct s.id) filter (
            where s.captured_at>=a.as_of_at-interval '24 hours'
              and si.id is not null
        )::integer as sector_observations_24h
    from base b
    cross join anchor a
    join public.snapshots s
      on s.ticket_event_id=b.ticket_event_id
     and s.captured_at<=a.as_of_at
     and s.captured_at>=a.as_of_at-interval '24 hours'
    left join public.sector_inventory si
      on si.snapshot_id=s.id
     and si.sector=b.sector
    group by b.sector
), scored as (
    select
        b.*,
        ws.snapshots_6h,
        sp.sector_observations_6h,
        case when ws.snapshots_6h>0
             then sp.sector_observations_6h::numeric/ws.snapshots_6h end as presence_6h,
        ws.snapshots_24h,
        sp.sector_observations_24h,
        case when ws.snapshots_24h>0
             then sp.sector_observations_24h::numeric/ws.snapshots_24h end as presence_24h,
        case when b.reference_available>0
             then b.max_positive_availability_delta_24h::numeric/b.reference_available end as positive_jump_ratio
    from base b
    cross join window_snapshots ws
    join sector_presence sp on sp.sector=b.sector
), quality as (
    select
        s.*,
        (
            s.max_positive_availability_delta_24h>=5
            and coalesce(s.positive_jump_ratio,0)>=0.10
        ) as potential_release,
        (
            coalesce(s.presence_6h,0)>=0.80
            and coalesce(s.presence_24h,0)>=0.80
        ) as coverage_stable
    from scored s
)
select
    'sector-gap-v1'::text,
    q.feature_version,
    q.baseline_version,
    'PROVISIONAL_RELEASE_HEURISTIC_V1_MIN5_AND_10PCT'::text,
    'COVERAGE_STABILITY_V1_PRESENCE80_6H_24H'::text,
    q.ticket_event_id,
    q.sector,
    q.source_snapshot_id,
    q.as_of_at,
    q.kickoff_at,
    q.hours_to_kickoff,
    q.current_available,
    q.reference_available,
    q.velocity_6h,
    q.velocity_24h,
    q.velocity_72h,
    q.velocity_7d,
    q.acceleration_6h_vs_24h,
    q.public_sell_through_proxy,
    q.sector_gap_available,
    q.sector_gap_ratio,
    q.snapshots_6h,
    q.sector_observations_6h,
    round(q.presence_6h,6),
    q.snapshots_24h,
    q.sector_observations_24h,
    round(q.presence_24h,6),
    q.max_positive_availability_delta_24h,
    round(q.positive_jump_ratio,6),
    q.potential_release,
    q.coverage_stable,
    q.availability_increase_24h_flag,
    q.sector_appeared_within_24h_flag,
    q.sector_coverage_gap_flag,
    q.sector_coverage_change_flag,
    q.data_gap_flag,
    q.trajectory_readiness,
    case
        when q.trajectory_readiness<>'READY' then 'INSUFFICIENT'
        when not q.coverage_stable then 'LOW'
        when q.potential_release then 'LOW'
        when q.availability_increase_24h_flag or q.sector_appeared_within_24h_flag then 'MEDIUM'
        else 'HIGH'
    end::text,
    (
        q.trajectory_readiness='READY'
        and q.coverage_stable
        and not q.potential_release
    ),
    q.point_in_time_validated
from quality q
order by q.sector;
$function$;

revoke all on function public.get_sector_gap_v1_asof(bigint,timestamptz) from public,anon,authenticated;
grant execute on function public.get_sector_gap_v1_asof(bigint,timestamptz) to service_role;

comment on function public.get_sector_gap_v1_asof(bigint,timestamptz) is
'Release/coverage-aware continuous E0 sector gap. Provisional quality heuristics only; no final sector status or learned demand curve.';
