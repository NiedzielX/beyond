"""Server-side Supabase adapters for Beyond Demand Engine.

Never expose the service-role key to a browser/client bundle. This module is
intended only for backend jobs, workers or scheduled forecast runners.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import json
import os
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from .contracts import ForecastRequest, LiveFeatures
from .live_features import RowLiveFeatureProvider


class SupabaseRpcError(RuntimeError):
    pass


@dataclass(frozen=True)
class EventRuntimeContext:
    ticket_event_id: int
    club_slug: str
    home_team: str
    away_team: str
    competition: str
    kickoff_at: datetime
    source_snapshot_id: int
    source_snapshot_captured_at: datetime


class _SupabaseServerClient:
    def __init__(
        self,
        supabase_url: str | None = None,
        service_role_key: str | None = None,
    ) -> None:
        self.supabase_url = (supabase_url or os.environ.get("SUPABASE_URL", "")).rstrip("/")
        self.service_role_key = service_role_key or os.environ.get(
            "SUPABASE_SERVICE_ROLE_KEY", ""
        )
        if not self.supabase_url:
            raise ValueError("SUPABASE_URL is required")
        if not self.service_role_key:
            raise ValueError("SUPABASE_SERVICE_ROLE_KEY is required")

    def _headers(self) -> dict[str, str]:
        return {
            "apikey": self.service_role_key,
            "Authorization": f"Bearer {self.service_role_key}",
            "Accept": "application/json",
        }

    def _get(self, table: str, params: dict[str, str]):
        endpoint = f"{self.supabase_url}/rest/v1/{table}?{urlencode(params)}"
        request = Request(endpoint, method="GET", headers=self._headers())
        try:
            with urlopen(request, timeout=30) as response:
                return json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise SupabaseRpcError(
                f"Supabase GET {table} failed with HTTP {exc.code}: {body}"
            ) from exc


class SupabaseEventContextProvider(_SupabaseServerClient):
    """Resolve one event plus the latest inventory snapshot for a backend run."""

    def get(self, ticket_event_id: int) -> EventRuntimeContext:
        events = self._get(
            "ticket_events",
            {
                "select": "id,club_slug,home_team,away_team,competition,kickoff_at",
                "id": f"eq.{ticket_event_id}",
                "limit": "1",
            },
        )
        if not events:
            raise SupabaseRpcError(f"ticket_event_id {ticket_event_id} does not exist")
        event = events[0]
        if not event.get("kickoff_at"):
            raise SupabaseRpcError(f"ticket_event_id {ticket_event_id} has no kickoff_at")

        snapshots = self._get(
            "snapshots",
            {
                "select": "id,ticket_event_id,captured_at",
                "ticket_event_id": f"eq.{ticket_event_id}",
                "order": "captured_at.desc,id.desc",
                "limit": "1",
            },
        )
        if not snapshots:
            raise SupabaseRpcError(
                f"ticket_event_id {ticket_event_id} has no inventory snapshot"
            )
        snapshot = snapshots[0]

        return EventRuntimeContext(
            ticket_event_id=int(event["id"]),
            club_slug=str(event.get("club_slug") or ""),
            home_team=str(event["home_team"]),
            away_team=str(event["away_team"]),
            competition=str(event.get("competition") or ""),
            kickoff_at=datetime.fromisoformat(str(event["kickoff_at"]).replace("Z", "+00:00")),
            source_snapshot_id=int(snapshot["id"]),
            source_snapshot_captured_at=datetime.fromisoformat(
                str(snapshot["captured_at"]).replace("Z", "+00:00")
            ),
        )


class SupabaseLiveFeatureProvider(_SupabaseServerClient):
    """Reads the latest versioned live feature row from get_live_features_v1."""

    def __init__(
        self,
        supabase_url: str | None = None,
        service_role_key: str | None = None,
    ) -> None:
        super().__init__(supabase_url, service_role_key)
        self._mapper = RowLiveFeatureProvider(self._fetch_latest)

    def features(self, request: ForecastRequest) -> LiveFeatures:
        return self._mapper.features(request)

    def _fetch_latest(self, ticket_event_id: int):
        endpoint = f"{self.supabase_url}/rest/v1/rpc/get_live_features_v1"
        payload = json.dumps({"p_ticket_event_id": ticket_event_id}).encode("utf-8")
        headers = self._headers()
        headers["Content-Type"] = "application/json"
        request = Request(
            endpoint,
            data=payload,
            method="POST",
            headers=headers,
        )
        try:
            with urlopen(request, timeout=30) as response:
                rows = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise SupabaseRpcError(
                f"get_live_features_v1 failed with HTTP {exc.code}: {body}"
            ) from exc

        if not rows:
            return None
        return rows[0]
