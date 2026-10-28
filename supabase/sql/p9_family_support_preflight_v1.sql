-- P9 prospective incumbent-family support preflight v1.
--
-- Observability only. This does not select curve neighbours, produce a P9
-- prediction, relax k=5/min-3 support, read future target attendance, train a
-- model, or change production forecasts.
--
-- It answers two narrower questions before a T-48/T-24 window opens:
-- 1) how many completed reference events currently have a genuine outcome and
--    a PIT-safe incumbent in each source family at the analogous cutoff; and
-- 2) which incumbent family is currently eligible for each future target under
--    the exact frozen builder rules, including the 6h Long72 staleness limit.
--
-- Global family-pool size is deliberately NOT described as selected-neighbour
-- support. The frozen builder still decides support only from its five nearest
-- booking-curve neighbours inside the immutable window.

create or replace function public.p9_family_support_preflight_v1(
  p_horizon_days integer default 10
)
returns jsonb
language plpgsql
stable
set search_path to 'public','private','pg_temp'
as $function$
declare
  v_days integer := greatest(1, least(coalesce(p_horizon_days,10), 31));
begin
  return (
    with reference_events as (
      select
        e.id as ticket_event_id,
        e.kickoff_at
      from public.ticket_events e
      join public.ticket_event_outcomes o
        on o.ticket_event_id=e.id
       and o.actual_attendance is not null
      where private.normalize_structural_prior_competition_v1(e.competition)='Ekstraklasa'
        and e.kickoff_at < now()
        and o.confirmed_at <= now()
    ), reference_cutoffs as (
      select
        r.ticket_event_id,
        r.kickoff_at,
        c.cutoff_hours,
        r.kickoff_at - make_interval(hours=>c.cutoff_hours) as analogous_cutoff_at
      from reference_events r
      cross join (values (48),(24)) c(cutoff_hours)
    ), reference_flags as (
      select
        c.*,
        exists (
          select 1
          from private.d2_long72_forward_predictions_v1 d
          where d.ticket_event_id=c.ticket_event_id
            and d.as_of_at <= c.analogous_cutoff_at
            and d.created_at <= c.analogous_cutoff_at
            and c.analogous_cutoff_at - d.as_of_at <= interval '6 hours'
        ) as d2_ready,
        exists (
          select 1
          from private.structural_prior_forecasts_v1 s
          where s.ticket_event_id=c.ticket_event_id
            and s.point_in_time_validated
            and s.target_as_of_at <= c.analogous_cutoff_at
            and s.created_at <= c.analogous_cutoff_at
        ) as structural_ready
      from reference_cutoffs c
    ), pool as (
      select
        cutoff_hours,
        count(*) filter (where d2_ready)::integer as d2_count,
        count(*) filter (where structural_ready)::integer as structural_count,
        coalesce(
          jsonb_agg(ticket_event_id order by ticket_event_id)
            filter (where d2_ready),
          '[]'::jsonb
        ) as d2_event_ids,
        coalesce(
          jsonb_agg(ticket_event_id order by ticket_event_id)
            filter (where structural_ready),
          '[]'::jsonb
        ) as structural_event_ids
      from reference_flags
      group by cutoff_hours
    ), future_events as (
      select
        e.id as ticket_event_id,
        e.home_team,
        e.away_team,
        e.kickoff_at,
        e.kickoff_at - interval '48 hours' as t48_at,
        e.kickoff_at - interval '24 hours' as t24_at
      from public.ticket_events e
      where private.normalize_structural_prior_competition_v1(e.competition)='Ekstraklasa'
        and e.kickoff_at > now()
        and e.kickoff_at <= now() + make_interval(days=>v_days)
        and not exists (
          select 1
          from public.ticket_event_outcomes o
          where o.ticket_event_id=e.id
            and o.actual_attendance is not null
        )
    ), target_state as (
      select
        f.*,
        (select count(*)::integer
         from private.d2_long72_forward_predictions_v1 d
         where d.ticket_event_id=f.ticket_event_id
           and d.as_of_at <= f.t48_at
           and d.created_at <= f.t48_at
           and f.t48_at - d.as_of_at <= interval '6 hours') as d2_t48,
        (select count(*)::integer
         from private.structural_prior_forecasts_v1 s
         where s.ticket_event_id=f.ticket_event_id
           and s.point_in_time_validated
           and s.target_as_of_at <= f.t48_at
           and s.created_at <= f.t48_at) as structural_t48,
        (select count(*)::integer
         from private.d2_long72_forward_predictions_v1 d
         where d.ticket_event_id=f.ticket_event_id
           and d.as_of_at <= f.t24_at
           and d.created_at <= f.t24_at
           and f.t24_at - d.as_of_at <= interval '6 hours') as d2_t24,
        (select count(*)::integer
         from private.structural_prior_forecasts_v1 s
         where s.ticket_event_id=f.ticket_event_id
           and s.point_in_time_validated
           and s.target_as_of_at <= f.t24_at
           and s.created_at <= f.t24_at) as structural_t24
      from future_events f
    ), classified as (
      select
        t.*,
        case
          when t.d2_t48>0 then 'd2_long72_forward_predictions_v1'
          when t.structural_t48>0 then 'structural_prior_forecasts_v1'
          else 'none'
        end as current_family_t48,
        case
          when t.d2_t24>0 then 'd2_long72_forward_predictions_v1'
          when t.structural_t24>0 then 'structural_prior_forecasts_v1'
          else 'none'
        end as current_family_t24,
        (now()<t.t48_at and t.d2_t48=0) as family_may_change_t48,
        (now()<t.t24_at and t.d2_t24=0) as family_may_change_t24
      from target_state t
    )
    select jsonb_build_object(
      'version','p9-family-support-preflight-v1',
      'checked_at',now(),
      'horizon_days',v_days,
      'k_neighbors',5,
      'minimum_selected_neighbor_support',3,
      'long72_max_staleness_hours',6,
      'global_pool_is_not_selected_neighbor_support',true,
      'target_values_used',false,
      'production_change',false,
      'reference_pools',jsonb_build_object(
        't48',jsonb_build_object(
          'd2_residual_ready_events',coalesce((select d2_count from pool where cutoff_hours=48),0),
          'structural_residual_ready_events',coalesce((select structural_count from pool where cutoff_hours=48),0),
          'd2_event_ids',coalesce((select d2_event_ids from pool where cutoff_hours=48),'[]'::jsonb),
          'structural_event_ids',coalesce((select structural_event_ids from pool where cutoff_hours=48),'[]'::jsonb)
        ),
        't24',jsonb_build_object(
          'd2_residual_ready_events',coalesce((select d2_count from pool where cutoff_hours=24),0),
          'structural_residual_ready_events',coalesce((select structural_count from pool where cutoff_hours=24),0),
          'd2_event_ids',coalesce((select d2_event_ids from pool where cutoff_hours=24),'[]'::jsonb),
          'structural_event_ids',coalesce((select structural_event_ids from pool where cutoff_hours=24),'[]'::jsonb)
        )
      ),
      'events',coalesce((
        select jsonb_agg(jsonb_build_object(
          'ticket_event_id',c.ticket_event_id,
          'home_team',c.home_team,
          'away_team',c.away_team,
          'kickoff_at',c.kickoff_at,
          't48_at',c.t48_at,
          't24_at',c.t24_at,
          'current_d2_eligible_rows_t48',c.d2_t48,
          'current_structural_eligible_rows_t48',c.structural_t48,
          'current_family_t48',c.current_family_t48,
          'family_may_change_before_t48',c.family_may_change_t48,
          'current_family_global_pool_t48',case
            when c.current_family_t48='d2_long72_forward_predictions_v1'
              then coalesce((select d2_count from pool where cutoff_hours=48),0)
            when c.current_family_t48='structural_prior_forecasts_v1'
              then coalesce((select structural_count from pool where cutoff_hours=48),0)
            else 0 end,
          'current_d2_eligible_rows_t24',c.d2_t24,
          'current_structural_eligible_rows_t24',c.structural_t24,
          'current_family_t24',c.current_family_t24,
          'family_may_change_before_t24',c.family_may_change_t24,
          'current_family_global_pool_t24',case
            when c.current_family_t24='d2_long72_forward_predictions_v1'
              then coalesce((select d2_count from pool where cutoff_hours=24),0)
            when c.current_family_t24='structural_prior_forecasts_v1'
              then coalesce((select structural_count from pool where cutoff_hours=24),0)
            else 0 end
        ) order by c.kickoff_at,c.ticket_event_id)
        from classified c
      ),'[]'::jsonb)
    )
  );
end;
$function$;

revoke all on function public.p9_family_support_preflight_v1(integer)
  from public,anon,authenticated;
grant execute on function public.p9_family_support_preflight_v1(integer)
  to service_role;

-- Add the diagnostic payload to the existing preflight contract without
-- changing any existing status calculation or learner behavior.
create or replace function public.p9_prospective_preflight_v1(p_horizon_days integer default 10)
returns jsonb
language plpgsql
stable
security definer
set search_path to 'public','private'
as $function$
declare
  v_days integer := greatest(1, least(coalesce(p_horizon_days,10), 31));
begin
  return (
    with future_events as (
      select
        e.id as ticket_event_id,
        e.home_team,
        e.away_team,
        e.kickoff_at,
        e.kickoff_at - interval '48 hours' as t48_at,
        e.kickoff_at - interval '24 hours' as t24_at
      from public.ticket_events e
      where private.normalize_structural_prior_competition_v1(e.competition)='Ekstraklasa'
        and e.kickoff_at > now()
        and e.kickoff_at <= now() + make_interval(days=>v_days)
        and not exists (
          select 1 from public.ticket_event_outcomes o
          where o.ticket_event_id=e.id and o.actual_attendance is not null
        )
    ), evidence as (
      select
        f.*,
        (select count(*) from public.snapshots s
          where s.ticket_event_id=f.ticket_event_id and s.available_total is not null and s.available_total>=0
            and s.captured_at < f.kickoff_at and s.captured_at <= f.t48_at) as snapshots_t48,
        (select count(*) from public.snapshots s
          where s.ticket_event_id=f.ticket_event_id and s.available_total is not null and s.available_total>=0
            and s.captured_at < f.kickoff_at and s.captured_at <= f.t24_at) as snapshots_t24,
        (
          (select count(*) from private.structural_prior_forecasts_v1 sp
            where sp.ticket_event_id=f.ticket_event_id and sp.point_in_time_validated
              and sp.target_as_of_at <= f.t48_at and sp.created_at <= f.t48_at)
          +
          (select count(*) from private.d2_long72_forward_predictions_v1 d
            where d.ticket_event_id=f.ticket_event_id
              and d.as_of_at <= f.t48_at and d.created_at <= f.t48_at)
        ) as incumbents_t48,
        (
          (select count(*) from private.structural_prior_forecasts_v1 sp
            where sp.ticket_event_id=f.ticket_event_id and sp.point_in_time_validated
              and sp.target_as_of_at <= f.t24_at and sp.created_at <= f.t24_at)
          +
          (select count(*) from private.d2_long72_forward_predictions_v1 d
            where d.ticket_event_id=f.ticket_event_id
              and d.as_of_at <= f.t24_at and d.created_at <= f.t24_at)
        ) as incumbents_t24,
        exists(select 1 from private.p9_booking_curve_prospective_predictions_v1 p where p.ticket_event_id=f.ticket_event_id and p.cutoff_hours=48) as prediction_t48_exists,
        exists(select 1 from private.p9_booking_curve_prospective_predictions_v1 p where p.ticket_event_id=f.ticket_event_id and p.cutoff_hours=24) as prediction_t24_exists
      from future_events f
    ), classified as (
      select e.*,
        case
          when prediction_t48_exists then 'CAPTURED'
          when now() > t48_at + interval '90 minutes' then 'MISSED_WINDOW'
          when now() >= t48_at then 'WINDOW_OPEN'
          when now() >= t48_at - interval '48 hours' and snapshots_t48=0 then 'CRITICAL_NO_SNAPSHOT'
          when now() >= t48_at - interval '48 hours' and incumbents_t48=0 then 'CRITICAL_NO_INCUMBENT'
          when snapshots_t48=0 then 'WATCH_NO_SNAPSHOT'
          when incumbents_t48=0 then 'WATCH_NO_INCUMBENT'
          else 'READY'
        end as t48_status,
        case
          when prediction_t24_exists then 'CAPTURED'
          when now() > t24_at + interval '90 minutes' then 'MISSED_WINDOW'
          when now() >= t24_at then 'WINDOW_OPEN'
          when now() >= t24_at - interval '48 hours' and snapshots_t24=0 then 'CRITICAL_NO_SNAPSHOT'
          when now() >= t24_at - interval '48 hours' and incumbents_t24=0 then 'CRITICAL_NO_INCUMBENT'
          when snapshots_t24=0 then 'WATCH_NO_SNAPSHOT'
          when incumbents_t24=0 then 'WATCH_NO_INCUMBENT'
          else 'READY'
        end as t24_status
      from evidence e
    )
    select jsonb_build_object(
      'version','p9-prospective-preflight-v1',
      'checked_at',now(),
      'horizon_days',v_days,
      'target_values_used',false,
      'production_change',false,
      'critical_count',coalesce((select count(*) from classified c where c.t48_status like 'CRITICAL%' or c.t24_status like 'CRITICAL%' or c.t48_status='MISSED_WINDOW' or c.t24_status='MISSED_WINDOW'),0),
      'watch_count',coalesce((select count(*) from classified c where c.t48_status like 'WATCH%' or c.t24_status like 'WATCH%'),0),
      'family_support',public.p9_family_support_preflight_v1(v_days),
      'events',coalesce((select jsonb_agg(jsonb_build_object(
        'ticket_event_id',c.ticket_event_id,
        'home_team',c.home_team,
        'away_team',c.away_team,
        'kickoff_at',c.kickoff_at,
        't48_at',c.t48_at,
        't24_at',c.t24_at,
        'hours_to_t48',round((extract(epoch from (c.t48_at-now()))/3600.0)::numeric,2),
        'hours_to_t24',round((extract(epoch from (c.t24_at-now()))/3600.0)::numeric,2),
        'snapshots_t48',c.snapshots_t48,
        'snapshots_t24',c.snapshots_t24,
        'incumbents_t48',c.incumbents_t48,
        'incumbents_t24',c.incumbents_t24,
        'prediction_t48_exists',c.prediction_t48_exists,
        'prediction_t24_exists',c.prediction_t24_exists,
        't48_status',c.t48_status,
        't24_status',c.t24_status
      ) order by c.kickoff_at,c.ticket_event_id) from classified c),'[]'::jsonb)
    )
  );
end;
$function$;

revoke all on function public.p9_prospective_preflight_v1(integer)
  from public,anon,authenticated;
grant execute on function public.p9_prospective_preflight_v1(integer)
  to service_role;
