-- P9 learner target-free incumbent catalog v1.
-- Contains no attendance outcomes. Used only after the 9/9 readiness gate to
-- freeze exact target/reference incumbent identities before label export.

create or replace function public.export_p9_learner_incumbent_catalog_v1(p_cutoff_hours integer)
returns jsonb
language plpgsql
security definer
set search_path='public','private'
as $function$
declare
  v_readiness jsonb;
  v_events integer;
  v_clubs integer;
begin
  if p_cutoff_hours not in (24,48) then raise exception 'P9_INCUMBENT_CATALOG_CUTOFF_REJECTED'; end if;

  v_readiness := public.p9_booking_curve_readiness_v1();
  v_events := coalesce((v_readiness#>>'{horizons,168.0,ready_events}')::integer,0);
  v_clubs := coalesce((v_readiness#>>'{horizons,168.0,ready_clubs}')::integer,0);
  if v_events < 9 or v_clubs < 3 then
    raise exception 'P9_LEARNER_GATE_CLOSED readiness_events=% readiness_clubs=%',v_events,v_clubs;
  end if;

  return (
    with event_rows as (
      select e.id as ticket_event_id,e.club_slug,e.home_team,e.away_team,e.kickoff_at,
             e.kickoff_at-make_interval(hours=>p_cutoff_hours) as analogous_cutoff_at
      from public.ticket_events e
      where private.normalize_structural_prior_competition_v1(e.competition)='Ekstraklasa'
        and e.kickoff_at < now()
    ), structural as (
      select sp.id as row_id,sp.ticket_event_id,'structural_prior_forecasts_v1'::text as source,
             sp.target_as_of_at as as_of_at,sp.created_at as persisted_at,
             sp.p50::double precision as p50,sp.stadium_capacity,sp.model_spec_id,
             sp.point_in_time_validated
      from private.structural_prior_forecasts_v1 sp
      join event_rows e on e.ticket_event_id=sp.ticket_event_id
      where sp.point_in_time_validated
        and sp.target_as_of_at <= e.analogous_cutoff_at
        and sp.created_at <= e.analogous_cutoff_at
    ), long72 as (
      select d.id as row_id,d.ticket_event_id,'d2_long72_forward_predictions_v1'::text as source,
             d.as_of_at,d.created_at as persisted_at,
             d.anchor_p50::double precision as p50,d.stadium_capacity,d.package_id as model_spec_id,
             true as point_in_time_validated
      from private.d2_long72_forward_predictions_v1 d
      join event_rows e on e.ticket_event_id=d.ticket_event_id
      where d.as_of_at <= e.analogous_cutoff_at
        and d.created_at <= e.analogous_cutoff_at
    ), incumbents as (
      select * from structural
      union all
      select * from long72
    )
    select jsonb_build_object(
      'version','p9-learner-incumbent-catalog-v1',
      'generated_at',now(),
      'cutoff_hours',p_cutoff_hours,
      'readiness_168_events',v_events,
      'readiness_168_clubs',v_clubs,
      'events',coalesce((select jsonb_agg(jsonb_build_object(
        'ticket_event_id',e.ticket_event_id,
        'club_slug',e.club_slug,
        'home_team',e.home_team,
        'away_team',e.away_team,
        'kickoff_at',e.kickoff_at,
        'analogous_cutoff_at',e.analogous_cutoff_at
      ) order by e.kickoff_at,e.ticket_event_id) from event_rows e),'[]'::jsonb),
      'incumbents',coalesce((select jsonb_agg(to_jsonb(i) order by i.ticket_event_id,i.source,i.as_of_at,i.persisted_at,i.row_id) from incumbents i),'[]'::jsonb),
      'attendance_values_included',false,
      'target_values_used',false,
      'production_activation_allowed',false,
      'live_adjustment',0,
      'production_change',false
    )
  );
end;
$function$;

revoke all on function public.export_p9_learner_incumbent_catalog_v1(integer) from public,anon,authenticated;
grant execute on function public.export_p9_learner_incumbent_catalog_v1(integer) to service_role;
