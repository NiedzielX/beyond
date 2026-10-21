#!/usr/bin/env python3
"""Regression checks for Long72 forward input timestamp normalization."""
from __future__ import annotations

from ml.d2_long72_forward_input_normalize_v1 import normalize_forward_input


def test_redundant_json_timestamp_is_removed() -> None:
    payload = {
        "forward": {
            "liveRows": [{
                "requested_as_of_at": "2026-10-21T19:35:01.562Z",
                "features": {
                    "as_of_at": "2026-10-21T19:35:01.562+00:00",
                    "feature_version": "live-trajectory-v1.1",
                },
            }],
        },
    }
    result = normalize_forward_input(payload)
    assert "as_of_at" not in result["forward"]["liveRows"][0]["features"]
    assert result["forward"]["liveRows"][0]["requested_as_of_at"] == "2026-10-21T19:35:01.562Z"
    # Input is not mutated.
    assert "as_of_at" in payload["forward"]["liveRows"][0]["features"]


def test_timestamp_mismatch_is_rejected() -> None:
    payload = {
        "forward": {
            "liveRows": [{
                "requested_as_of_at": "2026-10-21T19:35:01Z",
                "features": {"as_of_at": "2026-10-21T19:36:01Z"},
            }],
        },
    }
    try:
        normalize_forward_input(payload)
    except RuntimeError as exc:
        assert "as_of mismatch" in str(exc)
    else:
        raise AssertionError("timestamp mismatch should fail closed")


def main() -> None:
    test_redundant_json_timestamp_is_removed()
    test_timestamp_mismatch_is_rejected()
    print("d2 long72 forward input normalize v1 checks passed")


if __name__ == "__main__":
    main()
