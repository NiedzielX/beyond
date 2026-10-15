#!/usr/bin/env python3
"""Materialize genuine current-event T-30/T-14/T-7 Structural Priors.

Normal scheduled runs never fit a model. They load frozen joblib artifacts,
build a point-in-time current-event row from canonical DB evidence, predict P50,
and emit validated forecast payloads for the Supabase gateway to persist.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict, deque
from pathlib import Path
from zoneinfo import ZoneInfo

import joblib
import numpy as np
import pandas as pd

from ml.demand_engine.current_structural_prior_features import (
    CurrentStructuralPriorEvent,
    build_current_structural_prior_row,
)

WARSAW = ZoneInfo("Europe/Warsaw")
SUPPORTED = {"T-30", "T-14", "T-7"}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_frozen_bundle(artifact_dir: Path, required_horizons: set[str]):
    manifest_path = artifact_dir / "manifest.json"
    if not manifest_path.exists():
        raise RuntimeError(f"frozen Structural Prior manifest missing: {manifest_path}")
    manifest = json.loads(manifest_path.read_text())
    historical = artifact_dir / manifest["historical_runtime"]["filename"]
    if sha256_file(historical) != manifest["historical_runtime"]["sha256"]:
        raise RuntimeError("historical runtime hash mismatch")
    models = {}
    for horizon in sorted(required_horizons):
        if horizon not in SUPPORTED:
            continue
        spec = manifest["artifacts"].get(horizon)
        if not spec:
            # Fail closed only when the DB has actually made this horizon due.
            # This keeps rolling deployments safe while a new frozen artifact is
            # being committed, without silently falling back to another model.
            raise RuntimeError(f"frozen Structural Prior artifact missing for due horizon {horizon}")
        path = artifact_dir / spec["filename"]
        if sha256_file(path) != spec["sha256"]:
            raise RuntimeError(f"artifact hash mismatch for {horizon}")
        models[horizon] = joblib.load(path)
    return manifest, pd.read_csv(historical), models


def _aliases(payload: dict) -> dict[str, str]:
    return {str(row["alias"]): str(row["club_key"]) for row in payload.get("aliases", [])}


def build_sporting_state(
    matches: list[dict],
    aliases: dict[str, str],
    *,
    as_of_at: pd.Timestamp,
    source_season: str,
) -> pd.DataFrame:
    """Reconstruct conservative PIT league state from completed fixtures.

    `sporting_league_matches_shadow` currently stores an event date rather than
    exact kickoff. To guarantee no same-day future leakage, a fixture contributes
    only when its local event_date is strictly before the PIT cutoff local date.
    For rest/congestion features, the conservative representative kickoff is
    local noon on that prior date. This convention is versioned in forecast
    lineage and can be replaced once exact historic kickoff timestamps exist.
    """
    cutoff = pd.Timestamp(as_of_at).tz_convert("UTC")
    cutoff_local_date = cutoff.tz_convert(WARSAW).date()
    normalized_source_season = source_season.replace("/", "-")
    state: dict[str, dict] = defaultdict(
        lambda: {
            "played": 0,
            "points": 0,
            "gf": 0,
            "ga": 0,
            "last5": deque(maxlen=5),
            "last_kickoff": None,
            "match_times": [],
        }
    )

    def points(gf: int, ga: int) -> int:
        return 3 if gf > ga else 1 if gf == ga else 0

    usable = []
    for row in matches:
        if str(row.get("season")) != normalized_source_season:
            continue
        if not bool(row.get("completed")):
            continue
        event_date = pd.Timestamp(row["event_date"]).date()
        if event_date >= cutoff_local_date:
            continue
        home = aliases.get(str(row.get("home_team")))
        away = aliases.get(str(row.get("away_team")))
        if not home or not away:
            continue
        if row.get("home_score") is None or row.get("away_score") is None:
            continue
        local_noon = pd.Timestamp(f"{event_date.isoformat()} 12:00:00", tz=WARSAW).tz_convert("UTC")
        usable.append((event_date, home, away, int(row["home_score"]), int(row["away_score"]), local_noon))

    usable.sort(key=lambda x: (x[0], x[1], x[2]))
    for _, home, away, home_goals, away_goals, kickoff in usable:
        for club, gf, ga in ((home, home_goals, away_goals), (away, away_goals, home_goals)):
            s = state[club]
            pts = points(gf, ga)
            s["played"] += 1
            s["points"] += pts
            s["gf"] += gf
            s["ga"] += ga
            s["last5"].append((pts, gf - ga))
            s["last_kickoff"] = kickoff
            s["match_times"].append(kickoff)

    table = sorted(
        ((club, s["points"], s["gf"] - s["ga"], s["gf"]) for club, s in state.items()),
        key=lambda x: (-x[1], -x[2], -x[3], x[0]),
    )
    positions = {club: idx + 1 for idx, (club, *_rest) in enumerate(table)}

    rows = []
    for club, s in state.items():
        if s["played"] <= 0 or s["last_kickoff"] is None:
            continue
        last5 = list(s["last5"])
        n14 = sum(1 for value in s["match_times"] if value >= cutoff - pd.Timedelta(days=14))
        rows.append(
            {
                "club_key": club,
                "as_of_at": cutoff,
                "matches_played": s["played"],
                "points": s["points"],
                "ppg": s["points"] / s["played"],
                "gdpg": (s["gf"] - s["ga"]) / s["played"],
                "form5_points": sum(x[0] for x in last5),
                "form5_gd": sum(x[1] for x in last5),
                "last_kickoff_at": s["last_kickoff"],
                "matches_last14": n14,
                "position": positions[club],
            }
        )
    return pd.DataFrame(rows)


def _stable_feature_hash(row: pd.Series) -> str:
    payload = {}
    for key, value in row.to_dict().items():
        if isinstance(value, pd.Timestamp):
            payload[key] = value.isoformat()
        elif value is None or (isinstance(value, float) and np.isnan(value)):
            payload[key] = None
        elif isinstance(value, (np.integer, np.floating)):
            payload[key] = value.item()
        else:
            payload[key] = value
    raw = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"), default=str)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def materialize(payload: dict, artifact_dir: Path, generated_at: pd.Timestamp) -> dict:
    due_horizons = {
        str(row.get("horizon"))
        for row in payload.get("events") or []
        if row.get("input_status") == "ready" and str(row.get("horizon")) in SUPPORTED
    }
    manifest, historical, models = load_frozen_bundle(artifact_dir, due_horizons)
    aliases = _aliases(payload)
    attendance = pd.DataFrame(payload.get("attendance") or [])
    sporting_matches = payload.get("sportingMatches") or []
    predictions = []
    skipped = []

    for event_row in payload.get("events") or []:
        if event_row.get("input_status") != "ready":
            skipped.append({"ticket_event_id": event_row.get("ticket_event_id"), "reason": event_row.get("input_status")})
            continue
        horizon = str(event_row["horizon"])
        if horizon not in SUPPORTED:
            skipped.append({"ticket_event_id": event_row["ticket_event_id"], "reason": "unsupported_horizon"})
            continue
        target_as_of = pd.Timestamp(event_row["target_as_of_at"])
        if target_as_of.tzinfo is None:
            target_as_of = target_as_of.tz_localize("UTC")
        else:
            target_as_of = target_as_of.tz_convert("UTC")

        sporting_state = build_sporting_state(
            sporting_matches,
            aliases,
            as_of_at=target_as_of,
            source_season=str(event_row["season"]),
        )
        current_event = CurrentStructuralPriorEvent(
            ticket_event_id=int(event_row["ticket_event_id"]),
            season=str(event_row["season"]),
            round_no=int(event_row["round_no"]),
            kickoff_at=pd.Timestamp(event_row["kickoff_at"]),
            home_club_key=str(event_row["home_club_key"]),
            away_club_key=str(event_row["away_club_key"]),
            stadium_capacity=int(event_row["stadium_capacity"]),
        )
        feature_frame = build_current_structural_prior_row(
            historical_matches=historical,
            current_attendance=attendance,
            sporting_state=sporting_state,
            event=current_event,
            horizon=horizon,
        )
        runtime = models[horizon]
        if runtime.spec.model_spec_id != event_row["model_spec_id"]:
            raise RuntimeError(f"model spec mismatch for event {event_row['ticket_event_id']}")
        p50 = float(runtime.predict(feature_frame)[0])
        feature = feature_frame.iloc[0]
        artifact_meta = manifest["artifacts"][horizon]
        predictions.append(
            {
                "ticket_event_id": int(event_row["ticket_event_id"]),
                "horizon": horizon,
                "target_as_of_at": target_as_of.isoformat(),
                "kickoff_at": pd.Timestamp(event_row["kickoff_at"]).isoformat(),
                "model_spec_id": event_row["model_spec_id"],
                "model_family": event_row["model_family"],
                "feature_contract": event_row["feature_contract"],
                "p50": p50,
                "stadium_capacity": int(event_row["stadium_capacity"]),
                "generated_at": generated_at.isoformat(),
                "input_lineage": {
                    "artifact_version": manifest["artifact_version"],
                    "artifact_sha256": artifact_meta["sha256"],
                    "training_seasons": manifest["training_seasons"],
                    "historical_dataset_versions": manifest["historical_dataset_versions"],
                    "historical_runtime_sha256": manifest["historical_runtime"]["sha256"],
                    "feature_store_builder": "ml/features/structural_prior_feature_store_v1.py",
                    "current_feature_builder": "ml/demand_engine/current_structural_prior_features.py",
                    "runtime_impl": "ml/demand_engine/structural_prior_runtime.py",
                    "current_attendance_source": "public.ml_home_attendance_history_v2",
                    "current_sporting_source": "public.sporting_league_matches_shadow",
                    "sporting_pit_rule": "completed fixture event_date strictly before PIT local date; representative local noon for rest/congestion",
                    "capacity_source": event_row["capacity_source_url"],
                    "source_snapshot_id": event_row.get("source_snapshot_id"),
                    "source_snapshot_role": "lineage_anchor_only_not_model_input",
                    "feature_row_sha256": _stable_feature_hash(feature),
                },
                "metadata": {
                    "round_no": int(feature["round_no"]),
                    "home_position": int(feature["home_position"]),
                    "away_position": int(feature["away_position"]),
                    "season_home_n": int(feature["season_home_n"]),
                    "home_history_n": int(feature["home_history_n"]),
                    "baseline_season": None if pd.isna(feature["baseline_season"]) else float(feature["baseline_season"]),
                    "baseline_r3": None if pd.isna(feature["baseline_r3"]) else float(feature["baseline_r3"]),
                    "capacity_verification_status": event_row["capacity_verification_status"],
                    "backfilled_pit_forecast": bool(generated_at > target_as_of),
                    "interval_status": "not_yet_calibrated",
                    "artifact_frozen_no_runtime_fit": True,
                    "benchmark_reproduction": manifest["benchmark_reproduction"][horizon],
                },
            }
        )

    return {
        "version": "structural-prior-materializer-v1",
        "artifact_version": manifest["artifact_version"],
        "predictionCount": len(predictions),
        "skippedCount": len(skipped),
        "predictions": predictions,
        "skipped": skipped,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--artifact-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    payload = json.loads(args.input.read_text())
    result = materialize(payload, args.artifact_dir, pd.Timestamp.now(tz="UTC"))
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False, default=str) + "\n")
    print(json.dumps(result, indent=2, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
