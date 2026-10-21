#!/usr/bin/env python3
"""d2-v3 Stage 0: prove final-24h anchor/target equivalence before retraining.

The existing d2 Stage-0 frame is rebuilt under the frozen v2 lineage. This gate
then verifies that sealed Pre-Live v3 has an exactly identical T-1 package and
historical input lineage. Because the current d2 final-24h replay uses only that
T-1 event anchor, the row-level v3 anchor must be identical if all lineage gates
pass. No model is trained here.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

EXPERIMENT = "d2-v3-stage0-anchor-equivalence-v1"
EXPECTED_V2_FREEZE = "pre-live-v2-historical-candidate-2026-10-18-v1"
EXPECTED_V3_FREEZE = "pre-live-v3-historical-candidate-2026-10-21-v1"
EXPECTED_EVENTS = 9
EXPECTED_ROWS = 30
ANCHOR_SEAT_ATOL = 0.0
TARGET_ATTENDANCE_ATOL = 1e-9
OCCUPANCY_ATOL = 1e-12


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def horizon_row(manifest: dict[str, Any], horizon: str) -> dict[str, Any]:
    rows = [row for row in manifest.get("horizons", []) if row.get("horizon") == horizon]
    if len(rows) != 1:
        raise RuntimeError(f"expected one {horizon} row, found {len(rows)}")
    return rows[0]


def verify_t1_equivalence(v2: dict[str, Any], v3: dict[str, Any]) -> dict[str, Any]:
    if v2.get("freeze_id") != EXPECTED_V2_FREEZE:
        raise RuntimeError("unexpected v2 freeze id")
    if v3.get("freeze_id") != EXPECTED_V3_FREEZE:
        raise RuntimeError("unexpected v3 freeze id")

    v2_t1 = horizon_row(v2, "T-1")
    v3_t1 = horizon_row(v3, "T-1")
    v2_contract = v2_t1["contract"]
    v3_contract = v3_t1["contract"]

    contract_fields = (
        "historical_base",
        "current_season_regime",
        "historical_context_extension",
    )
    differences = {
        field: {"v2": v2_contract.get(field), "v3": v3_contract.get(field)}
        for field in contract_fields
        if v2_contract.get(field) != v3_contract.get(field)
    }
    if differences:
        raise RuntimeError(f"v2/v3 T-1 contract differs: {differences}")

    v2_mae = v2.get("expected_final_mae", {}).get("T-1")
    v3_mae = v3.get("expected_final_mae", {}).get("T-1")
    if v2_mae != v3_mae:
        raise RuntimeError(f"v2/v3 T-1 expected MAE differs v2={v2_mae} v3={v3_mae}")

    lineage_fields = (
        "historical_runtime_sha256",
        "feature_contract",
    )
    lineage_diff = {
        field: {
            "v2": (v2.get("input") or {}).get(field),
            "v3": (v3.get("input") or {}).get(field),
        }
        for field in lineage_fields
        if (v2.get("input") or {}).get(field) != (v3.get("input") or {}).get(field)
    }
    if lineage_diff:
        raise RuntimeError(f"v2/v3 historical input lineage differs: {lineage_diff}")

    return {
        "contracts_exactly_equal": True,
        "expected_mae_exactly_equal": True,
        "historical_input_lineage_equal": True,
        "t1_contract": v2_contract,
        "t1_expected_final_mae": v2_mae,
        "historical_runtime_sha256": (v2.get("input") or {}).get("historical_runtime_sha256"),
        "feature_contract": (v2.get("input") or {}).get("feature_contract"),
    }


def load_stage0(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path)
    if len(frame) != EXPECTED_ROWS:
        raise RuntimeError(f"expected {EXPECTED_ROWS} rows, got {len(frame)}")
    if frame["ticket_event_id"].nunique() != EXPECTED_EVENTS:
        raise RuntimeError(
            f"expected {EXPECTED_EVENTS} events, got {frame['ticket_event_id'].nunique()}"
        )
    if set(frame["anchor_status"].astype(str)) != {"FROZEN_V2_EXACT"}:
        raise RuntimeError("input is not exact Frozen-v2 Stage-0 replay")
    if set(frame["pre_live_freeze_id"].astype(str)) != {EXPECTED_V2_FREEZE}:
        raise RuntimeError("Stage-0 v2 freeze id drift")
    frame["as_of_at"] = pd.to_datetime(frame["as_of_at"], utc=True)
    frame = frame.sort_values(["ticket_event_id", "as_of_at"]).reset_index(drop=True)
    return frame


def build_equivalence_frame(frame: pd.DataFrame) -> pd.DataFrame:
    required = [
        "ticket_event_id",
        "as_of_at",
        "actual_attendance",
        "stadium_capacity",
        "frozen_v2_p50",
        "frozen_v2_expected_occupancy",
        "target_live_delta_attendance",
        "target_live_delta_occupancy",
    ]
    missing = [column for column in required if column not in frame.columns]
    if missing:
        raise RuntimeError(f"missing Stage-0 columns: {missing}")

    out = frame.copy()
    # The copy is allowed only after manifest-level exact T-1 contract + input
    # lineage equivalence has been hard-verified by the caller.
    out["frozen_v3_p50"] = out["frozen_v2_p50"].astype(float)
    out["frozen_v3_expected_occupancy"] = (
        out["frozen_v3_p50"] / out["stadium_capacity"].astype(float)
    )
    out["v3_minus_v2_anchor_seats"] = (
        out["frozen_v3_p50"] - out["frozen_v2_p50"].astype(float)
    )
    out["v3_minus_v2_anchor_occupancy"] = (
        out["frozen_v3_expected_occupancy"]
        - out["frozen_v2_expected_occupancy"].astype(float)
    )
    out["target_live_delta_attendance_v3"] = (
        out["actual_attendance"].astype(float) - out["frozen_v3_p50"]
    )
    out["target_live_delta_occupancy_v3"] = (
        out["actual_attendance"].astype(float) / out["stadium_capacity"].astype(float)
        - out["frozen_v3_expected_occupancy"]
    )
    out["v3_minus_v2_target_attendance"] = (
        out["target_live_delta_attendance_v3"]
        - out["target_live_delta_attendance"].astype(float)
    )
    out["v3_minus_v2_target_occupancy"] = (
        out["target_live_delta_occupancy_v3"]
        - out["target_live_delta_occupancy"].astype(float)
    )
    out["pre_live_v3_freeze_id"] = EXPECTED_V3_FREEZE
    out["v3_anchor_status"] = "FROZEN_V3_T1_CONTRACT_EQUIVALENT_TO_V2"
    return out


def assert_row_equivalence(frame: pd.DataFrame) -> dict[str, Any]:
    anchor_seats = frame["v3_minus_v2_anchor_seats"].astype(float).to_numpy()
    anchor_occ = frame["v3_minus_v2_anchor_occupancy"].astype(float).to_numpy()
    target_att = frame["v3_minus_v2_target_attendance"].astype(float).to_numpy()
    target_occ = frame["v3_minus_v2_target_occupancy"].astype(float).to_numpy()

    max_anchor_seats = float(np.max(np.abs(anchor_seats)))
    max_anchor_occ = float(np.max(np.abs(anchor_occ)))
    max_target_att = float(np.max(np.abs(target_att)))
    max_target_occ = float(np.max(np.abs(target_occ)))

    if max_anchor_seats != ANCHOR_SEAT_ATOL:
        raise RuntimeError(
            f"v3/v2 final24 anchor seat values differ max_abs={max_anchor_seats}"
        )
    if max_anchor_occ > OCCUPANCY_ATOL:
        raise RuntimeError(
            f"v3/v2 final24 anchor occupancy differs max_abs={max_anchor_occ}"
        )
    if max_target_att > TARGET_ATTENDANCE_ATOL:
        raise RuntimeError(
            f"v3/v2 live delta attendance targets differ max_abs={max_target_att}"
        )
    if max_target_occ > OCCUPANCY_ATOL:
        raise RuntimeError(
            f"v3/v2 live delta occupancy targets differ max_abs={max_target_occ}"
        )

    per_event = []
    for event_id, group in frame.groupby("ticket_event_id", sort=True):
        per_event.append({
            "ticket_event_id": int(event_id),
            "rows": int(len(group)),
            "frozen_v2_p50": float(group.iloc[0]["frozen_v2_p50"]),
            "frozen_v3_p50": float(group.iloc[0]["frozen_v3_p50"]),
            "max_abs_anchor_delta_seats": float(
                group["v3_minus_v2_anchor_seats"].abs().max()
            ),
            "max_abs_target_attendance_delta": float(
                group["v3_minus_v2_target_attendance"].abs().max()
            ),
            "max_abs_target_occupancy_delta": float(
                group["v3_minus_v2_target_occupancy"].abs().max()
            ),
        })
    return {
        "all_rows_exact_anchor_seat_equivalence": True,
        "all_rows_target_equivalence_within_atol": True,
        "anchor_seat_atol": ANCHOR_SEAT_ATOL,
        "target_attendance_atol": TARGET_ATTENDANCE_ATOL,
        "occupancy_atol": OCCUPANCY_ATOL,
        "max_abs_anchor_delta_seats": max_anchor_seats,
        "max_abs_anchor_delta_occupancy": max_anchor_occ,
        "max_abs_target_attendance_delta": max_target_att,
        "max_abs_target_occupancy_delta": max_target_occ,
        "events": per_event,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage0-csv", type=Path, required=True)
    parser.add_argument("--v2-manifest", type=Path, required=True)
    parser.add_argument("--v3-manifest", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-csv", type=Path, required=True)
    args = parser.parse_args()

    v2 = json.loads(args.v2_manifest.read_text())
    v3 = json.loads(args.v3_manifest.read_text())
    lineage = verify_t1_equivalence(v2, v3)
    frame = load_stage0(args.stage0_csv)
    out = build_equivalence_frame(frame)
    row_audit = assert_row_equivalence(out)

    result = {
        "experiment": EXPERIMENT,
        "status": "COMPLETED_NO_TRAINING",
        "decision": "V3_FINAL24_ANCHOR_EXACTLY_EQUIVALENT_TO_V2",
        "production_change": False,
        "model_training_performed": False,
        "v2_freeze_id": EXPECTED_V2_FREEZE,
        "v3_freeze_id": EXPECTED_V3_FREEZE,
        "lineage": {
            "v2_manifest_sha256": sha256_file(args.v2_manifest),
            "v3_manifest_sha256": sha256_file(args.v3_manifest),
            **lineage,
        },
        "dataset": {
            "event_count": int(out["ticket_event_id"].nunique()),
            "row_count": int(len(out)),
            "event_ids": sorted(int(value) for value in out["ticket_event_id"].unique()),
            "problem_window": "final-24h",
            "stage0_anchor_horizon": "T-1",
        },
        "row_equivalence": row_audit,
        "interpretation": {
            "new_final24_target_required": False,
            "stage1_retraining_required_due_to_v3_anchor": False,
            "stage2_reselection_required_due_to_v3_anchor": False,
            "reason": (
                "The current d2 final-24h replay is anchored on T-1 only, and sealed "
                "Pre-Live v3 retains the exact Frozen-v2 T-1 contract and historical input lineage."
            ),
            "next_rnd_requirement": (
                "Use a materially different live hypothesis rather than a cosmetic d2-v3 retrain. "
                "Preferred: evaluate extending live coverage earlier than 24h so changed v3 T-7 can matter, "
                "subject to PIT-safe snapshot availability."
            ),
        },
    }

    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_csv.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    out.to_csv(args.output_csv, index=False)
    print(json.dumps({
        "decision": result["decision"],
        "dataset": result["dataset"],
        "row_equivalence": {
            key: value for key, value in row_audit.items() if key != "events"
        },
        "interpretation": result["interpretation"],
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
