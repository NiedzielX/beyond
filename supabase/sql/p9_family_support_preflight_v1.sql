-- P9 prospective incumbent-family support preflight v1.
-- Observability only: no neighbour selection, no target labels, no model fit,
-- no support-gate relaxation and no production forecast change.
-- Global family-pool size is NOT selected-neighbour support; frozen P9 still
-- requires >=3 same-family residuals among its five nearest curve neighbours.

create or replace function public.p9_family_support_preflight_v1(
  p_horizon_days integer default 10
)
returns jsonb
language plpgsql
stable
set search_path to 'public','private','pg_temp'
as $function$
declare
  v_days integer := greatest(1, least(coalesce(p_horizon_days,10),31));
begin
  return (
    with reference_events as (
      select e.id ticket_event_id,e.kickoff_at
      from public.ticket_events e
      join public.ticket_event_outcomes o
        on o.ticket_event_id=e.id and o.actual_attendance is not null
      where private.normalize_structural_prior_competition_v1(e.competition)='Ekstraklasa'
        and e.kickoff_at<now()
        and o.confirmed_at<=now()
    ), reference_cutoffs as (
      select r.ticket_event_id,r.kickoff_at,c.cutoff_hours,
             r.kickoff_at-make_interval(hours=>c.cutoff_hours) analogous_cutoff_at
      from reference_events r
      cross join (values (48),(24)) c(cutoff_hours)
    ), reference_flags as (
      select c.*,
        exists(
          select 1 from private.d2_long72_forward_predictions_v1 d
          where d.ticket_event_id=c.ticket_event_id
            and d.as_of_at<=c.analogous_cutoff_at
            and d.created_at<=c.analogous_cutoff_at
            and c.analogous_cutoff_at-d.as_of_at<=interval '6 hours'
        ) d2_ready,
        exists(
          select 1 from private.structural_prior_forecasts_v1 s
          where s.ticket_event_id=c.ticket_event_id
            and s.point_in_time_validated
            and s.target_as_of_at<=c.analogous_cutoff_at
            and s.created_at<=c.analogous_cutoff_at
        ) structural_ready
      from reference_cutoffs c
    ), pool as (
      select cutoff_hours,
        count(*) filter(where d2_ready)::integer d2_count,
        count(*) filter(where structural_ready)::integer structural_count,
        coalesce(jsonb_agg(ticket_event_id order by ticket_event_id) filter(where d2_ready),'[]'::jsonb) d2_event_ids,
        coalesce(jsonb_agg(ticket_event_id order by ticket_event_id) filter(where structural_ready),'[]'::jsonb) structural_event_ids
      from reference_flags
      group by cutoff_hours
    ), future_events as (
      select e.id ticket_event_id,e.home_team,e.away_team,e.kickoff_at,
             e.kickoff_at-interval '48 hours' t48_at,
             e.kickoff_at-interval '24 hours' t24_at
      from public.ticket_events e
      where private.normalize_structural_prior_competition_v1(e.competition)='Ekstraklasa'
        and e.kickoff_at>now()
        and e.kickoff_at<=now()+make_interval(days=>v_days)
        and not exists(
          select 1 from public.ticket_event_outcomes o
          where o.ticket_event_id=e.id and o.actual_attendance is not null
        )
    ), target_state as (
      select f.*,
        (select count(*)::integer from private.d2_long72_forward_predictions_v1 d
          where d.ticket_event_id=f.ticket_event_id
            and d.as_of_at<=f.t48_at and d.created_at<=f.t48_at
            and f.t48_at-d.as_of_at<=interval '6 hours') d2_t48,
        (select count(*)::integer from private.structural_prior_forecasts_v1 s
          where s.ticket_event_id=f.ticket_event_id and s.point_in_time_validated
            and s.target_as_of_at<=f.t48_at and s.created_at<=f.t48_at) structural_t48,
        (select count(*)::integer from private.d2_long72_forward_predictions_v1 d
          where d.ticket_event_id=f.ticket_event_id
            and d.as_of_at<=f.t24_at and d.created_at<=f.t24_at
            and f.t24_at-d.as_of_at<=interval '6 hours') d2_t24,
        (select count(*)::integer from private.structural_prior_forecasts_v1 s
          where s.ticket_event_id=f.ticket_event_id and s.point_in_time_validated
            and s.target_as_of_at<=f.t24_at and s.created_at<=f.t24_at) structural_t24
      from future_events f
    ), classified as (
      select t.*,
        case when t.d2_t48>0 then 'd2_long72_forward_predictions_v1'
             when t.structural_t48>0 then 'structural_prior_forecasts_v1'
             else 'none' end current_family_t48,
        case when t.d2_t24>0 then 'd2_long72_forward_predictions_v1'
             when t.structural_t24>0 then 'structural_prior_forecasts_v1'
             else 'none' end current_family_t24,
        (now()<t.t48_at and t.d2_t48=0) family_may_change_t48,
        (now()<t.t24_at and t.d2_t24=0) family_may_change_t24
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
            when c.current_family_t48='d2_long72_forward_predictions_v1' then coalesce((select d2_count from pool where cutoff_hours=48),0)
            when c.current_family_t48='structural_prior_forecasts_v1' then coalesce((select structural_count from pool where cutoff_hours=48),0)
            else 0 end,
          'current_d2_eligible_rows_t24',c.d2_t24,
          'current_structural_eligible_rows_t24',c.structural_t24,
          'current_family_t24',c.current_family_t24,
          'family_may_change_before_t24',c.family_may_change_t24,
          'current_family_global_pool_t24',case
            when c.current_family_t24='d2_long72_forward_predictions_v1' then coalesce((select d2_count from pool where cutoff_hours=24),0)
            when c.current_family_t24='structural_prior_forecasts_v1' then coalesce((select structural_count from pool where cutoff_hours=24),0)
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
