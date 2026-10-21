import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createRemoteJWKSet, jwtVerify } from "npm:jose@5.9.6";

const ISSUER = "https://token.actions.githubusercontent.com";
const AUDIENCE = "beyond-d2-long72-forward";
const REPOSITORY = "NiedzielX/beyond";
const MAIN_REF = "refs/heads/main";
const PACKAGE_ID = "d2-long72-stage2-p2-observation-maturity-2026-10-21-v1";
const MAX_OBSERVATIONS = 100;
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

async function rpc(name: string, body: unknown) {
  const url = Deno.env.get("SUPABASE_URL");
  const key = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY");
  if (!url || !key) throw new Error("missing Supabase service environment");
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
  if (!response.ok) throw new Error(`RPC ${name} ${response.status}: ${text}`);
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
    const observations = Array.isArray(body?.observations) ? body.observations : [];
    if (observations.length > MAX_OBSERVATIONS) {
      throw new Error(`too many observations: ${observations.length}`);
    }
    if (body?.package_id !== PACKAGE_ID) {
      throw new Error(`package id mismatch: ${body?.package_id}`);
    }

    const inserted: Array<{ ticket_event_id: number; source_snapshot_id: number; forecast_observation_id: number }> = [];
    for (const observation of observations) {
      if (observation?.model_version !== PACKAGE_ID) {
        throw new Error(`observation package mismatch event=${observation?.ticket_event_id}`);
      }
      const raw = await rpc("insert_d2_long72_forward_forecast_v1", {
        p_observation: observation,
      });
      const id = Array.isArray(raw) ? Number(raw[0]) : Number(raw);
      if (!Number.isFinite(id) || id <= 0) {
        throw new Error(`invalid persisted forecast id=${String(raw)}`);
      }
      inserted.push({
        ticket_event_id: Number(observation.ticket_event_id),
        source_snapshot_id: Number(observation.source_snapshot_id),
        forecast_observation_id: id,
      });
    }

    return json({
      ok: true,
      version: "d2-long72-forward-shadow-writer-v1",
      package_id: PACKAGE_ID,
      observation_count: observations.length,
      persisted_count: inserted.length,
      persisted: inserted,
      repository: claims.repository,
      sha: claims.sha || null,
      production_change: false,
    });
  } catch (error) {
    return json({
      ok: false,
      version: "d2-long72-forward-shadow-writer-v1",
      package_id: PACKAGE_ID,
      production_change: false,
      error: String(error),
      repository: claims.repository,
      sha: claims.sha || null,
    }, 500);
  }
});
