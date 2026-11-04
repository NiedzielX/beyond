# Prepared daily-path gateway validation

Validate the undeployed Edge gateway using Deno's real typecheck and isolated authorization/header unit tests in cloud CI. Keep issuer/audience, exact repository/main/workflow restrictions and trusted Python inference boundary. Require normal signed GitHub token lifetime claims; do not mint or use production tokens in tests.

Check service-key transport consistently with the existing Python reader: opaque `sb_` API keys belong in `apikey`, while legacy JWT keys may also use Bearer authorization. No keys or request headers may be logged. This source change does not deploy a gateway, enable its schedule or change frozen prediction semantics.

Acceptance: typecheck and negative claim/header tests pass; production credentials are absent from the test job; migration/typed-feed checks stay green. Live Deno/OIDC request and production DB-chain proof remain separate deployment steps.
