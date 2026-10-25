-- Ticketing ingestion safety-net security hardening.
-- The dashboard frontend reads dashboard_ticketing_ingestion_status_v1.
-- Keep the lower-level helper view service-role only and security-invoker.

alter view public.dashboard_ticketing_ingestion_v1 set (security_invoker = true);
revoke all on public.dashboard_ticketing_ingestion_v1 from public, anon, authenticated;
grant select on public.dashboard_ticketing_ingestion_v1 to service_role;
