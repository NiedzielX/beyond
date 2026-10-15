-- Beyond Live Demand Engine — Phase B shadow contracts v1
-- Applied in Supabase on 2026-10-15. Kept here as reproducible schema evidence.

create table if not exists private.trajectory_gap_observations_v1 (
    id bigserial primary key,
    ticket_event_id bigint not null references public.ticket_events(id),
    source_prior_id bigint not null references private.structural_prior_forecasts_v1(id),
    source_snapshot_id bigint references public.snapshots(id),
    as_of_at timestamptz not null,
    kickoff_at timestamptz not null,
    structural_prior_horizon text not null,
    reference_horizon text,
    trajectory_gap_version text not null,
    live_feature_version text not null,
    reference_mode text not null,
    prior_mapping_mode text not null,
    structural_prior_p50 numeric not null,
    reference_event_count integer not null default 0,
    reference_club_count integer not null default 0,
    observed_progress numeric,
    expected_progress numeric,
    expected_progress_q25 numeric,
    expected_progress_q75 numeric,
    level_gap numeric,
    observed_velocity_24h numeric,
    expected_velocity_24h numeric,
    velocity_gap numeric,
    observed_acceleration_6h_vs_24h numeric,
    expected_acceleration_6h_vs_24h numeric,
    acceleration_gap numeric,
    trajectory_status text not null,
    confidence text not null,
    reason_code text not null,
    signal_readiness text not null,
    feature_quality text not null,
    point_in_time_validated boolean not null,
    metadata jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now(),
    constraint trajectory_gap_observations_v1_time_ck check (as_of_at < kickoff_at),
    constraint trajectory_gap_observations_v1_status_ck check (
      trajectory_status = any(array['UNDERPERFORMING','ON_TRACK','OUTPERFORMING','INSUFFICIENT_SIGNAL']::text[])
    ),
    constraint trajectory_gap_observations_v1_confidence_ck check (
      confidence = any(array['NONE','LOW','MEDIUM','HIGH']::text[])
    ),
    constraint trajectory_gap_observations_v1_reference_count_ck check (
      reference_event_count >= 0 and reference_club_count >= 0
    ),
    constraint trajectory_gap_observations_v1_uq unique(ticket_event_id,as_of_at,trajectory_gap_version)
);

create index if not exists trajectory_gap_observations_v1_event_time_idx
    on private.trajectory_gap_observations_v1(ticket_event_id,as_of_at desc);

create or replace view private.trajectory_gap_reference_pool_v1 as
select
    l.ticket_event_id,
    e.club_slug,
    l.horizon,
    l.as_of_at,
    l.feature_version,
    l.training_eligible,
    l.point_in_time_validated,
    l.signal_readiness,
    nullif(l.features->>'available_index','')::numeric as available_index,
    nullif(l.features->>'velocity_24h_pct_of_first_per_hour','')::numeric as velocity_24h_pct_of_first_per_hour,
    nullif(l.features->>'velocity_6h_pct_of_first_per_hour','')::numeric as velocity_6h_pct_of_first_per_hour
from private.live_trajectory_feature_snapshots_v1 l
join public.ticket_events e on e.id=l.ticket_event_id;

create table if not exists private.trajectory_first_detection_v1 (
    id bigserial primary key,
    ticket_event_id bigint not null references public.ticket_events(id),
    trajectory_gap_version text not null,
    first_gap_observation_id bigint not null references private.trajectory_gap_observations_v1(id),
    detected_at timestamptz not null,
    kickoff_at timestamptz not null,
    lead_hours numeric not null,
    structural_prior_id bigint not null references private.structural_prior_forecasts_v1(id),
    structural_prior_p50 numeric not null,
    reference_horizon text,
    direction text not null,
    level_gap numeric,
    velocity_gap numeric,
    acceleration_gap numeric,
    confidence text not null,
    reason_code text not null,
    created_at timestamptz not null default now(),
    constraint trajectory_first_detection_v1_direction_ck check (
      direction = any(array['UNDERPERFORMING','OUTPERFORMING']::text[])
    ),
    constraint trajectory_first_detection_v1_time_ck check (detected_at < kickoff_at),
    constraint trajectory_first_detection_v1_uq unique(ticket_event_id,trajectory_gap_version)
);

create or replace function private.capture_first_trajectory_divergence_v1()
returns trigger
language plpgsql
security definer
set search_path=private,public
as $function$
begin
    if new.trajectory_status not in ('UNDERPERFORMING','OUTPERFORMING') then
        return new;
    end if;
    if new.point_in_time_validated is not true then
        return new;
    end if;

    insert into private.trajectory_first_detection_v1 (
        ticket_event_id,trajectory_gap_version,first_gap_observation_id,detected_at,kickoff_at,
        lead_hours,structural_prior_id,structural_prior_p50,reference_horizon,direction,
        level_gap,velocity_gap,acceleration_gap,confidence,reason_code
    ) values (
        new.ticket_event_id,new.trajectory_gap_version,new.id,new.as_of_at,new.kickoff_at,
        extract(epoch from(new.kickoff_at-new.as_of_at))/3600.0,new.source_prior_id,new.structural_prior_p50,
        new.reference_horizon,new.trajectory_status,new.level_gap,new.velocity_gap,new.acceleration_gap,
        new.confidence,new.reason_code
    )
    on conflict (ticket_event_id,trajectory_gap_version) do update
    set first_gap_observation_id=excluded.first_gap_observation_id,
        detected_at=excluded.detected_at,
        kickoff_at=excluded.kickoff_at,
        lead_hours=excluded.lead_hours,
        structural_prior_id=excluded.structural_prior_id,
        structural_prior_p50=excluded.structural_prior_p50,
        reference_horizon=excluded.reference_horizon,
        direction=excluded.direction,
        level_gap=excluded.level_gap,
        velocity_gap=excluded.velocity_gap,
        acceleration_gap=excluded.acceleration_gap,
        confidence=excluded.confidence,
        reason_code=excluded.reason_code
    where excluded.detected_at < private.trajectory_first_detection_v1.detected_at;

    return new;
end;
$function$;

drop trigger if exists trajectory_gap_first_detection_v1_trg on private.trajectory_gap_observations_v1;
create trigger trajectory_gap_first_detection_v1_trg
after insert or update of trajectory_status,point_in_time_validated
on private.trajectory_gap_observations_v1
for each row execute function private.capture_first_trajectory_divergence_v1();

create or replace view private.structural_shadow_revision_history_v1 as
with revisions as (
    select
        fo.id as forecast_observation_id,
        fo.ticket_event_id,
        fo.forecast_generated_at,
        fo.source_snapshot_id,
        fo.horizon as structural_prior_horizon,
        fo.historical_model as structural_prior_model,
        fo.historical_p50 as structural_prior_p50,
        fo.live_adjustment,
        fo.final_p50,
        fo.signal_readiness,
        fo.payload->'trajectory_gap'->>'status' as trajectory_status,
        fo.payload->'trajectory_gap'->>'confidence' as trajectory_confidence,
        fo.payload->'trajectory_gap'->>'reason_code' as trajectory_reason_code,
        nullif(fo.payload->'trajectory_gap'->>'level_gap','')::numeric as level_gap,
        nullif(fo.payload->'engine'->>'source_prior_id','')::bigint as source_prior_id,
        row_number() over(partition by fo.ticket_event_id order by fo.forecast_generated_at,fo.id) as revision_no,
        lag(fo.final_p50) over(partition by fo.ticket_event_id order by fo.forecast_generated_at,fo.id) as previous_final_p50
    from public.forecast_observations fo
    where fo.model_version='beyond-demand-engine-v1-structural-prior-shadow'
      and fo.forecast_status='shadow'
), scored as (
    select
        r.*,
        (r.final_p50-r.previous_final_p50) as p50_revision_delta,
        o.actual_attendance,
        case when o.actual_attendance is not null and r.final_p50 is not null
             then abs(r.final_p50-o.actual_attendance) end as absolute_error,
        case when o.actual_attendance is not null and r.previous_final_p50 is not null
             then abs(r.previous_final_p50-o.actual_attendance) end as previous_absolute_error
    from revisions r
    left join public.ticket_event_outcomes o on o.ticket_event_id=r.ticket_event_id
)
select
    s.*,
    case
      when s.actual_attendance is null or s.previous_final_p50 is null then 'PENDING_OUTCOME'
      when s.absolute_error < s.previous_absolute_error then 'IMPROVED'
      when s.absolute_error > s.previous_absolute_error then 'WORSENED'
      else 'UNCHANGED'
    end as revision_effect
from scored s;
