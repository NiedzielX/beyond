import { assertWorkflowClaims, databaseHeaders } from "./policy.ts";

function assert(condition: unknown, message: string): asserts condition {
  if (!condition) throw new Error(message);
}

function rejected(run: () => void) {
  let failed = false;
  try { run(); } catch { failed = true; }
  assert(failed, "invalid authorization/credential input was accepted");
}

const fixture = () => ({
  repository: "NiedzielX/beyond", ref: "refs/heads/main", sha: "a".repeat(40),
  workflow_ref: "NiedzielX/beyond/.github/workflows/daily-inventory-path-shadow-v1.yml@refs/heads/main",
});

Deno.test("exact main-workflow claims pass the post-signature policy", () => {
  assertWorkflowClaims(fixture());
});

Deno.test("other repositories, branches, workflows and invalid SHAs fail closed", () => {
  const cases = [
    { repository: "other/beyond" }, { ref: "refs/heads/feature" }, { ref: "refs/pull/1/merge" },
    { workflow_ref: "NiedzielX/beyond/.github/workflows/other.yml@refs/heads/main" },
    { workflow_ref: "NiedzielX/beyond/.github/workflows/daily-inventory-path-shadow-v1.yml@refs/heads/feature" },
    { sha: "bad" }, { sha: "a".repeat(39) }, { sha: null }, { sha: "A".repeat(40) },
  ];
  for (const change of cases) rejected(() => assertWorkflowClaims({ ...fixture(), ...change }));
});

Deno.test("missing workflow identity fails closed", () => {
  rejected(() => assertWorkflowClaims({}));
});

Deno.test("opaque Supabase fixture key uses apikey without Bearer", () => {
  const headers = databaseHeaders("sb_secret_synthetic_test_only");
  assert(headers.apikey === "sb_secret_synthetic_test_only", "apikey missing");
  assert(!("Authorization" in headers), "opaque key must not be a Bearer JWT");
});

Deno.test("legacy JWT fixture preserves Bearer support", () => {
  const headers = databaseHeaders("synthetic.jwt.fixture");
  assert(headers.Authorization === "Bearer synthetic.jwt.fixture", "legacy Bearer support missing");
});

Deno.test("empty service key is rejected", () => {
  rejected(() => databaseHeaders(""));
});
