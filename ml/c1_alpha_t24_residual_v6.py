#!/usr/bin/env python3
"""C1-alpha T-24 Residual Challenger v6.

One independent row = one completed event.

Purpose:
- test the earlier Ticketing Challenger idea directly against the *current*
  frozen T-1 Structural Prior;
- avoid full-trajectory row duplication;
- use the PIT-safe T-24 `hybrid_v6` signal plus only low-dimensional context;
- validate by whole-event LOEO and, secondarily, leave-one-home-club-out.

No production activation is performed by this experiment.
"""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import HuberRegressor, Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from ml.c1_alpha_model_tournament_v1 import _event_prior_replay


@dataclass(frozen=True)
class Spec:
    name: str
    target_mode: str
    numeric: tuple[str, ...]
    categorical: tuple[str, ...]
    model: Any


FEATURE_SETS: dict[str, tuple[str, ...]] = {
    "hybrid": (
        "hybrid_v6",
        "hybrid_missing",
    ),
    "hybrid_prior": (
        "hybrid_v6",
        "hybrid_missing",
        "prior_expected_occupancy",
    ),
    "hybrid_maturity": (
        "hybrid_v6",
        "hybrid_missing",
        "prior_expected_occupancy",
        "season_home_evidence_n",
        "round_no",
    ),
    "hybrid_quality": (
        "hybrid_v6",
        "hybrid_missing",
        "prior_expected_occupancy",
        "season_home_evidence_n",
        "round_no",
        "hybrid_release_activity",
        "hybrid_sector_coverage_change",
    ),
}

CATEGORICAL = ("hybrid_v6_source",)


def _to_utc(value: Any) -> pd.Timestamp:
    ts = pd.Timestamp(value)
    return ts.tz_localize("UTC") if ts.tzinfo is None else ts.tz_convert("UTC")


def build_event_frame(payload: dict, priors: pd.DataFrame) -> pd.DataFrame:
    events = {int(row["ticket_event_id"]): row for row in payload.get("events") or []}
    hybrid_rows = {
        int(row["ticket_event_id"]): row
        for row in payload.get("ticketingChallengerRows") or []
    }
    attendance = pd.DataFrame(payload.get("attendance") or [])
    if not attendance.empty:
        attendance["kickoff_at"] = pd.to_datetime(attendance["kickoff_at"], utc=True)

    t1 = priors[(priors["horizon"] == "T-1") & priors["prior_p50"].notna()].copy()
    t1_by_event = {
        int(row.ticket_event_id): row
        for row in t1.itertuples(index=False)
    }

    records: list[dict[str, Any]] = []
    for event_id, event in sorted(events.items()):
        prior_row = t1_by_event.get(event_id)
        if prior_row is None:
            continue
        kickoff = _to_utc(event["kickoff_at"])
        checkpoint = kickoff - pd.Timedelta(days=1)
        capacity = float(event["stadium_capacity"])
        actual = float(event["actual_attendance"])
        prior = float(prior_row.prior_p50)
        hybrid = hybrid_rows.get(event_id)

        if attendance.empty:
            season_home_evidence_n = 0.0
        else:
            mask = (
                (attendance["club_slug"].astype(str) == str(event["club_slug"]))
                & (attendance["season"].astype(str) == str(event["season"]))
                & (attendance["kickoff_at"] < checkpoint)
            )
            season_home_evidence_n = float(mask.sum())

        hybrid_value = np.nan if hybrid is None else pd.to_numeric(hybrid.get("hybrid_v6"), errors="coerce")
        source = "missing" if hybrid is None else str(hybrid.get("hybrid_v6_source") or "missing")
        release = np.nan if hybrid is None or hybrid.get("release_activity_flag") is None else float(bool(hybrid.get("release_activity_flag")))
        coverage = np.nan if hybrid is None or hybrid.get("sector_coverage_change_flag") is None else float(bool(hybrid.get("sector_coverage_change_flag")))

        records.append({
            "ticket_event_id": event_id,
            "club_slug": str(event["club_slug"]),
            "home_team": str(event["home_team"]),
            "away_team": str(event["away_team"]),
            "checkpoint_at": checkpoint,
            "stadium_capacity": capacity,
            "actual_attendance": actual,
            "prior_p50": prior,
            "prior_expected_occupancy": prior / capacity,
            "actual_occupancy": actual / capacity,
            "residual_ratio": (actual - prior) / prior if prior else np.nan,
            "residual_occupancy": actual / capacity - prior / capacity,
            "hybrid_v6": hybrid_value,
            "hybrid_missing": float(pd.isna(hybrid_value)),
            "hybrid_v6_source": source,
            "hybrid_release_activity": release,
            "hybrid_sector_coverage_change": coverage,
            "season_home_evidence_n": season_home_evidence_n,
            "round_no": float(event["round_no"]),
        })

    frame = pd.DataFrame(records).sort_values("ticket_event_id").reset_index(drop=True)
    if frame.empty:
        raise RuntimeError("v6 event frame is empty")
    return frame


def preprocessor(numeric: list[str], categorical: list[str]) -> ColumnTransformer:
    return ColumnTransformer([
        (
            "num",
            Pipeline([
                ("impute", SimpleImputer(strategy="median", add_indicator=True)),
                ("scale", StandardScaler()),
            ]),
            numeric,
        ),
        (
            "cat",
            OneHotEncoder(handle_unknown="ignore", sparse_output=False),
            categorical,
        ),
    ], remainder="drop")


def make_model(numeric: list[str], categorical: list[str], estimator: Any) -> Pipeline:
    return Pipeline([
        ("prep", preprocessor(numeric, categorical)),
        ("model", estimator),
    ])


def specs(frame: pd.DataFrame) -> list[Spec]:
    result: list[Spec] = []
    for feature_name, base_features in FEATURE_SETS.items():
        numeric = [f for f in base_features if f in frame.columns]
        categorical = list(CATEGORICAL)
        for target_mode in ("residual_ratio", "residual_occupancy", "direct_occupancy"):
            for alpha in (1.0, 10.0, 30.0, 100.0):
                result.append(Spec(
                    name=f"ridge_{target_mode}_{feature_name}_a{alpha:g}",
                    target_mode=target_mode,
                    numeric=tuple(numeric),
                    categorical=tuple(categorical),
                    model=make_model(numeric, categorical, Ridge(alpha=alpha)),
                ))
            for epsilon, alpha in ((1.35, 0.001), (1.5, 0.01)):
                result.append(Spec(
                    name=f"huber_{target_mode}_{feature_name}_e{epsilon:g}_a{alpha:g}",
                    target_mode=target_mode,
                    numeric=tuple(numeric),
                    categorical=tuple(categorical),
                    model=make_model(
                        numeric,
                        categorical,
                        HuberRegressor(epsilon=epsilon, alpha=alpha, max_iter=2000),
                    ),
                ))
    return result


def target_values(frame: pd.DataFrame, mode: str) -> np.ndarray:
    if mode == "residual_ratio":
        return frame["residual_ratio"].astype(float).to_numpy()
    if mode == "residual_occupancy":
        return frame["residual_occupancy"].astype(float).to_numpy()
    if mode == "direct_occupancy":
        return frame["actual_occupancy"].astype(float).to_numpy()
    raise KeyError(mode)


def prediction_from_model(spec: Spec, train: pd.DataFrame, test: pd.DataFrame) -> np.ndarray:
    xcols = list(spec.numeric) + list(spec.categorical)
    model = clone(spec.model)
    model.fit(train[xcols], target_values(train, spec.target_mode))
    raw = np.asarray(model.predict(test[xcols]), dtype=float)
    prior = test["prior_p50"].astype(float).to_numpy()
    capacity = test["stadium_capacity"].astype(float).to_numpy()

    if spec.target_mode == "residual_ratio":
        prediction = prior * (1.0 + raw)
    elif spec.target_mode == "residual_occupancy":
        prediction = prior + raw * capacity
    elif spec.target_mode == "direct_occupancy":
        prediction = raw * capacity
    else:
        raise KeyError(spec.target_mode)
    return np.clip(prediction, 0.0, capacity)


def fold_iterator(frame: pd.DataFrame, protocol: str) -> Iterable[tuple[str, pd.DataFrame, pd.DataFrame]]:
    if protocol == "leave_one_event_out":
        for event_id in sorted(frame["ticket_event_id"].astype(int).unique()):
            test = frame[frame["ticket_event_id"] == event_id].copy()
            train = frame[frame["ticket_event_id"] != event_id].copy()
            yield str(event_id), train, test
        return
    if protocol == "leave_one_club_out":
        for club in sorted(frame["club_slug"].astype(str).unique()):
            test = frame[frame["club_slug"] == club].copy()
            train = frame[frame["club_slug"] != club].copy()
            yield club, train, test
        return
    raise KeyError(protocol)


def bias_prediction(train: pd.DataFrame, test: pd.DataFrame, statistic: str) -> np.ndarray:
    residuals = train["residual_ratio"].astype(float)
    correction = float(residuals.mean() if statistic == "mean" else residuals.median())
    prior = test["prior_p50"].astype(float).to_numpy()
    capacity = test["stadium_capacity"].astype(float).to_numpy()
    return np.clip(prior * (1.0 + correction), 0.0, capacity)


def evaluate(frame: pd.DataFrame, protocol: str, name: str, spec: Spec | None = None) -> dict[str, Any]:
    predictions: list[dict[str, Any]] = []
    for fold_key, train, test in fold_iterator(frame, protocol):
        if name == "structural_prior":
            pred = test["prior_p50"].astype(float).to_numpy()
        elif name == "bias_mean":
            pred = bias_prediction(train, test, "mean")
        elif name == "bias_median":
            pred = bias_prediction(train, test, "median")
        else:
            if spec is None:
                raise RuntimeError("model spec missing")
            pred = prediction_from_model(spec, train, test)

        for idx, (_, row) in enumerate(test.iterrows()):
            actual = float(row["actual_attendance"])
            prior = float(row["prior_p50"])
            p = float(pred[idx])
            predictions.append({
                "fold": fold_key,
                "ticket_event_id": int(row["ticket_event_id"]),
                "club_slug": str(row["club_slug"]),
                "home_team": str(row["home_team"]),
                "away_team": str(row["away_team"]),
                "hybrid_v6": None if pd.isna(row["hybrid_v6"]) else float(row["hybrid_v6"]),
                "hybrid_v6_source": str(row["hybrid_v6_source"]),
                "prior_p50": prior,
                "prediction": p,
                "actual_attendance": actual,
                "prior_error": abs(prior - actual),
                "error": abs(p - actual),
            })

    prior_mae = float(np.mean([r["prior_error"] for r in predictions]))
    mae = float(np.mean([r["error"] for r in predictions]))
    degradations = [r["error"] - r["prior_error"] for r in predictions]
    return {
        "candidate": name,
        "target_mode": None if spec is None else spec.target_mode,
        "protocol": protocol,
        "event_count": int(frame["ticket_event_id"].nunique()),
        "club_count": int(frame["club_slug"].nunique()),
        "prior_mae": prior_mae,
        "mae": mae,
        "absolute_uplift": prior_mae - mae,
        "relative_improvement": (prior_mae - mae) / prior_mae if prior_mae else 0.0,
        "event_improvement_rate": float(np.mean([r["error"] < r["prior_error"] for r in predictions])),
        "worst_event_degradation": float(max(degradations)),
        "median_absolute_error": float(np.median([r["error"] for r in predictions])),
        "bias": float(np.mean([r["prediction"] - r["actual_attendance"] for r in predictions])),
        "predictions": predictions,
    }


def oracle_switch(frame: pd.DataFrame, challenger: dict[str, Any]) -> dict[str, float]:
    rows = challenger["predictions"]
    return {
        "prior_mae": float(np.mean([r["prior_error"] for r in rows])),
        "challenger_mae": float(np.mean([r["error"] for r in rows])),
        "oracle_prior_or_challenger_mae": float(np.mean([min(r["prior_error"], r["error"]) for r in rows])),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--artifact-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    payload = json.loads(args.input.read_text())
    if payload.get("version") != "c1-alpha-training-export-v2":
        raise RuntimeError(f"v6 requires export v2, got {payload.get('version')}")

    priors = _event_prior_replay(payload, args.artifact_dir)
    frame = build_event_frame(payload, priors)
    all_specs = specs(frame)

    results: dict[str, list[dict[str, Any]]] = {}
    for protocol in ("leave_one_event_out", "leave_one_club_out"):
        leaderboard = [
            evaluate(frame, protocol, "structural_prior"),
            evaluate(frame, protocol, "bias_mean"),
            evaluate(frame, protocol, "bias_median"),
        ]
        for spec in all_specs:
            try:
                leaderboard.append(evaluate(frame, protocol, spec.name, spec))
            except Exception as exc:
                leaderboard.append({
                    "candidate": spec.name,
                    "target_mode": spec.target_mode,
                    "protocol": protocol,
                    "error": str(exc),
                    "mae": float("inf"),
                    "worst_event_degradation": float("inf"),
                })
        leaderboard.sort(key=lambda row: (
            row.get("mae", float("inf")),
            row.get("worst_event_degradation", float("inf")),
            row.get("candidate", ""),
        ))
        results[protocol] = leaderboard

    loeo = results["leave_one_event_out"]
    best = loeo[0]
    best_name = best["candidate"]
    loco_match = next(
        (r for r in results["leave_one_club_out"] if r.get("candidate") == best_name),
        None,
    )

    report = {
        "experiment": "c1-alpha-t24-residual-v6",
        "dataset_version": payload.get("version"),
        "unit": "one event at T-24h",
        "event_count": int(frame["ticket_event_id"].nunique()),
        "club_count": int(frame["club_slug"].nunique()),
        "hybrid_event_count": int(frame["hybrid_v6"].notna().groupby(frame["ticket_event_id"]).any().sum()),
        "candidate_count": len(all_specs) + 3,
        "selection_protocol": "leave_one_event_out",
        "secondary_protocol": "leave_one_club_out",
        "best": best,
        "best_loco": loco_match,
        "goal": {
            "beat_structural_prior": bool(best.get("mae", float("inf")) < best.get("prior_mae", -float("inf"))),
            "under_1900": bool(best.get("mae", float("inf")) < 1900.0),
            "under_1700": bool(best.get("mae", float("inf")) < 1700.0),
            "under_1500_stretch": bool(best.get("mae", float("inf")) < 1500.0),
        },
        "oracle_diagnostic_not_for_selection": oracle_switch(frame, best),
        "leaderboards": results,
        "event_frame": frame.to_dict(orient="records"),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False, default=str) + "\n")

    print(json.dumps({
        "experiment": report["experiment"],
        "event_count": report["event_count"],
        "club_count": report["club_count"],
        "hybrid_event_count": report["hybrid_event_count"],
        "best": {k: best.get(k) for k in (
            "candidate", "target_mode", "prior_mae", "mae", "absolute_uplift",
            "relative_improvement", "event_improvement_rate", "worst_event_degradation",
            "median_absolute_error", "bias"
        )},
        "best_loco": None if loco_match is None else {k: loco_match.get(k) for k in (
            "candidate", "prior_mae", "mae", "absolute_uplift", "relative_improvement",
            "event_improvement_rate", "worst_event_degradation"
        )},
        "goal": report["goal"],
        "oracle_diagnostic_not_for_selection": report["oracle_diagnostic_not_for_selection"],
        "top_10_loeo": [
            {k: row.get(k) for k in (
                "candidate", "target_mode", "mae", "absolute_uplift",
                "relative_improvement", "event_improvement_rate", "worst_event_degradation"
            )}
            for row in loeo[:10]
        ],
        "best_predictions": best.get("predictions"),
    }, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
