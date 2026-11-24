-- One new source-only job. Existing collectors/forecast/scoring jobs unchanged.
-- Run only after the reviewed source migration and exact manifest activation.
do $install$
declare
 v_command text := $command$
do $tick$
begin
 if clock_timestamp() >= coalesce((
  select scoring_until from private.rolling72_mvp_research_v1_lane
  where lane_id='rolling72-mvp-research-v1'
 ), '-infinity'::timestamptz) then
  perform cron.unschedule('rolling72_mvp_research_v1_capture');
 else
  perform public.capture_rolling72_mvp_research_v1(25);
 end if;
end
$tick$;
$command$;
 v_old cron.job%rowtype;
begin
 if not exists(select 1 from private.rolling72_mvp_research_v1_lane
   where lane_id='rolling72-mvp-research-v1'
    and manifest_sha256='10d6c91af793348993a5c90212b6a340646b42518b6d75ac6b1be3b3864e406d'
    and issue_until=timestamptz '2026-12-01 00:00:00+00'
    and scoring_until=timestamptz '2026-12-04 06:00:00+00'
    and scoring_until>clock_timestamp()) then
  raise exception 'MVP_CAPTURE_CRON_MANIFEST_MISMATCH';
 end if;
 select * into v_old from cron.job where jobname='rolling72_mvp_research_v1_capture';
 if found then
  if v_old.command is distinct from v_command or v_old.schedule is distinct from '4-59/5 * * * *'
   or v_old.active is distinct from true or v_old.database is distinct from current_database()
   or v_old.username is distinct from current_user then
   raise exception 'MVP_CAPTURE_CRON_EXISTING_JOB_MISMATCH';
  end if;
 else
  perform cron.schedule('rolling72_mvp_research_v1_capture','4-59/5 * * * *',v_command);
 end if;
end
$install$;
