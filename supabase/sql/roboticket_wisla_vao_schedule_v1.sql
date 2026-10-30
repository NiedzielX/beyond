-- Beyond Ticketing — Wisla Krakow Roboticket VAO collector schedule v1
--
-- Companion schedule for supabase/functions/roboticket_vao_collect_v1/index.ts.
-- No credential is embedded because the collector accepts no parameters and is
-- hard-scoped to verified future Wisla Krakow Roboticket events. The collector
-- is fail-closed and writes only when the Roboticket frontend contract exposes
-- a complete geometry-matched set of genuinely selectable anonymous seats.
--
-- It never writes available_total=0. If public selectable inventory is absent,
-- the run returns no_public_selectable_seats and persists nothing.

select cron.schedule(
  'roboticket-wisla-vao-15m',
  '*/15 * * * *',
  $$select net.http_post(
      url := 'https://adchzwqboeekhokapxqi.supabase.co/functions/v1/roboticket_vao_collect_v1',
      headers := '{"Content-Type":"application/json"}'::jsonb,
      body := '{}'::jsonb,
      timeout_milliseconds := 30000
    );$$
);
