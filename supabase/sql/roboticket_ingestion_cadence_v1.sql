-- Roboticket ingestion cadence v1
-- Discovery hourly; unmapped match candidates buffered every 10 minutes.

do $$
declare v_job bigint;
begin
  select jobid into v_job from cron.job where jobname='roboticket_discovery_6h' limit 1;
  if v_job is not null then perform cron.unschedule(v_job); end if;
  select jobid into v_job from cron.job where jobname='roboticket_discovery_hourly' limit 1;
  if v_job is not null then perform cron.unschedule(v_job); end if;
  select jobid into v_job from cron.job where jobname='roboticket_candidate_buffer_10m' limit 1;
  if v_job is not null then perform cron.unschedule(v_job); end if;
end $$;

select cron.schedule(
  'roboticket_discovery_hourly',
  '2 * * * *',
  $$select net.http_get(
      url := 'https://adchzwqboeekhokapxqi.supabase.co/functions/v1/roboticket_discover_clubs',
      headers := jsonb_build_object('x-discovery-key','bt-discovery-v1-Q8m2L5x7R4p9V3k6'),
      timeout_milliseconds := 120000
    );$$
);

select cron.schedule(
  'roboticket_candidate_buffer_10m',
  '7,17,27,37,47,57 * * * *',
  $$select net.http_get(
      url := 'https://adchzwqboeekhokapxqi.supabase.co/functions/v1/roboticket_buffer_candidates_v1',
      timeout_milliseconds := 120000
    );$$
);
