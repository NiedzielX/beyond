-- Structural Prior Runtime v1 — exact pinned historical training export
--
-- Historical training rows must preserve the source dataset semantics exactly.
-- Current-event aliases belong to the inference adapter and MUST NOT rewrite
-- historical club keys. In particular, the pinned 2025/26 dataset contains
-- `radomiak` as the away_club_key and `radomiak_radom` as the home_club_key.
-- Normalizing both to one key changes PIT demand/sporting history and therefore
-- no longer reproduces the approved Structural Prior Runtime v1 benchmark.

create or replace function public.export_historical_runtime_v1()
returns table(
  dataset_version text,
  season text,
  round_no integer,
  match_date date,
  kickoff_time_local text,
  home_team text,
  away_team text,
  home_club_key text,
  away_club_key text,
  home_goals integer,
  away_goals integer,
  attendance integer,
  default_demand_training_eligible boolean,
  match_key text
)
language sql
stable
security definer
set search_path=private,public
as $function$
select
  h.dataset_version,
  h.season,
  h.round_no,
  h.match_date,
  h.kickoff_time_local,
  h.home_team,
  h.away_team,
  h.home_club_key,
  h.away_club_key,
  h.home_goals,
  h.away_goals,
  h.attendance,
  h.default_demand_training_eligible,
  h.match_key
from private.historical_match_attendance_v1 h
where h.dataset_version in (
  'historical-multiclub-2021-25-v2.1',
  'historical-multiclub-2025-26-v1'
)
order by h.match_date,h.kickoff_time_local,h.home_club_key;
$function$;

create or replace function public.export_historical_runtime_payload_v1()
returns jsonb
language sql
stable
security definer
set search_path=public,private
as $function$
select jsonb_build_object(
  'version','structural-prior-training-export-v1',
  'rowCount',count(*),
  'rows',coalesce(
    jsonb_agg(
      to_jsonb(x)
      order by x.season,x.round_no,x.match_date,x.home_club_key,x.away_club_key
    ),
    '[]'::jsonb
  )
)
from public.export_historical_runtime_v1() x;
$function$;

comment on function public.export_historical_runtime_v1() is
'Exact historical training export for Structural Prior Runtime v1. Historical club keys are preserved from the pinned dataset; current-event alias normalization must not be applied here.';
