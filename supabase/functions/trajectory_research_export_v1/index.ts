import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createRemoteJWKSet, jwtVerify } from "npm:jose@5.9.6";

const ISSUER = "https://token.actions.githubusercontent.com";
const AUDIENCE = "beyond-trajectory-research";
const REPOSITORY = "NiedzielX/beyond";
const MAIN_REF = "refs/heads/main";
const JWKS = createRemoteJWKSet(new URL("https://token.actions.githubusercontent.com/.well-known/jwks"));

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

async function dbRpc(name: string, body: unknown) {
  const url = Deno.env.get("SUPABASE_URL");
  const key = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY");
  if (!url || !key) throw new Error("Missing Supabase service environment");

  const response = await fetch(`${url}/rest/v1/rpc/${name}`, {
    method: "POST",
    headers: {
      apikey: key,
      Authorization: `Bearer ${key}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
  });
  const text = await response.text();
  if (!response.ok) throw new Error(`DB RPC ${name} ${response.status}: ${text}`);
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
    const body = await req.json();
    const eventIds = Array.isArray(body?.event_ids)
      ? body.event_ids.map((value: unknown) => Number(value))
      : [];

    if (
      eventIds.length < 1 ||
      eventIds.length > 100 ||
      eventIds.some((value: number) => !Number.isInteger(value) || value <= 0)
    ) {
      throw new Error("event_ids must contain 1..100 positive integers");
    }

    const payload = await dbRpc("export_trajectory_development_rows_v1", {
      p_event_ids: eventIds,
    });

    const eventCount = Number(payload?.event_count ?? 0);
    const rowCount = Number(payload?.row_count ?? 0);
    if (eventCount < 1 || rowCount < 1) {
      throw new Error(`empty trajectory export events=${eventCount} rows=${rowCount}`);
    }

    return json({
      ok: true,
      ...payload,
      repository: claims.repository,
      sha: claims.sha || null,
    });
  } catch (error) {
    return json(
      {
        ok: false,
        version: "trajectory-research-export-gateway-v1",
        error: String(error),
        repository: claims.repository,
        sha: claims.sha || null,
      },
      500,
    );
  }
});
