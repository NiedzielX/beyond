-- Beyond Ticketing Context Matrix v0.1 — browser-facing research projection.
-- Exposes only the frozen research contract. These weights are research priors,
-- not production forecast coefficients.

drop policy if exists dashboard_context_matrix_versions_read on public.context_matrix_versions;
create policy dashboard_context_matrix_versions_read
on public.context_matrix_versions
for select
to anon, authenticated
using (status = 'frozen');

drop policy if exists dashboard_context_feature_definitions_read on public.context_feature_definitions;
create policy dashboard_context_feature_definitions_read
on public.context_feature_definitions
for select
to anon, authenticated
using (is_active = true);

drop policy if exists dashboard_context_feature_weights_read on public.context_feature_weights;
create policy dashboard_context_feature_weights_read
on public.context_feature_weights
for select
to anon, authenticated
using (matrix_version = 'context-v0.1');

grant select (version,target_metric,status,description,created_at)
on public.context_matrix_versions to anon, authenticated;

grant select (
  feature_key,group_key,display_name,description,value_type,production_role,
  refresh_cadence,primary_source,fallback_source,is_active
)
on public.context_feature_definitions to anon, authenticated;

grant select (matrix_version,feature_key,weight_pct,rationale)
on public.context_feature_weights to anon, authenticated;

create or replace view public.dashboard_context_matrix_v1
with (security_invoker = true)
as
select
  w.matrix_version,
  d.feature_key,
  d.group_key,
  d.display_name,
  d.description,
  w.weight_pct,
  d.production_role,
  d.refresh_cadence,
  d.primary_source,
  d.fallback_source,
  w.rationale
from public.context_feature_weights w
join public.context_feature_definitions d on d.feature_key = w.feature_key
join public.context_matrix_versions m on m.version = w.matrix_version
where w.matrix_version = 'context-v0.1'
  and m.status = 'frozen'
  and d.is_active = true;

revoke all on public.dashboard_context_matrix_v1 from public;
grant select on public.dashboard_context_matrix_v1 to anon, authenticated, service_role;
