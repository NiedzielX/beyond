#!/usr/bin/env python3
"""Normalize redundant timestamp fields in Long72 forward gateway payloads.

The live-trajectory feature payload includes ``features.as_of_at`` as a JSON
string, while the frozen materializer needs ``as_of_at`` to remain a typed
pandas timestamp. ``requested_as_of_at`` is the canonical row timestamp already
validated by the forward SQL contract. This normalizer proves the two values
match and removes the redundant nested string before materialization.
"""
from __future__ import annotations

import argparse
import json
from copy import deepcopy
from pathlib import Path
from typing import Any

import pandas as pd


def _utc(value: Any) -> pd.Timestamp:
    ts = pd.Timestamp(value)
    if ts.tzinfo is None:
        return ts.tz_localize("UTC")
    return ts.tz_convert("UTC")


def normalize_forward_input(payload: dict[str, Any]) -> dict[str, Any]:
    out = deepcopy(payload)
    forward = out.get("forward") if isinstance(out.get("forward"), dict) else out
    rows = forward.get("liveRows") or []
    if not isinstance(rows, list):
        raise RuntimeError("forward.liveRows must be a list")

    for row in rows:
        requested = row.get("requested_as_of_at")
        if requested is None:
            raise RuntimeError("missing requested_as_of_at")
        features = row.get("features")
        if not isinstance(features, dict):
            raise RuntimeError("missing live feature payload")
        nested = features.get("as_of_at")
        if nested is not None:
            if _utc(nested) != _utc(requested):
                raise RuntimeError(
                    f"feature/requested as_of mismatch: feature={nested} requested={requested}"
                )
            del features["as_of_at"]
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    payload = json.loads(args.input.read_text())
    normalized = normalize_forward_input(payload)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(normalized, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "version": "d2-long72-forward-input-normalize-v1",
        "live_row_count": len((normalized.get("forward") or normalized).get("liveRows") or []),
        "status": "NORMALIZED",
    }, sort_keys=True))


if __name__ == "__main__":
    main()
