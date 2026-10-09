"""Server-side Supabase adapters for Beyond Demand Engine.

Never expose the service-role key to a browser/client bundle. This module is
intended only for backend jobs, workers or scheduled forecast runners.
"""
from __future__ import annotations

import json
import os
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from .contracts import ForecastRequest, LiveFeatures
from .live_features import RowLiveFeatureProvider


class SupabaseRpcError(RuntimeError):
    pass


class SupabaseLiveFeatureProvider:
    """Reads the latest versioned live feature row from get_live_features_v1."""

    def __init__(
        self,
        supabase_url: str | None = None,
        service_role_key: str | None = None,
    ) -> None:
        self.supabase_url = (supabase_url or os.environ.get("SUPABASE_URL", "")).rstrip("/")
        self.service_role_key = service_role_key or os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
        if not self.supabase_url:
            raise ValueError("SUPABASE_URL is required")
        if not self.service_role_key:
            raise ValueError("SUPABASE_SERVICE_ROLE_KEY is required")
        self._mapper = RowLiveFeatureProvider(self._fetch_latest)

    def features(self, request: ForecastRequest) -> LiveFeatures:
        return self._mapper.features(request)

    def _fetch_latest(self, ticket_event_id: int):
        endpoint = f"{self.supabase_url}/rest/v1/rpc/get_live_features_v1"
        payload = json.dumps({"p_ticket_event_id": ticket_event_id}).encode("utf-8")
        request = Request(
            endpoint,
            data=payload,
            method="POST",
            headers={
                "apikey": self.service_role_key,
                "Authorization": f"Bearer {self.service_role_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
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
