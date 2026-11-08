"""One precommitted rolling72 median-tree candidate, gated before any fit.

Original receipt bytes and archived fixture-identity evidence are verified by
the dataset builder. The shared training-row validator checks their declared
hashes/clocks; declarations alone are not independent source authentication.
Support and event/horizon weights are recomputed from actual canonical rows,
never accepted as caller-supplied counts. No random split/search or refit occurs.

Successful fitting returns a trusted private Python estimator plus a hashed
manifest. There is no pickle loader, public artifact endpoint or automatic
production activation. Synthetic tests are explicitly marked and rejected by
default inference. A result in memory is not persisted prospective evidence.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import pickle

from ml.demand_engine.rolling72_features_v1 import (
    HORIZONS, VERSION as FEATURE_VERSION, _hash, _time, features,
)


MODEL_VERSION = "rolling72-global-quantile-tree-v1"
PRECOMMIT_VERSION = "rolling72-benchmarks-and-quantile-tree-precommit-v1"
PRECOMMIT_SHA256 = "9fc87bf69f796d644585ea0a5dc96800cb4322d42ad523cab2a75fb3ef5a7bc0"
PRECOMMIT_PATH = Path(__file__).parents[1] / "artifacts/rolling72_v1/precommit.json"
FEATURE_NAMES = (
    "last_available_total", "observed_delta_since_first", "prefix_span_hours",
    "latest_staleness_hours", "hours_to_kickoff", "horizon_hours",
    "delta_6h", "slope_6h", "delta_24h", "slope_24h", "delta_72h", "slope_72h",
)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def load_precommit() -> dict:
    """Load the exact already-declared recipe; no parameter overrides exist."""
    recipe = json.loads(PRECOMMIT_PATH.read_text())
    digest = _hash({key: value for key, value in recipe.items() if key != "precommit_sha256"})
    if (recipe.get("version") != PRECOMMIT_VERSION or recipe.get("precommit_sha256") != digest
            or digest != PRECOMMIT_SHA256 or recipe["candidate"]["id"] != MODEL_VERSION
            or tuple(recipe["features"]) != FEATURE_NAMES
            or tuple(recipe["horizons_hours"]) != HORIZONS
            or recipe.get("production_change") is not False or recipe.get("live_adjustment") != 0):
        raise ValueError("Challenger requires the exact frozen precommit")
    return recipe


def _gate_rows(rows: list[dict], cutoff: datetime, recipe: dict) -> tuple[list[dict], dict]:
    # Import only when evaluating support, keeping the dependency direction
    # from this candidate to the shared benchmark/data-boundary validator.
    from ml.demand_engine.rolling72_benchmarks_v1 import validated_training_rows

    clean = validated_training_rows(rows, cutoff.isoformat())
    by_group: dict[str, list[dict]] = defaultdict(list)
    ticket_groups, group_clubs, seen = {}, {}, set()
    for row in clean:
        group, club, identity = row["fixture_group"], row["club_slug"], row["event_id"]
        if identity in ticket_groups and ticket_groups[identity] != group:
            raise ValueError("One ticket event cannot become multiple independent fixture groups")
        if group in group_clubs and group_clubs[group] != club:
            raise ValueError("Fixture aliases disagree on club identity")
        ticket_groups[identity], group_clubs[group] = group, club
        key = (group, row["issue"]["issued_at"], row["horizon_hours"])
        if key in seen:
            raise ValueError("Duplicate fixture/issue/horizon cannot multiply training support")
        seen.add(key)
        by_group[group].append(row)
    common = {group for group, values in by_group.items()
              if {row["horizon_hours"] for row in values} == set(HORIZONS)}
    training = [row for row in clean if row["fixture_group"] in common]
    # Stable order binds the matrix/weight manifest independently of row order.
    training.sort(key=lambda row: (row["fixture_group"], row["issue"]["issued_at"],
                                   row["horizon_hours"], row["event_id"]))
    per_horizon = {}
    for horizon in HORIZONS:
        selected = [row for row in training if row["horizon_hours"] == horizon]
        per_horizon[str(horizon)] = {
            "rows": len(selected), "fixtures": len({row["fixture_group"] for row in selected}),
            "clubs": len({row["club_slug"] for row in selected}),
        }
    requirement = recipe["training"]
    reasons = []
    if len(common) < requirement["min_common_all_horizons_fixtures"]:
        reasons.append("INSUFFICIENT_COMMON_ALL_HORIZONS_FIXTURES")
    if len(training) < requirement["min_total_labeled_rows"]:
        reasons.append("INSUFFICIENT_TOTAL_LABELED_ROWS")
    for horizon, support in per_horizon.items():
        if support["fixtures"] < requirement["min_independent_fixtures_per_horizon"]:
            reasons.append(f"INSUFFICIENT_FIXTURES_{horizon}H")
        if support["clubs"] < requirement["min_clubs_per_horizon"]:
            reasons.append(f"INSUFFICIENT_CLUBS_{horizon}H")
    gate = {
        "status": "READY_TO_FIT" if not reasons else "NO_FIT",
        "reasons": reasons, "supplied_row_count": len(rows),
        "validated_row_count": len(clean), "training_row_count": len(training),
        "common_fixture_count": len(common),
        "common_club_count": len({group_clubs[group] for group in common}),
        "partial_horizon_fixture_groups_excluded": sorted(set(by_group) - common),
        "per_horizon": per_horizon,
    }
    return training, gate


def training_weights(rows: list[dict]) -> list[float]:
    """Equal fixture weight, then each of its three horizons, mean weight1."""
    if not rows:
        return []
    counts = Counter((row["fixture_group"], row["horizon_hours"]) for row in rows)
    groups = {row["fixture_group"] for row in rows}
    if any((group, horizon) not in counts for group in groups for horizon in HORIZONS):
        raise ValueError("Training weights require common all-horizon fixtures")
    number = len(rows)
    return [number / (len(groups) * len(HORIZONS) * counts[(row["fixture_group"], row["horizon_hours"])])
            for row in rows]


def _feature_values(issue: dict, horizon: int) -> list[float]:
    point = features(issue, horizon)
    if point["status"] != "READY" or set(point["features"]) != set(FEATURE_NAMES):
        raise ValueError("Candidate requires a canonical READY twelve-feature point")
    values = []
    for key in FEATURE_NAMES:
        value = point["features"][key]
        if value is None:
            values.append(float("nan"))
        elif isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
            raise ValueError("Candidate feature must be finite or missing")
        else:
            values.append(float(value))
    return values


def _model_hash(model) -> str:
    # Only serialize our own trusted private in-memory estimator. Never load
    # pickle bytes from a public request/source; no deserialization is offered.
    return hashlib.sha256(pickle.dumps(model, protocol=5)).hexdigest()


def fit_candidate(rows: list[dict], fit_cutoff=None, *, synthetic_test: bool = False) -> dict:
    """Fit the one recipe only after data-derived support passes every gate.

    ``rows`` come from the original-byte/identity-verified archive builder.
    Failure to meet support returns NO_FIT without importing/fitting sklearn.
    Malformed or unverifiable rows fail closed in the shared row validator.
    The fixed precommit cutoff cannot be advanced to admit newly seen labels.
    """
    recipe = load_precommit()
    cutoff = _time(recipe["fit_cutoff_at"] if fit_cutoff is None else fit_cutoff)
    if cutoff != _time(recipe["fit_cutoff_at"]):
        raise ValueError("Fit cutoff differs from the frozen precommit")
    if not isinstance(synthetic_test, bool):
        raise ValueError("Explicit synthetic-test boolean required")
    training, gate = _gate_rows(rows, cutoff, recipe)
    result = {
        "version": MODEL_VERSION, "precommit_sha256": PRECOMMIT_SHA256,
        "status": "NO_FIT", "gate": gate, "model": None, "manifest": None,
        "production_change": False, "live_adjustment": 0,
    }
    if gate["status"] != "READY_TO_FIT":
        return result
    if _now() < cutoff:
        gate["status"] = "NO_FIT"
        gate["reasons"].append("FIT_CUTOFF_NOT_REACHED")
        return result
    import numpy as np
    import sklearn
    from sklearn.ensemble import HistGradientBoostingRegressor

    if sklearn.__version__ != recipe["candidate"]["sklearn_version"]:
        raise ValueError("Candidate requires the precommitted sklearn version")
    matrix = np.asarray([_feature_values(row["issue"], row["horizon_hours"]) for row in training], dtype=float)
    targets = np.asarray([row["delta"] for row in training], dtype=float)
    weights = training_weights(training)
    lineage = [
        {"fixture_group": row["fixture_group"], "event_id": row["event_id"],
         "horizon_hours": row["horizon_hours"],
         "input_manifest_sha256": row["issue"]["input_manifest_sha256"],
         "label_sha256": row["matched_label"]["label_sha256"],
         "source_lineage": {
             **{key: row["source_lineage"][key] for key in (
                 "evidence", "identity_proven", "input_receipt_sha256",
                 "label_receipt_sha256", "identity_registry_sha256")},
             **{key: _time(row["source_lineage"][key]).isoformat()
                for key in ("input_receipt_known_at", "label_receipt_known_at")}}}
        for row in training
    ]
    # Validate all metadata serialization before the one expensive fit, too.
    training_digest, weight_digest = _hash(lineage), _hash(weights)
    model = HistGradientBoostingRegressor(**recipe["candidate"]["parameters"])
    started = _now()
    model.fit(matrix, targets, sample_weight=np.asarray(weights))
    frozen = _now()
    manifest = {
        "version": MODEL_VERSION, "precommit_sha256": PRECOMMIT_SHA256,
        "fit_cutoff_at": cutoff.isoformat(), "fit_started_at": started.isoformat(),
        "frozen_at": frozen.isoformat(), "synthetic_test": synthetic_test,
        "feature_version": FEATURE_VERSION, "feature_names": list(FEATURE_NAMES),
        "parameters": recipe["candidate"]["parameters"], "sklearn_version": sklearn.__version__,
        "training_row_count": len(training), "training_rows_sha256": training_digest,
        "training_weights_sha256": weight_digest, "training_weight_sum": sum(weights),
        "training_fixture_groups": sorted({row["fixture_group"] for row in training}),
        "training_event_ids": sorted({row["event_id"] for row in training}),
        "source_receipt_sha256s": sorted({row["source_lineage"][key] for row in training
                                         for key in ("input_receipt_sha256", "label_receipt_sha256")}),
        "identity_registry_sha256s": sorted({row["source_lineage"]["identity_registry_sha256"] for row in training}),
        "trusted_boundary": "original bytes and archived identities verified by dataset builder",
        "source_code_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "model_sha256": _model_hash(model), "production_change": False, "live_adjustment": 0,
    }
    manifest["manifest_sha256"] = _hash(manifest)
    result.update({"status": "SYNTHETIC_TEST_FITTED" if synthetic_test else "FITTED",
                   "model": model, "manifest": manifest})
    return result


def predict_candidate(fitted: dict, issue: dict, horizon_hours: int, fixture_group: str,
                      *, allow_synthetic_test: bool = False) -> dict:
    """Infer only for a new fixture after a genuine artifact freeze; no writes."""
    coordinate = features(issue, horizon_hours)
    result = {
        "version": MODEL_VERSION, "precommit_sha256": PRECOMMIT_SHA256,
        "input_manifest_sha256": issue["input_manifest_sha256"],
        "issued_at": issue["issued_at"], "target_at": coordinate["target_at"],
        "horizon_hours": horizon_hours, "fixture_group": fixture_group,
        "status": "MODEL_NOT_FITTED", "predicted_available_total": None,
        "predicted_delta": None, "raw_predicted_delta": None,
        "evidence_kind": "inference_only_not_proof_of_persisted_prospective_forecast",
        "production_change": False, "live_adjustment": 0,
    }
    if coordinate["status"] != "READY":
        result["status"] = coordinate["status"]
        return result
    from ml.demand_engine.rolling72_benchmarks_v1 import source_family

    if source_family(issue) is None:
        result["status"] = "UNSUPPORTED_SOURCE_FAMILY"
        return result
    if fitted.get("status") not in {"FITTED", "SYNTHETIC_TEST_FITTED"} or fitted.get("model") is None:
        return result
    manifest = fitted.get("manifest")
    if (not isinstance(manifest, dict) or manifest.get("manifest_sha256") != _hash({
            key: value for key, value in manifest.items() if key != "manifest_sha256"})):
        raise ValueError("Candidate manifest hash mismatch")
    recipe = load_precommit()
    if (manifest.get("version") != MODEL_VERSION or manifest.get("precommit_sha256") != PRECOMMIT_SHA256
            or manifest.get("feature_names") != list(FEATURE_NAMES)
            or manifest.get("parameters") != recipe["candidate"]["parameters"]
            or manifest.get("fit_cutoff_at") != recipe["fit_cutoff_at"]
            or manifest.get("production_change") is not False or manifest.get("live_adjustment") != 0):
        raise ValueError("Candidate differs from the exact precommitted recipe")
    if manifest.get("synthetic_test") is not False and not allow_synthetic_test:
        result["status"] = "SYNTHETIC_MODEL_NOT_SERVABLE"
        return result
    if not isinstance(fixture_group, str) or not fixture_group.strip():
        raise ValueError("Proven inference fixture group required")
    if (fixture_group in manifest["training_fixture_groups"]
            or issue["event"]["ticket_event_id"] in manifest["training_event_ids"]):
        result["status"] = "INFERENCE_FIXTURE_IN_TRAIN"
        return result
    issued, frozen = _time(issue["issued_at"]), _time(manifest["frozen_at"])
    if not _time(manifest["fit_cutoff_at"]) <= _time(manifest["fit_started_at"]) <= frozen:
        raise ValueError("Candidate fit/freeze clocks are inconsistent")
    if frozen >= issued:
        result["status"] = "MODEL_NOT_FROZEN_BEFORE_ISSUE"
        return result
    if issued > _now():
        raise ValueError("Inference issue cannot lie in the future")
    import numpy as np
    import sklearn
    from sklearn.ensemble import HistGradientBoostingRegressor

    model = fitted["model"]
    if (type(model) is not HistGradientBoostingRegressor
            or sklearn.__version__ != manifest["sklearn_version"]
            or _model_hash(model) != manifest["model_sha256"]):
        raise ValueError("Private estimator bytes/version differ from frozen manifest")
    prediction = float(model.predict(np.asarray([_feature_values(issue, horizon_hours)], dtype=float))[0])
    if not math.isfinite(prediction):
        raise ValueError("Candidate returned a nonfinite forecast")
    last = issue["last_available_total"]
    available = max(0.0, last + prediction)
    result.update({"status": "READY", "predicted_available_total": available,
                   "raw_predicted_delta": prediction, "predicted_delta": available - last,
                   "model_manifest_sha256": manifest["manifest_sha256"],
                   "scenario_stability": "UNKNOWN", "intervals": None})
    return result
