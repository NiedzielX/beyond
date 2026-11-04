# Prepared daily-path gateway validation

Status:complete for isolated validation. Hosted run41811081476passed actual Deno typecheck,6policy/header tests, and the real entry point's isolated HTTP405/401checks, alongside PostgreSQL and typed-feed tests. The function is still undeployed; no successful live OIDC request or production DB-chain proof is claimed.

Validate the undeployed Edge gateway using Deno's real typecheck and isolated authorization/header unit tests in cloud CI. Keep issuer/audience, exact repository/main/workflow restrictions and trusted Python inference boundary. Require normal signed GitHub token lifetime claims; do not mint or use production tokens in tests.

Check service-key transport consistently with the existing Python reader: opaque `sb_` API keys belong in `apikey`, while legacy JWT keys may also use Bearer authorization. No keys or request headers may be logged. This source change does not deploy a gateway, enable its schedule or change frozen prediction semantics.

Acceptance: typecheck and negative claim/header tests pass; run the actual Deno entry point on isolated localhost without inherited credentials and check405/401responses before body parsing. Production credentials are absent from the test job; migration/typed-feed checks stay green. A locally rejected request is not a successful live signed OIDC request. Live Deno/OIDC and production DB-chain proof remain separate deployment steps.
