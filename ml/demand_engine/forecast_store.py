"""Persistence adapter for Beyond Demand Engine forecasts."""
from __future__ import annotations

import json
import os
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from .contracts import EngineForecast
from .storage import to_forecast_observation


class SupabaseWriteError(RuntimeError):
    pass


class SupabaseForecastStore:
    """Insert engine output into public.forecast_observations server-side."""

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

    def insert(self, forecast: EngineForecast) -> dict:
        forecast.validate()
        endpoint = f"{self.supabase_url}/rest/v1/forecast_observations"
        payload = json.dumps(to_forecast_observation(forecast)).encode("utf-8")
        request = Request(
            endpoint,
            data=payload,
            method="POST",
            headers={
                "apikey": self.service_role_key,
                "Authorization": f"Bearer {self.service_role_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
                "Prefer": "return=representation",
            },
        )
        try:
            with urlopen(request, timeout=30) as response:
                rows = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise SupabaseWriteError(
                f"forecast_observations insert failed with HTTP {exc.code}: {body}"
            ) from exc

        if not rows:
            raise SupabaseWriteError("forecast_observations insert returned no row")
        return rows[0]
