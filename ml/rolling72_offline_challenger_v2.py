"""One precommitted offline fit, followed only by genuine future evaluation.

Historical input-delivery and metadata clocks are explicitly UNPROVEN. This
module never manufactures historical known_at, computes historical accuracy,
searches parameters or creates prospective evidence. The trusted local dataset
builder verifies original source bytes; hashes here bind that declared dataset,
not independently authenticated database immutability.

Private joblib loading is ONLY for artifacts created by this local research
pipeline. Checksums are verified before deserialization; they are not signatures
and do not make arbitrary uploaded pickle files safe. No public loader exists.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import re

from ml.demand_engine.rolling72_features_v1 import HORIZONS, _hash, _id, _time, features


VERSION = "rolling72-capture-segment-quantile-tree-v2"
DATASET_VERSION = "rolling72-offline-capture-segment-dataset-v2"
PRECOMMIT_SHA256 = "c48c3c9d8128a518bb6ae2b3f2d459537f3b032adc84b2749f753daaaf8b4371"
ROOT = Path(__file__).resolve().parent.parent
PRECOMMIT_PATH = ROOT / "ml/artifacts/rolling72_v2/precommit.json"
FEATURE_NAMES = (
    "last_available_total", "observed_delta_since_first", "prefix_span_hours",
    "latest_staleness_hours", "hours_to_kickoff", "horizon_hours",
    "delta_6h", "slope_6h", "delta_24h", "slope_24h", "delta_72h", "slope_72h",
)
ROW_FIELDS = {
    "features", "nominal_horizon_hours", "target_delta", "matched_available_total",
    "last_available_total", "origin_capture_at", "target_at", "label_captured_at", "kickoff_at",
    "ticket_event_id", "fixture_group", "club_slug", "source_family", "historical_input_known_at",
    "historical_knowledge_unproven", "source_received_at", "segment_lineage", "prefix_sha256", "row_sha256",
}


def _now():
    return datetime.now(timezone.utc)


def _sha(value, name):
    if not isinstance(value, str) or re.fullmatch("[a-f0-9]{64}", value) is None:
        raise ValueError(f"Invalid {name} SHA256")
    return value


def _number(value, name, *, nonnegative=False):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"Invalid numeric {name}")
    result = float(value)
    if not math.isfinite(result) or (nonnegative and result < 0):
        raise ValueError(f"Invalid finite {name}")
    return result


def _same(left, right):
    return math.isclose(float(left), float(right), rel_tol=1e-12, abs_tol=1e-9)


def _digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_precommit():
    recipe = json.loads(PRECOMMIT_PATH.read_text())
    if (recipe.get("version") != "rolling72-offline-fit-prospective-shadow-precommit-v2"
            or recipe.get("precommit_sha256") != PRECOMMIT_SHA256
            or _hash({k: v for k, v in recipe.items() if k != "precommit_sha256"}) != PRECOMMIT_SHA256
            or tuple(recipe.get("features", ())) != FEATURE_NAMES
            or tuple(recipe.get("horizons_hours", ())) != HORIZONS
            or recipe["candidate"]["id"] != VERSION
            or recipe.get("production_change") is not False or recipe.get("live_adjustment") != 0):
        raise ValueError("Exact v2 precommit required")
    return recipe


def _source_code_hashes():
    names = ("ml/rolling72_offline_challenger_v2.py", "ml/rolling72_offline_dataset_v2.py",
             "ml/rolling72_receipt_dataset_v1.py",
             "ml/demand_engine/rolling72_features_v1.py")
    return {name: _digest(ROOT / name) for name in names}


def validate_dataset(dataset: dict, *, synthetic_test=False):
    """Validate fixed source declarations and derive support from actual rows."""
    recipe = load_precommit()
    if not isinstance(synthetic_test, bool) or not isinstance(dataset, dict):
        raise ValueError("Explicit synthetic mode and dataset required")
    if (dataset.get("version") != DATASET_VERSION
            or dataset.get("precommit_sha256") != PRECOMMIT_SHA256
            or dataset.get("dataset_sha256") != _hash({k: v for k, v in dataset.items() if k != "dataset_sha256"})
            or dataset.get("synthetic_test") is not synthetic_test
            or dataset.get("servable_training_input") is not (not synthetic_test)
            or dataset.get("historical_knowledge_unproven") is not True
            or dataset.get("historical_input_known_at") is not None
            or dataset.get("model_fit_performed") is not False
            or dataset.get("production_change") is not False or dataset.get("live_adjustment") != 0):
        raise ValueError("Offline dataset hash/evidence/mode mismatch")
    bindings = dataset.get("source_bindings")
    if not isinstance(bindings, dict):
        raise ValueError("Original source bindings required")
    for kind, expected in recipe["source_bindings"].items():
        actual = bindings.get(kind)
        if (not isinstance(actual, dict) or any(actual.get(k) != v for k, v in expected.items())
                or actual.get("verified_file_sha256") != expected["file_sha256"]):
            raise ValueError("Original source binding differs from precommit")
    cutoff = _time(recipe["training_data_cutoff_at"])
    received_bound = _time(recipe["source_bindings"]["inventory"]["received_at"])
    rows = dataset.get("rows")
    if not isinstance(rows, list):
        raise ValueError("Offline rows list required")
    clean, seen, event_groups, group_clubs = [], set(), {}, {}
    for row in rows:
        if not isinstance(row, dict) or set(row) != ROW_FIELDS:
            raise ValueError("Exact declared offline row schema required")
        if row["row_sha256"] != _hash({k: v for k, v in row.items() if k != "row_sha256"}):
            raise ValueError("Offline row hash mismatch")
        if row["historical_input_known_at"] is not None or row["historical_knowledge_unproven"] is not True:
            raise ValueError("Historical knowledge must remain explicitly unproven")
        values = row["features"]
        if not isinstance(values, dict) or set(values) != set(FEATURE_NAMES):
            raise ValueError("Exactly twelve precommitted features required")
        for key, value in values.items():
            if value is None and key.startswith(("delta_", "slope_")):
                continue
            _number(value, key)
        for window in (6, 24, 72):
            if (values[f"delta_{window}h"] is None) != (values[f"slope_{window}h"] is None):
                raise ValueError("Genuine window delta/slope missingness differs")
        horizon = row["nominal_horizon_hours"]
        if isinstance(horizon, bool) or not isinstance(horizon, int) or horizon not in HORIZONS:
            raise ValueError("Unsupported offline horizon")
        origin, target, captured, kickoff, received = [_time(row[key]) for key in (
            "origin_capture_at", "target_at", "label_captured_at", "kickoff_at", "source_received_at")]
        if (target != origin + timedelta(hours=horizon) or not origin < captured <= target < kickoff < cutoff
                or received != received_bound or captured > received or received > cutoff
                or (target - captured).total_seconds() > 6 * 3600):
            raise ValueError("Offline capture/label/source clocks violate precommit")
        last = _number(row["last_available_total"], "last", nonnegative=True)
        actual = _number(row["matched_available_total"], "future observation", nonnegative=True)
        delta = _number(row["target_delta"], "target delta")
        if (not _same(delta, actual - last) or not _same(values["last_available_total"], last)
                or not _same(values["horizon_hours"], horizon)
                or not _same(values["latest_staleness_hours"], 0)
                or not _same(values["hours_to_kickoff"], (kickoff - origin).total_seconds() / 3600)
                or _number(values["prefix_span_hours"], "prefix span", nonnegative=True) < 0):
            raise ValueError("Offline features disagree with actual coordinates")
        if row["source_family"] not in recipe["data_evidence"]["source_families"]:
            raise ValueError("Unsupported measurement source family")
        event_id, group, club = _id(row["ticket_event_id"]), row["fixture_group"], row["club_slug"]
        if not isinstance(group, str) or not group.strip() or not isinstance(club, str) or not club.strip():
            raise ValueError("Declared fixture group and club required")
        if event_id in event_groups and event_groups[event_id] != group:
            raise ValueError("An event cannot inflate independent fixture groups")
        if group in group_clubs and group_clubs[group] != club:
            raise ValueError("Fixture aliases cannot inflate club support")
        event_groups[event_id], group_clubs[group] = group, club
        key = (group, origin, horizon)
        if key in seen:
            raise ValueError("Duplicate fixture origin/horizon")
        seen.add(key)
        _sha(row["prefix_sha256"], "prefix")
        lineage = row["segment_lineage"]
        if not isinstance(lineage, dict) or lineage.get("measurement_key") != row["source_family"]:
            raise ValueError("Comparable segment lineage required")
        ids = lineage.get("raw_prefix_snapshot_ids")
        if (not isinstance(ids, list) or not ids or len(set(ids)) != len(ids)
                or any(_id(value) != value for value in ids)
                or lineage.get("start_snapshot_id") != ids[0]
                or lineage.get("origin_snapshot_id") != ids[-1]
                or _id(lineage.get("label_snapshot_id")) in ids):
            raise ValueError("Comparable prefix/label identity conflict")
        clean.append(row)
    by_group = defaultdict(set)
    for row in clean:
        by_group[row["fixture_group"]].add(row["nominal_horizon_hours"])
    common = {group for group, horizons in by_group.items() if horizons == set(HORIZONS)}
    training = sorted((r for r in clean if r["fixture_group"] in common),
                      key=lambda r: (r["fixture_group"], r["origin_capture_at"], r["nominal_horizon_hours"], r["ticket_event_id"]))
    per_horizon = {str(h): {"rows": sum(r["nominal_horizon_hours"] == h for r in training),
                           "fixtures": len(common), "clubs": len({group_clubs[g] for g in common})}
                   for h in HORIZONS}
    required = recipe["gate"]
    reasons = []
    if len(common) < required["min_common_fixtures"]:
        reasons.append("INSUFFICIENT_COMMON_FIXTURES")
    clubs = len({group_clubs[g] for g in common})
    if clubs < required["min_common_clubs"]:
        reasons.append("INSUFFICIENT_COMMON_CLUBS")
    if len(training) < required["min_rows"]:
        reasons.append("INSUFFICIENT_ROWS")
    for h, support in per_horizon.items():
        if support["fixtures"] < required["min_fixtures_per_horizon"]:
            reasons.append(f"INSUFFICIENT_FIXTURES_{h}H")
        if support["clubs"] < required["min_clubs_per_horizon"]:
            reasons.append(f"INSUFFICIENT_CLUBS_{h}H")
    gate = {"status": "NO_FIT" if reasons else "READY_TO_FIT", "reasons": reasons,
            "supplied_rows": len(rows), "training_rows": len(training), "common_fixtures": len(common),
            "common_clubs": clubs, "per_horizon": per_horizon,
            "partial_horizon_fixture_groups_excluded": sorted(set(by_group) - common)}
    return training, gate


def training_weights(rows):
    counts = Counter((r["fixture_group"], r["nominal_horizon_hours"]) for r in rows)
    groups = {r["fixture_group"] for r in rows}
    if not rows or any((g, h) not in counts for g in groups for h in HORIZONS):
        raise ValueError("Weights require common all-horizon fixtures")
    return [len(rows) / (len(groups) * 3 * counts[(r["fixture_group"], r["nominal_horizon_hours"])]) for r in rows]


def _runtime_model_hash(model):
    """Fingerprint numerical inference state, independent of pickle layout.

    Joblib changes ndarray sharing/layout during round-trip, so pickle bytes
    cannot identify a restored estimator. Persisted bytes have their own SHA.
    This second digest detects changes to the loaded numeric prediction state.
    """
    import numpy as np

    def state(value):
        if isinstance(value, np.ndarray):
            return {"array_dtype": str(value.dtype), "array_shape": list(value.shape),
                    "array_bytes_sha256": hashlib.sha256(value.tobytes(order="C")).hexdigest()}
        if isinstance(value, np.generic):
            return value.item()
        if isinstance(value, dict):
            return {key: state(item) for key, item in value.items()}
        if isinstance(value, (list, tuple)):
            return [state(item) for item in value]
        if value is None or isinstance(value, (str, int, float, bool)):
            return value
        raise ValueError("Unexpected estimator inference-state type")

    if (model._preprocessor is not None or model._is_categorical_remapped is not None
            or model.is_categorical_ is not None or getattr(model, "_in_fit", False)
            or type(model._loss.link).__name__ != "IdentityLink"):
        raise ValueError("Unexpected estimator numeric inference semantics")
    return _hash(state({"parameters": model.get_params(deep=False),
                       "baseline": model._baseline_prediction,
                       "n_features_in": model.n_features_in_,
                       "n_features": model._n_features,
                       "n_trees_per_iteration": model.n_trees_per_iteration_,
                       "bin_mapper": model._bin_mapper.__dict__,
                       "trees": [[tree.__dict__ for tree in iteration] for iteration in model._predictors],
                       "identity_link_state": model._loss.link.__dict__}))


def _write_private(path, value, *, exclusive=False):
    flags = os.O_WRONLY | os.O_CREAT | (os.O_EXCL if exclusive else os.O_TRUNC)
    with os.fdopen(os.open(path, flags, 0o600), "w") as stream:
        json.dump(value, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")


def _matrix(rows):
    import numpy as np
    return np.asarray([[float("nan") if row["features"][k] is None else row["features"][k]
                        for k in FEATURE_NAMES] for row in rows], dtype=float)


def mechanism_audit(model):
    """Fixed counterfactual probes, never accuracy or a reason to refit."""
    import numpy as np
    history_names = {"observed_delta_since_first", "delta_6h", "slope_6h", "delta_24h",
                     "slope_24h", "delta_72h", "slope_72h"}
    splits = Counter()
    for iteration in model._predictors:
        for predictor in iteration:
            for node in predictor.nodes:
                if not node["is_leaf"]:
                    splits[FEATURE_NAMES[int(node["feature_idx"])]] += 1
    probes = []
    for horizon in HORIZONS:
        values = []
        for slope in (-5.0, 0.0, 5.0):
            mapping = {"last_available_total": 1000.0, "observed_delta_since_first": 72 * slope,
                       "prefix_span_hours": 72.0, "latest_staleness_hours": 0.0,
                       "hours_to_kickoff": 240.0, "horizon_hours": horizon}
            for hours in (6, 24, 72):
                mapping[f"delta_{hours}h"], mapping[f"slope_{hours}h"] = hours * slope, slope
            value = float(model.predict(np.asarray([[mapping[k] for k in FEATURE_NAMES]], dtype=float))[0])
            values.append({"historical_slope_places_per_hour": slope, "predicted_delta": value})
        probes.append({"horizon_hours": horizon, "fixed_last_available_total": 1000.0, "probes": values,
                       "sensitivity_range": max(v["predicted_delta"] for v in values) - min(v["predicted_delta"] for v in values)})
    count = sum(splits[k] for k in history_names)
    return {"kind": "fixed_synthetic_mechanism_not_accuracy", "value_history_split_count": count,
            "feature_split_counts": dict(sorted(splits.items())), "probes": probes,
            "status": "MECHANISM_DEMONSTRATED" if count and any(p["sensitivity_range"] > 1e-9 for p in probes)
                      else "MECHANISM_NOT_DEMONSTRATED", "retune_permitted": False, "mae_computed": False}


def fit_once(outputdir, dataset, *, synthetic_test=False):
    """Gate before fitting; one exclusive marker prevents overwrite or refit."""
    recipe = load_precommit()
    training, gate = validate_dataset(dataset, synthetic_test=synthetic_test)
    result = {"version": VERSION, "status": "NO_FIT", "gate": gate,
              "precommit_sha256": PRECOMMIT_SHA256, "dataset_sha256": dataset["dataset_sha256"],
              "historical_knowledge_unproven": True, "production_change": False, "live_adjustment": 0}
    if gate["status"] != "READY_TO_FIT":
        return result
    if _now() < _time(recipe["created_at"]) or _now() < _time(recipe["training_data_cutoff_at"]):
        raise ValueError("Precommit/training cutoff must exist before actual fit")
    destination = Path(outputdir).resolve()
    if destination.is_relative_to(ROOT) or destination.is_symlink():
        raise ValueError("Trusted private model artifacts must remain outside Git")
    destination.mkdir(parents=True, exist_ok=True)
    lock = (destination / "fit.lock").open("a")
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if (destination / "manifest.json").exists():
            loaded = load_artifact(destination, allow_synthetic_test=synthetic_test)
            if loaded["manifest"]["dataset_sha256"] != dataset["dataset_sha256"]:
                raise ValueError("Existing artifact belongs to another dataset; no refit")
            return {**result, "status": "FROZEN_REUSED", "manifest": loaded["manifest"], "model_fit_performed": False}
        marker = destination / "fit-marker.json"
        code = _source_code_hashes()
        started = _now()
        marker_body = {"version": VERSION, "precommit_sha256": PRECOMMIT_SHA256,
                       "dataset_sha256": dataset["dataset_sha256"], "fit_started_at": started.isoformat(),
                       "status": "FIT_STARTED", "synthetic_test": synthetic_test}
        _write_private(marker, marker_body, exclusive=True)
        try:
            import joblib
            import numpy as np
            import sklearn
            from sklearn.ensemble import HistGradientBoostingRegressor
            if sklearn.__version__ != recipe["candidate"]["sklearn_version"]:
                raise ValueError("Precommitted sklearn version required")
            x, weights = _matrix(training), training_weights(training)
            model = HistGradientBoostingRegressor(**recipe["candidate"]["parameters"])
            model.fit(x, np.asarray([r["target_delta"] for r in training]), sample_weight=np.asarray(weights))
            audit = mechanism_audit(model)
            model_path = destination / "model.joblib"
            with os.fdopen(os.open(model_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), "wb") as stream:
                joblib.dump(model, stream, compress=3, protocol=5)
            if _source_code_hashes() != code:
                raise ValueError("Trainer/dataset code changed during the one fit")
            frozen = _now()
            manifest = {"version": VERSION, "precommit_sha256": PRECOMMIT_SHA256,
                        "dataset_sha256": dataset["dataset_sha256"], "source_bindings": dataset["source_bindings"],
                        "source_code_sha256": code, "parameters": recipe["candidate"]["parameters"],
                        "feature_names": list(FEATURE_NAMES), "sklearn_version": sklearn.__version__,
                        "training_data_cutoff_at": recipe["training_data_cutoff_at"],
                        "fit_started_at": started.isoformat(), "frozen_at": frozen.isoformat(),
                        "synthetic_test": synthetic_test, "historical_knowledge_unproven": True,
                        "historical_validation_accuracy_claim_allowed": False,
                        "model_file_sha256": _digest(model_path), "runtime_model_sha256": _runtime_model_hash(model),
                        "training_rows_sha256": _hash([r["row_sha256"] for r in training]),
                        "training_weights_sha256": _hash(weights), "training_weight_sum": sum(weights),
                        "training_fixture_groups": sorted({r["fixture_group"] for r in training}),
                        "training_event_ids": sorted({r["ticket_event_id"] for r in training}),
                        "gate": gate, "mechanism_audit": audit,
                        "training_maturity_range_hours": [min(r["features"]["hours_to_kickoff"] for r in training),
                                                          max(r["features"]["hours_to_kickoff"] for r in training)],
                        "private_artifact_trusted_local_only": True, "mae_computed": False,
                        "production_change": False, "live_adjustment": 0}
            manifest["manifest_sha256"] = _hash(manifest)
            _write_private(marker, {**marker_body, "status": "FIT_COMPLETE", "frozen_at": frozen.isoformat(),
                                    "manifest_sha256": manifest["manifest_sha256"]})
            _write_private(destination / "manifest.json", manifest, exclusive=True)
        except BaseException as exc:
            _write_private(marker, {**marker_body, "status": "FAILED_NO_REFIT", "error_type": type(exc).__name__})
            raise
        return {**result, "status": "SYNTHETIC_TEST_FITTED" if synthetic_test else "FITTED",
                "manifest": manifest, "model_fit_performed": True}
    except BlockingIOError:
        raise ValueError("Another fit owns this artifact directory") from None
    finally:
        fcntl.flock(lock, fcntl.LOCK_UN)
        lock.close()


def _validate_manifest(manifest, *, allow_synthetic_test=False):
    recipe = load_precommit()
    if not isinstance(manifest, dict) or manifest.get("manifest_sha256") != _hash({
            k: v for k, v in manifest.items() if k != "manifest_sha256"}):
        raise ValueError("Private model manifest checksum mismatch")
    if (manifest.get("version") != VERSION or manifest.get("precommit_sha256") != PRECOMMIT_SHA256
            or manifest.get("parameters") != recipe["candidate"]["parameters"]
            or manifest.get("feature_names") != list(FEATURE_NAMES)
            or manifest.get("training_data_cutoff_at") != recipe["training_data_cutoff_at"]
            or manifest.get("historical_knowledge_unproven") is not True
            or manifest.get("historical_validation_accuracy_claim_allowed") is not False
            or manifest.get("private_artifact_trusted_local_only") is not True
            or manifest.get("mae_computed") is not False
            or not isinstance(manifest.get("synthetic_test"), bool)
            or manifest.get("sklearn_version") != recipe["candidate"]["sklearn_version"]
            or manifest.get("production_change") is not False or manifest.get("live_adjustment") != 0
            or manifest.get("source_code_sha256") != _source_code_hashes()):
        raise ValueError("Private model differs from precommitted recipe/code")
    bindings = manifest.get("source_bindings")
    if not isinstance(bindings, dict) or any(
            not isinstance(bindings.get(kind), dict)
            or any(bindings[kind].get(k) != v for k, v in expected.items())
            or bindings[kind].get("verified_file_sha256") != expected["file_sha256"]
            for kind, expected in recipe["source_bindings"].items()):
        raise ValueError("Private model source bindings differ from precommit")
    if manifest.get("synthetic_test") is not False and not allow_synthetic_test:
        raise ValueError("Synthetic model is not servable")
    if not _time(recipe["created_at"]) <= _time(manifest["fit_started_at"]) <= _time(manifest["frozen_at"]) <= _now():
        raise ValueError("Actual fit/freeze clocks inconsistent")


def load_artifact(outputdir, *, allow_synthetic_test=False):
    """Read ONLY our trusted private outputs; verify file before joblib loading."""
    destination = Path(outputdir).resolve()
    if destination.is_relative_to(ROOT):
        raise ValueError("Private artifact cannot be loaded from Git")
    required = [destination / name for name in ("manifest.json", "fit-marker.json", "model.joblib")]
    if any(not p.is_file() or p.is_symlink() for p in required):
        raise ValueError("Complete trusted private artifact files required")
    manifest = json.loads(required[0].read_text())
    _validate_manifest(manifest, allow_synthetic_test=allow_synthetic_test)
    marker = json.loads(required[1].read_text())
    if (marker.get("status") != "FIT_COMPLETE" or marker.get("manifest_sha256") != manifest["manifest_sha256"]
            or marker.get("dataset_sha256") != manifest["dataset_sha256"]
            or marker.get("precommit_sha256") != PRECOMMIT_SHA256):
        raise ValueError("Incomplete/failed fit marker; no load or refit")
    if _digest(required[2]) != manifest["model_file_sha256"]:
        raise ValueError("Private model bytes checksum mismatch")
    import joblib
    import sklearn
    from sklearn.ensemble import HistGradientBoostingRegressor
    if sklearn.__version__ != manifest["sklearn_version"]:
        raise ValueError("Frozen estimator sklearn version mismatch")
    model = joblib.load(required[2])
    if type(model) is not HistGradientBoostingRegressor or _runtime_model_hash(model) != manifest["runtime_model_sha256"]:
        raise ValueError("Private estimator state differs from manifest")
    return {"version": VERSION, "model": model, "manifest": manifest}


def predict(artifactdir_or_loaded, issue, horizon, fixture_group, *, allow_synthetic_test=False):
    """Actual receipt-bound inference only; persistence is a separate caller step."""
    coordinate = features(issue, horizon)
    result = {"version": VERSION, "status": coordinate["status"], "horizon_hours": horizon,
              "target_at": coordinate["target_at"], "issued_at": issue["issued_at"], "computed_at": _now().isoformat(),
              "input_manifest_sha256": issue["input_manifest_sha256"], "predicted_available_total": None,
              "predicted_delta": None, "historical_training_knowledge_unproven": True,
              "evidence_kind": "pure_inference_not_persisted_prospective_evidence",
              "production_change": False, "live_adjustment": 0}
    if coordinate["status"] != "READY":
        return result
    loaded = (load_artifact(artifactdir_or_loaded, allow_synthetic_test=allow_synthetic_test)
              if isinstance(artifactdir_or_loaded, (str, Path)) else artifactdir_or_loaded)
    if not isinstance(loaded, dict) or loaded.get("model") is None:
        result["status"] = "MODEL_UNAVAILABLE"
        return result
    manifest, model = loaded.get("manifest"), loaded["model"]
    if isinstance(manifest, dict) and manifest.get("synthetic_test") is not False and not allow_synthetic_test:
        result["status"] = "SYNTHETIC_MODEL_NOT_SERVABLE"
        return result
    _validate_manifest(manifest, allow_synthetic_test=allow_synthetic_test)
    if not isinstance(fixture_group, str) or not fixture_group.strip():
        raise ValueError("Verified current fixture group required")
    if fixture_group in manifest["training_fixture_groups"] or issue["event"]["ticket_event_id"] in manifest["training_event_ids"]:
        result["status"] = "CURRENT_FIXTURE_IN_TRAINING"
        return result
    issued = _time(issue["issued_at"])
    if _time(manifest["frozen_at"]) >= issued:
        result["status"] = "MODEL_NOT_FROZEN_BEFORE_ISSUE"
        return result
    if issued > _now():
        raise ValueError("Future inference issue is forbidden")
    from ml.demand_engine.rolling72_benchmarks_v1 import source_family
    if source_family(issue) not in load_precommit()["data_evidence"]["source_families"]:
        result["status"] = "UNSUPPORTED_SOURCE_FAMILY"
        return result
    values = dict(coordinate["features"])
    age = values["latest_staleness_hours"]
    if age > load_precommit()["feature_semantics"]["live_freshness_limit_hours"]:
        result["status"] = "STALE_INPUT_FOR_V2"
        return result
    values["horizon_hours"] = horizon + age
    if _runtime_model_hash(model) != manifest["runtime_model_sha256"]:
        raise ValueError("Private estimator mutated after freeze")
    import numpy as np
    from sklearn.ensemble import HistGradientBoostingRegressor
    if type(model) is not HistGradientBoostingRegressor:
        raise ValueError("Unexpected estimator class")
    x = np.asarray([[float("nan") if values[k] is None else values[k] for k in FEATURE_NAMES]], dtype=float)
    delta = float(model.predict(x)[0])
    if not math.isfinite(delta) or not math.isfinite(issue["last_available_total"] + delta):
        raise ValueError("Nonfinite model forecast")
    predicted = max(0.0, issue["last_available_total"] + delta)
    minimum, maximum = manifest["training_maturity_range_hours"]
    result.update({"status": "READY", "predicted_available_total": predicted,
                   "predicted_delta": predicted - issue["last_available_total"], "raw_predicted_delta": delta,
                   "model_manifest_sha256": manifest["manifest_sha256"], "effective_lead_hours": horizon + age,
                   "capture_alignment_shift_hours": age,
                   "outside_training_maturity_range": not minimum <= values["hours_to_kickoff"] <= maximum,
                   "scenario_stability": "UNKNOWN", "intervals": None})
    return result
