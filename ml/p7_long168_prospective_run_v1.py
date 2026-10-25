#!/usr/bin/env python3
"""Pinned execution wrapper for P7 Long168 prospective validation v1.

The underlying builder intentionally keeps the prospective fingerprint unset.
This wrapper is the canonical execution boundary after the fingerprint-only run:
it pins the verified deterministic fingerprint from GitHub Actions run
40201818862 and refuses prediction if the rebuilt model differs.

No candidate search, hyperparameter search, target access or production change
is allowed here.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import ml.p7_long168_prospective_v1 as prospective

VERSION = "p7-long168-prospective-run-v1"
PINNED_MODEL_FINGERPRINT_SHA256 = (
    "70fa929181531276c80a75c0b78a60fb821cf50e714e2bc001de8251cea1793f"
)
FINGERPRINT_EVIDENCE_RUN_ID = 40201818862
FINGERPRINT_ARTIFACT_DIGEST = (
    "a6dab7c220e065a9e2d2b5f32954303bf067387b1d24458b1fa1066d5a507184"
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--artifact-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    bundle = json.loads(args.bundle.read_text())

    prospective.EXPECTED_MODEL_FINGERPRINT_SHA256 = PINNED_MODEL_FINGERPRINT_SHA256
    result = prospective.build(bundle, args.artifact_dir, "predict")

    observed = result.get("model_fingerprint_sha256")
    if observed != PINNED_MODEL_FINGERPRINT_SHA256:
        raise RuntimeError(
            f"P7_PROSPECTIVE_MODEL_FINGERPRINT_DRIFT expected={PINNED_MODEL_FINGERPRINT_SHA256} observed={observed}"
        )
    if result.get("target_values_used") is not False:
        raise RuntimeError("P7_PROSPECTIVE_TARGET_USE_REJECTED")
    if result.get("production_activation_allowed") is not False:
        raise RuntimeError("P7_PROSPECTIVE_PRODUCTION_ACTIVATION_REJECTED")
    if result.get("production_change") is not False:
        raise RuntimeError("P7_PROSPECTIVE_PRODUCTION_CHANGE_REJECTED")
    if result.get("live_adjustment") != 0:
        raise RuntimeError("P7_PROSPECTIVE_LIVE_ADJUSTMENT_DRIFT")
    if result.get("bootstrap_backfill_performed") is not False:
        raise RuntimeError("P7_PROSPECTIVE_BOOTSTRAP_BACKFILL_REJECTED")

    result["execution_wrapper_version"] = VERSION
    result["pinned_model_fingerprint_sha256"] = PINNED_MODEL_FINGERPRINT_SHA256
    result["fingerprint_evidence_run_id"] = FINGERPRINT_EVIDENCE_RUN_ID
    result["fingerprint_artifact_digest"] = FINGERPRINT_ARTIFACT_DIGEST

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
