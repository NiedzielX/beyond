-- Structural Prior fixture-date tolerance hardening — 2026-10-26
--
-- Problem:
-- `sporting_league_matches_shadow.event_date` can represent a round-date
-- placeholder rather than the verified kickoff date. Example: Cracovia–Motor
-- is verified for 2026-10-30, while the shadow row carries 2026-10-31.
-- The previous exact-date-only resolver therefore returned
-- `missing_fixture_round`, preventing a genuine PIT Structural Prior from being
-- materialized before downstream P9 prospective cutoffs.
--
-- Safety contract:
-- 1. Keep club identity exact through the verified alias keys.
-- 2. Prefer an exact Warsaw calendar-date match.
-- 3. Only if no exact-date row exists, allow a fallback when there is exactly
--    ONE unique same-home/same-away fixture within +/- 3 calendar days.
-- 4. If zero or multiple nearby fixtures exist, fail closed.
-- 5. This does not alter ticket_event kickoff_at and does not create historical
--    evidence. It only resolves season/round metadata for future PIT scoring.

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
   and r.horizon in ('T-30','T-14','T-7','T-3','T-1')
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
   with exact_match as (
     select s.season,s.round_number,s.event_date,s.fetched_at
     from public.sporting_league_matches_shadow s
     left join private.structural_prior_club_aliases_v1 sh on sh.alias=s.home_team and sh.is_active
     left join private.structural_prior_club_aliases_v1 sa on sa.alias=s.away_team and sa.is_active
     where s.event_date=(m.kickoff_at at time zone 'Europe/Warsaw')::date
       and sh.club_key=m.home_key and sa.club_key=m.away_key
     order by s.fetched_at desc
     limit 1
   ), nearby_unique as (
     select s.season,s.round_number,s.event_date,max(s.fetched_at) fetched_at
     from public.sporting_league_matches_shadow s
     left join private.structural_prior_club_aliases_v1 sh on sh.alias=s.home_team and sh.is_active
     left join private.structural_prior_club_aliases_v1 sa on sa.alias=s.away_team and sa.is_active
     where s.event_date between (m.kickoff_at at time zone 'Europe/Warsaw')::date - 3
                            and (m.kickoff_at at time zone 'Europe/Warsaw')::date + 3
       and sh.club_key=m.home_key and sa.club_key=m.away_key
     group by s.season,s.round_number,s.event_date
   )
   select e.season,e.round_number
   from exact_match e
   union all
   select n.season,n.round_number
   from nearby_unique n
   where not exists(select 1 from exact_match)
     and (select count(*) from nearby_unique)=1
   order by 2 desc
   limit 1
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
