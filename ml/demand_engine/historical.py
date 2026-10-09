"""Historical forecast adapters for Beyond Demand Engine."""
from __future__ import annotations

import json
import os
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError

from .contracts import ForecastRequest, QuantileForecast


class HistoricalForecastError(RuntimeError):
    pass


class SupabaseStoredHistoricalForecaster:
    """Bridge the current live pipeline into Demand Engine v1.

    This adapter does not retrain or reinterpret the incumbent model. It reads the
    latest already-persisted historical P10/P50/P90 for the event before the new
    engine run. It is therefore suitable for shadow migration while the exact
    v1.7 implementation is being recovered.
    """

    def __init__(
        self,
        supabase_url: str | None = None,
        service_role_key: str | None = None,
        source_model_version: str = "beyond-forecast-v0.3",
    ) -> None:
        self.supabase_url = (supabase_url or os.environ.get("SUPABASE_URL", "")).rstrip("/")
        self.service_role_key = service_role_key or os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
        self.source_model_version = source_model_version
        if not self.supabase_url:
            raise ValueError("SUPABASE_URL is required")
        if not self.service_role_key:
            raise ValueError("SUPABASE_SERVICE_ROLE_KEY is required")

    def forecast(self, request: ForecastRequest) -> QuantileForecast:
        params = urlencode(
            {
                "select": "historical_model,historical_p10,historical_p50,historical_p90,forecast_generated_at",
                "ticket_event_id": f"eq.{request.ticket_event_id}",
                "model_version": f"eq.{self.source_model_version}",
                "historical_p50": "not.is.null",
                "forecast_generated_at": f"lte.{request.forecast_generated_at.isoformat()}",
                "order": "forecast_generated_at.desc,id.desc",
                "limit": "1",
            }
        )
        endpoint = f"{self.supabase_url}/rest/v1/forecast_observations?{params}"
        http_request = Request(
            endpoint,
            method="GET",
            headers={
                "apikey": self.service_role_key,
                "Authorization": f"Bearer {self.service_role_key}",
                "Accept": "application/json",
            },
        )
        try:
            with urlopen(http_request, timeout=30) as response:
                rows = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise HistoricalForecastError(
                f"stored historical forecast query failed with HTTP {exc.code}: {body}"
            ) from exc

        if not rows:
            raise HistoricalForecastError(
                f"No stored historical forecast for event {request.ticket_event_id} "
                f"from {self.source_model_version}"
            )

        row = rows[0]
        if any(row.get(key) is None for key in ("historical_p10", "historical_p50", "historical_p90")):
            raise HistoricalForecastError("Stored historical row is missing P10/P50/P90")

        historical_label = row.get("historical_model") or "stored-historical"
        return QuantileForecast(
            p10=float(row["historical_p10"]),
            p50=float(row["historical_p50"]),
            p90=float(row["historical_p90"]),
            model_name=str(historical_label),
            model_version=self.source_model_version,
            feature_set_version="legacy-stored-lineage",
            interval_method="stored_legacy_interval_unverified",
            calibration_version=None,
        )
