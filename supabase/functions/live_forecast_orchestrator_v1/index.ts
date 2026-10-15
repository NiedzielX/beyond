import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createRemoteJWKSet, jwtVerify } from "npm:jose@5.9.6";

const ISSUER = "https://token.actions.githubusercontent.com";
const AUDIENCE = "beyond-live-forecast-orchestrator";
const REPOSITORY = "NiedzielX/beyond";
const MAIN_REF = "refs/heads/main";
const JWKS = createRemoteJWKSet(
  new URL("https://token.actions.githubusercontent.com/.well-known/jwks"),
);

const json = (body: unknown, status = 200) =>
  new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json" },
  });

async function authorize(req: Request) {
  const auth = req.headers.get("authorization") || "";
  const token = auth.startsWith("Bearer ") ? auth.slice(7) : "";
  if (!token) throw new Error("missing bearer token");

  const { payload } = await jwtVerify(token, JWKS, {
    issuer: ISSUER,
    audience: AUDIENCE,
  });
  if (payload.repository !== REPOSITORY) throw new Error("repository not allowed");
  if (payload.ref !== MAIN_REF) throw new Error("ref not allowed");
  return payload;
}

async function runOrchestrator(requestedAt: string) {
  const url = Deno.env.get("SUPABASE_URL");
  const key = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY");
  if (!url || !key) throw new Error("Missing Supabase service environment");

  const response = await fetch(
    `${url}/rest/v1/rpc/run_live_forecast_orchestrator_v1`,
    {
      method: "POST",
      headers: {
        apikey: key,
        Authorization: `Bearer ${key}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ p_requested_at: requestedAt }),
    },
  );
  const text = await response.text();
  if (!response.ok) {
    throw new Error(`orchestrator RPC ${response.status}: ${text}`);
  }
  return text ? JSON.parse(text) : null;
}

Deno.serve(async (req: Request) => {
  let claims: any;
  try {
    claims = await authorize(req);
  } catch (error) {
    return json({ ok: false, error: `unauthorized: ${String(error)}` }, 401);
  }

  if (req.method !== "POST") {
    return json({ ok: false, error: "method not allowed" }, 405);
  }

  try {
    // Forward-only: use function runtime time, not caller-provided historical time.
    const requestedAt = new Date().toISOString();
    const result = await runOrchestrator(requestedAt);
    return json({
      ok: result?.ok ?? true,
      edgeVersion: "live-forecast-orchestrator-edge-v1",
      requestedAt,
      repository: claims.repository,
      sha: claims.sha || null,
      githubRunId: claims.run_id || null,
      result,
    });
  } catch (error) {
    return json({
      ok: false,
      edgeVersion: "live-forecast-orchestrator-edge-v1",
      error: String(error),
      repository: claims.repository,
      sha: claims.sha || null,
    }, 500);
  }
});
