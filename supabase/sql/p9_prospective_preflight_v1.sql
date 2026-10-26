-- P9 prospective preflight v1
--
-- Goal: protect immutable T-48/T-24 windows before they open.
-- This is target-free and production-safe. It audits only whether future targets
-- already have the evidence needed to enter the frozen P9 prospective builder:
-- booking snapshots plus a genuinely persisted PIT incumbent before each cutoff.
--
-- Statuses:
-- READY                 evidence exists before the cutoff
-- WATCH_*               evidence is missing, but cutoff is still >48h away
-- CRITICAL_*            evidence is missing within 48h of cutoff
-- WINDOW_OPEN           cutoff is currently open (P9 workflow should capture)
-- CAPTURED              immutable P9 prediction already exists
-- MISSED_WINDOW         no prediction exists and cutoff+90m has passed

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

revoke all on function public.p9_prospective_preflight_v1(integer) from public,anon,authenticated;
grant execute on function public.p9_prospective_preflight_v1(integer) to service_role;
