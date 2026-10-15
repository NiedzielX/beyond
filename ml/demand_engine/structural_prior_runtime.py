"""Executable Structural Prior runtime v1.

This module is the single implementation path for the frozen historical
champions that have an executable current-event runtime. It fits on an
explicit list of historical seasons and scores point-in-time feature rows.
It does not fetch future data and does not materialize forecasts by itself.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import ExtraTreesRegressor, GradientBoostingRegressor, HistGradientBoostingRegressor
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder

Horizon = Literal["T-30", "T-14", "T-7", "T-3"]
CAT = ["home_club_key", "away_club_key"]
META = {
    "feature_set_version", "match_key", "season", "horizon", "as_of_at", "kickoff_at",
    "home_club_key", "away_club_key", "target_attendance", "target_eligible", "training_eligible",
}
IMPORTANCE = {
    "combined_ppg", "abs_ppg_gap", "abs_position_gap", "combined_table_strength",
    "top4_any", "top4_both", "bottom4_any", "late_season_top4", "late_season_bottom4",
    "combined_form5", "abs_form5_gap", "rest_gap", "congestion_sum",
    "opponent_demand_x_progress", "opponent_demand_x_weekend",
}


@dataclass(frozen=True)
class RuntimeSpec:
    horizon: Horizon
    model_spec_id: str
    baseline_column: str
    feature_mode: Literal["base", "full"]
    estimator_name: Literal["extra_leaf3", "hist15", "gbr_huber", "hist250"]
    feature_contract: str = "structural-prior-pit-v1+verified-capacity-v1"
    validated_competitions: tuple[str, ...] = ("Ekstraklasa",)


CURRENT_EARLY_RUNTIME_SPECS: dict[Horizon, RuntimeSpec] = {
    "T-30": RuntimeSpec(
        horizon="T-30",
        model_spec_id="structural-prior-runtime-v1-t30-extra-full",
        baseline_column="baseline_season",
        feature_mode="full",
        estimator_name="extra_leaf3",
    ),
    "T-14": RuntimeSpec(
        horizon="T-14",
        model_spec_id="structural-prior-runtime-v1-t14-hist-base",
        baseline_column="baseline_r3",
        feature_mode="base",
        estimator_name="hist15",
    ),
    "T-7": RuntimeSpec(
        horizon="T-7",
        model_spec_id="structural-prior-runtime-v1-t7-gbr-base",
        baseline_column="baseline_season",
        feature_mode="base",
        estimator_name="gbr_huber",
    ),
    "T-3": RuntimeSpec(
        horizon="T-3",
        model_spec_id="structural-prior-runtime-v1-t3-hist-full",
        baseline_column="baseline_season",
        feature_mode="full",
        estimator_name="hist250",
    ),
}


@dataclass
class FittedStructuralPriorRuntime:
    spec: RuntimeSpec
    preprocessor: ColumnTransformer
    estimator: object
    numeric_features: list[str]
    training_seasons: tuple[str, ...]
    training_rows: int

    def predict(self, feature_rows: pd.DataFrame) -> np.ndarray:
        if feature_rows.empty:
            return np.asarray([], dtype=float)
        if set(feature_rows["horizon"].astype(str)) != {self.spec.horizon}:
            raise ValueError(f"Runtime {self.spec.horizon} received another horizon")
        if feature_rows[self.spec.baseline_column].isna().any():
            raise ValueError(f"Missing {self.spec.baseline_column} in inference row")
        if feature_rows["capacity"].isna().any() or (feature_rows["capacity"] <= 0).any():
            raise ValueError("Verified capacity is required for Structural Prior runtime")
        matrix = self.preprocessor.transform(feature_rows[CAT + self.numeric_features])
        residual = self.estimator.predict(matrix)
        prediction = (
            feature_rows[self.spec.baseline_column].astype(float).to_numpy()
            + residual * feature_rows["capacity"].astype(float).to_numpy()
        )
        return np.clip(prediction, 0.0, feature_rows["capacity"].astype(float).to_numpy())


def feature_columns(frame: pd.DataFrame, mode: Literal["base", "full"]) -> list[str]:
    numeric = [
        column for column in frame.columns
        if column not in META | set(CAT) and pd.api.types.is_numeric_dtype(frame[column])
    ]
    if mode == "base":
        return [column for column in numeric if column not in IMPORTANCE]
    return numeric


def _preprocessor(numeric: list[str]) -> ColumnTransformer:
    return ColumnTransformer([
        ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), CAT),
        ("num", SimpleImputer(strategy="median", add_indicator=True), numeric),
    ])


def _estimator(name: str):
    if name == "extra_leaf3":
        return ExtraTreesRegressor(
            n_estimators=500,
            min_samples_leaf=3,
            max_features=0.8,
            random_state=42,
            n_jobs=-1,
        )
    if name == "hist15":
        return HistGradientBoostingRegressor(
            loss="absolute_error",
            learning_rate=0.05,
            max_iter=180,
            max_leaf_nodes=15,
            min_samples_leaf=10,
            l2_regularization=1.0,
            random_state=42,
        )
    if name == "gbr_huber":
        return GradientBoostingRegressor(
            loss="huber",
            n_estimators=180,
            learning_rate=0.03,
            max_depth=2,
            min_samples_leaf=8,
            random_state=42,
        )
    if name == "hist250":
        return HistGradientBoostingRegressor(
            loss="absolute_error",
            learning_rate=0.05,
            max_iter=250,
            max_leaf_nodes=15,
            min_samples_leaf=10,
            l2_regularization=1.0,
            random_state=42,
        )
    raise KeyError(name)


def fit_structural_prior_runtime(
    feature_store: pd.DataFrame,
    horizon: Horizon,
    training_seasons: list[str] | tuple[str, ...],
) -> FittedStructuralPriorRuntime:
    spec = CURRENT_EARLY_RUNTIME_SPECS[horizon]
    rows = feature_store[
        (feature_store["horizon"].astype(str) == horizon)
        & feature_store["training_eligible"].astype(bool)
        & feature_store["season"].isin(training_seasons)
    ].copy()
    rows = rows[rows[spec.baseline_column].notna()].copy()
    if rows.empty:
        raise ValueError(f"No eligible training rows for {horizon}")
    numeric = feature_columns(feature_store, spec.feature_mode)
    pre = _preprocessor(numeric)
    x_train = pre.fit_transform(rows[CAT + numeric])
    y_train = (
        rows["target_attendance"].astype(float) / rows["capacity"].astype(float)
        - rows[spec.baseline_column].astype(float) / rows["capacity"].astype(float)
    )
    model = _estimator(spec.estimator_name)
    model.fit(x_train, y_train)
    return FittedStructuralPriorRuntime(
        spec=spec,
        preprocessor=pre,
        estimator=model,
        numeric_features=numeric,
        training_seasons=tuple(training_seasons),
        training_rows=int(len(rows)),
    )
