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

async function rpc(name: string, body: unknown = {}) {
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

function unwrap(value: any, functionName: string) {
  if (Array.isArray(value)) {
    return value[0]?.[functionName] ?? value[0]?.payload ?? value[0] ?? null;
  }
  return value;
}

Deno.serve(async (req: Request) => {
  let claims: any;
  try {
    claims = await authorize(req);
  } catch (error) {
    return json({ ok: false, error: `unauthorized: ${String(error)}` }, 401);
  }

  const requestedAt = new Date().toISOString();
  try {
    if (req.method === "GET") {
      const forwardName = "get_d2_long72_forward_inputs_v1";
      const attendanceName = "export_c1_alpha_v7_attendance_v1";
      const sportingName = "export_c1_alpha_v7_sporting_v1";
      const aliasesName = "export_c1_alpha_v7_aliases_v1";
      const capacityName = "export_d2_capacity_registry_v1";

      const [forwardRaw, attendanceRaw, sportingRaw, aliasesRaw, capacityRaw] =
        await Promise.all([
          rpc(forwardName, { p_requested_at: requestedAt }),
          rpc(attendanceName),
          rpc(sportingName),
          rpc(aliasesName),
          rpc(capacityName),
        ]);

      const forward = unwrap(forwardRaw, forwardName);
      if (forward?.packageId !== PACKAGE_ID) {
        throw new Error(`forward package mismatch: ${forward?.packageId}`);
      }
      if (forward?.outcomeAccessAllowed !== false) {
        throw new Error("forward input must not expose target outcomes");
      }

      return json({
        ok: true,
        version: "d2-long72-forward-gateway-v1",
        requested_at: requestedAt,
        package_id: PACKAGE_ID,
        forward,
        attendance: unwrap(attendanceRaw, attendanceName),
        sporting: unwrap(sportingRaw, sportingName),
        aliases: unwrap(aliasesRaw, aliasesName),
        capacity: unwrap(capacityRaw, capacityName),
        repository: claims.repository,
        sha: claims.sha || null,
        production_change: false,
      });
    }

    if (req.method !== "POST") {
      return json({ ok: false, error: "method not allowed" }, 405);
    }

    const body = await req.json();
    const action = String(body?.action || "");
    if (body?.package_id && body.package_id !== PACKAGE_ID) {
      throw new Error(`package id mismatch: ${body.package_id}`);
    }

    if (action === "persist") {
      const observations = Array.isArray(body?.observations) ? body.observations : [];
      if (observations.length > MAX_OBSERVATIONS) {
        throw new Error(`too many observations: ${observations.length}`);
      }
      const resultRaw = await rpc("insert_d2_long72_forward_predictions_v1", {
        p_rows: observations,
        p_requested_at: body?.requested_at || requestedAt,
      });
      return json({
        ok: true,
        version: "d2-long72-forward-gateway-v1",
        action,
        package_id: PACKAGE_ID,
        result: unwrap(resultRaw, "insert_d2_long72_forward_predictions_v1"),
        repository: claims.repository,
        sha: claims.sha || null,
        production_change: false,
      });
    }

    if (action === "score") {
      const resultRaw = await rpc("score_d2_long72_forward_completed_events_v1", {
        p_requested_at: body?.requested_at || requestedAt,
      });
      return json({
        ok: true,
        version: "d2-long72-forward-gateway-v1",
        action,
        package_id: PACKAGE_ID,
        result: unwrap(resultRaw, "score_d2_long72_forward_completed_events_v1"),
        repository: claims.repository,
        sha: claims.sha || null,
        production_change: false,
      });
    }

    throw new Error(`unsupported action: ${action}`);
  } catch (error) {
    return json({
      ok: false,
      version: "d2-long72-forward-gateway-v1",
      package_id: PACKAGE_ID,
      production_change: false,
      error: String(error),
      repository: claims.repository,
      sha: claims.sha || null,
    }, 500);
  }
});
