#!/usr/bin/env python3
"""Pinned P7 Long168 prospective prediction wrapper v1.

This wrapper exists only to bind the deterministic fingerprint produced by the
pre-prediction fingerprint run. It does not alter the candidate, features,
training set, weights, hyperparameters or prediction rule.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import ml.p7_long168_prospective_v1 as base

PINNED_MODEL_FINGERPRINT_SHA256 = "70fa929181531276c80a75c0b78a60fb821cf50e714e2bc001de8251cea1793f"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--artifact-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    bundle = json.loads(args.bundle.read_text())
    base.EXPECTED_MODEL_FINGERPRINT_SHA256 = PINNED_MODEL_FINGERPRINT_SHA256
    result = base.build(bundle, args.artifact_dir, "predict")

    if result["model_fingerprint_sha256"] != PINNED_MODEL_FINGERPRINT_SHA256:
        raise RuntimeError(
            f"P7_PROSPECTIVE_MODEL_FINGERPRINT_DRIFT expected={PINNED_MODEL_FINGERPRINT_SHA256} "
            f"observed={result['model_fingerprint_sha256']}"
        )
    if result["target_values_used"] is not False:
        raise RuntimeError("P7_PROSPECTIVE_TARGET_USE_REJECTED")
    if result["production_change"] is not False or result["live_adjustment"] != 0:
        raise RuntimeError("P7_PROSPECTIVE_PRODUCTION_BOUNDARY_REJECTED")
    if result["bootstrap_backfill_performed"] is not False:
        raise RuntimeError("P7_PROSPECTIVE_BOOTSTRAP_BACKFILL_REJECTED")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
