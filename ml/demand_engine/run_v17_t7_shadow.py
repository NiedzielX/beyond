#!/usr/bin/env python3
"""Run the exact recovered Lech v1.7 T-7 model in shadow mode.

Input is a point-in-time JSON evidence file containing completed league results
and Lech home attendance known by the canonical T-7 checkpoint. The runner:
1. resolves the event and latest inventory snapshot from Supabase;
2. preflights evidence completeness and source auditability;
3. reconstructs strict T-7 sporting state without leakage;
4. runs exact recovered v1.7 T-7 + its matching conformal interval;
5. attaches live-features-v1 with a no-op live correction;
6. persists a separate shadow observation through the protected RPC.

It never replaces or updates production v0.3 rows.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

from .contracts import ForecastRequest
from .engine import DemandEngine
from .storage import SupabaseForecastStore, engine_forecast_to_shadow_observation
from .supabase import SupabaseEventContextProvider, SupabaseLiveFeatureProvider
from .t7_preflight import validate_t7_evidence
from .t7_state import LeagueResult, build_t7_static_features
from .v17_t7 import RecoveredV17T7Forecaster

ENGINE_VERSION = "beyond-demand-engine-v1-v17-t7-shadow"


def _parse_datetime(value: str) -> datetime:
    parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError(f"Datetime must include timezone: {value}")
    return parsed


def _load_evidence(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text())
    required = {
        "season",
        "opponent_key",
        "target_round_no",
        "total_rounds",
        "league_team_keys",
        "completed_results",
        "current_season_home_attendance",
    }
    missing = sorted(required - set(data))
    if missing:
        raise ValueError("Evidence JSON missing fields: " + ", ".join(missing))
    if not isinstance(data["completed_results"], list):
        raise ValueError("completed_results must be a list")
    if not isinstance(data["current_season_home_attendance"], list):
        raise ValueError("current_season_home_attendance must be a list")
    return data


def _league_results(rows: list[dict[str, Any]]) -> list[LeagueResult]:
    result: list[LeagueResult] = []
    for index, row in enumerate(rows):
        try:
            result.append(
                LeagueResult(
                    kickoff_at=_parse_datetime(row["kickoff_at"]),
                    home_team_key=str(row["home_team_key"]),
                    away_team_key=str(row["away_team_key"]),
                    home_goals=int(row["home_goals"]),
                    away_goals=int(row["away_goals"]),
                )
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(f"Invalid completed_results[{index}]: {exc}") from exc
    return result


def run(
    *,
    ticket_event_id: int,
    evidence_path: Path,
    generated_at: datetime,
    dry_run: bool,
) -> dict[str, Any]:
    if generated_at.tzinfo is None:
        raise ValueError("generated_at must be timezone-aware")

    evidence = _load_evidence(evidence_path)
    context = SupabaseEventContextProvider().get(ticket_event_id)
    if context.club_slug.lower() not in {"lech", "lech-poznan", "lech_poznan"}:
        raise ValueError(f"Event {ticket_event_id} is not a Lech home event")

    expected_event = evidence.get("ticket_event_id")
    if expected_event is not None and int(expected_event) != ticket_event_id:
        raise ValueError(
            f"Evidence is for event {expected_event}, requested event is {ticket_event_id}"
        )

    preflight = validate_t7_evidence(
        evidence=evidence,
        ticket_event_id=ticket_event_id,
        home_team=context.home_team,
        away_team=context.away_team,
        competition=context.competition,
        kickoff_at=context.kickoff_at,
        persist=not dry_run,
    )

    static_features = build_t7_static_features(
        season=str(evidence["season"]),
        target_kickoff_at=context.kickoff_at,
        home_team_key=str(evidence.get("home_team_key", "lech")),
        opponent_key=str(evidence["opponent_key"]),
        target_round_no=int(evidence["target_round_no"]),
        total_rounds=int(evidence["total_rounds"]),
        league_team_keys=[str(team) for team in evidence["league_team_keys"]],
        completed_results=_league_results(evidence["completed_results"]),
        current_season_home_attendance=evidence["current_season_home_attendance"],
    )

    request = ForecastRequest(
        ticket_event_id=context.ticket_event_id,
        club_slug=context.club_slug,
        home_team=context.home_team,
        away_team=context.away_team,
        competition=context.competition,
        kickoff_at=context.kickoff_at,
        forecast_generated_at=generated_at,
        source_snapshot_id=context.source_snapshot_id,
        source_snapshot_captured_at=context.source_snapshot_captured_at,
        stadium_capacity=int(evidence.get("stadium_capacity", 43269)),
        static_features=static_features,
    )

    engine = DemandEngine(
        historical_forecaster=RecoveredV17T7Forecaster(),
        live_feature_provider=SupabaseLiveFeatureProvider(),
        engine_version=ENGINE_VERSION,
    )
    forecast = engine.forecast(request)
    observation = engine_forecast_to_shadow_observation(forecast)

    if dry_run:
        return {
            "dry_run": True,
            "preflight": preflight,
            "observation": observation,
        }

    persisted = SupabaseForecastStore().insert(forecast)
    return {
        "dry_run": False,
        "preflight": preflight,
        "persisted": persisted,
        "observation": observation,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--event-id", type=int, required=True)
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument(
        "--generated-at",
        help="Timezone-aware ISO timestamp; default is current UTC time.",
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    generated_at = (
        _parse_datetime(args.generated_at)
        if args.generated_at
        else datetime.now(timezone.utc)
    )
    result = run(
        ticket_event_id=args.event_id,
        evidence_path=args.evidence,
        generated_at=generated_at,
        dry_run=args.dry_run,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()
