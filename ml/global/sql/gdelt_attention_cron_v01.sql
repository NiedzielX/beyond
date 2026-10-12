-- Beyond Ticketing Attention & Hype v0.1 scheduler.
-- Deployed cadence: every 3 hours, one upcoming Lech match per run.
-- Replace <BEYOND_GDELT_CRON_SECRET> at deployment time; never commit the runtime secret.
-- Raw attention observations are research-only and MUST NOT modify production forecasts.

select cron.schedule(
  'gdelt_attention_lech_3h',
  '52 */3 * * *',
  $$
  select net.http_post(
    url := 'https://adchzwqboeekhokapxqi.supabase.co/functions/v1/gdelt_attention_v01',
    headers := jsonb_build_object(
      'Content-Type','application/json',
      'x-beyond-cron','<BEYOND_GDELT_CRON_SECRET>'
    ),
    body := '{}'::jsonb,
    timeout_milliseconds := 45000
  );
  $$
);
