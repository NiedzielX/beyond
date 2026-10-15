-- Register Structural Prior v1 in the canonical Live Demand Engine contract registry.

insert into private.live_model_contract_registry_v1(
    contract_name,contract_version,object_name,object_kind,status,activated_at,notes
) values
('structural_prior_specs','v1','private.current_structural_prior_model_specs_v1','view','current','2026-10-15T00:00:00Z','Current horizon-specific historical champion specifications.'),
('structural_prior_store','v1','private.structural_prior_forecasts_v1','table','current','2026-10-15T00:00:00Z','Append-only materialized Structural Prior forecasts.'),
('structural_prior_resolver','v1','public.get_structural_prior_v1','function','current','2026-10-15T00:00:00Z','Resolves latest already-due Structural Prior checkpoint with no legacy fallback.')
on conflict(contract_name,contract_version) do update
set object_name=excluded.object_name,
    object_kind=excluded.object_kind,
    status=excluded.status,
    notes=excluded.notes;
