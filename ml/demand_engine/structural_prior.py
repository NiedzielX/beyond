"""Versioned Structural Prior adapter for Beyond Live Demand Engine.

The live engine must consume the validated historical champion without silently
retraining it, falling back to an older Lech-only incumbent, or applying a model
outside its validated competition domain.

P10/P90 remain optional at this stage. Structural Prior v1 is primarily a P50
contract; probabilistic live forecasting is a later phase.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
import json
import os
from typing import Any, Callable, Literal, Mapping
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from .contracts import ForecastRequest

Horizon = Literal["T-30", "T-14", "T-7", "T-3", "T-1"]


class StructuralPriorError(RuntimeError):
    pass


class StructuralPriorNotDueError(StructuralPriorError):
    pass


class StructuralPriorUnavailableError(StructuralPriorError):
    pass


class StructuralPriorOutOfDomainError(StructuralPriorError):
    pass


@dataclass(frozen=True)
class StructuralPriorSpec:
    horizon: Horizon
    target_days_before: int
    model_spec_id: str
    model_family: str
    feature_contract: str
    validation_report: str
    validated_competitions: tuple[str, ...]
    status: str = "historical_champion_candidate"


CURRENT_STRUCTURAL_PRIOR_SPECS: dict[Horizon, StructuralPriorSpec] = {
    "T-30": StructuralPriorSpec(
        horizon="T-30",
        target_days_before=30,
        model_spec_id="global-v2-verified-capacity-occupancy-t30",
        model_family="GradientBoostingRegressor",
        feature_contract="global-pit-v2+verified-capacity-v1",
        validation_report="ml/results/BEYOND_GLOBAL_FORECAST_V2_2_VERIFIED_CAPACITY_2026-10-14.md",
        validated_competitions=("Ekstraklasa",),
    ),
    "T-14": StructuralPriorSpec(
        horizon="T-14",
        target_days_before=14,
        model_spec_id="global-v2-verified-capacity-occupancy-t14",
        model_family="HistGradientBoostingRegressor",
        feature_contract="global-pit-v2+verified-capacity-v1",
        validation_report="ml/results/BEYOND_GLOBAL_FORECAST_V2_2_VERIFIED_CAPACITY_2026-10-14.md",
        validated_competitions=("Ekstraklasa",),
    ),
    "T-7": StructuralPriorSpec(
        horizon="T-7",
        target_days_before=7,
        model_spec_id="global-v2-verified-capacity-occupancy-t7",
        model_family="GradientBoostingRegressor",
        feature_contract="global-pit-v2+verified-capacity-v1",
        validation_report="ml/results/BEYOND_GLOBAL_FORECAST_V2_2_VERIFIED_CAPACITY_2026-10-14.md",
        validated_competitions=("Ekstraklasa",),
    ),
    "T-3": StructuralPriorSpec(
        horizon="T-3",
        target_days_before=3,
        model_spec_id="global-v2.3-verified-capacity-importance-t3",
        model_family="HistGradientBoostingRegressor",
        feature_contract="global-pit-v2+verified-capacity-v1+match-importance-v1",
        validation_report="ml/results/BEYOND_GLOBAL_FORECAST_V2_3_CAPACITY_IMPORTANCE_COMBO_2026-10-15.md",
        validated_competitions=("Ekstraklasa",),
    ),
    "T-1": StructuralPriorSpec(
        horizon="T-1",
        target_days_before=1,
        model_spec_id="global-v2.3-verified-capacity-importance-t1",
        model_family="HistGradientBoostingRegressor",
        feature_contract="global-pit-v2+verified-capacity-v1+match-importance-v1",
        validation_report="ml/results/BEYOND_GLOBAL_FORECAST_V2_3_CAPACITY_IMPORTANCE_COMBO_2026-10-15.md",
        validated_competitions=("Ekstraklasa",),
    ),
}


@dataclass(frozen=True)
class StructuralPrior:
    ticket_event_id: int
    horizon: Horizon
    requested_as_of_at: datetime
    target_as_of_at: datetime
    kickoff_at: datetime
    model_spec_id: str
    model_family: str
    feature_contract: str
    p50: float
    p10: float | None = None
    p90: float | None = None
    stadium_capacity: int | None = None
    expected_occupancy: float | None = None
    point_in_time_validated: bool = True
    source_prior_id: int | None = None
    generated_at: datetime | None = None
    metadata: Mapping[str, Any] | None = None

    def validate(self) -> None:
        if self.target_as_of_at > self.requested_as_of_at:
            raise StructuralPriorError("Structural prior target cutoff is after requested as_of")
        if self.target_as_of_at >= self.kickoff_at:
            raise StructuralPriorError("Structural prior target cutoff must be before kickoff")
        if not self.point_in_time_validated:
            raise StructuralPriorError("Structural prior is not point-in-time validated")
        if self.p50 < 0:
            raise StructuralPriorError("Structural prior P50 cannot be negative")
        if self.stadium_capacity is not None and self.p50 > self.stadium_capacity:
            raise StructuralPriorError("Structural prior P50 exceeds stadium capacity")
        if self.p10 is not None and self.p90 is not None and not self.p10 <= self.p50 <= self.p90:
            raise StructuralPriorError("Structural prior interval is not ordered")


def resolve_structural_prior_spec(
    *,
    kickoff_at: datetime,
    requested_as_of_at: datetime,
) -> tuple[StructuralPriorSpec, datetime]:
    """Resolve the latest already-due validated historical checkpoint.

    Carry-forward is intentionally one-way. At T-10 the system may use T-14,
    but never the future T-7 prior.
    """
    _require_aware("kickoff_at", kickoff_at)
    _require_aware("requested_as_of_at", requested_as_of_at)
    hours_to_kickoff = (kickoff_at - requested_as_of_at).total_seconds() / 3600.0
    if hours_to_kickoff <= 0:
        raise StructuralPriorError("requested_as_of_at must be before kickoff")
    if hours_to_kickoff > 30 * 24:
        raise StructuralPriorNotDueError("No Structural Prior checkpoint is due before T-30")

    if hours_to_kickoff > 14 * 24:
        horizon: Horizon = "T-30"
    elif hours_to_kickoff > 7 * 24:
        horizon = "T-14"
    elif hours_to_kickoff > 3 * 24:
        horizon = "T-7"
    elif hours_to_kickoff > 1 * 24:
        horizon = "T-3"
    else:
        horizon = "T-1"

    spec = CURRENT_STRUCTURAL_PRIOR_SPECS[horizon]
    target_as_of = kickoff_at - timedelta(days=spec.target_days_before)
    if target_as_of > requested_as_of_at:
        raise StructuralPriorError("Resolved prior would use a future checkpoint")
    return spec, target_as_of


class RowStructuralPriorAdapter:
    """Validate and expose a materialized current Structural Prior row."""

    def __init__(self, fetch_prior: Callable[[int, datetime], Mapping[str, Any] | None]) -> None:
        self.fetch_prior = fetch_prior

    def prior(self, request: ForecastRequest) -> StructuralPrior:
        spec, target_as_of = resolve_structural_prior_spec(
            kickoff_at=request.kickoff_at,
            requested_as_of_at=request.forecast_generated_at,
        )
        if request.competition not in spec.validated_competitions:
            raise StructuralPriorOutOfDomainError(
                f"{spec.model_spec_id} is not validated for competition {request.competition!r}; "
                f"validated competitions: {', '.join(spec.validated_competitions)}"
            )

        row = self.fetch_prior(request.ticket_event_id, request.forecast_generated_at)
        if not row:
            raise StructuralPriorUnavailableError(
                f"No materialized structural prior for event {request.ticket_event_id} at {spec.horizon}"
            )

        status = str(row.get("status") or "ready")
        if status == "out_of_domain":
            raise StructuralPriorOutOfDomainError(
                f"Structural prior is out of domain for event {request.ticket_event_id}"
            )
        if status != "ready":
            raise StructuralPriorUnavailableError(
                f"Structural prior status is {status!r} for event {request.ticket_event_id}"
            )
        if row.get("model_spec_id") != spec.model_spec_id:
            raise StructuralPriorError(
                f"Wrong model spec for {spec.horizon}: expected {spec.model_spec_id}, got {row.get('model_spec_id')}"
            )
        if row.get("feature_contract") != spec.feature_contract:
            raise StructuralPriorError(
                f"Wrong feature contract for {spec.horizon}: expected {spec.feature_contract}, got {row.get('feature_contract')}"
            )

        row_target = _datetime(row.get("target_as_of_at"), "target_as_of_at")
        row_kickoff = _datetime(row.get("kickoff_at"), "kickoff_at")
        if row_target != target_as_of:
            raise StructuralPriorError(
                f"Wrong target cutoff for {spec.horizon}: expected {target_as_of.isoformat()}, got {row_target.isoformat()}"
            )
        if row_kickoff != request.kickoff_at:
            raise StructuralPriorError("Structural prior kickoff does not match request")

        capacity = _int(row.get("stadium_capacity"))
        p50 = float(row["p50"])
        occupancy = _float(row.get("expected_occupancy"))
        if occupancy is None and capacity:
            occupancy = p50 / capacity

        prior = StructuralPrior(
            ticket_event_id=request.ticket_event_id,
            horizon=spec.horizon,
            requested_as_of_at=request.forecast_generated_at,
            target_as_of_at=row_target,
            kickoff_at=row_kickoff,
            model_spec_id=spec.model_spec_id,
            model_family=spec.model_family,
            feature_contract=spec.feature_contract,
            p50=p50,
            p10=_float(row.get("p10")),
            p90=_float(row.get("p90")),
            stadium_capacity=capacity,
            expected_occupancy=occupancy,
            point_in_time_validated=bool(row.get("point_in_time_validated", False)),
            source_prior_id=_int(row.get("source_prior_id") or row.get("id")),
            generated_at=_datetime_optional(row.get("generated_at")),
            metadata=row.get("metadata") if isinstance(row.get("metadata"), Mapping) else None,
        )
        prior.validate()
        return prior


class SupabaseStructuralPriorAdapter(RowStructuralPriorAdapter):
    """Fetch Structural Prior v1 through a versioned Supabase RPC."""

    def __init__(self, supabase_url: str | None = None, service_role_key: str | None = None) -> None:
        self.supabase_url = (supabase_url or os.environ.get("SUPABASE_URL", "")).rstrip("/")
        self.service_role_key = service_role_key or os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
        if not self.supabase_url:
            raise ValueError("SUPABASE_URL is required")
        if not self.service_role_key:
            raise ValueError("SUPABASE_SERVICE_ROLE_KEY is required")
        super().__init__(self._fetch)

    def _fetch(self, ticket_event_id: int, requested_as_of_at: datetime) -> Mapping[str, Any] | None:
        endpoint = f"{self.supabase_url}/rest/v1/rpc/get_structural_prior_v1"
        payload = json.dumps(
            {
                "p_ticket_event_id": ticket_event_id,
                "p_requested_as_of_at": requested_as_of_at.isoformat(),
            }
        ).encode("utf-8")
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
            raise StructuralPriorError(
                f"get_structural_prior_v1 failed with HTTP {exc.code}: {body}"
            ) from exc
        if not rows:
            return None
        return rows[0]


def _require_aware(name: str, value: datetime) -> None:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")


def _datetime(value: Any, name: str) -> datetime:
    parsed = _datetime_optional(value)
    if parsed is None:
        raise StructuralPriorError(f"Structural prior row is missing {name}")
    return parsed


def _datetime_optional(value: Any) -> datetime | None:
    if value is None:
        return None
    parsed = value if isinstance(value, datetime) else datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    _require_aware("datetime value", parsed)
    return parsed


def _float(value: Any) -> float | None:
    return None if value is None else float(value)


def _int(value: Any) -> int | None:
    return None if value is None else int(value)
