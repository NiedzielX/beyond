#!/usr/bin/env python3
"""Attach frozen evidence classes to prospective scoring output.

The model scorer intentionally stays focused on frozen prediction logic. This
post-processor joins each scored/blocked event back to the independently
produced readiness report so delayed-label holdouts cannot be mistaken for
true post-freeze prospective evidence.

No forecasts, errors, model inputs, registry rows, or policies are changed.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd

from ml.d2_prospective_evidence_class_v1 import (
    EVIDENCE_DELAYED_LABEL,
    EVIDENCE_TRUE_PROSPECTIVE,
)

ALLOWED_CLASSES = {EVIDENCE_DELAYED_LABEL, EVIDENCE_TRUE_PROSPECTIVE}
EXPERIMENT = "d2-prospective-score-evidence-tag-v1"


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def readiness_index(readiness: dict[str, Any]) -> dict[int, dict[str, Any]]:
    index: dict[int, dict[str, Any]] = {}
    for row in readiness.get("events") or []:
        event_id = int(row["ticket_event_id"])
        evidence = str(row.get("evidence_class") or "")
        if evidence not in ALLOWED_CLASSES:
            raise RuntimeError(
                f"invalid/missing readiness evidence class event={event_id} class={evidence}"
            )
        if event_id in index:
            raise RuntimeError(f"duplicate readiness event={event_id}")
        index[event_id] = row
    return index


def _tag_event(row: dict[str, Any], index: dict[int, dict[str, Any]]) -> dict[str, Any]:
    event_id = int(row["ticket_event_id"])
    readiness = index.get(event_id)
    if readiness is None:
        raise RuntimeError(
            f"scoring event missing from readiness evidence event={event_id}"
        )
    tagged = dict(row)
    tagged["evidence_class"] = readiness["evidence_class"]
    tagged["counts_toward_true_prospective_promotion_evidence"] = bool(
        readiness["counts_toward_true_prospective_promotion_evidence"]
    )
    tagged["readiness_status_at_scoring"] = readiness["readiness_status"]
    tagged["readiness_final24_snapshot_count"] = int(
        readiness.get("final24_snapshot_count") or 0
    )
    return tagged


def tag_scoring_evidence(
    scoring: dict[str, Any],
    readiness: dict[str, Any],
    rows: pd.DataFrame,
) -> tuple[dict[str, Any], pd.DataFrame]:
    index = readiness_index(readiness)

    scored = [_tag_event(row, index) for row in (scoring.get("scored_events") or [])]
    blocked = [_tag_event(row, index) for row in (scoring.get("blocked_events") or [])]

    tagged = dict(scoring)
    tagged["evidence_tag_experiment"] = EXPERIMENT
    tagged["stage2_freeze_cutoff_at"] = readiness.get("stage2_freeze_cutoff_at")
    tagged["scored_events"] = scored
    tagged["blocked_events"] = blocked
    tagged["delayed_label_scored_event_ids"] = [
        int(row["ticket_event_id"])
        for row in scored
        if row["evidence_class"] == EVIDENCE_DELAYED_LABEL
    ]
    tagged["true_prospective_scored_event_ids"] = [
        int(row["ticket_event_id"])
        for row in scored
        if row["evidence_class"] == EVIDENCE_TRUE_PROSPECTIVE
    ]
    tagged["true_prospective_scored_event_count"] = len(
        tagged["true_prospective_scored_event_ids"]
    )
    tagged["delayed_label_scored_event_count"] = len(
        tagged["delayed_label_scored_event_ids"]
    )
    tagged["promotion_evidence_boundary"] = (
        "Only TRUE_POST_FREEZE_PROSPECTIVE scored events count toward genuine "
        "forward production-promotion evidence. DELAYED_LABEL_HOLDOUT events "
        "remain diagnostic/chronological evidence only."
    )

    tagged_rows = rows.copy()
    if not tagged_rows.empty:
        classes: list[str] = []
        promotion_flags: list[bool] = []
        for event_id in tagged_rows["ticket_event_id"].astype(int).tolist():
            readiness_row = index.get(event_id)
            if readiness_row is None:
                raise RuntimeError(
                    f"prediction row missing readiness evidence event={event_id}"
                )
            classes.append(str(readiness_row["evidence_class"]))
            promotion_flags.append(bool(
                readiness_row["counts_toward_true_prospective_promotion_evidence"]
            ))
        tagged_rows["evidence_class"] = classes
        tagged_rows["counts_toward_true_prospective_promotion_evidence"] = promotion_flags

    return tagged, tagged_rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scoring-json", type=Path, required=True)
    parser.add_argument("--scoring-csv", type=Path, required=True)
    parser.add_argument("--readiness-json", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-csv", type=Path, required=True)
    args = parser.parse_args()

    scoring = _load(args.scoring_json)
    readiness = _load(args.readiness_json)
    rows = pd.read_csv(args.scoring_csv) if args.scoring_csv.stat().st_size else pd.DataFrame()
    tagged, tagged_rows = tag_scoring_evidence(scoring, readiness, rows)

    args.output_json.write_text(json.dumps(tagged, indent=2, sort_keys=True) + "\n")
    tagged_rows.to_csv(args.output_csv, index=False)
    print(json.dumps({
        "status": tagged.get("status"),
        "delayed_label_scored_event_ids": tagged["delayed_label_scored_event_ids"],
        "true_prospective_scored_event_ids": tagged["true_prospective_scored_event_ids"],
        "scored_events": tagged.get("scored_events") or [],
        "blocked_events": tagged.get("blocked_events") or [],
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
