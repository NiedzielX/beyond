#!/usr/bin/env python3
"""Curated wrapper for historical multi-season dataset v2.

The raw Paszport API has exactly one null attendance in the 2021/22–2024/25
scope: Radomiak Radom 2-2 Piast Gliwice, 2021-12-14 (Paszport id 17964).
Independent contemporary sources state that the match was played without
spectators after the stadium was closed by the Mazovian voivode.

Therefore this is not an imputation. The verified attendance is 0 and the row
is explicitly marked as a closed-door exception that should not enter standard
demand-model training or historical home-demand baselines by default.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd
import requests

from ml.data.build_historical_multiseason_v2 import (
    DATASET_VERSION,
    fetch_pasport,
    load_reference,
    normalize_pasport,
    quality_and_join,
)

VERIFIED_ATTENDANCE_OVERRIDES = {
    "17964": {
        "attendance": 0,
        "season": "2021/2022",
        "home_team": "Radomiak Radom",
        "away_team": "Piast Gliwice",
        "home_goals": 2,
        "away_goals": 2,
        "canonical_date": "2021-12-14",
        "exception_type": "closed_doors_government_order",
        "reason": "Match played without public attendance after stadium closure.",
        "verification_sources": [
            "https://sport.tvp.pl/57433264/pko-ekstraklasa-radomiak-zagra-z-piastem-bez-kibicow",
            "https://sport.dziennik.pl/pilka-nozna/ekstraklasa/artykuly/8314382,radomiak-radom-leandro-piast-gliwice.html",
        ],
    }
}


def apply_verified_overrides(paszport: pd.DataFrame) -> tuple[pd.DataFrame, list[dict]]:
    data = paszport.copy()
    applied: list[dict] = []

    for paszport_id, override in VERIFIED_ATTENDANCE_OVERRIDES.items():
        mask = data["paszport_id"].astype(str).eq(paszport_id)
        if int(mask.sum()) != 1:
            raise RuntimeError(
                f"Verified override {paszport_id}: expected exactly one source row, got {int(mask.sum())}"
            )
        row = data.loc[mask].iloc[0]
        checks = {
            "season": str(row["season"]) == override["season"],
            "home_team": str(row["home_name_raw"]) == override["home_team"],
            "away_team": str(row["away_name_raw"]) == override["away_team"],
            "home_goals": int(row["home_goals"]) == override["home_goals"],
            "away_goals": int(row["away_goals"]) == override["away_goals"],
            "source_attendance_is_null": pd.isna(row["attendance"]),
        }
        failed = [name for name, ok in checks.items() if not ok]
        if failed:
            raise RuntimeError(
                f"Verified override {paszport_id} source identity changed; failed checks={failed}"
            )

        data.loc[mask, "attendance"] = override["attendance"]
        applied.append({"paszport_id": paszport_id, **override})

    return data, applied


def annotate_output(output: pd.DataFrame, applied: list[dict]) -> pd.DataFrame:
    out = output.copy()
    out["attendance_source_kind"] = "source_observed"
    out["attendance_exception"] = pd.NA
    out["default_demand_training_eligible"] = True
    out["attendance_verification_sources"] = pd.NA

    by_id = {item["paszport_id"]: item for item in applied}
    for paszport_id, item in by_id.items():
        mask = out["paszport_id"].astype(str).eq(paszport_id)
        if int(mask.sum()) != 1:
            raise RuntimeError(
                f"Output annotation {paszport_id}: expected one row, got {int(mask.sum())}"
            )
        out.loc[mask, "attendance_source_kind"] = "verified_external_override"
        out.loc[mask, "attendance_exception"] = item["exception_type"]
        out.loc[mask, "default_demand_training_eligible"] = False
        out.loc[mask, "attendance_verification_sources"] = ";".join(
            item["verification_sources"]
        )
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()

    session = requests.Session()
    paszport = normalize_pasport(fetch_pasport(session))
    paszport, applied = apply_verified_overrides(paszport)
    reference = load_reference(session)
    output, report = quality_and_join(paszport, reference)
    output = annotate_output(output, applied)

    report["curation_layer"] = "verified-attendance-exceptions-v1"
    report["verified_attendance_overrides"] = applied
    report["default_demand_training_eligible_rows"] = int(
        output["default_demand_training_eligible"].sum()
    )
    report["default_demand_training_excluded_rows"] = int(
        (~output["default_demand_training_eligible"]).sum()
    )

    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, default=str) + "\n"
    )
    print(json.dumps(report, ensure_ascii=False, indent=2, default=str))

    if report["status"] != "PASS":
        raise SystemExit("Verified historical multi-season dataset failed quality gate")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    output.to_csv(args.output, index=False)


if __name__ == "__main__":
    main()
