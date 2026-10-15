-- Avoid Supabase Data API max-row truncation for the canonical 1,530-match
-- Structural Prior training export by returning one JSONB value.

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

revoke all on function public.export_historical_runtime_payload_v1() from public;
revoke all on function public.export_historical_runtime_payload_v1() from anon;
revoke all on function public.export_historical_runtime_payload_v1() from authenticated;
grant execute on function public.export_historical_runtime_payload_v1() to service_role;

comment on function public.export_historical_runtime_payload_v1() is
'Service-role-only single-JSON payload wrapper around the canonical 1,530-row historical runtime export. Avoids Data API max-row truncation without changing model data.';
