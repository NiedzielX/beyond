-- Run immediately before the scorer replacement, in the same transaction.
set local search_path=pg_catalog,public;
do $guard$
begin
  if encode(sha256(convert_to(pg_get_functiondef('public.score_ticketing_challenger_v1()'::regprocedure),'UTF8')),'hex')
       is distinct from 'a1d7fb9eec84a16b17662049d911912f12f52d7a5233c5f61b12a3fb5f15a484'
    or encode(sha256(convert_to(pg_get_functiondef('public.get_multiclub_feature_store_v2()'::regprocedure),'UTF8')),'hex')
       is distinct from '69097ef8b8a82655a5bcaea60e9cf64f42ba69e8750354b18658a69483156d54'
    or encode(sha256(convert_to(pg_get_functiondef('public.get_weather_feature_store_v1()'::regprocedure),'UTF8')),'hex')
       is distinct from '6001514be86f2438affcf6205f158c473465fd5974528cce32299b92f700cd5f'
    or encode(sha256(convert_to(pg_get_functiondef('public.get_live_features_v1_asof(bigint,timestamptz)'::regprocedure),'UTF8')),'hex')
       is distinct from '1e569c160f6fc5acd32021b572d421de63d8a2d2b8aa20cff5664eb6c26e4021'
    or encode(sha256(convert_to(pg_get_viewdef('public.multiclub_feature_store_v3'::regclass,true),'UTF8')),'hex')
       is distinct from '61279539761db95efc7c43ecf19f3688d791db908bcfed5f3023f4b7fa0a4c69'
    or encode(sha256(convert_to(pg_get_viewdef('public.multiclub_feature_store_v4'::regclass,true),'UTF8')),'hex')
       is distinct from '9ebb1a261a5c4a7ac0d47c2920a3022ec2eec4c578c887d60a05fb8013c927bb' then
    raise exception 'TICKETING_SCORER_IO_DEPENDENCY_CHANGED';
  end if;
  if to_regprocedure('private.ticketing_challenger_t24_features_io_v1(bigint[])') is not null
    or not exists(select 1 from pg_proc where oid='public.score_ticketing_challenger_v1()'::regprocedure
      and proowner::regrole::text='postgres' and not prosecdef
      and proacl::text='{postgres=X/postgres,service_role=X/postgres}'
      and proconfig=array['search_path=public, pg_temp'])
    or not (select rolbypassrls from pg_roles where rolname='service_role')
    or not has_schema_privilege('service_role','private','USAGE')
    or not has_function_privilege('service_role','public.get_live_features_v1_asof(bigint,timestamptz)','EXECUTE')
    or exists(select 1 from unnest(array['public.ticket_events','public.snapshots',
      'public.ticket_event_outcomes','public.ticket_event_inventory_reference']) r
      where not has_table_privilege('service_role',r,'SELECT')) then
    raise exception 'TICKETING_SCORER_IO_ACL_OR_VERSION_CHANGED';
  end if;
  if not exists(select 1 from cron.job where jobid=17 and jobname='ticketing_challenger_score_15m'
    and active and schedule='4,19,34,49 * * * *'
    and database=current_database() and username='postgres'
    and md5(command)='4925e82911782fe4d3ab0d627e4400fd') then
    raise exception 'TICKETING_SCORER_IO_JOB_CHANGED';
  end if;
end
$guard$;
