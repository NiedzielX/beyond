import "jsr:@supabase/functions-js/edge-runtime.d.ts";

const VERSION = "stellis-source-probe-v1";
const SOURCES = [
  { club_slug: "koronakielce", base_url: "https://bilety.korona-kielce.pl" },
  { club_slug: "motorlublin", base_url: "https://bilety.motorlublin.eu" },
  { club_slug: "piastgliwice", base_url: "https://bilety.piast-gliwice.eu" },
  { club_slug: "radomiak_radom", base_url: "https://bilety.rksradomiak.pl" },
  { club_slug: "widzewlodz", base_url: "https://bilety.widzew.com" },
] as const;

const HEADERS = {
  "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/126 Safari/537.36",
  "Accept-Language": "pl-PL,pl;q=0.9,en;q=0.8",
};

function uniq(values: string[]) { return [...new Set(values.filter(Boolean))]; }
function clean(value: string) { return value.replace(/\s+/g, " ").trim(); }

function snippets(html: string, ids: string[]) {
  const result: Record<string, string[]> = {};
  for (const id of ids.slice(0, 8)) {
    const matches: string[] = [];
    let start = 0;
    while (matches.length < 3) {
      const index = html.indexOf(id, start);
      if (index < 0) break;
      matches.push(clean(html.slice(Math.max(0, index - 800), Math.min(html.length, index + 1600))));
      start = index + id.length;
    }
    result[id] = matches;
  }
  return result;
}

function extractJsonScripts(html: string) {
  const scripts = [];
  const re = /<script\b([^>]*)>([\s\S]*?)<\/script>/gi;
  let m: RegExpExecArray | null;
  while ((m = re.exec(html)) && scripts.length < 30) {
    const attrs = m[1] || "";
    const body = (m[2] || "").trim();
    const type = attrs.match(/type=["']([^"']+)["']/i)?.[1] || null;
    const id = attrs.match(/id=["']([^"']+)["']/i)?.[1] || null;
    if (type?.includes("json") || id === "__NEXT_DATA__" || body.includes("eventId") || body.includes("availableSeats")) {
      scripts.push({ id, type, length: body.length, prefix: clean(body.slice(0, 1200)) });
    }
  }
  return scripts;
}

async function probe(source: typeof SOURCES[number]) {
  const response = await fetch(`${source.base_url}/`, { headers: HEADERS, redirect: "follow" });
  const html = await response.text();
  const eventIds = uniq([...html.matchAll(/eventId["'=:\s]+(\d+)/gi)].map((m) => m[1]));
  const allNumberIds = uniq([
    ...[...html.matchAll(/eventId=(\d+)/gi)].map((m) => m[1]),
    ...[...html.matchAll(/["']eventId["']\s*:\s*(\d+)/gi)].map((m) => m[1]),
    ...[...html.matchAll(/["']eventId["']\s*:\s*["'](\d+)["']/gi)].map((m) => m[1]),
  ]);
  const ids = uniq([...eventIds, ...allNumberIds]);
  const visibleText = clean(html.replace(/<script[\s\S]*?<\/script>/gi, " ").replace(/<style[\s\S]*?<\/style>/gi, " ").replace(/<[^>]+>/g, " "));
  return {
    club_slug: source.club_slug,
    base_url: source.base_url,
    status: response.status,
    final_url: response.url,
    html_length: html.length,
    event_ids: ids,
    snippets: snippets(html, ids),
    json_scripts: extractJsonScripts(html),
    visible_text_prefix: visibleText.slice(0, 5000),
    known_tokens: {
      occupied: /zaj[eę]tych miejsc/i.test(visibleText),
      available: /dost[eę]pne miejsca/i.test(visibleText),
      sale_open: /sprzeda[zż]\s+otwarta/i.test(visibleText),
    },
  };
}

Deno.serve(async () => {
  const results = [];
  for (const source of SOURCES) {
    try { results.push(await probe(source)); }
    catch (error) { results.push({ club_slug: source.club_slug, base_url: source.base_url, error: String(error) }); }
  }
  return new Response(JSON.stringify({ ok: true, version: VERSION, results, production_change: false }), {
    headers: { "content-type": "application/json" },
  });
});
