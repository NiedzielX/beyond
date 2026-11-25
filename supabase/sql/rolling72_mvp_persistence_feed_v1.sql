-- Read-only service feed for the fixed PERS lane. This is an additive projection
-- over immutable P0-4b source seals and P0-4c persistence ledgers.
create function public.get_rolling72_mvp_persistence_feed_v1(
 p_ticket_event_id bigint,
 p_lane_id text,
 p_before_bundle_id bigint default null,
 p_limit integer default 50,
 p_before_receipt_id bigint default null
) returns jsonb
language plpgsql stable security definer
set search_path='' set timezone='UTC' as $$
declare
 v_now timestamptz:=statement_timestamp();
 v_lane private.rolling72_mvp_persistence_v1_lane%rowtype;
 v_registry private.rolling72_mvp_research_v1_registry%rowtype;
 v_event public.ticket_events%rowtype;
 v_has_lane boolean:=false;
 v_has_fixture boolean:=false;
 v_binding jsonb;
 v_current_binding jsonb;
 v_fixture jsonb;
 v_latest_observation jsonb;
 v_latest_attempt record;
 v_observations_raw jsonb:='[]'::jsonb;
 v_observations jsonb:='[]'::jsonb;
 v_observation_more boolean:=false;
 v_observations_page jsonb;
 v_issues_raw jsonb:='[]'::jsonb;
 v_issues jsonb:='[]'::jsonb;
 v_issue_more boolean:=false;
 v_issues_page jsonb;
 v_status jsonb;
 v_scorecards jsonb:='[]'::jsonb;
 v_extra_scores jsonb:='{}'::jsonb;
 v_scorecard_scope jsonb;
 v_fixture_ids jsonb:='[]'::jsonb;
 v_status_text text;
begin
 if p_ticket_event_id is null or p_ticket_event_id<=0 then
  raise exception 'ROLLING72_PERSISTENCE_FEED_EVENT_REQUIRED';
 end if;
 if p_lane_id is distinct from 'rolling72-mvp-persistence-v1' then
  raise exception 'ROLLING72_PERSISTENCE_FEED_LANE_UNSUPPORTED';
 end if;
 if p_limit is null or p_limit not between 1 and 200 then
  raise exception 'ROLLING72_PERSISTENCE_FEED_LIMIT';
 end if;
 if p_before_bundle_id is not null and p_before_bundle_id<=0 then
  raise exception 'ROLLING72_PERSISTENCE_FEED_BUNDLE_CURSOR';
 end if;
 if p_before_receipt_id is not null and p_before_receipt_id<=0 then
  raise exception 'ROLLING72_PERSISTENCE_FEED_RECEIPT_CURSOR';
 end if;

 select * into v_lane from private.rolling72_mvp_persistence_v1_lane
  where lane_id=p_lane_id;
 v_has_lane:=found;
 v_status:=public.get_rolling72_mvp_persistence_v1_status();
 if v_status->>'read_watermark' is not null then
  v_now:=(v_status->>'read_watermark')::timestamptz;
 end if;

 select coalesce(jsonb_agg(r.ticket_event_id order by r.ticket_event_id),'[]'::jsonb)
  into v_fixture_ids
 from private.rolling72_mvp_research_v1_registry r
 where v_has_lane and r.lane_id=v_lane.source_lane_id;

 select jsonb_build_object(
  'lane_id',p_lane_id,'scope','FULL_LANE_COHORT',
  'read_watermark',v_now,'coverage_basis','SOURCE_BACKED_ELIGIBLE_CANDIDATES',
  'unissued_source_opportunities',(select coalesce(sum(greatest(
    coalesce((c->>'valid_pre_kickoff_opportunities')::bigint,0)-coalesce((c->>'numeric_forecasts')::bigint,0),0)),0)
    from jsonb_array_elements(coalesce(v_status->'scorecards','[]'::jsonb)) c),
  'unissued_source_opportunities_status','KNOWN',
  'candidate_denominator',coalesce(v_status->'candidate_denominator','{}'::jsonb),
  'fixture_ids',v_fixture_ids,'fixture_count',jsonb_array_length(v_fixture_ids),
  'issue_until',v_status->'issue_until','scoring_until',v_status->'scoring_until')
 into v_scorecard_scope;

 with event_scores as materialized (
  select p.horizon_hours,p.ticket_event_id,avg(l.absolute_error::numeric) event_mae
  from private.rolling72_mvp_persistence_v1_predictions p
  join private.rolling72_mvp_persistence_v1_labels l on l.prediction_id=p.id
  where p.status='ISSUED' and p.prediction is not null
  group by p.horizon_hours,p.ticket_event_id
 )
 select coalesce(jsonb_object_agg(h.horizon_hours::text,jsonb_build_object(
  'p90_absolute_error',(select percentile_cont(0.9) within group(order by l.absolute_error::double precision)
    from private.rolling72_mvp_persistence_v1_predictions p
    join private.rolling72_mvp_persistence_v1_labels l on l.prediction_id=p.id
    where p.horizon_hours=h.horizon_hours and p.status='ISSUED' and p.prediction is not null),
  'p90_event_mae',(select percentile_cont(0.9) within group(order by es.event_mae::double precision)
    from event_scores es where es.horizon_hours=h.horizon_hours),
  'worst_event_mae',(select es.event_mae from event_scores es where es.horizon_hours=h.horizon_hours
    order by es.event_mae desc,es.ticket_event_id limit 1),
  'worst_event_id',(select es.ticket_event_id from event_scores es where es.horizon_hours=h.horizon_hours
    order by es.event_mae desc,es.ticket_event_id limit 1)
  )),'{}'::jsonb)
 into v_extra_scores from (values(24),(48),(72)) h(horizon_hours);

 select coalesce(jsonb_agg(jsonb_build_object(
   'lane_id',p_lane_id,'target','public_available_total','method','persistence',
   'horizon_hours',(card->>'horizon_hours')::integer,
   'status',card->>'status','issues',coalesce((card->>'numeric_forecasts')::bigint,0),
   'labels',coalesce((card->>'labels')::bigint,0),
   'fixtures',coalesce((card->>'fixtures')::bigint,0),'clubs',coalesce((card->>'clubs')::bigint,0),
   'forecast_fixtures',coalesce(fc.forecast_fixtures,0),
   'forecast_clubs',coalesce(fc.forecast_clubs,0),
   'scored_fixtures',coalesce((card->>'fixtures')::bigint,0),
   'coverage_basis','SOURCE_BACKED_ELIGIBLE_CANDIDATES',
   'eligible_source_candidates',coalesce((horizon_row->>'eligible_source_candidates')::bigint,0),
   'source_outside_kickoff_candidates',coalesce((horizon_row->>'source_outside_candidates')::bigint,0),
   'refused_eligible_candidates',coalesce((horizon_row->>'refused_eligible')::bigint,0),
   'unattempted_eligible_candidates',coalesce((horizon_row->>'unattempted_eligible')::bigint,0),
   'unissued_source_opportunities',greatest(coalesce((horizon_row->>'eligible_source_candidates')::bigint,0)-coalesce((card->>'numeric_forecasts')::bigint,0),0),
   'forecast_coverage',case when card->'forecast_coverage'='null'::jsonb then null else (card->>'forecast_coverage')::numeric end,
   'scoring_coverage',case when card->'scoring_coverage'='null'::jsonb then null else (card->>'scoring_coverage')::numeric end,
   'valid_pre_kickoff_opportunities',coalesce((horizon_row->>'eligible_source_candidates')::bigint,0),
   'numeric_forecasts',coalesce((card->>'numeric_forecasts')::bigint,0),
   'matured_eligible_targets',coalesce((card->>'matured_eligible_targets')::bigint,0),
   'accepted_labels',coalesce((card->>'accepted_labels')::bigint,0),
   'future_targets',coalesce((card->>'future_targets')::bigint,0),
   'due_unscored_targets',coalesce((card->>'due_unscored_targets')::bigint,0),
   'outside_kickoff_targets',coalesce((card->>'outside_kickoff_targets')::bigint,0),
   'event_balanced_mae',case when card->'event_balanced_mae'='null'::jsonb then null else (card->>'event_balanced_mae')::numeric end,
   'event_balanced_bias',case when card->'event_balanced_bias'='null'::jsonb then null else (card->>'event_balanced_bias')::numeric end,
   'p90_absolute_error',case when v_extra_scores->(card->>'horizon_hours')->'p90_absolute_error'='null'::jsonb then null else (v_extra_scores->(card->>'horizon_hours')->>'p90_absolute_error')::numeric end,
   'p90_event_mae',case when v_extra_scores->(card->>'horizon_hours')->'p90_event_mae'='null'::jsonb then null else (v_extra_scores->(card->>'horizon_hours')->>'p90_event_mae')::numeric end,
   'worst_event_mae',case when v_extra_scores->(card->>'horizon_hours')->'worst_event_mae'='null'::jsonb then null else (v_extra_scores->(card->>'horizon_hours')->>'worst_event_mae')::numeric end,
   'worst_event_id',case when v_extra_scores->(card->>'horizon_hours')->'worst_event_id'='null'::jsonb then null else (v_extra_scores->(card->>'horizon_hours')->>'worst_event_id')::bigint end,
   'fallback_issues',0)
   order by (card->>'horizon_hours')::integer),'[]'::jsonb)
 into v_scorecards
 from jsonb_array_elements(coalesce(v_status->'scorecards','[]'::jsonb)) card
 left join lateral (
  select hrow as horizon_row
  from jsonb_array_elements(coalesce(v_status->'candidate_denominator'->'per_horizon','[]'::jsonb)) hrow
  where (hrow->>'horizon_hours')::integer=(card->>'horizon_hours')::integer
  limit 1
 ) h on true
 left join lateral (
  select count(distinct p.ticket_event_id) forecast_fixtures,
   count(distinct r.club_slug) forecast_clubs
  from private.rolling72_mvp_persistence_v1_predictions p
  join private.rolling72_mvp_research_v1_registry r on r.ticket_event_id=p.ticket_event_id
  where p.horizon_hours=(card->>'horizon_hours')::integer
   and p.status='ISSUED' and p.prediction is not null
 ) fc on true;

 select r.* into v_registry
 from private.rolling72_mvp_research_v1_registry r
 where r.ticket_event_id=p_ticket_event_id
  and v_has_lane and r.lane_id=v_lane.source_lane_id;
 v_has_fixture:=found;
 if v_has_fixture then
  v_binding:=v_registry.binding;
  select * into v_event from public.ticket_events e where e.id=p_ticket_event_id;
  if v_event.id is not null then
   select private.rolling72_mvp_research_v1_binding(to_jsonb(a),to_jsonb(e),to_jsonb(c))
    into v_current_binding
   from private.roboticket_admission_receipts_v2 a
   join public.ticket_events e on e.id=p_ticket_event_id
   join public.roboticket_clubs c on c.club_slug=e.club_slug
   where a.id=v_registry.admission_receipt_id;
  end if;
  v_fixture:=jsonb_build_object(
   'ticket_event_id',p_ticket_event_id,
   'club_slug',v_binding->>'club_slug','home',v_binding->>'home_team','away',v_binding->>'away_team',
   'competition',v_binding->>'competition','match_date',v_binding->>'match_date',
   'kickoff_at',v_binding->>'kickoff_at','provider',v_binding->>'provider',
   'external_event_id',v_binding->>'external_event_id','source_domain',v_binding->>'source_domain',
   'source_url',v_binding->>'source_url',
   'metadata_status',case when v_event.id is null then 'MISSING_CURRENT_METADATA'
    when v_current_binding is not distinct from v_binding then 'MATCH' else 'MISMATCH' end,
   'current_metadata',case when v_event.id is null then null else jsonb_build_object(
    'provider',v_event.provider,'external_event_id',v_event.external_event_id,
    'club_slug',v_event.club_slug,'home',v_event.home_team,'away',v_event.away_team,
    'competition',v_event.competition,'match_date',v_event.match_date,
    'kickoff_at',v_event.kickoff_at,'source_domain',v_event.source_domain,
    'source_url',v_event.source_url,'mapping_source',v_event.mapping_source,
    'mapping_confidence',v_event.mapping_confidence) end);

  select a.id,a.status,a.reason,a.known_at,a.snapshot_id into v_latest_attempt
  from private.rolling72_mvp_research_v1_attempts a
  where a.ticket_event_id=p_ticket_event_id and a.known_at<=v_now
  order by a.known_at desc,a.id desc limit 1;

  select jsonb_build_object(
   'receipt_id',s.id,'snapshot_id',s.snapshot_id,'captured_at',s.captured_at,'known_at',s.known_at,
   'available_total',s.available_total,'sector_count',s.sector_count,
   'scope_count_delta',case when s.transition_status in('COMPLETE','GAPPED')
    then coalesce((s.transition->>'added_sector_count')::integer,0)-coalesce((s.transition->>'removed_sector_count')::integer,0) else null end,
   'scope_status',case when coalesce((s.transition->>'added_sector_count')::integer,0)>0
      or coalesce((s.transition->>'removed_sector_count')::integer,0)>0
      or coalesce((s.transition->>'price_area_membership_change_count')::integer,0)>0 then 'CHANGED' else 'UNKNOWN' end,
   'source_scope_status',s.transition_status,
   'receipt_status','VALID',
   'source_status',case when v_latest_attempt.known_at>s.known_at and
     (v_latest_attempt.status not in('READY','NO_NEW_SOURCE') or
      (v_latest_attempt.status='READY' and not exists(select 1 from private.rolling72_mvp_research_v1_seals sx where sx.attempt_id=v_latest_attempt.id))
      ) then 'VALID_WITH_NEWER_FAILED_ATTEMPT' else 'VALID' end,
   'latest_attempt_status',v_latest_attempt.status,'latest_attempt_known_at',v_latest_attempt.known_at,
   'freshness_now',case when v_now-s.captured_at>interval '1 hour' then 'STALE' else 'CURRENT' end)
  into v_latest_observation
  from private.rolling72_mvp_research_v1_seals s
  where s.ticket_event_id=p_ticket_event_id and s.known_at<=v_now
  order by s.captured_at desc,s.snapshot_id desc limit 1;

  with selected as materialized (
   select s.id,s.snapshot_id,s.captured_at,s.known_at,s.available_total,s.sector_count,
    s.transition_status,s.transition
   from private.rolling72_mvp_research_v1_seals s
   where s.ticket_event_id=p_ticket_event_id and s.known_at<=v_now
    and (p_before_receipt_id is null or s.id<p_before_receipt_id)
   order by s.id desc limit p_limit+1
  )
  select coalesce(jsonb_agg(jsonb_build_object(
   'receipt_id',s.id,'snapshot_id',s.snapshot_id,'captured_at',s.captured_at,'known_at',s.known_at,
   'available_total',s.available_total,'sector_count',s.sector_count,
   'scope_count_delta',case when s.transition_status in('COMPLETE','GAPPED')
    then coalesce((s.transition->>'added_sector_count')::integer,0)-coalesce((s.transition->>'removed_sector_count')::integer,0) else null end,
   'scope_status',case when coalesce((s.transition->>'added_sector_count')::integer,0)>0
      or coalesce((s.transition->>'removed_sector_count')::integer,0)>0
      or coalesce((s.transition->>'price_area_membership_change_count')::integer,0)>0 then 'CHANGED' else 'UNKNOWN' end,
   'source_scope_status',s.transition_status,
   'receipt_status','VALID','status','VALID',
   'freshness_now',case when v_now-s.captured_at>interval '1 hour' then 'STALE' else 'CURRENT' end)
   order by s.id desc),'[]'::jsonb),count(*)>p_limit
   into v_observations_raw,v_observation_more from selected s;
  select coalesce(jsonb_agg(value order by ordinality),'[]'::jsonb)
   into v_observations from jsonb_array_elements(v_observations_raw) with ordinality
   where ordinality<=p_limit;
  select jsonb_build_object('cursor_in',p_before_receipt_id,
   'next_cursor',case when v_observation_more then (v_observations->(jsonb_array_length(v_observations)-1)->>'receipt_id')::bigint else null end,
   'has_more',v_observation_more,
   'first_receipt_id',case when jsonb_array_length(v_observations)>0 then (v_observations->0->>'receipt_id')::bigint else null end,
   'last_receipt_id',case when jsonb_array_length(v_observations)>0 then (v_observations->(jsonb_array_length(v_observations)-1)->>'receipt_id')::bigint else null end)
   into v_observations_page;

  with selected as materialized (
   select b.*,s.snapshot_id origin_snapshot_id,s.sector_count origin_sector_count,
    s.transition_status origin_transition_status
   from private.rolling72_mvp_persistence_v1_issue_bundles b
   join private.rolling72_mvp_research_v1_seals s on s.id=b.seal_id
   where b.ticket_event_id=p_ticket_event_id
    and (p_before_bundle_id is null or b.id<p_before_bundle_id)
   order by b.id desc limit p_limit+1
  ), issue_rows as (
   select b.id bundle_id,
    jsonb_build_object(
     'bundle_id',b.id,'lane_id',p_lane_id,'model_version',p_lane_id,
     'target_contract','public_available_total_with_scope_events_v1',
     'issue_receipt_id',b.seal_id,'issued_at',b.issued_at,
     'input_read_completed_at',b.read_completed_at,
     'source_age_seconds',b.source_age_seconds,
     'origin_observation',jsonb_build_object(
      'receipt_id',b.seal_id,'snapshot_id',b.origin_snapshot_id,
      'captured_at',b.source_captured_at,'known_at',b.source_known_at,
      'available_total',b.input_available_total,'sector_count',b.sector_count,
      'scope_count_delta',case when b.origin_transition_status in('COMPLETE','GAPPED')
       then coalesce((b.transition->>'added_sector_count')::integer,0)-coalesce((b.transition->>'removed_sector_count')::integer,0) else null end,
      'scope_status',case when coalesce((b.transition->>'added_sector_count')::integer,0)>0
       or coalesce((b.transition->>'removed_sector_count')::integer,0)>0
       or coalesce((b.transition->>'price_area_membership_change_count')::integer,0)>0 then 'CHANGED' else 'UNKNOWN' end,
      'source_status','VALID','receipt_status','VALID',
      'freshness_now',case when v_now-b.source_captured_at>interval '1 hour' then 'STALE' else 'CURRENT' end),
     'source_metadata',jsonb_build_object('family',v_lane.source_family,'unit',v_lane.unit,
      'scope_status',b.scope_status,'source_scope_status',b.origin_transition_status,'transition',b.transition,
      'membership_change_count',b.membership_change_count),
     'lineage',jsonb_build_object('parent_bundle_id',null,'parent_prefix_sha256',null),
     'scenario',jsonb_build_object('price','UNKNOWN','promotion','UNKNOWN','advertising','UNKNOWN',
      'pool_policy','UNKNOWN','pool_interpretation','LIMITED_PUBLIC_INVENTORY_PROXY'),
     'targets',(select coalesce(jsonb_agg(jsonb_build_object(
       'prediction_id',p.id,'horizon_hours',p.horizon_hours,'target_at',p.target_at,
       'status',case when p.status='OUTSIDE_KICKOFF' then 'OUTSIDE_KICKOFF'
         when l.prediction_id is not null then 'SCORED' when p.target_at>v_now then 'FUTURE' else 'DUE_UNSCORED' end,
       'source_status','VALID',
       'last_score_attempt_status',(select sa.status from private.rolling72_mvp_persistence_v1_score_attempts sa
        where sa.prediction_id=p.id order by sa.id desc limit 1),
       'methods',jsonb_build_array(jsonb_build_object('method','persistence','value',p.prediction,
        'predicted_delta_from_origin',case when p.prediction is null then null else p.prediction-b.input_available_total end,
        'status',p.status,'fallback_reason',null)),
       'label',case when l.id is null then null else jsonb_build_object(
        'receipt_id',l.source_seal_id,'snapshot_id',l.snapshot_id,'scored_at',l.scored_at,
        'captured_at',l.source_captured_at,'known_at',l.source_known_at,
        'age_seconds',l.target_age_seconds,'actual_available_total',l.actual_available_total,
        'origin_sector_count',b.sector_count,'target_sector_count',l.source_sector_count,
        'sector_count_delta',l.source_sector_count-b.sector_count,
        'membership_change_count',l.source_membership_change_count,
        'continuity','UNKNOWN','source_scope_status',l.source_scope_status,
        'source_transition',l.source_transition,
        'scope_status',case when coalesce((l.source_transition->>'added_sector_count')::integer,0)>0
          or coalesce((l.source_transition->>'removed_sector_count')::integer,0)>0
          or coalesce((l.source_transition->>'price_area_membership_change_count')::integer,0)>0 then 'CHANGED' else 'UNKNOWN' end,
        'source_family',v_lane.source_family,'source_unit',v_lane.unit,
        'signed_error',l.signed_error,'method_absolute_errors',jsonb_build_object('persistence',l.absolute_error)) end)
       order by p.horizon_hours),'[]'::jsonb)
      from private.rolling72_mvp_persistence_v1_predictions p
      left join private.rolling72_mvp_persistence_v1_labels l on l.prediction_id=p.id
      where p.bundle_id=b.id)) as issue
   from selected b
  )
  select coalesce(jsonb_agg(issue order by bundle_id desc),'[]'::jsonb),count(*)>p_limit
   into v_issues_raw,v_issue_more from issue_rows;
  select coalesce(jsonb_agg(value order by ordinality),'[]'::jsonb)
   into v_issues from jsonb_array_elements(v_issues_raw) with ordinality
   where ordinality<=p_limit;
  select jsonb_build_object('cursor_in',p_before_bundle_id,
   'next_cursor',case when v_issue_more then (v_issues->(jsonb_array_length(v_issues)-1)->>'bundle_id')::bigint else null end,
   'has_more',v_issue_more,
   'first_bundle_id',case when jsonb_array_length(v_issues)>0 then (v_issues->0->>'bundle_id')::bigint else null end,
   'last_bundle_id',case when jsonb_array_length(v_issues)>0 then (v_issues->(jsonb_array_length(v_issues)-1)->>'bundle_id')::bigint else null end)
   into v_issues_page;
 end if;

 v_status_text:=case when not v_has_fixture then 'EMPTY'
  when coalesce(v_issue_more,false) or coalesce(v_observation_more,false)
   or v_fixture->>'metadata_status'<>'MATCH'
   or v_latest_observation->>'source_status'='VALID_WITH_NEWER_FAILED_ATTEMPT' then 'PARTIAL'
  else 'OK' end;
 return jsonb_build_object(
  'schema_version','rolling72-investor-feed-v1','generated_at',v_now,'status',v_status_text,
  'fixtures',case when not v_has_fixture then '[]'::jsonb else jsonb_build_array(v_fixture||jsonb_build_object(
   'latest_observation',v_latest_observation,'latest_source_attempt',
    case when v_latest_attempt.status is null then null else jsonb_build_object('status',v_latest_attempt.status,
      'reason',v_latest_attempt.reason,'known_at',v_latest_attempt.known_at,'snapshot_id',v_latest_attempt.snapshot_id) end,
   'observations',v_observations,'observations_page',v_observations_page,
   'availability_lanes',jsonb_build_array(jsonb_build_object('lane_id',p_lane_id,'model_version',p_lane_id,
    'target_contract','public_available_total_with_scope_events_v1','issues',v_issues)),
   'attendance_lane',jsonb_build_object('status','UNAVAILABLE',
    'source','This PERS feed measures public available inventory only; it does not provide sales or attendance.',
    'issues','[]'::jsonb))) end,
  'issues_page',coalesce(v_issues_page,jsonb_build_object('cursor_in',p_before_bundle_id,'next_cursor',null,
   'has_more',false,'first_bundle_id',null,'last_bundle_id',null)),
  'scorecard_scope',v_scorecard_scope,'scorecards',v_scorecards);
end $$;

revoke all on function public.get_rolling72_mvp_persistence_feed_v1(bigint,text,bigint,integer,bigint)
 from public,anon,authenticated;
grant execute on function public.get_rolling72_mvp_persistence_feed_v1(bigint,text,bigint,integer,bigint)
 to service_role;
