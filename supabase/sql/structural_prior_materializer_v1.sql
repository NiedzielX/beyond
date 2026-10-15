-- Structural Prior Materializer v1
-- Production schema contract applied to Supabase project adchzwqboeekhokapxqi on 2026-10-15.
-- Runtime scope is intentionally T-30/T-14 only. T-7/T-3/T-1 remain fail-closed
-- until dedicated executable current-event runtimes are frozen for those horizons.

create table if not exists private.structural_prior_competition_aliases_v1 (
  alias text primary key,
  canonical_competition text not null,
  is_active boolean not null default true,
  source text not null default 'manual_verified',
  created_at timestamptz not null default now()
);

create table if not exists private.structural_prior_club_aliases_v1 (
  alias text primary key,
  club_key text not null,
  canonical_name text not null,
  is_active boolean not null default true,
  source text not null default 'verified_mapping',
  created_at timestamptz not null default now()
);

create table if not exists private.structural_prior_capacity_registry_v1 (
  id bigserial primary key,
  club_key text not null,
  valid_from date not null,
  valid_to date,
  stadium_capacity integer not null check(stadium_capacity > 0),
  verification_status text not null check(verification_status in ('verified','carry_forward')),
  source_name text not null,
  source_url text not null,
  verified_at timestamptz not null,
  notes text,
  created_at timestamptz not null default now(),
  unique(club_key,valid_from,stadium_capacity)
);

insert into private.structural_prior_competition_aliases_v1(alias,canonical_competition,source)
values
  ('Ekstraklasa','Ekstraklasa','canonical'),
  ('PKO BP Ekstraklasa','Ekstraklasa','verified_alias')
on conflict(alias) do update set
  canonical_competition=excluded.canonical_competition,
  is_active=true,
  source=excluded.source;

insert into private.structural_prior_club_aliases_v1(alias,club_key,canonical_name) values
 ('Cracovia','cracovia','Cracovia'),
 ('GKS Katowice','gkskatowice','GKS Katowice'),
 ('Górnik Zabrze','gornikzabrze','Górnik Zabrze'),
 ('Jagiellonia Białystok','jagiellonia','Jagiellonia Białystok'),
 ('KGHM Zagłębie Lubin','zaglebie_lubin','Zagłębie Lubin'),
 ('Zagłębie Lubin','zaglebie_lubin','Zagłębie Lubin'),
 ('Korona Kielce','koronakielce','Korona Kielce'),
 ('Lech Poznań','lech','Lech Poznań'),
 ('Legia Warsaw','legia','Legia Warszawa'),
 ('Legia Warszawa','legia','Legia Warszawa'),
 ('Motor Lublin','motorlublin','Motor Lublin'),
 ('Piast Gliwice','piastgliwice','Piast Gliwice'),
 ('Pogoń Szczecin','pogonszczecin','Pogoń Szczecin'),
 ('Radomiak Radom','radomiak_radom','Radomiak Radom'),
 ('Raków Częstochowa','rakow','Raków Częstochowa'),
 ('Śląsk Wrocław','slask_wroclaw','Śląsk Wrocław'),
 ('Widzew Łódź','widzewlodz','Widzew Łódź'),
 ('Wieczysta Kraków','wieczysta_krakow','Wieczysta Kraków'),
 ('Wisła Kraków','wisla_krakow','Wisła Kraków'),
 ('Wisła Płock','wisla_plock','Wisła Płock')
on conflict(alias) do update set
  club_key=excluded.club_key,
  canonical_name=excluded.canonical_name,
  is_active=true;

insert into private.structural_prior_capacity_registry_v1
(club_key,valid_from,valid_to,stadium_capacity,verification_status,source_name,source_url,verified_at,notes)
values
 ('lech','2026-07-01',null,43269,'verified','Lech Poznań official stadium page','https://www.lechpoznan.pl/pl/ul-bulgarska','2026-10-15T12:41:09Z','Same verified capacity used by first genuine current Structural Prior.'),
 ('pogonszczecin','2026-07-01',null,21163,'verified','Pogoń Szczecin official stadium page','https://ovh.pogonszczecin.pl/klub/stadion','2026-10-15T14:00:00Z',null),
 ('jagiellonia','2026-07-01',null,22372,'verified','Chorten Arena / Stadion Białystok','https://stadion.bialystok.pl/en/business_offer/tournaments-and-matches/','2026-10-15T14:00:00Z',null),
 ('wisla_krakow','2026-07-01',null,33130,'verified','Zarząd Infrastruktury Sportowej w Krakowie','https://zis.krakow.pl/stadion-miejski-im-henryka-reymana-w-krakowie','2026-10-15T14:00:00Z','Current municipal-stadium published capacity.'),
 ('legia','2026-07-01',null,31006,'carry_forward','Beyond verified-capacity history v1','repo://ml/data/STADIUM_CAPACITY_HISTORY_V1.md','2026-10-15T14:00:00Z','Exact capacity carried forward from the verified historical registry.'),
 ('slask_wroclaw','2026-07-01',null,43708,'verified','Śląsk Wrocław ticketing / Tarczyński Arena technical data','https://bilety.slaskwroclaw.pl/CMS?page=dojazd','2026-10-15T14:00:00Z','Current published covered-seat capacity.')
on conflict(club_key,valid_from,stadium_capacity) do update set
 verification_status=excluded.verification_status,
 source_name=excluded.source_name,
 source_url=excluded.source_url,
 verified_at=excluded.verified_at,
 notes=excluded.notes;

create or replace function private.normalize_structural_prior_competition_v1(p_competition text)
returns text
language sql
stable
security invoker
set search_path=private,public
as $function$
 select coalesce(
   (select canonical_competition
    from private.structural_prior_competition_aliases_v1
    where alias=p_competition and is_active
    limit 1),
   p_competition
 );
$function$;

create or replace function public.get_structural_prior_v1(
  p_ticket_event_id bigint,
  p_requested_as_of_at timestamptz
)
returns table(
  status text,source_prior_id bigint,ticket_event_id bigint,horizon text,
  requested_as_of_at timestamptz,target_as_of_at timestamptz,kickoff_at timestamptz,
  model_spec_id text,model_family text,feature_contract text,p50 numeric,p10 numeric,p90 numeric,
  stadium_capacity integer,expected_occupancy numeric,point_in_time_validated boolean,
  generated_at timestamptz,metadata jsonb
)
language sql
stable
security definer
set search_path=private,public
as $function$
with event_row as (
 select id,kickoff_at,competition,
        private.normalize_structural_prior_competition_v1(competition) canonical_competition
 from public.ticket_events
 where id=p_ticket_event_id and kickoff_at is not null
), resolved as (
 select e.*,
 case when p_requested_as_of_at >= e.kickoff_at then 'invalid'
      when extract(epoch from(e.kickoff_at-p_requested_as_of_at))/3600.0 > 720 then 'not_due'
      when extract(epoch from(e.kickoff_at-p_requested_as_of_at))/3600.0 > 336 then 'T-30'
      when extract(epoch from(e.kickoff_at-p_requested_as_of_at))/3600.0 > 168 then 'T-14'
      when extract(epoch from(e.kickoff_at-p_requested_as_of_at))/3600.0 > 72 then 'T-7'
      when extract(epoch from(e.kickoff_at-p_requested_as_of_at))/3600.0 > 24 then 'T-3'
      else 'T-1' end resolved_horizon
 from event_row e
), spec as (
 select r.*,s.target_days_before,s.model_spec_id,s.model_family,s.feature_contract,s.validated_competitions
 from resolved r
 left join private.structural_prior_model_specs_v1 s
   on s.horizon=r.resolved_horizon and s.is_current
), target as (
 select s.*,
        case when s.target_days_before is not null
             then s.kickoff_at-make_interval(days=>s.target_days_before) end target_cutoff
 from spec s
), picked as (
 select t.*,p.id prior_id,p.p50,p.p10,p.p90,p.stadium_capacity,p.expected_occupancy,
        p.point_in_time_validated,p.generated_at,p.metadata,
        p.target_as_of_at stored_target_as_of_at,p.kickoff_at stored_kickoff_at,
        p.model_spec_id stored_model_spec_id,p.feature_contract stored_feature_contract
 from target t
 left join private.structural_prior_forecasts_v1 p
   on p.ticket_event_id=t.id
  and p.horizon=t.resolved_horizon
  and p.target_as_of_at=t.target_cutoff
  and p.model_spec_id=t.model_spec_id
)
select
 case when resolved_horizon='invalid' then 'invalid_request'
      when resolved_horizon='not_due' then 'not_due'
      when model_spec_id is null then 'missing_spec'
      when canonical_competition is null or not(canonical_competition=any(validated_competitions)) then 'out_of_domain'
      when prior_id is null then 'missing_prior'
      when point_in_time_validated is not true then 'invalid_prior'
      when stored_target_as_of_at<>target_cutoff then 'invalid_prior'
      when stored_kickoff_at<>kickoff_at then 'invalid_prior'
      when stored_model_spec_id<>model_spec_id then 'invalid_prior'
      when stored_feature_contract<>feature_contract then 'invalid_prior'
      else 'ready' end::text,
 prior_id,id,
 case when resolved_horizon in ('T-30','T-14','T-7','T-3','T-1') then resolved_horizon end,
 p_requested_as_of_at,target_cutoff,kickoff_at,model_spec_id,model_family,feature_contract,
 p50,p10,p90,stadium_capacity,
 coalesce(expected_occupancy,case when stadium_capacity>0 then p50/stadium_capacity end),
 point_in_time_validated,generated_at,metadata
from picked;
$function$;

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
   and r.horizon in ('T-30','T-14')
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

create or replace function public.get_structural_prior_club_aliases_v1()
returns table(alias text,club_key text)
language sql
stable
security definer
set search_path=private,public
as $function$
 select a.alias,a.club_key
 from private.structural_prior_club_aliases_v1 a
 where a.is_active
 order by a.alias;
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
 if v_event_id is null or v_horizon not in ('T-30','T-14') or v_target is null or
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

grant usage on schema private to service_role;
grant select on private.structural_prior_competition_aliases_v1,
                private.structural_prior_club_aliases_v1,
                private.structural_prior_capacity_registry_v1 to service_role;
grant select,insert on private.structural_prior_forecasts_v1 to service_role;
grant usage,select on sequence private.structural_prior_forecasts_v1_id_seq to service_role;

revoke all on function public.get_due_early_structural_prior_inputs_v1(timestamptz,bigint) from public,anon,authenticated;
grant execute on function public.get_due_early_structural_prior_inputs_v1(timestamptz,bigint) to service_role;
revoke all on function public.get_structural_prior_club_aliases_v1() from public,anon,authenticated;
grant execute on function public.get_structural_prior_club_aliases_v1() to service_role;
revoke all on function public.insert_structural_prior_forecast_v1(jsonb) from public,anon,authenticated;
grant execute on function public.insert_structural_prior_forecast_v1(jsonb) to service_role;
