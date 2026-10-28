-- Beyond Ticketing — Trajectory Research Event Bundle v1
-- Applied live: 2026-10-28
-- Research-only helper for frozen Lane A/Lane B development.
-- It exposes raw historical event evidence to service_role only.

create or replace function public.get_trajectory_research_event_bundle_v1(
  p_ticket_event_id bigint
)
returns jsonb
language plpgsql
security definer
set search_path = public, private
as $$
declare
  v_event public.ticket_events%rowtype;
  v_outcome public.ticket_event_outcomes%rowtype;
  v_payload jsonb;
begin
  select * into v_event
  from public.ticket_events
  where id = p_ticket_event_id;

  if not found then
    raise exception 'TRAJECTORY_RESEARCH_EVENT_NOT_FOUND';
  end if;

  select * into v_outcome
  from public.ticket_event_outcomes
  where ticket_event_id = p_ticket_event_id;

  v_payload := jsonb_build_object(
    'version','trajectory-research-event-bundle-v1',
    'ticket_event_id',v_event.id,
    'club_slug',v_event.club_slug,
    'kickoff_at',v_event.kickoff_at,
    'competition',v_event.competition,
    'snapshots',coalesce((
      select jsonb_agg(
        jsonb_build_object(
          'snapshot_id',s.id,
          'captured_at',s.captured_at,
          'available_total',s.available_total,
          'sector_count',s.sector_count
        ) order by s.captured_at,s.id
      )
      from public.snapshots s
      where s.ticket_event_id=v_event.id
        and s.captured_at < v_event.kickoff_at
    ),'[]'::jsonb),
    'sectors',coalesce((
      select jsonb_agg(
        jsonb_build_object(
          'snapshot_id',si.snapshot_id,
          'sector',si.sector,
          'available',si.available
        ) order by si.snapshot_id,si.sector
      )
      from public.sector_inventory si
      join public.snapshots s on s.id=si.snapshot_id
      where s.ticket_event_id=v_event.id
        and s.captured_at < v_event.kickoff_at
    ),'[]'::jsonb),
    'structural_priors',coalesce((
      select jsonb_agg(
        jsonb_build_object(
          'source_prior_id',p.id,
          'horizon',p.horizon,
          'requested_as_of_at',p.target_as_of_at,
          'target_as_of_at',p.target_as_of_at,
          'kickoff_at',p.kickoff_at,
          'model_spec_id',p.model_spec_id,
          'model_family',p.model_family,
          'feature_contract',p.feature_contract,
          'p50',p.p50,
          'p10',p.p10,
          'p90',p.p90,
          'stadium_capacity',p.stadium_capacity,
          'point_in_time_validated',p.point_in_time_validated,
          'generated_at',p.generated_at
        ) order by p.target_as_of_at,p.generated_at,p.id
      )
      from private.structural_prior_forecasts_v1 p
      where p.ticket_event_id=v_event.id
    ),'[]'::jsonb),
    'outcome',case when v_outcome.ticket_event_id is null then null else jsonb_build_object(
      'actual_attendance',v_outcome.actual_attendance,
      'attendance_definition',v_outcome.attendance_definition,
      'source_name',v_outcome.source_name,
      'confirmed_at',v_outcome.confirmed_at
    ) end,
    'production_change',false
  );

  return v_payload;
end;
$$;

revoke all on function public.get_trajectory_research_event_bundle_v1(bigint)
  from public, anon, authenticated;
grant execute on function public.get_trajectory_research_event_bundle_v1(bigint)
  to service_role;
