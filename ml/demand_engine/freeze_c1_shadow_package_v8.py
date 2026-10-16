#!/usr/bin/env python3
"""Build and freeze the prospective C1 v2+v8 shadow package.

This is an intentional build-time fit. Scheduled shadow inference must load the
resulting artifact and must never fit/re-fit the live expert.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.linear_model import Ridge

from ml.c1_alpha_model_tournament_v1 import _event_prior_replay, _training_frame
from ml.c1_alpha_t1_tournament_v2 import (
    COMPACT_NUMERIC,
    WINDOW_HOURS,
    event_weights,
    fit_with_weights,
    pipeline,
)
from ml.demand_engine.c1_shadow_runtime_v8 import (
    C1ShadowRuntimeV8,
    FEATURE_CONTRACT,
    LIVE_MODEL_ID,
    MULTI_OBS_DISAGREEMENT_THRESHOLD,
    POLICY_ID,
    SINGLE_OBS_DISAGREEMENT_THRESHOLD,
)


PACKAGE_VERSION = "c1-shadow-v8-frozen-2026-10-16-n9"
EXPECTED_EVENT_IDS = (1, 3, 4, 8, 9, 12, 13, 14, 17)
EXPECTED_EVENT_COUNT = 9
EXPECTED_ROW_COUNT = 30


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_training_contract(frame: pd.DataFrame, features: list[str]) -> dict:
    rows = []
    ordered = frame.sort_values(["ticket_event_id", "as_of_at"]).copy()
    for row in ordered.to_dict("records"):
        feature_values = {}
        for feature in features:
            value = row.get(feature)
            if pd.isna(value):
                feature_values[feature] = None
            elif isinstance(value, (bool, np.bool_)):
                feature_values[feature] = bool(value)
            elif isinstance(value, (int, float, np.integer, np.floating)):
                feature_values[feature] = float(value)
            else:
                feature_values[feature] = value
        rows.append({
            "ticket_event_id": int(row["ticket_event_id"]),
            "as_of_at": pd.Timestamp(row["as_of_at"]).isoformat(),
            "home_team": str(row["home_team"]),
            "away_team": str(row["away_team"]),
            "stadium_capacity": float(row["stadium_capacity"]),
            "actual_attendance": float(row["actual_attendance"]),
            "prior_p50": float(row["prior_p50"]),
            "features": feature_values,
        })
    return {
        "contract_version": "c1-shadow-v8-training-contract-v1",
        "package_version": PACKAGE_VERSION,
        "live_model_id": LIVE_MODEL_ID,
        "feature_contract": FEATURE_CONTRACT,
        "features": features,
        "training_event_ids": list(EXPECTED_EVENT_IDS),
        "training_rows": len(rows),
        "rows": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--source-sha", default=None)
    args = parser.parse_args()

    payload = json.loads(args.input.read_text())
    priors = _event_prior_replay(payload, args.output_dir.parent / "structural_prior_runtime_v1")
    frame = _training_frame(payload, priors)
    frame = frame[
        (frame["hours_to_kickoff"].astype(float) >= 0.0)
        & (frame["hours_to_kickoff"].astype(float) <= WINDOW_HOURS)
        & (frame["prior_horizon"] == "T-1")
    ].copy()

    event_ids = tuple(sorted(int(v) for v in frame["ticket_event_id"].unique()))
    if event_ids != EXPECTED_EVENT_IDS:
        raise RuntimeError(f"C1 shadow freeze event set changed: actual={event_ids} expected={EXPECTED_EVENT_IDS}")
    if frame["ticket_event_id"].nunique() != EXPECTED_EVENT_COUNT or len(frame) != EXPECTED_ROW_COUNT:
        raise RuntimeError(
            f"C1 shadow freeze expected events={EXPECTED_EVENT_COUNT} rows={EXPECTED_ROW_COUNT}, "
            f"got events={frame['ticket_event_id'].nunique()} rows={len(frame)}"
        )

    features = [feature for feature in COMPACT_NUMERIC if feature in frame.columns]
    if not features:
        raise RuntimeError("C1 shadow freeze found no v2 compact features")

    model = pipeline(features, False, Ridge(alpha=10.0), scale=True)
    target = (
        frame["actual_attendance"].astype(float)
        / frame["stadium_capacity"].astype(float)
    ).to_numpy()
    fitted = fit_with_weights(
        model,
        frame[features],
        target,
        event_weights(frame),
    )

    output = args.output_dir
    output.mkdir(parents=True, exist_ok=True)

    contract = canonical_training_contract(frame, features)
    contract_path = output / "training_contract_v1.json"
    contract_path.write_text(
        json.dumps(contract, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
    )

    runtime = C1ShadowRuntimeV8(
        estimator=fitted,
        features=tuple(features),
        package_version=PACKAGE_VERSION,
        training_event_ids=EXPECTED_EVENT_IDS,
        training_rows=EXPECTED_ROW_COUNT,
    )
    artifact_path = output / "c1_v2_live_expert_v1.joblib"
    joblib.dump(runtime, artifact_path, compress=3)

    # Load-back is part of the freeze contract: the committed artifact must be
    # independently deserializable and produce finite predictions.
    loaded: C1ShadowRuntimeV8 = joblib.load(artifact_path)
    replay = loaded.predict_live_p50(frame)
    if len(replay) != EXPECTED_ROW_COUNT or not np.isfinite(replay).all():
        raise RuntimeError("C1 shadow frozen artifact load-back prediction failed")

    manifest = {
        "package_version": PACKAGE_VERSION,
        "status": "EXPERIMENTAL_SHADOW",
        "production_activation": False,
        "live_adjustment": 0,
        "live_model_id": LIVE_MODEL_ID,
        "policy_id": POLICY_ID,
        "feature_contract": FEATURE_CONTRACT,
        "structural_prior_dependency": "structural-prior-runtime-v1-frozen-2026-10-15-t1",
        "source_sha": args.source_sha,
        "training": {
            "event_ids": list(EXPECTED_EVENT_IDS),
            "event_count": EXPECTED_EVENT_COUNT,
            "row_count": EXPECTED_ROW_COUNT,
            "target": "direct_occupancy",
            "event_balanced_weights": True,
            "training_contract_filename": contract_path.name,
            "training_contract_sha256": sha256_file(contract_path),
        },
        "model": {
            "family": "Ridge",
            "alpha": 10.0,
            "club_aware": False,
            "scaled": True,
            "features": features,
            "feature_count": len(features),
        },
        "policy": {
            "multi_observation_abs_disagreement_threshold": MULTI_OBS_DISAGREEMENT_THRESHOLD,
            "multi_observation_live_slope_gt": 0.0,
            "single_observation_abs_disagreement_threshold": SINGLE_OBS_DISAGREEMENT_THRESHOLD,
            "fallback": "PRIOR",
            "pit_rule": "use only live observations available up to the current row",
        },
        "artifact": {
            "filename": artifact_path.name,
            "sha256": sha256_file(artifact_path),
            "bytes": artifact_path.stat().st_size,
        },
        "libraries": {
            "scikit_learn": sklearn.__version__,
            "pandas": pd.__version__,
            "numpy": np.__version__,
            "joblib": joblib.__version__,
        },
        "governance": {
            "thresholds_frozen_after_v7": True,
            "do_not_retune_on_original_9_events": True,
            "prospective_validation_required": True,
            "scheduled_inference_must_not_fit": True,
        },
    }
    manifest_path = output / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print(json.dumps(manifest, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
