// Run the real undeployed entry point locally with no inherited credentials.
// These negative HTTP checks do not prove a live GitHub OIDC/Supabase request.
import assert from "node:assert/strict";

Deno.test("actual gateway rejects unsupported methods and unauthenticated requests", async () => {
  const environment: Record<string, string> = {};
  for (const name of ["HOME", "DENO_DIR"]) {
    const value = Deno.env.get(name);
    if (value) environment[name] = value;
  }
  const child = new Deno.Command(Deno.execPath(), {
    args: ["run", "--cached-only", "--allow-env", "--allow-net=0.0.0.0:8000,127.0.0.1:8000",
      new URL("./index.ts", import.meta.url).pathname],
    clearEnv: true, env: environment, stdin: "null", stdout: "null", stderr: "piped",
  }).spawn();
  const url = "http://127.0.0.1:8000";
  try {
    let ready = false;
    for (let count = 0; count < 100; count++) {
      try {
        const response = await fetch(url);
        assert.equal(response.status, 405);
        assert.deepEqual(await response.json(), { error: "method not allowed" });
        ready = true;
        break;
      } catch {
        await new Promise((resolve) => setTimeout(resolve, 50));
      }
    }
    assert.ok(ready, "isolated gateway did not become ready");
    for (const authorization of [null, "Bearer invalid.synthetic.token"]) {
      const headers: Record<string, string> = { "Content-Type": "application/json" };
      if (authorization) headers.Authorization = authorization;
      const response = await fetch(url, { method: "POST", headers, body: "malformed body must not reach parsing" });
      assert.equal(response.status, 401);
      assert.deepEqual(await response.json(), { error: "unauthorized" });
    }
  } finally {
    try { child.kill("SIGTERM"); } catch { /* Already exited. */ }
    const output = await child.output();
    // Synthetic runtime only; failure diagnostics never include service credentials.
    if (output.stderr.length) console.error(new TextDecoder().decode(output.stderr));
  }
});
