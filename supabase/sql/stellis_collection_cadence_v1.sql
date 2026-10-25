-- Canonical Stellis collector cadence.
-- v1/v2/probe functions remain diagnostics only; only v3 is scheduled.

do $$
declare v_job bigint;
begin
  for v_job in
    select jobid from cron.job where jobname in (
      'stellis_public_collect_10m',
      'stellis_collect_v1_10m',
      'stellis_collect_v2_10m',
      'stellis_collect_v3_10m'
    )
  loop
    perform cron.unschedule(v_job);
  end loop;
end $$;

select cron.schedule(
  'stellis_collect_v3_10m',
  '3,13,23,33,43,53 * * * *',
  $$select net.http_get(
      url := 'https://adchzwqboeekhokapxqi.supabase.co/functions/v1/stellis_collect_v3?mode=collect',
      timeout_milliseconds := 120000
    );$$
);
