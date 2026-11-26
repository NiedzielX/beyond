-- One finite, additive paired-comparator job. Install only after activation.
-- Existing collector/source/PERS/frozen jobs are not changed.
do $install$
declare
 v_expected_manifest constant text := '6f8ee5d4e0ac0a3892f8b5525ee10a0c7b02559c04c705147a47677e4260bf0d';
 v_command text := $command$
do $tick$
declare
 v_lane private.rolling72_mvp_paired_drift24_v1_lane%rowtype;
begin
 select * into v_lane from private.rolling72_mvp_paired_drift24_v1_lane
 where lane_id='rolling72-mvp-paired-drift24-v1';
 if not found then
  perform cron.unschedule('rolling72_mvp_paired_drift24_v1_tick');
 elsif v_lane.manifest_sha256 is distinct from '6f8ee5d4e0ac0a3892f8b5525ee10a0c7b02559c04c705147a47677e4260bf0d'
  or v_lane.source_manifest_sha256 is distinct from '10d6c91af793348993a5c90212b6a340646b42518b6d75ac6b1be3b3864e406d'
  or v_lane.issue_until is distinct from timestamptz '2026-12-01 00:00:00+00'
  or v_lane.scoring_until is distinct from timestamptz '2026-12-04 06:00:00+00' then
  raise exception 'MVP_PAIRED_DRIFT24_CRON_MANIFEST_MISMATCH';
 elsif clock_timestamp() >= v_lane.scoring_until then
  perform cron.unschedule('rolling72_mvp_paired_drift24_v1_tick');
 else
  if clock_timestamp() < v_lane.issue_until then
   perform public.issue_rolling72_mvp_paired_drift24_v1(25);
  end if;
  perform public.score_rolling72_mvp_paired_drift24_v1(100);
 end if;
end
$tick$;
$command$;
 v_old cron.job%rowtype;
begin
 perform pg_advisory_xact_lock(hashtextextended('rolling72-mvp-paired-drift24-v1:cron',20261125));
 if v_expected_manifest !~ '^[0-9a-f]{64}$' or not exists(
  select 1 from private.rolling72_mvp_paired_drift24_v1_lane
  where lane_id='rolling72-mvp-paired-drift24-v1'
   and manifest_sha256=v_expected_manifest
   and manifest_sha256=encode(sha256(convert_to(manifest_text,'UTF8')),'hex')
   and source_manifest_sha256='10d6c91af793348993a5c90212b6a340646b42518b6d75ac6b1be3b3864e406d'
   and issue_until=timestamptz '2026-12-01 00:00:00+00'
   and scoring_until=timestamptz '2026-12-04 06:00:00+00'
   and scoring_until>clock_timestamp()) then
  raise exception 'MVP_PAIRED_DRIFT24_CRON_MANIFEST_MISMATCH';
 end if;
 select * into v_old from cron.job where jobname='rolling72_mvp_paired_drift24_v1_tick';
 if found then
  if v_old.command is distinct from v_command or v_old.schedule is distinct from '1-59/5 * * * *'
   or v_old.active is distinct from true or v_old.database is distinct from current_database()
   or v_old.username is distinct from current_user then
   raise exception 'MVP_PAIRED_DRIFT24_CRON_EXISTING_JOB_MISMATCH';
  end if;
 else
  perform cron.schedule('rolling72_mvp_paired_drift24_v1_tick','1-59/5 * * * *',v_command);
 end if;
end
$install$;
