// Pure checks used only after cryptographic issuer/audience/lifetime verification.
export function assertWorkflowClaims(payload: Record<string, unknown>): void {
  if (payload.repository !== "NiedzielX/beyond" || payload.ref !== "refs/heads/main"
    || payload.workflow_ref !== "NiedzielX/beyond/.github/workflows/daily-inventory-path-shadow-v1.yml@refs/heads/main"
    || typeof payload.sha !== "string" || !/^[0-9a-f]{40}$/.test(payload.sha)) {
    throw new Error("repository/ref/sha not allowed");
  }
}

export function databaseHeaders(key: string): Record<string, string> {
  if (!key) throw new Error("service environment missing");
  const headers: Record<string, string> = { apikey: key, "Content-Type": "application/json" };
  // New opaque Supabase API keys are not JWTs. Do not send them as Bearer JWTs.
  if (!key.startsWith("sb_")) headers.Authorization = `Bearer ${key}`;
  return headers;
}
