-- Structural Prior Runtime v1 — enable frozen T-7 current-event inference.
--
-- Apply only after the T-7 artifact freeze has reproduced the approved
-- development + untouched holdout values. T-3/T-1 intentionally remain
-- fail-closed.

begin;

update private.structural_prior_model_specs_v1
set is_current = false
where horizon = 'T-7'
  and is_current;

insert into private.structural_prior_model_specs_v1(
  horizon,
  target_days_before,
  model_spec_id,
  model_family,
  feature_contract,
  validation_report,
  status,
  is_current,
  activated_at,
  notes,
  validated_competitions
) values (
  'T-7',
  7,
  'structural-prior-runtime-v1-t7-gbr-base',
  'GradientBoostingRegressor',
  'structural-prior-pit-v1+verified-capacity-v1',
  'ml/results/STRUCTURAL_PRIOR_RUNTIME_V1_2026-10-15.md',
  'historical_champion_candidate',
  true,
  now(),
  'Executable Structural Prior Runtime v1. Frozen T-7 spec; MAE dev 2476.8, holdouts 1777.7 / 1802.3.',
  array['Ekstraklasa']::text[]
)
on conflict(horizon,model_spec_id) do update set
  target_days_before = excluded.target_days_before,
  model_family = excluded.model_family,
  feature_contract = excluded.feature_contract,
  validation_report = excluded.validation_report,
  status = excluded.status,
  is_current = excluded.is_current,
  activated_at = excluded.activated_at,
  notes = excluded.notes,
  validated_competitions = excluded.validated_competitions;

create or replace function public.get_due_early_structural_prior_inputs_v1(
 p_requested_at timestamptz default now(),
 p_include_ready_event_id bigint default null
)
returns table(
 ticket_event_id bigint,home_team text,away_team text,competition text,canonical_competition text,
 kickoff_at timestamptz,horizon text,target_as_of_at timestamptz,model_spec_id text,model_family text,
 feature_contract text,season text,round_no integer,home_club_key text,away_club_key text,
 stadium_capacity integer,capacity_source_name text,capacity_source_url text,
 capacity_verification_status text,source_snapshot_id bigint,resolver_status text,input_status text
)
language sql
stable
security definer
set search_path=private,public
as $function$
with candidates as (
 select e.*,r.status resolver_status,r.horizon,r.target_as_of_at,r.model_spec_id,r.model_family,r.feature_contract,
        private.normalize_structural_prior_competition_v1(e.competition) canonical_competition
 from public.ticket_events e
 cross join lateral public.get_structural_prior_v1(e.id,p_requested_at) r
 where e.kickoff_at>p_requested_at
   and (e.kickoff_at<=p_requested_at+interval '31 days' or e.id=p_include_ready_event_id)
   and r.horizon in ('T-30','T-14','T-7')
   and (r.status='missing_prior' or e.id=p_include_ready_event_id)
), mapped as (
 select c.*,ha.club_key home_key,aa.club_key away_key
 from candidates c
 left join private.structural_prior_club_aliases_v1 ha on ha.alias=c.home_team and ha.is_active
 left join private.structural_prior_club_aliases_v1 aa on aa.alias=c.away_team and aa.is_active
), fixture as (
 select m.*,f.season source_season,f.round_number
 from mapped m
 left join lateral (
   select s.season,s.round_number
   from public.sporting_league_matches_shadow s
   left join private.structural_prior_club_aliases_v1 sh on sh.alias=s.home_team and sh.is_active
   left join private.structural_prior_club_aliases_v1 sa on sa.alias=s.away_team and sa.is_active
   where s.event_date=(m.kickoff_at at time zone 'Europe/Warsaw')::date
     and sh.club_key=m.home_key and sa.club_key=m.away_key
   order by s.fetched_at desc limit 1
 ) f on true
), cap as (
 select f.*,cr.stadium_capacity cap_value,cr.source_name cap_source_name,
        cr.source_url cap_source_url,cr.verification_status cap_status
 from fixture f
 left join lateral (
   select c2.*
   from private.structural_prior_capacity_registry_v1 c2
   where c2.club_key=f.home_key
     and (f.kickoff_at at time zone 'Europe/Warsaw')::date>=c2.valid_from
     and (c2.valid_to is null or (f.kickoff_at at time zone 'Europe/Warsaw')::date<=c2.valid_to)
   order by c2.valid_from desc,c2.id desc limit 1
 ) cr on true
), snap as (
 select cap.*,ss.id snapshot_id
 from cap
 left join lateral (
   select s.id
   from public.snapshots s
   where s.ticket_event_id=cap.id and s.captured_at<=cap.target_as_of_at
   order by s.captured_at desc,s.id desc limit 1
 ) ss on true
)
select id,home_team,away_team,competition,canonical_competition,kickoff_at,horizon,target_as_of_at,
       model_spec_id,model_family,feature_contract,replace(source_season,'-','/'),round_number,
       home_key,away_key,cap_value,cap_source_name,cap_source_url,cap_status,snapshot_id,resolver_status,
       case when canonical_competition<>'Ekstraklasa' then 'out_of_domain'
            when home_key is null then 'missing_home_alias'
            when away_key is null then 'missing_away_alias'
            when source_season is null or round_number is null then 'missing_fixture_round'
            when cap_value is null then 'missing_capacity'
            else 'ready' end
from snap
order by kickoff_at,id;
$function$;

create or replace function public.insert_structural_prior_forecast_v1(p_forecast jsonb)
returns bigint
language plpgsql
security invoker
set search_path=public,private
as $function$
declare
 v_event_id bigint; v_horizon text; v_target timestamptz; v_kickoff timestamptz; v_spec_id text;
 v_family text; v_feature_contract text; v_p50 numeric; v_capacity integer; v_id bigint;
 v_event record; v_spec record; v_reg_capacity integer; v_canonical_comp text;
begin
 if p_forecast is null then raise exception 'p_forecast is required'; end if;
 v_event_id:=nullif(p_forecast->>'ticket_event_id','')::bigint;
 v_horizon:=nullif(p_forecast->>'horizon','');
 v_target:=nullif(p_forecast->>'target_as_of_at','')::timestamptz;
 v_kickoff:=nullif(p_forecast->>'kickoff_at','')::timestamptz;
 v_spec_id:=nullif(p_forecast->>'model_spec_id','');
 v_family:=nullif(p_forecast->>'model_family','');
 v_feature_contract:=nullif(p_forecast->>'feature_contract','');
 v_p50:=nullif(p_forecast->>'p50','')::numeric;
 v_capacity:=nullif(p_forecast->>'stadium_capacity','')::integer;
 if v_event_id is null or v_horizon not in ('T-30','T-14','T-7') or v_target is null or
    v_kickoff is null or v_spec_id is null or v_p50 is null or v_capacity is null then
   raise exception 'invalid structural prior payload';
 end if;
 select e.*,private.normalize_structural_prior_competition_v1(e.competition) canonical_competition
 into v_event from public.ticket_events e where e.id=v_event_id;
 if not found then raise exception 'ticket event % not found',v_event_id; end if;
 select * into v_spec from private.structural_prior_model_specs_v1 where horizon=v_horizon and is_current;
 if not found then raise exception 'current spec missing for %',v_horizon; end if;
 if v_event.kickoff_at<>v_kickoff then raise exception 'kickoff mismatch'; end if;
 if v_target<>v_event.kickoff_at-make_interval(days=>v_spec.target_days_before) then raise exception 'target cutoff mismatch'; end if;
 if v_spec.model_spec_id<>v_spec_id or v_spec.model_family<>v_family or v_spec.feature_contract<>v_feature_contract then
   raise exception 'model lineage mismatch';
 end if;
 v_canonical_comp:=v_event.canonical_competition;
 if v_canonical_comp is null or not(v_canonical_comp=any(v_spec.validated_competitions)) then
   raise exception 'competition out of domain';
 end if;
 select cr.stadium_capacity into v_reg_capacity
 from private.structural_prior_club_aliases_v1 ca
 join private.structural_prior_capacity_registry_v1 cr on cr.club_key=ca.club_key
 where ca.alias=v_event.home_team and ca.is_active
   and (v_event.kickoff_at at time zone 'Europe/Warsaw')::date>=cr.valid_from
   and (cr.valid_to is null or (v_event.kickoff_at at time zone 'Europe/Warsaw')::date<=cr.valid_to)
 order by cr.valid_from desc,cr.id desc limit 1;
 if v_reg_capacity is null or v_reg_capacity<>v_capacity then raise exception 'verified capacity mismatch'; end if;
 if v_p50<0 or v_p50>v_capacity then raise exception 'p50 outside capacity bounds'; end if;
 select id into v_id from private.structural_prior_forecasts_v1
 where ticket_event_id=v_event_id and horizon=v_horizon and target_as_of_at=v_target and model_spec_id=v_spec_id
 limit 1;
 if found then return v_id; end if;
 insert into private.structural_prior_forecasts_v1(
  ticket_event_id,horizon,target_as_of_at,kickoff_at,model_spec_id,model_family,feature_contract,
  p50,p10,p90,stadium_capacity,expected_occupancy,point_in_time_validated,generated_at,
  source_kind,input_lineage,metadata
 ) values(
  v_event_id,v_horizon,v_target,v_kickoff,v_spec_id,v_family,v_feature_contract,
  v_p50,null,null,v_capacity,v_p50/v_capacity,true,
  coalesce(nullif(p_forecast->>'generated_at','')::timestamptz,now()),
  'structural_prior_materializer_v1',
  coalesce(p_forecast->'input_lineage','{}'::jsonb),
  coalesce(p_forecast->'metadata','{}'::jsonb)
 ) returning id into v_id;
 return v_id;
end;
$function$;

revoke all on function public.get_due_early_structural_prior_inputs_v1(timestamptz,bigint) from public,anon,authenticated;
grant execute on function public.get_due_early_structural_prior_inputs_v1(timestamptz,bigint) to service_role;
revoke all on function public.insert_structural_prior_forecast_v1(jsonb) from public,anon,authenticated;
grant execute on function public.insert_structural_prior_forecast_v1(jsonb) to service_role;

commit;
