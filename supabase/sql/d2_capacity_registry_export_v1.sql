-- d2 Capacity Registry Export v1
-- Service-role-only support export for PIT current-season anchor replay.
-- Keeps capacity validity/source lineage explicit; slug -> club_key mapping stays
-- in the canonical Python feature layer rather than being duplicated in SQL.

begin;

create or replace function public.export_d2_capacity_registry_v1()
returns jsonb
language sql
stable
security invoker
set search_path = public, private
as $function$
with rows as (
  select
    c.id,
    c.club_key,
    c.stadium_capacity,
    c.valid_from,
    c.valid_to,
    c.source_name,
    c.source_url,
    c.verification_status
  from private.structural_prior_capacity_registry_v1 c
  order by c.club_key,c.valid_from,c.id
), payload as (
  select coalesce(jsonb_agg(to_jsonb(r) order by r.club_key,r.valid_from,r.id),'[]'::jsonb) as value
  from rows r
)
select jsonb_build_object(
  'version','d2-capacity-registry-v1',
  'rowCount',(select count(*) from rows),
  'rows',(select value from payload)
);
$function$;

revoke all on function public.export_d2_capacity_registry_v1()
  from public,anon,authenticated;
grant execute on function public.export_d2_capacity_registry_v1()
  to service_role;

commit;
