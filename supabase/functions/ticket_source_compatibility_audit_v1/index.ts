import "jsr:@supabase/functions-js/edge-runtime.d.ts";

const VERSION = "ticket-source-compatibility-audit-v1";
const SOURCES = [
  { club_slug: "koronakielce", base_url: "https://bilety.korona-kielce.pl" },
  { club_slug: "motorlublin", base_url: "https://bilety.motorlublin.eu" },
  { club_slug: "piastgliwice", base_url: "https://bilety.piast-gliwice.eu" },
  { club_slug: "radomiak_radom", base_url: "https://bilety.rksradomiak.pl" },
  { club_slug: "widzewlodz", base_url: "https://bilety.widzew.com" },
  { club_slug: "wieczysta_krakow", base_url: "https://bilety.kswieczysta.com" },
] as const;

const HEADERS = {
  "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/126 Safari/537.36",
  "Accept-Language": "pl-PL,pl;q=0.9,en;q=0.8",
};

function uniq(values: string[]) { return [...new Set(values.filter(Boolean))]; }

function extractEventIds(html: string): string[] {
  return uniq([
    ...[...html.matchAll(/eventId=(\d+)/gi)].map((m) => m[1]),
    ...[...html.matchAll(/eventReservationSelector\((\d+)/gi)].map((m) => m[1]),
  ]);
}

function classify(html: string, finalUrl: string, layouts: string[], eventIds: string[]) {
  const lower = html.toLowerCase();
  const roboticketSignals = [
    lower.includes("roboticket"),
    lower.includes("eventreservationselector"),
    lower.includes("/stadium/index?eventid="),
    layouts.length > 0,
    finalUrl.toLowerCase().includes("roboticket"),
  ].filter(Boolean).length;
  const stellisSignals = [
    lower.includes("stellis"),
    lower.includes("api-motor.stellis.dev"),
    finalUrl.toLowerCase().includes("stellis"),
  ].filter(Boolean).length;

  if (roboticketSignals >= 2 || (roboticketSignals >= 1 && eventIds.length > 0)) {
    return { provider_family: "roboticket", confidence: "high", roboticket_signals: roboticketSignals, stellis_signals: stellisSignals };
  }
  if (stellisSignals > 0) {
    return { provider_family: "stellis", confidence: "high", roboticket_signals: roboticketSignals, stellis_signals: stellisSignals };
  }
  return { provider_family: "unknown", confidence: "low", roboticket_signals: roboticketSignals, stellis_signals: stellisSignals };
}

async function auditSource(source: typeof SOURCES[number]) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 15000);
  try {
    const response = await fetch(`${source.base_url}/`, { headers: HEADERS, redirect: "follow", signal: controller.signal });
    const html = await response.text();
    const layouts = uniq([...html.matchAll(/https:\/\/static-fr\.roboticket\.com\/Content\/[^"']+?\.html/gi)].map((m) => m[0])).slice(0, 20);
    const docs = [{ url: response.url, html }];
    for (const url of layouts.slice(0, 12)) {
      try {
        const r = await fetch(url, { headers: HEADERS, redirect: "follow" });
        docs.push({ url: r.url, html: await r.text() });
      } catch {
        // Keep auditing remaining sources fail-closed.
      }
    }
    const eventIds = uniq(docs.flatMap((d) => extractEventIds(d.html)));
    const combined = docs.map((d) => d.html).join("\n");
    const classification = classify(combined, response.url, layouts, eventIds);
    return {
      club_slug: source.club_slug,
      base_url: source.base_url,
      status: response.status,
      final_url: response.url,
      html_length: html.length,
      layout_count: layouts.length,
      event_ids: eventIds.slice(0, 50),
      event_id_count: eventIds.length,
      ...classification,
      compatible_with_existing_roboticket_discovery:
        classification.provider_family === "roboticket" && eventIds.length > 0,
    };
  } catch (error) {
    return {
      club_slug: source.club_slug,
      base_url: source.base_url,
      error: String(error),
      provider_family: "unknown",
      confidence: "none",
      compatible_with_existing_roboticket_discovery: false,
    };
  } finally {
    clearTimeout(timer);
  }
}

Deno.serve(async () => {
  const results = [];
  for (const source of SOURCES) results.push(await auditSource(source));
  return new Response(JSON.stringify({
    ok: true,
    version: VERSION,
    checked_at: new Date().toISOString(),
    results,
    production_change: false,
  }), { headers: { "content-type": "application/json" } });
});
