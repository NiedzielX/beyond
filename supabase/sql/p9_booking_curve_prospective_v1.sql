-- P9 Booking Curve prospective validation v1.
-- Scientific contract: ml/P9_BOOKING_CURVE_PROSPECTIVE_PRECOMMIT_V1.md
-- Uses the already-frozen p9-knn-median-residual-k5-v1 learner.
-- No production activation.

create or replace function public.export_p9_prospective_inputs_v1(p_cutoff_hours integer)
returns jsonb
language plpgsql
stable
security definer
set search_path='public','private'
as $function$
declare
  v_cutoff integer := p_cutoff_hours;
begin
  if v_cutoff not in (24,48) then raise exception 'P9_PROSPECTIVE_CUTOFF_REJECTED'; end if;
  return (
    with candidate_targets as (
      select e.id ticket_event_id,e.club_slug,e.home_team,e.away_team,e.competition,e.kickoff_at,
             e.kickoff_at-make_interval(hours=>v_cutoff) target_as_of_at
      from public.ticket_events e
      where private.normalize_structural_prior_competition_v1(e.competition)='Ekstraklasa'
        and e.kickoff_at>now()
        and now()>=e.kickoff_at-make_interval(hours=>v_cutoff)
        and now()<=e.kickoff_at-make_interval(hours=>v_cutoff)+interval '90 minutes'
        and not exists(select 1 from public.ticket_event_outcomes o where o.ticket_event_id=e.id and o.actual_attendance is not null)
        and not exists(select 1 from private.p9_booking_curve_prospective_predictions_v1 p where p.ticket_event_id=e.id and p.cutoff_hours=v_cutoff)
        and exists(
          select 1 from public.snapshots s
          where s.ticket_event_id=e.id and s.available_total is not null and s.available_total>=0
            and s.captured_at<e.kickoff_at and s.captured_at<=e.kickoff_at-make_interval(hours=>v_cutoff)
        )
    ), target_payload as (
      select t.*,
             coalesce((select jsonb_agg(jsonb_build_object('snapshot_id',s.id,'captured_at',s.captured_at,'available_total',s.available_total) order by s.captured_at,s.id)
                       from public.snapshots s
                       where s.ticket_event_id=t.ticket_event_id and s.available_total is not null and s.available_total>=0
                         and s.captured_at<t.kickoff_at and s.captured_at<=t.target_as_of_at),'[]'::jsonb) target_snapshots,
             coalesce((select jsonb_agg(row_data order by (row_data->>'source')::text,(row_data->>'as_of_at')::timestamptz,(row_data->>'row_id')::bigint)
                       from (
                         select jsonb_build_object('source','structural_prior_forecasts_v1','row_id',sp.id,'as_of_at',sp.target_as_of_at,'persisted_at',sp.created_at,'p50',sp.p50,'model_spec_id',sp.model_spec_id,'point_in_time_validated',sp.point_in_time_validated) row_data
                         from private.structural_prior_forecasts_v1 sp
                         where sp.ticket_event_id=t.ticket_event_id and sp.point_in_time_validated
                           and sp.target_as_of_at<=t.target_as_of_at and sp.created_at<=t.target_as_of_at
                         union all
                         select jsonb_build_object('source','d2_long72_forward_predictions_v1','row_id',d.id,'as_of_at',d.as_of_at,'persisted_at',d.created_at,'p50',d.anchor_p50,'model_spec_id',d.package_id,'point_in_time_validated',true) row_data
                         from private.d2_long72_forward_predictions_v1 d
                         where d.ticket_event_id=t.ticket_event_id
                           and d.as_of_at<=t.target_as_of_at and d.created_at<=t.target_as_of_at
                       ) incumbents),'[]'::jsonb) persisted_incumbents
      from candidate_targets t
    ), reference_catalog as (
      select r.id ticket_event_id,r.club_slug,r.home_team,r.away_team,r.kickoff_at,
             coalesce((select jsonb_agg(jsonb_build_object('snapshot_id',rs.id,'captured_at',rs.captured_at,'available_total',rs.available_total) order by rs.captured_at,rs.id)
                       from public.snapshots rs
                       where rs.ticket_event_id=r.id and rs.available_total is not null and rs.available_total>=0 and rs.captured_at<r.kickoff_at),'[]'::jsonb) snapshots
      from public.ticket_events r
      where private.normalize_structural_prior_competition_v1(r.competition)='Ekstraklasa'
        and r.kickoff_at<now()
        and exists(select 1 from public.snapshots rs0 where rs0.ticket_event_id=r.id and rs0.available_total is not null and rs0.available_total>=0 and rs0.captured_at<r.kickoff_at)
    )
    select jsonb_build_object(
      'version','p9a-booking-curve-inputs-v1',
      'execution_mode','prospective',
      'generated_at',now(),
      'cutoff_hours',v_cutoff,
      'prediction_window_minutes',90,
      'canonical_hours',jsonb_build_array(168,144,120,96,72,60,48,36,24,18,12,6),
      'max_interpolation_gap_hours',12,
      'minimum_overlap_points',3,
      'inventory_interpretation','demand_proxy_not_confirmed_sales',
      'independent_unit','ticket_event',
      'target_values_used',false,
      'post_cutoff_target_snapshots_exported',false,
      'reference_catalog_semantics','freeze harness must use only reference kickoff < target_as_of_at and exclude self',
      'incumbent_rule','only rows persisted at or before exact target_as_of_at are exposed',
      'production_change',false,
      'targets',coalesce((select jsonb_agg(jsonb_build_object(
        'ticket_event_id',p.ticket_event_id,'club_slug',p.club_slug,'home_team',p.home_team,'away_team',p.away_team,
        'competition',p.competition,'kickoff_at',p.kickoff_at,'target_as_of_at',p.target_as_of_at,
        'target_snapshots',p.target_snapshots,'persisted_incumbents',p.persisted_incumbents
      ) order by p.kickoff_at,p.ticket_event_id) from target_payload p),'[]'::jsonb),
      'reference_catalog',coalesce((select jsonb_agg(jsonb_build_object(
        'ticket_event_id',r.ticket_event_id,'club_slug',r.club_slug,'home_team',r.home_team,'away_team',r.away_team,
        'kickoff_at',r.kickoff_at,'snapshots',r.snapshots
      ) order by r.kickoff_at,r.ticket_event_id) from reference_catalog r),'[]'::jsonb)
    )
  );
end;
$function$;

create or replace function public.export_p9_prospective_incumbent_catalog_v1(p_cutoff_hours integer)
returns jsonb
language plpgsql
stable
security definer
set search_path='public','private'
as $function$
declare
  v_cutoff integer := p_cutoff_hours;
begin
  if v_cutoff not in (24,48) then raise exception 'P9_PROSPECTIVE_CUTOFF_REJECTED'; end if;
  return (
    with eligible_targets as (
      select e.id
      from public.ticket_events e
      where private.normalize_structural_prior_competition_v1(e.competition)='Ekstraklasa'
        and e.kickoff_at>now()
        and now()>=e.kickoff_at-make_interval(hours=>v_cutoff)
        and now()<=e.kickoff_at-make_interval(hours=>v_cutoff)+interval '90 minutes'
        and not exists(select 1 from public.ticket_event_outcomes o where o.ticket_event_id=e.id and o.actual_attendance is not null)
        and not exists(select 1 from private.p9_booking_curve_prospective_predictions_v1 p where p.ticket_event_id=e.id and p.cutoff_hours=v_cutoff)
    ), event_rows as (
      select e.id ticket_event_id,e.club_slug,e.home_team,e.away_team,e.kickoff_at,
             e.kickoff_at-make_interval(hours=>v_cutoff) analogous_cutoff_at,
             (e.id in (select id from eligible_targets)) as is_target
      from public.ticket_events e
      where private.normalize_structural_prior_competition_v1(e.competition)='Ekstraklasa'
        and (e.kickoff_at<now() or e.id in (select id from eligible_targets))
    ), structural as (
      select sp.id row_id,sp.ticket_event_id,'structural_prior_forecasts_v1'::text source,
             sp.target_as_of_at as as_of_at,sp.created_at persisted_at,sp.p50::double precision p50,
             sp.stadium_capacity,sp.model_spec_id,sp.point_in_time_validated
      from private.structural_prior_forecasts_v1 sp
      join event_rows e on e.ticket_event_id=sp.ticket_event_id
      where sp.point_in_time_validated and sp.target_as_of_at<=e.analogous_cutoff_at and sp.created_at<=e.analogous_cutoff_at
    ), long72 as (
      select d.id row_id,d.ticket_event_id,'d2_long72_forward_predictions_v1'::text source,
             d.as_of_at,d.created_at persisted_at,d.anchor_p50::double precision p50,
             d.stadium_capacity,d.package_id model_spec_id,true point_in_time_validated
      from private.d2_long72_forward_predictions_v1 d
      join event_rows e on e.ticket_event_id=d.ticket_event_id
      where d.as_of_at<=e.analogous_cutoff_at and d.created_at<=e.analogous_cutoff_at
    ), incumbents as (select * from structural union all select * from long72)
    select jsonb_build_object(
      'version','p9-prospective-incumbent-catalog-v1',
      'generated_at',now(),
      'cutoff_hours',v_cutoff,
      'target_event_ids',coalesce((select jsonb_agg(id order by id) from eligible_targets),'[]'::jsonb),
      'events',coalesce((select jsonb_agg(jsonb_build_object(
        'ticket_event_id',e.ticket_event_id,'club_slug',e.club_slug,'home_team',e.home_team,'away_team',e.away_team,
        'kickoff_at',e.kickoff_at,'analogous_cutoff_at',e.analogous_cutoff_at,'is_target',e.is_target
      ) order by e.kickoff_at,e.ticket_event_id) from event_rows e),'[]'::jsonb),
      'incumbents',coalesce((select jsonb_agg(to_jsonb(i) order by i.ticket_event_id,i.source,i.as_of_at,i.persisted_at,i.row_id) from incumbents i),'[]'::jsonb),
      'attendance_values_included',false,
      'target_values_used',false,
      'production_change',false
    )
  );
end;
$function$;

create or replace function public.export_p9_prospective_reference_outcomes_v1()
returns jsonb
language sql
stable
security definer
set search_path='public','private'
as $function$
with completed as (
  select e.id ticket_event_id,e.kickoff_at
  from public.ticket_events e
  where private.normalize_structural_prior_competition_v1(e.competition)='Ekstraklasa' and e.kickoff_at<now()
), outcomes as (
  select o.ticket_event_id,o.actual_attendance,o.attendance_definition,o.source_name,o.source_url,o.confirmed_at
  from public.ticket_event_outcomes o
  join completed e on e.ticket_event_id=o.ticket_event_id
  where o.actual_attendance is not null and o.confirmed_at is not null and o.confirmed_at>=e.kickoff_at
)
select jsonb_build_object(
  'version','p9-prospective-reference-outcomes-v1',
  'generated_at',now(),
  'attendance',coalesce((select jsonb_agg(to_jsonb(o) order by o.ticket_event_id) from outcomes o),'[]'::jsonb),
  'target_attendance_included',false,
  'production_change',false
);
$function$;

create table if not exists private.p9_booking_curve_prospective_predictions_v1 (
  id bigint generated always as identity primary key,
  ticket_event_id bigint not null references public.ticket_events(id),
  cutoff_hours integer not null,
  target_as_of_at timestamptz not null,
  predicted_at timestamptz not null default clock_timestamp(),
  target_at timestamptz not null,
  stadium_capacity integer not null,
  incumbent_source text not null,
  incumbent_row_id bigint not null,
  incumbent_p50 double precision not null,
  trajectory_residual double precision not null,
  challenger_p50 double precision not null,
  selected_neighbor_event_ids bigint[] not null,
  residual_reference_event_ids bigint[] not null,
  reference_incumbent_row_ids bigint[] not null,
  p9a_manifest_sha256 text not null,
  support_manifest_sha256 text not null,
  reference_outcomes_sha256 text not null,
  prediction_identity_sha256 text not null,
  source_version text not null,
  github_sha text,
  created_at timestamptz not null default clock_timestamp(),
  production_change boolean not null default false,
  constraint p9_prospective_cutoff check (cutoff_hours in (24,48)),
  constraint p9_prospective_capacity check (stadium_capacity>0),
  constraint p9_prospective_anchor check (incumbent_p50>=0 and incumbent_p50<=stadium_capacity),
  constraint p9_prospective_challenger check (challenger_p50>=0 and challenger_p50<=stadium_capacity),
  constraint p9_prospective_time_order check (predicted_at>=target_as_of_at and predicted_at<=target_as_of_at+interval '90 minutes' and predicted_at<target_at),
  constraint p9_prospective_refs check (cardinality(residual_reference_event_ids)>=3 and cardinality(reference_incumbent_row_ids)=cardinality(residual_reference_event_ids)),
  constraint p9_prospective_sha1 check (p9a_manifest_sha256 ~ '^[0-9a-f]{64}$'),
  constraint p9_prospective_sha2 check (support_manifest_sha256 ~ '^[0-9a-f]{64}$'),
  constraint p9_prospective_sha3 check (reference_outcomes_sha256 ~ '^[0-9a-f]{64}$'),
  constraint p9_prospective_sha4 check (prediction_identity_sha256 ~ '^[0-9a-f]{64}$'),
  constraint p9_prospective_prod check (production_change=false),
  unique(ticket_event_id,cutoff_hours)
);

create table if not exists private.p9_booking_curve_prospective_scores_v1 (
  prediction_id bigint primary key references private.p9_booking_curve_prospective_predictions_v1(id),
  ticket_event_id bigint not null references public.ticket_events(id),
  cutoff_hours integer not null,
  actual_attendance integer not null,
  attendance_confirmed_at timestamptz not null,
  incumbent_abs_error double precision not null,
  challenger_abs_error double precision not null,
  delta_abs_error double precision not null,
  incumbent_bias double precision not null,
  challenger_bias double precision not null,
  improved boolean not null,
  scored_at timestamptz not null default clock_timestamp(),
  production_change boolean not null default false,
  constraint p9_prospective_score_time check (attendance_confirmed_at>(select p.predicted_at from private.p9_booking_curve_prospective_predictions_v1 p where p.id=prediction_id)),
  constraint p9_prospective_score_prod check (production_change=false)
);

create or replace function private.reject_p9_prospective_mutation_v1()
returns trigger language plpgsql security definer set search_path='public','private'
as $function$
begin raise exception 'P9_PROSPECTIVE_IMMUTABLE'; end;$function$;

drop trigger if exists p9_prospective_predictions_immutable_v1 on private.p9_booking_curve_prospective_predictions_v1;
create trigger p9_prospective_predictions_immutable_v1 before update or delete on private.p9_booking_curve_prospective_predictions_v1 for each row execute function private.reject_p9_prospective_mutation_v1();
drop trigger if exists p9_prospective_scores_immutable_v1 on private.p9_booking_curve_prospective_scores_v1;
create trigger p9_prospective_scores_immutable_v1 before update or delete on private.p9_booking_curve_prospective_scores_v1 for each row execute function private.reject_p9_prospective_mutation_v1();

create or replace function public.insert_p9_booking_curve_prospective_predictions_v1(p_payload jsonb,p_github_sha text default null)
returns jsonb
language plpgsql
security definer
set search_path='public','private'
as $function$
declare
  v_row jsonb;
  v_now timestamptz:=clock_timestamp();
  v_inserted integer:=0;
  v_event public.ticket_events%rowtype;
  v_cutoff integer;
  v_target_as_of timestamptz;
begin
  if p_payload is null or jsonb_typeof(p_payload)<>'object' then raise exception 'P9_PROSPECTIVE_PAYLOAD_REQUIRED'; end if;
  if coalesce((p_payload->>'target_values_used')::boolean,true) then raise exception 'P9_PROSPECTIVE_TARGET_VALUES_USED'; end if;
  if coalesce((p_payload->>'production_change')::boolean,true) then raise exception 'P9_PROSPECTIVE_PRODUCTION_CHANGE_REJECTED'; end if;
  if p_payload->>'precommit_id'<>'p9-knn-median-residual-k5-v1' then raise exception 'P9_PROSPECTIVE_PRECOMMIT_MISMATCH'; end if;
  if jsonb_typeof(p_payload->'predictions')<>'array' then raise exception 'P9_PROSPECTIVE_PREDICTIONS_ARRAY_REQUIRED'; end if;
  if lower(p_payload::text) ~ '"(actual_attendance|target_attendance|target_outcome)"\s*:' then raise exception 'P9_PROSPECTIVE_TARGET_KEY_REJECTED'; end if;

  for v_row in select value from jsonb_array_elements(p_payload->'predictions')
  loop
    select * into v_event from public.ticket_events where id=(v_row->>'ticket_event_id')::bigint;
    if not found then raise exception 'P9_PROSPECTIVE_EVENT_NOT_FOUND'; end if;
    v_cutoff:=(v_row->>'cutoff_hours')::integer;
    if v_cutoff not in (24,48) then raise exception 'P9_PROSPECTIVE_CUTOFF_REJECTED'; end if;
    v_target_as_of:=v_event.kickoff_at-make_interval(hours=>v_cutoff);
    if abs(extract(epoch from ((v_row->>'target_as_of_at')::timestamptz-v_target_as_of)))>1 then raise exception 'P9_PROSPECTIVE_TARGET_ASOF_MISMATCH'; end if;
    if v_now<v_target_as_of or v_now>v_target_as_of+interval '90 minutes' then raise exception 'P9_PROSPECTIVE_PERSISTENCE_WINDOW_CLOSED event=% cutoff=%',v_event.id,v_cutoff; end if;
    if v_now>=v_event.kickoff_at then raise exception 'P9_PROSPECTIVE_TARGET_ALREADY_STARTED'; end if;
    if exists(select 1 from public.ticket_event_outcomes o where o.ticket_event_id=v_event.id and o.actual_attendance is not null) then raise exception 'P9_PROSPECTIVE_TARGET_OUTCOME_ALREADY_KNOWN'; end if;

    insert into private.p9_booking_curve_prospective_predictions_v1(
      ticket_event_id,cutoff_hours,target_as_of_at,predicted_at,target_at,stadium_capacity,
      incumbent_source,incumbent_row_id,incumbent_p50,trajectory_residual,challenger_p50,
      selected_neighbor_event_ids,residual_reference_event_ids,reference_incumbent_row_ids,
      p9a_manifest_sha256,support_manifest_sha256,reference_outcomes_sha256,prediction_identity_sha256,
      source_version,github_sha,production_change
    ) values (
      v_event.id,v_cutoff,v_target_as_of,v_now,v_event.kickoff_at,(v_row->>'stadium_capacity')::integer,
      v_row->>'incumbent_source',(v_row->>'incumbent_row_id')::bigint,(v_row->>'incumbent_p50')::double precision,
      (v_row->>'trajectory_residual')::double precision,(v_row->>'challenger_p50')::double precision,
      array(select jsonb_array_elements_text(v_row->'selected_neighbor_event_ids')::bigint),
      array(select jsonb_array_elements_text(v_row->'residual_reference_event_ids')::bigint),
      array(select jsonb_array_elements_text(v_row->'reference_incumbent_row_ids')::bigint),
      v_row->>'p9a_manifest_sha256',v_row->>'support_manifest_sha256',v_row->>'reference_outcomes_sha256',
      v_row->>'prediction_identity_sha256',v_row->>'source_version',nullif(trim(p_github_sha),''),false
    ) on conflict(ticket_event_id,cutoff_hours) do nothing;
    if found then v_inserted:=v_inserted+1; end if;
  end loop;

  return jsonb_build_object(
    'version','p9-booking-curve-prospective-insert-v1',
    'inserted_predictions',v_inserted,
    'prediction_rows_after',(select count(*) from private.p9_booking_curve_prospective_predictions_v1),
    'independent_events_after',(select count(distinct ticket_event_id) from private.p9_booking_curve_prospective_predictions_v1),
    'target_values_used',false,'production_change',false
  );
end;
$function$;

create or replace function public.score_p9_booking_curve_prospective_completed_v1()
returns jsonb
language plpgsql
security definer
set search_path='public','private'
as $function$
declare v_inserted integer:=0;
begin
  with eligible as (
    select p.id prediction_id,p.ticket_event_id,p.cutoff_hours,p.incumbent_p50,p.challenger_p50,p.predicted_at,
           o.actual_attendance,o.confirmed_at
    from private.p9_booking_curve_prospective_predictions_v1 p
    join public.ticket_event_outcomes o on o.ticket_event_id=p.ticket_event_id
      and o.actual_attendance is not null and o.confirmed_at is not null and o.confirmed_at>p.predicted_at
  ), ins as (
    insert into private.p9_booking_curve_prospective_scores_v1(
      prediction_id,ticket_event_id,cutoff_hours,actual_attendance,attendance_confirmed_at,
      incumbent_abs_error,challenger_abs_error,delta_abs_error,incumbent_bias,challenger_bias,improved,production_change
    )
    select e.prediction_id,e.ticket_event_id,e.cutoff_hours,e.actual_attendance,e.confirmed_at,
           abs(e.incumbent_p50-e.actual_attendance),abs(e.challenger_p50-e.actual_attendance),
           abs(e.challenger_p50-e.actual_attendance)-abs(e.incumbent_p50-e.actual_attendance),
           e.incumbent_p50-e.actual_attendance,e.challenger_p50-e.actual_attendance,
           abs(e.challenger_p50-e.actual_attendance)<abs(e.incumbent_p50-e.actual_attendance),false
    from eligible e on conflict(prediction_id) do nothing returning 1
  ) select count(*) into v_inserted from ins;
  return jsonb_build_object('version','p9-booking-curve-prospective-score-v1','inserted_scores',v_inserted,'score_rows_after',(select count(*) from private.p9_booking_curve_prospective_scores_v1),'production_change',false);
end;
$function$;

create or replace function public.p9_booking_curve_prospective_summary_v1()
returns jsonb
language sql
stable
security invoker
set search_path='public','private'
as $function$
with p as (
  select count(*)::int prediction_rows,count(distinct ticket_event_id)::int prediction_events,min(predicted_at) first_predicted_at,max(predicted_at) last_predicted_at
  from private.p9_booking_curve_prospective_predictions_v1
), event_scores as (
  select ticket_event_id,count(*)::int cutoff_count,
         avg(incumbent_abs_error)::double precision incumbent_event_ae,
         avg(challenger_abs_error)::double precision challenger_event_ae,
         avg(incumbent_bias)::double precision incumbent_event_bias,
         avg(challenger_bias)::double precision challenger_event_bias
  from private.p9_booking_curve_prospective_scores_v1 group by ticket_event_id
), s as (
  select count(*)::int scored_events,
         avg(incumbent_event_ae)::double precision incumbent_event_balanced_mae,
         avg(challenger_event_ae)::double precision challenger_event_balanced_mae,
         avg(challenger_event_ae-incumbent_event_ae)::double precision delta_event_balanced_mae,
         avg(incumbent_event_bias)::double precision incumbent_event_balanced_bias,
         avg(challenger_event_bias)::double precision challenger_event_balanced_bias,
         avg(case when challenger_event_ae<incumbent_event_ae then 1.0 else 0.0 end)::double precision event_improvement_rate,
         percentile_cont(0.5) within group(order by challenger_event_ae) challenger_event_median_ae,
         percentile_cont(0.9) within group(order by challenger_event_ae) challenger_event_p90_ae,
         max(challenger_event_ae-incumbent_event_ae)::double precision worst_event_degradation
  from event_scores
)
select jsonb_build_object(
  'version','p9-booking-curve-prospective-summary-v1','checked_at',now(),
  'prediction_rows',(select prediction_rows from p),'prediction_events',(select prediction_events from p),
  'first_predicted_at',(select first_predicted_at from p),'last_predicted_at',(select last_predicted_at from p),
  'scored_events',(select scored_events from s),
  'incumbent_event_balanced_mae',(select incumbent_event_balanced_mae from s),
  'challenger_event_balanced_mae',(select challenger_event_balanced_mae from s),
  'delta_event_balanced_mae',(select delta_event_balanced_mae from s),
  'incumbent_event_balanced_bias',(select incumbent_event_balanced_bias from s),
  'challenger_event_balanced_bias',(select challenger_event_balanced_bias from s),
  'event_improvement_rate',(select event_improvement_rate from s),
  'challenger_event_median_ae',(select challenger_event_median_ae from s),
  'challenger_event_p90_ae',(select challenger_event_p90_ae from s),
  'worst_event_degradation',(select worst_event_degradation from s),
  'evidence_status',case when (select scored_events from s)=0 then 'PROSPECTIVE_PREDICTIONS_ONLY' else 'PROSPECTIVE_EVIDENCE_ACCUMULATING' end,
  'production_activation_allowed',false,'live_adjustment',0,'production_change',false
);
$function$;

revoke all on private.p9_booking_curve_prospective_predictions_v1 from public,anon,authenticated;
revoke all on private.p9_booking_curve_prospective_scores_v1 from public,anon,authenticated;
revoke all on function public.export_p9_prospective_inputs_v1(integer) from public,anon,authenticated;
revoke all on function public.export_p9_prospective_incumbent_catalog_v1(integer) from public,anon,authenticated;
revoke all on function public.export_p9_prospective_reference_outcomes_v1() from public,anon,authenticated;
revoke all on function public.insert_p9_booking_curve_prospective_predictions_v1(jsonb,text) from public,anon,authenticated;
revoke all on function public.score_p9_booking_curve_prospective_completed_v1() from public,anon,authenticated;
revoke all on function public.p9_booking_curve_prospective_summary_v1() from public,anon,authenticated;
grant execute on function public.export_p9_prospective_inputs_v1(integer) to service_role;
grant execute on function public.export_p9_prospective_incumbent_catalog_v1(integer) to service_role;
grant execute on function public.export_p9_prospective_reference_outcomes_v1() to service_role;
grant execute on function public.insert_p9_booking_curve_prospective_predictions_v1(jsonb,text) to service_role;
grant execute on function public.score_p9_booking_curve_prospective_completed_v1() to service_role;
grant execute on function public.p9_booking_curve_prospective_summary_v1() to service_role;
grant select on private.p9_booking_curve_prospective_predictions_v1 to service_role;
grant select on private.p9_booking_curve_prospective_scores_v1 to service_role;
