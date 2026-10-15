-- Structural Prior Materializer v1 — minimal writer permission fix
-- Applied to production on 2026-10-15 after the first frozen-artifact
-- materialization run exposed that the SECURITY INVOKER writer reads the
-- current model spec before validating/inserting a prior.

grant select on private.structural_prior_model_specs_v1 to service_role;
