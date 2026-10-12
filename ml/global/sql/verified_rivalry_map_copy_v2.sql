-- Verified rivalry map v2: club-facing Polish copy.

create or replace function public.refresh_verified_rivalry_context_v1()
returns integer
language plpgsql
security invoker
set search_path=public,pg_temp
as $$
declare
  v_count integer := 0;
begin
  insert into public.event_context_observations(
    ticket_event_id,feature_key,observed_at,numeric_value,text_value,normalized_score,
    source_name,source_url,source_observed_at,confidence,source_record_key,metadata
  )
  select e.id,'sport.rivalry_opponent',now(),1,
    format('%s – %s: %s; rywalizacja potwierdzona w zweryfikowanej mapie Beyond.',
      e.home_team,e.away_team,r.rivalry_type),
    null,'Beyond verified rivalry map',r.source_url,r.verified_at,r.confidence,
    format('rivalry-map:v01:event:%s:relation:%s',e.id,r.id),
    jsonb_build_object(
      'relation_id',r.id,'rivalry_flag',true,'rivalry_type',r.rivalry_type,
      'verification_source',r.source_name,'verification_date',r.verified_at,
      'coverage_note','Only configured verified rivalries are emitted. Missing relation is unknown, not a negative rivalry label.',
      'opponent_attractiveness_status','not_scored_by_rivalry_map',
      'scoring_status','raw_verified_rivalry_not_model_scored',
      'production_impact','none_context_research_only'
    )
  from public.ticket_events e
  join public.sporting_rivalry_relations r
    on r.is_active
   and least(public.sporting_canonical_team_v1(e.home_team),public.sporting_canonical_team_v1(e.away_team))=r.team_a_key
   and greatest(public.sporting_canonical_team_v1(e.home_team),public.sporting_canonical_team_v1(e.away_team))=r.team_b_key
  where e.kickoff_at >= now()-interval '3 hours'
    and e.kickoff_at < now()+interval '90 days'
  on conflict (ticket_event_id,feature_key,source_name,source_record_key)
  do update set observed_at=excluded.observed_at,numeric_value=excluded.numeric_value,
    text_value=excluded.text_value,source_url=excluded.source_url,
    source_observed_at=excluded.source_observed_at,confidence=excluded.confidence,
    metadata=excluded.metadata;

  get diagnostics v_count = row_count;
  return v_count;
end;
$$;

revoke all on function public.refresh_verified_rivalry_context_v1() from public,anon,authenticated;
grant execute on function public.refresh_verified_rivalry_context_v1() to service_role;

select public.refresh_verified_rivalry_context_v1();
