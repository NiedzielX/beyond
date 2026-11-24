-- One finite PERS-only job; source and frozen jobs remain unchanged.
do $install$
declare
 v_command text := $command$
do $tick$
declare
 v_issue_until timestamptz;
 v_scoring_until timestamptz;
begin
 select issue_until,scoring_until into v_issue_until,v_scoring_until
 from private.rolling72_mvp_persistence_v1_lane
 where lane_id='rolling72-mvp-persistence-v1';
 if clock_timestamp() >= coalesce(v_scoring_until,'-infinity'::timestamptz) then
  perform cron.unschedule('rolling72_mvp_persistence_v1_tick');
 else
  if clock_timestamp() < v_issue_until then
   perform public.issue_rolling72_mvp_persistence_v1(25);
  end if;
  perform public.score_rolling72_mvp_persistence_v1(100);
 end if;
end
$tick$;
$command$;
 v_old cron.job%rowtype;
begin
 if not exists(select 1 from private.rolling72_mvp_persistence_v1_lane
  where lane_id='rolling72-mvp-persistence-v1'
   and manifest_sha256='22290ba42d6f93d63c694c93ed77401e12c943040a0ee298739d9fbef26391ad'
   and source_manifest_sha256='10d6c91af793348993a5c90212b6a340646b42518b6d75ac6b1be3b3864e406d'
   and issue_until=timestamptz '2026-12-01 00:00:00+00'
   and scoring_until=timestamptz '2026-12-04 06:00:00+00'
   and scoring_until>clock_timestamp()) then
  raise exception 'MVP_PERSISTENCE_CRON_MANIFEST_MISMATCH';
 end if;
 select * into v_old from cron.job where jobname='rolling72_mvp_persistence_v1_tick';
 if found then
  if v_old.command is distinct from v_command or v_old.schedule is distinct from '0-59/5 * * * *'
   or v_old.active is distinct from true or v_old.database is distinct from current_database()
   or v_old.username is distinct from current_user then
   raise exception 'MVP_PERSISTENCE_CRON_EXISTING_JOB_MISMATCH';
  end if;
 else
  perform cron.schedule('rolling72_mvp_persistence_v1_tick','0-59/5 * * * *',v_command);
 end if;
end
$install$;
