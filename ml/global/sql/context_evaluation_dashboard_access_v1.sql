-- Browser-safe access for Context Snapshot & Ablation dashboards.
-- Raw JSON payloads/metadata remain service-role only; browser roles receive only
-- the limited columns required by the security-invoker dashboard views.

drop policy if exists dashboard_context_checkpoint_read on public.context_checkpoint_definitions;
create policy dashboard_context_checkpoint_read
on public.context_checkpoint_definitions
for select to anon,authenticated
using (is_active=true);

grant select (checkpoint_code,hours_before_kickoff,sort_order,is_active,description)
on public.context_checkpoint_definitions to anon,authenticated;

drop policy if exists dashboard_context_snapshot_summary_read on public.event_context_snapshots_v1;
create policy dashboard_context_snapshot_summary_read
on public.event_context_snapshots_v1
for select to anon,authenticated
using (true);

grant select (
  id,ticket_event_id,checkpoint_code,checkpoint_at,captured_at,capture_mode,
  baseline_historical_p50,snapshot_status,context_observed_count,context_total_count,
  blocked_feature_count,degraded_feature_count
) on public.event_context_snapshots_v1 to anon,authenticated;

drop policy if exists dashboard_context_ablation_variant_read on public.context_ablation_variants_v1;
create policy dashboard_context_ablation_variant_read
on public.context_ablation_variants_v1
for select to anon,authenticated
using (is_active=true);

grant select (variant_key,sort_order,display_name,description,is_active)
on public.context_ablation_variants_v1 to anon,authenticated;

drop policy if exists dashboard_context_ablation_prediction_read on public.context_ablation_predictions_v1;
create policy dashboard_context_ablation_prediction_read
on public.context_ablation_predictions_v1
for select to anon,authenticated
using (true);

grant select (snapshot_id,variant_key,predicted_p50)
on public.context_ablation_predictions_v1 to anon,authenticated;
