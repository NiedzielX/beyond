#!/usr/bin/env python3
"""Compatibility runner for d2 Stage 0.

Two explicit adapters are kept local to d2 replay:

1. Freeze lineage is verified by a canonical semantic JSON digest rather than
   whitespace/raw-float serialization bytes. The freeze generator still hard-
   asserts raw MAE to 1e-9 before serializing metrics to 9 decimal places.
2. Current Structural Prior sporting replay gets a complete zero-match league
   state for early-season cutoffs. The shared production materializer is not
   changed. This reproduces the offline historical builder's ability to score
   fixtures before every club has a completed league match.
"""
from __future__ import annotations

import hashlib
import json
from collections import defaultdict, deque
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

import ml.c1_alpha_model_tournament_v1 as c1
import ml.d2_live_replay_anchor_v1 as d2

WARSAW = ZoneInfo("Europe/Warsaw")
FREEZE_SEMANTIC_SHA256 = "da4fe301516ff1ba298b869e7f7ac6d3d316515b2ad0a02ed986bf9a1b8d9c7b"


def semantic_json_sha256(value: object) -> str:
    raw = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def load_and_verify_freeze_manifest_semantic(path: Path) -> dict:
    manifest = json.loads(path.read_text())
    digest = semantic_json_sha256(manifest)
    if digest != FREEZE_SEMANTIC_SHA256:
        raise RuntimeError(
            f"frozen Pre-Live v2 semantic manifest SHA mismatch actual={digest} "
            f"expected={FREEZE_SEMANTIC_SHA256}"
        )
    if manifest.get("freeze_id") != d2.EXPECTED_FREEZE_ID:
        raise RuntimeError(
            f"unexpected freeze_id {manifest.get('freeze_id')} != {d2.EXPECTED_FREEZE_ID}"
        )
    if int(manifest.get("manifest_float_decimals", -1)) != 9:
        raise RuntimeError("frozen Pre-Live v2 manifest serialization contract is not 9 decimals")
    t1 = next(row for row in manifest["horizons"] if row["horizon"] == "T-1")
    if t1["contract"]["current_season_regime"] != "ewma50-resid-k6-cap05-min3":
        raise RuntimeError("frozen T-1 b2 contract changed")
    if t1["contract"]["historical_context_extension"] != "NO_CONTEXT":
        raise RuntimeError("d2 Stage 0 expects no frozen historical c2 extension at T-1")
    return manifest


def complete_sporting_state(
    matches: list[dict],
    aliases: dict[str, str],
    *,
    as_of_at: pd.Timestamp,
    source_season: str,
) -> pd.DataFrame:
    """Rebuild PIT sporting state including zero-match clubs.

    This follows the same completed-fixture/date semantics as the canonical
    current materializer but seeds every club appearing in the source-season
    fixture export. Before a club has played, its statistics are zero/NaN and
    its table position is the deterministic tied-table order by club key.
    """
    cutoff = pd.Timestamp(as_of_at).tz_convert("UTC")
    cutoff_local_date = cutoff.tz_convert(WARSAW).date()
    normalized_source_season = source_season.replace("/", "-")

    season_clubs: set[str] = set()
    for row in matches:
        if str(row.get("season")) != normalized_source_season:
            continue
        home = aliases.get(str(row.get("home_team")))
        away = aliases.get(str(row.get("away_team")))
        if home:
            season_clubs.add(home)
        if away:
            season_clubs.add(away)
    if not season_clubs:
        return c1.build_sporting_state(
            matches,
            aliases,
            as_of_at=as_of_at,
            source_season=source_season,
        )

    state: dict[str, dict] = {
        club: {
            "played": 0,
            "points": 0,
            "gf": 0,
            "ga": 0,
            "last5": deque(maxlen=5),
            "last_kickoff": None,
            "match_times": [],
        }
        for club in season_clubs
    }

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
        local_noon = pd.Timestamp(
            f"{event_date.isoformat()} 12:00:00",
            tz=WARSAW,
        ).tz_convert("UTC")
        usable.append(
            (
                event_date,
                home,
                away,
                int(row["home_score"]),
                int(row["away_score"]),
                local_noon,
            )
        )

    usable.sort(key=lambda x: (x[0], x[1], x[2]))
    for _, home, away, home_goals, away_goals, kickoff in usable:
        for club, gf, ga in (
            (home, home_goals, away_goals),
            (away, away_goals, home_goals),
        ):
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
        (
            (club, s["points"], s["gf"] - s["ga"], s["gf"])
            for club, s in state.items()
        ),
        key=lambda x: (-x[1], -x[2], -x[3], x[0]),
    )
    positions = {club: idx + 1 for idx, (club, *_rest) in enumerate(table)}

    rows = []
    for club in sorted(state):
        s = state[club]
        played = int(s["played"])
        last5 = list(s["last5"])
        n14 = sum(
            1
            for value in s["match_times"]
            if value >= cutoff - pd.Timedelta(days=14)
        )
        rows.append(
            {
                "club_key": club,
                "as_of_at": cutoff,
                "matches_played": played,
                "points": float(s["points"]),
                "ppg": float(s["points"] / played) if played else np.nan,
                "gdpg": float((s["gf"] - s["ga"]) / played) if played else np.nan,
                "form5_points": float(sum(x[0] for x in last5)) if last5 else np.nan,
                "form5_gd": float(sum(x[1] for x in last5)) if last5 else np.nan,
                "last_kickoff_at": s["last_kickoff"] if s["last_kickoff"] is not None else pd.NaT,
                "matches_last14": int(n14),
                "position": int(positions[club]),
            }
        )
    return pd.DataFrame(rows)


# Patch only the C1 replay module namespace used by _event_prior_replay. The
# shared production materializer implementation remains unchanged.
c1.build_sporting_state = complete_sporting_state

d2.EXPECTED_FREEZE_MANIFEST_SHA256 = FREEZE_SEMANTIC_SHA256
d2.load_and_verify_freeze_manifest = load_and_verify_freeze_manifest_semantic


if __name__ == "__main__":
    d2.main()
