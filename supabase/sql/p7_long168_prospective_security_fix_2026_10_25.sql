-- P7 Long168 prospective execution plumbing fix.
-- Scientific contract unchanged. This only allows the service-role-only
-- summary/export RPCs to read the private immutable prospective ledger.

alter function public.p7_long168_prospective_summary_v1() security definer;
alter function public.export_p7_long168_prospective_scores_v1() security definer;

revoke all on function public.p7_long168_prospective_summary_v1() from public, anon, authenticated;
revoke all on function public.export_p7_long168_prospective_scores_v1() from public, anon, authenticated;
grant execute on function public.p7_long168_prospective_summary_v1() to service_role;
grant execute on function public.export_p7_long168_prospective_scores_v1() to service_role;
