"""Beyond Ticketing media-attention collector v0.1 using GDELT DOC 2.0.

The collector is intentionally research-only. It records raw article volume and
short-term acceleration but never changes production attendance forecasts.
GDELT DOC 2.0 does not require a project API key.
"""
from __future__ import annotations

import json
import math
import unicodedata
from datetime import datetime, timedelta, timezone
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from .sporting_context_v01 import ContextCollectorError, SupabaseRest, TicketEvent, _utc_now, _iso


GDELT_DOC_URL = "https://api.gdeltproject.org/api/v2/doc/doc"


def _ascii_name(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    return "".join(ch for ch in normalized if not unicodedata.combining(ch))


def build_match_query(event: TicketEvent) -> str:
    home = _ascii_name(event.home_team).replace('"', '')
    away = _ascii_name(event.away_team).replace('"', '')
    return f'"{home}" "{away}"'


def _parse_gdelt_date(value: str) -> datetime:
    # Timeline JSON commonly returns YYYYMMDDTHHMMSSZ.
    return datetime.strptime(value, "%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc)


def summarize_timeline_raw(payload: dict[str, Any], now: datetime | None = None) -> dict[str, Any]:
    now = now or _utc_now()
    timeline = payload.get("timeline") or []
    if not timeline:
        return {
            "total_7d": 0,
            "last_24h": 0,
            "previous_24h": 0,
            "acceleration_ratio": None,
            "coverage_per_million": 0.0,
            "points": 0,
        }

    data = timeline[0].get("data") or []
    total = recent = previous = norm_total = 0.0
    recent_start = now - timedelta(hours=24)
    previous_start = now - timedelta(hours=48)

    for point in data:
        value = float(point.get("value") or 0)
        norm = float(point.get("norm") or 0)
        total += value
        norm_total += norm
        try:
            observed = _parse_gdelt_date(str(point.get("date")))
        except (TypeError, ValueError):
            continue
        if recent_start <= observed <= now:
            recent += value
        elif previous_start <= observed < recent_start:
            previous += value

    if recent == 0 and previous == 0:
        acceleration = None
    else:
        # +1 smoothing prevents division-by-zero explosions on tiny samples.
        acceleration = (recent + 1.0) / (previous + 1.0)

    coverage_per_million = (total / norm_total * 1_000_000.0) if norm_total > 0 else 0.0
    return {
        "total_7d": int(round(total)),
        "last_24h": int(round(recent)),
        "previous_24h": int(round(previous)),
        "acceleration_ratio": None if acceleration is None else round(acceleration, 4),
        "coverage_per_million": round(coverage_per_million, 6),
        "points": len(data),
    }


class GdeltDocClient:
    def timeline_vol_raw(self, query: str, timespan: str = "7d") -> dict[str, Any]:
        params = urlencode({
            "query": query,
            "mode": "TimelineVolRaw",
            "format": "json",
            "timespan": timespan,
            "TIMELINESMOOTH": 0,
        })
        request = Request(
            f"{GDELT_DOC_URL}?{params}",
            method="GET",
            headers={
                "Accept": "application/json",
                "User-Agent": "BeyondTicketingResearch/0.1",
            },
        )
        with urlopen(request, timeout=45) as response:
            content_type = response.headers.get("content-type", "")
            raw = response.read().decode("utf-8", errors="replace")
        if "json" not in content_type.lower():
            raise ContextCollectorError(f"GDELT returned non-JSON response: {raw[:300]}")
        return json.loads(raw)


def collect_event(db: SupabaseRest, client: GdeltDocClient, event: TicketEvent, observed_at: datetime) -> dict[str, Any]:
    query = build_match_query(event)
    payload = client.timeline_vol_raw(query, "7d")
    summary = summarize_timeline_raw(payload, observed_at)
    hour_key = observed_at.astimezone(timezone.utc).strftime("%Y%m%dT%H")

    acceleration = summary["acceleration_ratio"]
    if acceleration is None:
        direction = "brak wystarczającego sygnału"
    elif acceleration >= 1.5:
        direction = "uwaga medialna przyspiesza"
    elif acceleration <= 0.67:
        direction = "uwaga medialna słabnie"
    else:
        direction = "uwaga medialna jest stabilna"

    db.insert_observation({
        "ticket_event_id": event.id,
        "feature_key": "hype.media_attention",
        "observed_at": _iso(observed_at),
        "numeric_value": summary["last_24h"],
        "text_value": (
            f"Media: {summary['last_24h']} publikacji w ostatnich 24h, "
            f"{summary['previous_24h']} w poprzednich 24h; {direction}."
        ),
        "source_name": "GDELT DOC 2.0 TimelineVolRaw",
        "source_url": GDELT_DOC_URL,
        "source_record_key": f"gdelt:media-attention:v01:{event.id}:{hour_key}",
        "confidence": 0.75,
        "metadata": {
            "query": query,
            "window": "7d",
            **summary,
            "scoring_status": "raw_media_attention_not_model_scored",
        },
    })
    return summary


def run(days: int = 30) -> dict[str, Any]:
    db = SupabaseRest()
    client = GdeltDocClient()
    observed_at = _utc_now()
    events = db.upcoming_events(days=days)
    result = {"events": len(events), "collected": 0, "failed": 0}
    for event in events:
        try:
            collect_event(db, client, event, observed_at)
            result["collected"] += 1
        except Exception as exc:  # keep one bad query from killing the batch
            result["failed"] += 1
            print(f"event {event.id}: media attention collection failed: {exc}")
    print(json.dumps(result, ensure_ascii=False))
    return result


if __name__ == "__main__":
    run()
