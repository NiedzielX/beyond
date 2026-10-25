-- P7 Long168 prospective validation v1.
-- Frozen by ml/P7_LONG168_PROSPECTIVE_PRECOMMIT_V1.md before prospective outcomes.
-- This migration creates:
--   1) future-only target-free Long168 export,
--   2) immutable prediction ledger,
--   3) outcome-later event scoring,
--   4) prospective score summary/export.
-- Production behavior is unchanged.

create or replace function public.export_p7_long168_prospective_inputs_v1()
returns jsonb
language sql
stable
security invoker
set search_path to 'public', 'private'
as $function$
with eligible_base as (
  select
    e.id as ticket_event_id,
    e.club_slug,
    e.home_team,
    e.away_team,
    e.competition,
    private.normalize_structural_prior_competition_v1(e.competition) as canonical_competition,
    e.kickoff_at,
    ha.club_key as home_club_key,
    aa.club_key as away_club_key
  from public.ticket_events e
  left join private.structural_prior_club_aliases_v1 ha
    on ha.alias = e.home_team and ha.is_active
  left join private.structural_prior_club_aliases_v1 aa
    on aa.alias = e.away_team and aa.is_active
  where e.kickoff_at > now()
    and e.kickoff_at <= now() + interval '168 hours'
    and private.normalize_structural_prior_competition_v1(e.competition) = 'Ekstraklasa'
    and not exists (
      select 1
      from public.ticket_event_outcomes o
      where o.ticket_event_id = e.id
        and o.actual_attendance is not null
    )
), enriched as (
  select
    e.*,
    f.season as sporting_season,
    replace(f.season,'-','/') as season,
    f.round_number as round_no,
    cr.stadium_capacity,
    cr.source_name as capacity_source_name,
    cr.source_url as capacity_source_url,
    cr.verification_status as capacity_verification_status
  from eligible_base e
  left join lateral (
    select s.season, s.round_number
    from public.sporting_league_matches_shadow s
    left join private.structural_prior_club_aliases_v1 sh on sh.alias=s.home_team and sh.is_active
    left join private.structural_prior_club_aliases_v1 sa on sa.alias=s.away_team and sa.is_active
    where s.event_date=(e.kickoff_at at time zone 'Europe/Warsaw')::date
      and sh.club_key=e.home_club_key
      and sa.club_key=e.away_club_key
    order by s.fetched_at desc
    limit 1
  ) f on true
  left join lateral (
    select c.stadium_capacity,c.source_name,c.source_url,c.verification_status
    from private.structural_prior_capacity_registry_v1 c
    where c.club_key=e.home_club_key
      and (e.kickoff_at at time zone 'Europe/Warsaw')::date>=c.valid_from
      and (c.valid_to is null or (e.kickoff_at at time zone 'Europe/Warsaw')::date<=c.valid_to)
    order by c.valid_from desc,c.id desc
    limit 1
  ) cr on true
), usable as (
  select *
  from enriched
  where home_club_key is not null
    and away_club_key is not null
    and season is not null
    and round_no is not null
    and stadium_capacity is not null
), candidates as (
  select
    s.id as requested_snapshot_id,
    s.ticket_event_id,
    s.captured_at as requested_as_of_at,
    e.kickoff_at,
    e.stadium_capacity,
    extract(epoch from (e.kickoff_at - s.captured_at)) / 3600.0 as hours_to_kickoff,
    floor(extract(epoch from (e.kickoff_at - s.captured_at)) / 21600.0)::integer as bucket_6h,
    row_number() over (
      partition by s.ticket_event_id,
        floor(extract(epoch from (e.kickoff_at - s.captured_at)) / 21600.0)::integer
      order by s.captured_at desc, s.id desc
    ) as rn
  from public.snapshots s
  join usable e on e.ticket_event_id=s.ticket_event_id
  where s.captured_at <= now()
    and s.captured_at < e.kickoff_at
    and s.captured_at >= e.kickoff_at - interval '168 hours'
), live_rows as (
  select
    c.ticket_event_id,
    c.requested_snapshot_id,
    c.requested_as_of_at,
    c.hours_to_kickoff,
    c.bucket_6h,
    to_jsonb(f) as features
  from candidates c
  cross join lateral public.get_live_trajectory_features_v1_1_asof(
    c.ticket_event_id,
    c.requested_as_of_at,
    c.stadium_capacity
  ) f
  where c.rn=1
    and c.hours_to_kickoff > 72
    and c.hours_to_kickoff <= 168
    and f.point_in_time_validated
    and f.snapshot_id is not null
), used_events as (
  select distinct ticket_event_id from live_rows
), event_payload as (
  select coalesce(jsonb_agg(
    jsonb_build_object(
      'ticket_event_id',u.ticket_event_id,
      'club_slug',u.club_slug,
      'home_team',u.home_team,
      'away_team',u.away_team,
      'competition',u.competition,
      'canonical_competition',u.canonical_competition,
      'kickoff_at',u.kickoff_at,
      'home_club_key',u.home_club_key,
      'away_club_key',u.away_club_key,
      'sporting_season',u.sporting_season,
      'season',u.season,
      'round_no',u.round_no,
      'stadium_capacity',u.stadium_capacity,
      'capacity_source_name',u.capacity_source_name,
      'capacity_source_url',u.capacity_source_url,
      'capacity_verification_status',u.capacity_verification_status
    ) order by u.kickoff_at,u.ticket_event_id
  ),'[]'::jsonb) as rows
  from usable u
  join used_events x on x.ticket_event_id=u.ticket_event_id
), live_payload as (
  select coalesce(jsonb_agg(to_jsonb(l) order by l.ticket_event_id,l.requested_as_of_at),'[]'::jsonb) as rows
  from live_rows l
)
select jsonb_build_object(
  'version','p7-long168-prospective-inputs-v1',
  'generated_at',now(),
  'sampling',jsonb_build_object(
    'window_hours',168,
    'lower_exclusive_hours',72,
    'cadence_hours',6,
    'rule','latest snapshot in each event x 6h bucket; future event only; target outcome absent',
    'pit_feature_function','get_live_trajectory_features_v1_1_asof'
  ),
  'eventCount',(select count(*) from used_events),
  'liveRowCount',(select count(*) from live_rows),
  'events',(select rows from event_payload),
  'liveRows',(select rows from live_payload),
  'targetValuesIncluded',false,
  'targetValuesUsed',false,
  'productionChange',false
);
$function$;

revoke all on function public.export_p7_long168_prospective_inputs_v1() from public, anon, authenticated;
grant execute on function public.export_p7_long168_prospective_inputs_v1() to service_role;

create table if not exists private.p7_long168_prospective_predictions_v1 (
  id bigint generated always as identity primary key,
  ticket_event_id bigint not null references public.ticket_events(id),
  requested_snapshot_id bigint not null references public.snapshots(id),
  as_of_at timestamptz not null,
  predicted_at timestamptz not null default clock_timestamp(),
  target_at timestamptz not null,
  hours_to_kickoff double precision not null,
  bucket_6h integer not null,
  stadium_capacity integer not null,
  anchor_p50 double precision not null,
  challenger_p50 double precision not null,
  candidate_id text not null,
  training_freeze_manifest_sha256 text not null,
  source_scorecard_sha256 text not null,
  model_fingerprint_sha256 text not null,
  prospective_anchor_package_sha256 text not null,
  source_payload_sha256 text not null,
  prediction_identity_sha256 text not null,
  source_version text not null,
  created_at timestamptz not null default clock_timestamp(),
  constraint p7_long168_prospective_window check (hours_to_kickoff > 72 and hours_to_kickoff <= 168),
  constraint p7_long168_prospective_time_order check (as_of_at <= predicted_at and predicted_at < target_at),
  constraint p7_long168_prospective_capacity check (stadium_capacity > 0),
  constraint p7_long168_prospective_anchor_range check (anchor_p50 >= 0 and anchor_p50 <= stadium_capacity),
  constraint p7_long168_prospective_challenger_range check (challenger_p50 >= 0 and challenger_p50 <= stadium_capacity),
  constraint p7_long168_prospective_candidate check (candidate_id='gbr-l1-depth2-n50-lr003'),
  constraint p7_long168_prospective_freeze_sha check (training_freeze_manifest_sha256='185a9fc90e646bd5fa1bbed3b50c625d65d127a2b2943501761bdfcb89f354ed'),
  constraint p7_long168_prospective_scorecard_sha check (source_scorecard_sha256='f684570856e264dae288599a8e24dde6802f84669a43e304c1d900726aa94e45'),
  constraint p7_long168_prospective_model_sha check (model_fingerprint_sha256 ~ '^[0-9a-f]{64}$'),
  constraint p7_long168_prospective_anchor_sha check (prospective_anchor_package_sha256 ~ '^[0-9a-f]{64}$'),
  constraint p7_long168_prospective_source_sha check (source_payload_sha256 ~ '^[0-9a-f]{64}$'),
  constraint p7_long168_prospective_identity_sha check (prediction_identity_sha256 ~ '^[0-9a-f]{64}$'),
  unique(ticket_event_id,requested_snapshot_id,candidate_id)
);

create index if not exists p7_long168_prospective_predictions_event_idx
  on private.p7_long168_prospective_predictions_v1(ticket_event_id,as_of_at);

create table if not exists private.p7_long168_prospective_event_scores_v1 (
  ticket_event_id bigint primary key references public.ticket_events(id),
  actual_attendance integer not null,
  attendance_confirmed_at timestamptz not null,
  prediction_row_count integer not null,
  first_predicted_at timestamptz not null,
  last_predicted_at timestamptz not null,
  anchor_mae double precision not null,
  challenger_mae double precision not null,
  delta_mae double precision not null,
  anchor_bias double precision not null,
  challenger_bias double precision not null,
  improved boolean not null,
  scored_at timestamptz not null default clock_timestamp(),
  production_change boolean not null default false,
  constraint p7_long168_prospective_score_rows check (prediction_row_count > 0),
  constraint p7_long168_prospective_score_time check (last_predicted_at < attendance_confirmed_at),
  constraint p7_long168_prospective_score_prod check (production_change=false)
);

create or replace function private.reject_p7_long168_prospective_mutation_v1()
returns trigger
language plpgsql
security definer
set search_path to 'public','private'
as $function$
begin
  raise exception 'P7_LONG168_PROSPECTIVE_IMMUTABLE';
end;
$function$;

drop trigger if exists p7_long168_prospective_predictions_immutable_v1 on private.p7_long168_prospective_predictions_v1;
create trigger p7_long168_prospective_predictions_immutable_v1
before update or delete on private.p7_long168_prospective_predictions_v1
for each row execute function private.reject_p7_long168_prospective_mutation_v1();

drop trigger if exists p7_long168_prospective_scores_immutable_v1 on private.p7_long168_prospective_event_scores_v1;
create trigger p7_long168_prospective_scores_immutable_v1
before update or delete on private.p7_long168_prospective_event_scores_v1
for each row execute function private.reject_p7_long168_prospective_mutation_v1();

create or replace function public.insert_p7_long168_prospective_predictions_v1(p_payload jsonb)
returns jsonb
language plpgsql
security definer
set search_path to 'public','private'
as $function$
declare
  v_rows jsonb;
  v_row jsonb;
  v_inserted integer := 0;
  v_existing_model_sha text;
  v_now timestamptz := clock_timestamp();
begin
  if p_payload is null or jsonb_typeof(p_payload) <> 'object' then
    raise exception 'P7_PROSPECTIVE_INVALID_PAYLOAD';
  end if;
  if lower(p_payload::text) ~ '"(actual_attendance|attendance_actual|target_attendance|outcome)"\s*:' then
    raise exception 'P7_PROSPECTIVE_TARGET_KEY_REJECTED';
  end if;
  if coalesce((p_payload->>'production_change')::boolean,true) then
    raise exception 'P7_PROSPECTIVE_PRODUCTION_CHANGE_REJECTED';
  end if;
  if coalesce((p_payload->>'target_values_used')::boolean,true) then
    raise exception 'P7_PROSPECTIVE_TARGET_USE_REJECTED';
  end if;
  v_rows := p_payload->'predictions';
  if jsonb_typeof(v_rows) <> 'array' then
    raise exception 'P7_PROSPECTIVE_PREDICTIONS_ARRAY_REQUIRED';
  end if;

  select min(model_fingerprint_sha256)
  into v_existing_model_sha
  from private.p7_long168_prospective_predictions_v1;

  for v_row in select value from jsonb_array_elements(v_rows)
  loop
    if v_existing_model_sha is not null and v_existing_model_sha <> v_row->>'model_fingerprint_sha256' then
      raise exception 'P7_PROSPECTIVE_MODEL_FINGERPRINT_DRIFT';
    end if;
    if exists (
      select 1 from public.ticket_event_outcomes o
      where o.ticket_event_id=(v_row->>'ticket_event_id')::bigint
        and o.actual_attendance is not null
    ) then
      raise exception 'P7_PROSPECTIVE_OUTCOME_ALREADY_KNOWN event=%',v_row->>'ticket_event_id';
    end if;
    if (v_row->>'as_of_at')::timestamptz > v_now then
      raise exception 'P7_PROSPECTIVE_AS_OF_FROM_FUTURE event=%',v_row->>'ticket_event_id';
    end if;
    if v_now >= (v_row->>'target_at')::timestamptz then
      raise exception 'P7_PROSPECTIVE_TARGET_ALREADY_STARTED event=%',v_row->>'ticket_event_id';
    end if;

    insert into private.p7_long168_prospective_predictions_v1(
      ticket_event_id,requested_snapshot_id,as_of_at,predicted_at,target_at,
      hours_to_kickoff,bucket_6h,stadium_capacity,anchor_p50,challenger_p50,
      candidate_id,training_freeze_manifest_sha256,source_scorecard_sha256,
      model_fingerprint_sha256,prospective_anchor_package_sha256,
      source_payload_sha256,prediction_identity_sha256,source_version
    ) values (
      (v_row->>'ticket_event_id')::bigint,
      (v_row->>'requested_snapshot_id')::bigint,
      (v_row->>'as_of_at')::timestamptz,
      v_now,
      (v_row->>'target_at')::timestamptz,
      (v_row->>'hours_to_kickoff')::double precision,
      (v_row->>'bucket_6h')::integer,
      (v_row->>'stadium_capacity')::integer,
      (v_row->>'anchor_p50')::double precision,
      (v_row->>'challenger_p50')::double precision,
      v_row->>'candidate_id',
      v_row->>'training_freeze_manifest_sha256',
      v_row->>'source_scorecard_sha256',
      v_row->>'model_fingerprint_sha256',
      v_row->>'prospective_anchor_package_sha256',
      v_row->>'source_payload_sha256',
      v_row->>'prediction_identity_sha256',
      v_row->>'source_version'
    )
    on conflict(ticket_event_id,requested_snapshot_id,candidate_id) do nothing;
    if found then v_inserted := v_inserted + 1; end if;
  end loop;

  return jsonb_build_object(
    'version','p7-long168-prospective-insert-v1',
    'inserted_predictions',v_inserted,
    'prediction_count_after',(select count(*) from private.p7_long168_prospective_predictions_v1),
    'independent_event_count_after',(select count(distinct ticket_event_id) from private.p7_long168_prospective_predictions_v1),
    'target_values_used',false,
    'production_change',false
  );
end;
$function$;

create or replace function public.score_p7_long168_prospective_completed_events_v1()
returns jsonb
language plpgsql
security definer
set search_path to 'public','private'
as $function$
declare
  v_inserted integer := 0;
begin
  with eligible as (
    select
      p.ticket_event_id,
      o.actual_attendance,
      o.confirmed_at,
      count(*)::int as prediction_row_count,
      min(p.predicted_at) as first_predicted_at,
      max(p.predicted_at) as last_predicted_at,
      avg(abs(p.anchor_p50-o.actual_attendance))::double precision as anchor_mae,
      avg(abs(p.challenger_p50-o.actual_attendance))::double precision as challenger_mae,
      avg(p.anchor_p50-o.actual_attendance)::double precision as anchor_bias,
      avg(p.challenger_p50-o.actual_attendance)::double precision as challenger_bias
    from private.p7_long168_prospective_predictions_v1 p
    join public.ticket_event_outcomes o
      on o.ticket_event_id=p.ticket_event_id
     and o.actual_attendance is not null
     and o.confirmed_at is not null
     and p.predicted_at < o.confirmed_at
    group by p.ticket_event_id,o.actual_attendance,o.confirmed_at
    having max(p.predicted_at) < o.confirmed_at
  ), inserted as (
    insert into private.p7_long168_prospective_event_scores_v1(
      ticket_event_id,actual_attendance,attendance_confirmed_at,prediction_row_count,
      first_predicted_at,last_predicted_at,anchor_mae,challenger_mae,delta_mae,
      anchor_bias,challenger_bias,improved,production_change
    )
    select
      e.ticket_event_id,e.actual_attendance,e.confirmed_at,e.prediction_row_count,
      e.first_predicted_at,e.last_predicted_at,e.anchor_mae,e.challenger_mae,
      e.challenger_mae-e.anchor_mae,e.anchor_bias,e.challenger_bias,
      e.challenger_mae<e.anchor_mae,false
    from eligible e
    on conflict(ticket_event_id) do nothing
    returning 1
  )
  select count(*) into v_inserted from inserted;

  return jsonb_build_object(
    'version','p7-long168-prospective-score-v1',
    'inserted_event_scores',v_inserted,
    'scored_event_count',(select count(*) from private.p7_long168_prospective_event_scores_v1),
    'production_change',false
  );
end;
$function$;

create or replace function public.p7_long168_prospective_summary_v1()
returns jsonb
language sql
stable
security invoker
set search_path to 'public','private'
as $function$
with p as (
  select
    count(*)::int as prediction_rows,
    count(distinct ticket_event_id)::int as prediction_events,
    min(predicted_at) as first_predicted_at,
    max(predicted_at) as last_predicted_at,
    min(model_fingerprint_sha256) as model_fingerprint_sha256,
    count(distinct model_fingerprint_sha256)::int as model_fingerprint_count
  from private.p7_long168_prospective_predictions_v1
), s as (
  select
    count(*)::int as scored_events,
    avg(anchor_mae)::double precision as anchor_event_balanced_mae,
    avg(challenger_mae)::double precision as challenger_event_balanced_mae,
    avg(delta_mae)::double precision as delta_event_balanced_mae,
    avg(anchor_bias)::double precision as anchor_event_balanced_bias,
    avg(challenger_bias)::double precision as challenger_event_balanced_bias,
    avg(case when improved then 1.0 else 0.0 end)::double precision as event_improvement_rate,
    percentile_cont(0.5) within group(order by challenger_mae) as challenger_event_median_ae,
    percentile_cont(0.9) within group(order by challenger_mae) as challenger_event_p90_ae,
    max(delta_mae)::double precision as worst_event_degradation
  from private.p7_long168_prospective_event_scores_v1
)
select jsonb_build_object(
  'version','p7-long168-prospective-summary-v1',
  'checked_at',now(),
  'prediction_rows',(select prediction_rows from p),
  'prediction_events',(select prediction_events from p),
  'first_predicted_at',(select first_predicted_at from p),
  'last_predicted_at',(select last_predicted_at from p),
  'model_fingerprint_sha256',(select model_fingerprint_sha256 from p),
  'model_fingerprint_count',(select model_fingerprint_count from p),
  'scored_events',(select scored_events from s),
  'anchor_event_balanced_mae',(select anchor_event_balanced_mae from s),
  'challenger_event_balanced_mae',(select challenger_event_balanced_mae from s),
  'delta_event_balanced_mae',(select delta_event_balanced_mae from s),
  'anchor_event_balanced_bias',(select anchor_event_balanced_bias from s),
  'challenger_event_balanced_bias',(select challenger_event_balanced_bias from s),
  'event_improvement_rate',(select event_improvement_rate from s),
  'challenger_event_median_ae',(select challenger_event_median_ae from s),
  'challenger_event_p90_ae',(select challenger_event_p90_ae from s),
  'worst_event_degradation',(select worst_event_degradation from s),
  'evidence_status',case
    when (select scored_events from s)=0 then 'PROSPECTIVE_PREDICTIONS_ONLY'
    else 'PROSPECTIVE_EVIDENCE_ACCUMULATING'
  end,
  'production_activation_allowed',false,
  'live_adjustment',0,
  'production_change',false
);
$function$;

create or replace function public.export_p7_long168_prospective_scores_v1()
returns jsonb
language sql
stable
security invoker
set search_path to 'public','private'
as $function$
select jsonb_build_object(
  'version','p7-long168-prospective-scores-v1',
  'eventCount',(select count(*) from private.p7_long168_prospective_event_scores_v1),
  'scores',coalesce((select jsonb_agg(to_jsonb(s) order by s.attendance_confirmed_at,s.ticket_event_id) from private.p7_long168_prospective_event_scores_v1 s),'[]'::jsonb),
  'production_change',false
);
$function$;

revoke all on private.p7_long168_prospective_predictions_v1 from public, anon, authenticated;
revoke all on private.p7_long168_prospective_event_scores_v1 from public, anon, authenticated;
revoke all on function public.insert_p7_long168_prospective_predictions_v1(jsonb) from public, anon, authenticated;
revoke all on function public.score_p7_long168_prospective_completed_events_v1() from public, anon, authenticated;
revoke all on function public.p7_long168_prospective_summary_v1() from public, anon, authenticated;
revoke all on function public.export_p7_long168_prospective_scores_v1() from public, anon, authenticated;

grant execute on function public.insert_p7_long168_prospective_predictions_v1(jsonb) to service_role;
grant execute on function public.score_p7_long168_prospective_completed_events_v1() to service_role;
grant execute on function public.p7_long168_prospective_summary_v1() to service_role;
grant execute on function public.export_p7_long168_prospective_scores_v1() to service_role;
