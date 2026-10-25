-- Service-role read grants for immutable P9 governance registries.
-- Required by SECURITY INVOKER status functions called through the main-only
-- OIDC Edge gateway. No anon/authenticated access is added.

grant select on private.p9_learner_target_freeze_registry_v1 to service_role;
grant select on private.p9_learner_support_freeze_registry_v1 to service_role;
grant select on private.p9_learner_result_registry_v1 to service_role;
