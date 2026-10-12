-- Verified absence registry v2: club-facing Polish copy.

update public.sporting_verified_absences
set reason='operacja stopy / rehabilitacja',
    reported_recovery='3–4 miesiące',
    updated_at=now()
where team_key=public.sporting_canonical_team_v1('Lech Poznań')
  and player_name='João Moutinho'
  and is_active=true;

create or replace function public.refresh_verified_absence_context_v1()
returns integer
language plpgsql
security invoker
set search_path=public,pg_temp
as $$
declare
  v_count integer := 0;
begin
  with applicable as (
    select e.id as ticket_event_id,a.id as absence_id,a.team_name,a.player_name,
      a.absence_status,a.reason,a.reported_recovery,a.source_name,a.source_url,
      a.source_published_at,a.confidence,a.absence_certainty,a.novelty,a.player_salience,
      a.valid_from,a.valid_until,a.review_due_at
    from public.ticket_events e
    join public.sporting_verified_absences a
      on a.is_active
     and a.valid_from <= e.kickoff_at
     and (a.valid_until is null or a.valid_until > e.kickoff_at)
     and a.team_key in (
       public.sporting_canonical_team_v1(e.home_team),
       public.sporting_canonical_team_v1(e.away_team)
     )
    where e.kickoff_at >= now()-interval '3 hours'
      and e.kickoff_at < now()+interval '120 days'
  ), grouped as (
    select ticket_event_id,
      min(confidence) as confidence,
      max(source_published_at) as source_observed_at,
      string_agg(
        format('%s: %s — %s; %s%s',
          team_name,
          player_name,
          case when absence_status='confirmed_unavailable' then 'potwierdzona absencja' else replace(absence_status,'_',' ') end,
          reason,
          case when reported_recovery is not null then format(' (szacowany powrót: %s)',reported_recovery) else '' end
        ),
        ' | ' order by team_name,player_name
      ) as absence_summary,
      jsonb_agg(
        jsonb_build_object(
          'absence_id',absence_id,'team',team_name,'player',player_name,'status',absence_status,
          'reason',reason,'reported_recovery',reported_recovery,'source_name',source_name,
          'source_url',source_url,'source_published_at',source_published_at,
          'absence_certainty',absence_certainty,'novelty',novelty,'player_salience',player_salience,
          'valid_from',valid_from,'valid_until',valid_until,'review_due_at',review_due_at
        ) order by team_name,player_name
      ) as absences,
      bool_and(player_salience is not null) as all_salience_supported
    from applicable
    group by ticket_event_id
  )
  insert into public.event_context_observations(
    ticket_event_id,feature_key,observed_at,numeric_value,text_value,normalized_score,
    source_name,source_url,source_observed_at,confidence,source_record_key,metadata
  )
  select ticket_event_id,'sport.absence_impact',now(),null,
    absence_summary || '. Na razie nie oceniamy wpływu tej absencji na popyt bez potwierdzonej istotności zawodnika, pewności absencji i jej aktualności.',
    null,'Beyond verified absence register',null,source_observed_at,confidence,
    format('verified-absence-register:v01:event:%s',ticket_event_id),
    jsonb_build_object(
      'verified_absences',absences,
      'coverage_complete',false,
      'registry_status','verified_manual_input_automated_propagation',
      'player_importance_scored',all_salience_supported,
      'scoring_status',case when all_salience_supported then 'eligible_for_separate_demand_shock_review' else 'raw_verified_absence_only' end,
      'production_impact','none_context_research_only',
      'coverage_note','Register propagates known verified absences only. Missing player is unknown, not confirmed available.'
    )
  from grouped
  on conflict (ticket_event_id,feature_key,source_name,source_record_key)
  do update set observed_at=excluded.observed_at,numeric_value=excluded.numeric_value,
    text_value=excluded.text_value,source_observed_at=excluded.source_observed_at,
    confidence=excluded.confidence,metadata=excluded.metadata;

  get diagnostics v_count = row_count;
  return v_count;
end;
$$;

revoke all on function public.refresh_verified_absence_context_v1() from public,anon,authenticated;
grant execute on function public.refresh_verified_absence_context_v1() to service_role;

select public.refresh_verified_absence_context_v1();
