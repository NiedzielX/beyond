#!/usr/bin/env python3
"""Unit checks for a2 external + ensemble closure audit."""
from __future__ import annotations

import numpy as np

from ml.a2_external_ensemble_closure_v1 import (
    HORIZONS,
    candidate_specs,
    median_prediction,
    select_weighted_ensemble,
    simplex_weight_vectors,
    weighted_prediction,
)


def test_candidate_contracts() -> None:
    for horizon in HORIZONS:
        specs = candidate_specs(horizon)
        ids = [item.id for item in specs]
        assert len(ids) == len(set(ids))
        assert ids[0] == "current-a2-base"
        families = {item.family for item in specs}
        assert {"current_a2", "catboost", "lightgbm", "xgboost"}.issubset(families)
        if horizon == "T-7":
            assert "hist" not in families
        else:
            assert "hist" in families


def test_simplex_weights() -> None:
    vectors = simplex_weight_vectors(3, step=0.25, min_nonzero=2)
    assert vectors
    assert all(np.isclose(sum(item), 1.0) for item in vectors)
    assert all(sum(value > 0 for value in item) >= 2 for item in vectors)
    assert (1.0, 0.0, 0.0) not in vectors


def test_ensemble_predictions() -> None:
    p1 = np.asarray([10.0, 20.0, 30.0])
    p2 = np.asarray([20.0, 30.0, 40.0])
    p3 = np.asarray([30.0, 40.0, 50.0])

    median = median_prediction([p1, p2, p3])
    np.testing.assert_allclose(median, np.asarray([20.0, 30.0, 40.0]))

    weighted = weighted_prediction([p1, p2], (0.25, 0.75))
    np.testing.assert_allclose(weighted, np.asarray([17.5, 27.5, 37.5]))


def test_weight_selection_uses_only_supplied_development_labels() -> None:
    actual = np.asarray([10.0, 10.0, 10.0, 10.0])
    member_ids = ["a", "b", "c"]
    predictions = [
        np.asarray([10.0, 10.0, 10.0, 10.0]),
        np.asarray([12.0, 12.0, 12.0, 12.0]),
        np.asarray([20.0, 20.0, 20.0, 20.0]),
    ]
    selected = select_weighted_ensemble(actual, member_ids, predictions)
    assert selected["member_ids"] == member_ids
    assert np.isclose(sum(selected["weights"]), 1.0)
    assert sum(value > 0 for value in selected["weights"]) >= 2
    assert selected["candidate_weight_vectors"] > 0
    assert selected["mae"] > 0.0


def main() -> None:
    test_candidate_contracts()
    test_simplex_weights()
    test_ensemble_predictions()
    test_weight_selection_uses_only_supplied_development_labels()
    print("a2 external ensemble closure unit checks: PASS")


if __name__ == "__main__":
    main()
