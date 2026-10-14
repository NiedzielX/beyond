import "jsr:@supabase/functions-js/edge-runtime.d.ts";

type JsonPrimitive = string | number | boolean | null;
type JsonValue = JsonPrimitive | JsonValue[] | { [key: string]: JsonValue };

interface AssignmentRow {
  subjectKeyHash: string;
  armKey: "treatment" | "holdout";
  assignedAt?: string;
  sourceRecordKey?: string;
  metadata?: Record<string, JsonValue>;
}

interface ArmMetrics {
  armKey: "treatment" | "holdout";
  assignedCount: number;
  exposedCount: number;
  purchasersCount: number;
  ticketsCount: number;
  grossTicketRevenue: number;
  refundsAmount?: number;
  campaignCost?: number;
  metadata?: Record<string, JsonValue>;
}

interface ExecutionPayload {
  experimentKey: string;
  sourceName: string;
  batchKey: string;
  assignmentMode: "exact_manifest" | "aggregate_only";
  observedAt: string;
  assignments?: AssignmentRow[];
  arms?: ArmMetrics[];
  metadata?: Record<string, JsonValue>;
}

const MAX_BODY_BYTES = 2_000_000;
const MAX_ASSIGNMENTS = 5_000;
const FORBIDDEN_KEYS = new Set([
  "email",
  "emailaddress",
  "phone",
  "phonenumber",
  "firstname",
  "lastname",
  "fullname",
  "address",
  "customerid",
  "customername",
  "customeremail",
  "customerphone",
  "userid",
  "subjectid",
]);

const json = (body: unknown, status = 200) => new Response(JSON.stringify(body), {
  status,
  headers: { "content-type": "application/json" },
});

function normalizeKey(value: string): string {
  return value.replace(/[_\-\s]/g, "").toLowerCase();
}

function assertNoRawPii(value: unknown, path = "payload"): void {
  if (Array.isArray(value)) {
    value.forEach((item, index) => assertNoRawPii(item, `${path}[${index}]`));
    return;
  }
  if (typeof value !== "object" || value === null) return;

  for (const [key, child] of Object.entries(value)) {
    if (FORBIDDEN_KEYS.has(normalizeKey(key))) {
      throw new Error(`raw PII field is not allowed: ${path}.${key}`);
    }
    assertNoRawPii(child, `${path}.${key}`);
  }
}

function stableSerialize(value: unknown): string {
  if (value === null || typeof value !== "object") return JSON.stringify(value);
  if (Array.isArray(value)) return `[${value.map(stableSerialize).join(",")}]`;

  const objectValue = value as Record<string, unknown>;
  const keys = Object.keys(objectValue).filter((key) => key !== "payloadSha256").sort();
  return `{${keys.map((key) => `${JSON.stringify(key)}:${stableSerialize(objectValue[key])}`).join(",")}}`;
}

async function sha256Hex(value: string): Promise<string> {
  const bytes = new TextEncoder().encode(value);
  const digest = await crypto.subtle.digest("SHA-256", bytes);
  return Array.from(new Uint8Array(digest)).map((byte) => byte.toString(16).padStart(2, "0")).join("");
}

function parsePayload(value: unknown): ExecutionPayload {
  if (typeof value !== "object" || value === null || Array.isArray(value)) throw new Error("JSON object required");
  const row = value as Record<string, unknown>;

  const requiredText = (key: string) => {
    const candidate = row[key];
    if (typeof candidate !== "string" || candidate.trim() === "") throw new Error(`${key} required`);
    return candidate.trim();
  };

  const assignmentMode = requiredText("assignmentMode");
  if (assignmentMode !== "exact_manifest" && assignmentMode !== "aggregate_only") {
    throw new Error("assignmentMode must be exact_manifest or aggregate_only");
  }

  const assignments = row.assignments === undefined ? [] : row.assignments;
  const arms = row.arms === undefined ? [] : row.arms;
  if (!Array.isArray(assignments)) throw new Error("assignments must be an array");
  if (!Array.isArray(arms)) throw new Error("arms must be an array");
  if (assignments.length > MAX_ASSIGNMENTS) throw new Error(`assignments may contain at most ${MAX_ASSIGNMENTS} rows`);
  if (arms.length > 2) throw new Error("arms may contain at most treatment and holdout rows");

  const payload: ExecutionPayload = {
    experimentKey: requiredText("experimentKey"),
    sourceName: requiredText("sourceName"),
    batchKey: requiredText("batchKey"),
    assignmentMode,
    observedAt: requiredText("observedAt"),
    assignments: assignments as AssignmentRow[],
    arms: arms as ArmMetrics[],
  };

  if (row.metadata !== undefined) payload.metadata = row.metadata as Record<string, JsonValue>;
  return payload;
}

function authorizeServiceRole(req: Request): void {
  const serviceKey = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY");
  if (!serviceKey) throw new Error("service environment unavailable");
  const auth = req.headers.get("authorization") ?? "";
  const token = auth.startsWith("Bearer ") ? auth.slice(7) : "";
  if (!token || token !== serviceKey) throw new Error("service authorization required");
}

async function callIngestRpc(payload: Record<string, unknown>): Promise<unknown> {
  const supabaseUrl = Deno.env.get("SUPABASE_URL");
  const serviceKey = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY");
  if (!supabaseUrl || !serviceKey) throw new Error("service environment unavailable");

  const response = await fetch(`${supabaseUrl}/rest/v1/rpc/ingest_growth_execution_batch_v2`, {
    method: "POST",
    headers: {
      apikey: serviceKey,
      Authorization: `Bearer ${serviceKey}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ p_payload: payload }),
  });

  const text = await response.text();
  let body: unknown = null;
  try {
    body = text ? JSON.parse(text) : null;
  } catch {
    body = null;
  }

  if (!response.ok) {
    const message = typeof body === "object" && body !== null && "message" in body && typeof (body as { message?: unknown }).message === "string"
      ? (body as { message: string }).message
      : "execution batch rejected";
    throw new Error(message);
  }
  return body;
}

Deno.serve(async (req: Request) => {
  if (req.method !== "POST") return json({ ok: false, error: "method not allowed" }, 405);

  try {
    authorizeServiceRole(req);
  } catch {
    return json({ ok: false, error: "unauthorized" }, 401);
  }

  try {
    const contentLength = Number(req.headers.get("content-length") ?? "0");
    if (Number.isFinite(contentLength) && contentLength > MAX_BODY_BYTES) {
      return json({ ok: false, error: "payload too large" }, 413);
    }

    const raw = await req.text();
    if (new TextEncoder().encode(raw).byteLength > MAX_BODY_BYTES) return json({ ok: false, error: "payload too large" }, 413);

    let parsed: unknown;
    try {
      parsed = JSON.parse(raw);
    } catch {
      return json({ ok: false, error: "invalid JSON" }, 400);
    }

    assertNoRawPii(parsed);
    const payload = parsePayload(parsed);
    const payloadSha256 = await sha256Hex(stableSerialize(payload));
    const rpcPayload: Record<string, unknown> = {
      ...payload,
      payloadSha256,
      actor: `edge:growth_execution_ingest_v1:${payload.sourceName}`,
    };

    const result = await callIngestRpc(rpcPayload);
    return json({ ok: true, ingest: result, payloadSha256 });
  } catch (error) {
    const message = error instanceof Error ? error.message : "execution batch rejected";
    return json({ ok: false, error: message }, 400);
  }
});
