import unittest
from datetime import datetime, timezone

from ml.demand_engine.live_trajectory_feature_store import LiveTrajectoryFeatures
from ml.demand_engine.structural_prior_shadow import (
    ENGINE_VERSION,
    P50ShadowForecast,
    StructuralPriorShadowError,
    StructuralPriorSnapshot,
    to_forecast_observation,
)
from ml.demand_engine.trajectory_gap import TrajectoryGapResult

UTC = timezone.utc
AS_OF = datetime(2026, 10, 15, 12, 31, tzinfo=UTC)
KICKOFF = datetime(2026, 10, 31, 16, 30, tzinfo=UTC)


def prior(**overrides):
    values = dict(
        status="ready",
        source_prior_id=1,
        horizon="T-30",
        model_spec_id="structural-prior-runtime-v1-t30-extra-full",
        model_family="ExtraTreesRegressor",
        feature_contract="structural-prior-pit-v1+verified-capacity-v1",
        p50=31832.4063,
        stadium_capacity=43269,
        expected_occupancy=0.735686,
        point_in_time_validated=True,
    )
    values.update(overrides)
    return StructuralPriorSnapshot(**values)


def live(**overrides):
    values = dict(
        feature_version="live-trajectory-v1.1",
        signal_readiness="ready",
        feature_quality="sector_matched_plus_raw",
        inventory_interpretation="demand_proxy_not_confirmed_sales",
        point_in_time_validated=True,
        snapshot_id=15278,
        snapshot_captured_at=AS_OF,
        as_of=AS_OF,
        kickoff_at=KICKOFF,
        hours_to_kickoff=(KICKOFF-AS_OF).total_seconds()/3600,
        days_to_kickoff=(KICKOFF-AS_OF).total_seconds()/86400,
        checkpoint_label=None,
        checkpoint_ready=False,
        available_total=10534,
        first_available_total=17683,
        available_index=0.5957134,
        net_removed_since_first=7149,
        velocity_6h=12.822181,
        velocity_24h=13.709691,
        velocity_6h_pct_of_first_per_hour=0.0725113414,
        velocity_24h_pct_of_first_per_hour=0.0775303476,
        acceleration_6h_vs_24h=-0.88751,
        raw_snapshot_count=754,
        clean_snapshot_count=754,
        excluded_anomaly_count=0,
    )
    values.update(overrides)
    return LiveTrajectoryFeatures(**values)


def gap(**overrides):
    values = dict(
        version="trajectory-gap-v1",
        reference_mode="empirical_inventory_progress_by_horizon_v1",
        prior_mapping_mode="anchor_only_no_inventory_to_attendance_conversion",
        ticket_event_id=6,
        as_of_at=AS_OF,
        structural_prior_id=1,
        structural_prior_horizon="T-30",
        structural_prior_p50=31832.4063,
        reference_horizon=None,
        reference_event_count=0,
        reference_club_count=0,
        observed_progress=0.4042866,
        expected_progress=None,
        expected_progress_q25=None,
        expected_progress_q75=None,
        level_gap=None,
        observed_velocity_24h=0.0775303476,
        expected_velocity_24h=None,
        velocity_gap=None,
        observed_acceleration_6h_vs_24h=-0.0050190062,
        expected_acceleration_6h_vs_24h=None,
        acceleration_gap=None,
        status="INSUFFICIENT_SIGNAL",
        confidence="NONE",
        reason_code="outside_reference_checkpoint_window",
        signal_readiness="ready",
        feature_quality="sector_matched_plus_raw",
        point_in_time_validated=True,
    )
    values.update(overrides)
    return TrajectoryGapResult(**values)


def forecast(**overrides):
    values = dict(
        ticket_event_id=6,
        club_slug="lech",
        home_team="Lech Poznań",
        away_team="Wisła Kraków",
        competition="Ekstraklasa",
        kickoff_at=KICKOFF,
        forecast_generated_at=AS_OF,
        source_snapshot_id=15278,
        source_snapshot_captured_at=AS_OF,
        prior=prior(),
        live=live(),
        trajectory_gap=gap(),
    )
    values.update(overrides)
    return P50ShadowForecast(**values)


class StructuralPriorShadowTest(unittest.TestCase):
    def test_serializes_p50_only_without_fake_intervals(self):
        row = to_forecast_observation(forecast())
        self.assertEqual(row["model_version"], ENGINE_VERSION)
        self.assertEqual(row["horizon"], "T-30")
        self.assertEqual(row["historical_model"], "structural-prior-runtime-v1-t30-extra-full")
        self.assertEqual(row["historical_p50"], 31832)
        self.assertEqual(row["final_p50"], 31832)
        self.assertEqual(row["live_adjustment"], 0)
        self.assertNotIn("historical_p10", row)
        self.assertNotIn("historical_p90", row)
        self.assertNotIn("final_p10", row)
        self.assertNotIn("final_p90", row)
        self.assertEqual(row["payload"]["trajectory_gap"]["status"], "INSUFFICIENT_SIGNAL")
        self.assertEqual(
            row["payload"]["trajectory_gap"]["reason_code"],
            "outside_reference_checkpoint_window",
        )
        self.assertEqual(row["payload"]["engine"]["historical_interval_method"], "not_yet_calibrated")

    def test_keeps_prior_horizon_not_legacy_nearest_horizon(self):
        row = to_forecast_observation(forecast())
        self.assertEqual(row["horizon"], "T-30")
        self.assertIsNone(row["payload"]["live"]["checkpoint_label"])

    def test_rejects_non_ready_prior(self):
        with self.assertRaisesRegex(StructuralPriorShadowError, "must be ready"):
            to_forecast_observation(forecast(prior=prior(status="missing_prior")))

    def test_rejects_prior_gap_lineage_mismatch(self):
        with self.assertRaisesRegex(StructuralPriorShadowError, "prior mismatch"):
            to_forecast_observation(forecast(trajectory_gap=gap(structural_prior_id=999)))

    def test_rejects_fake_or_mismatched_live_lineage(self):
        with self.assertRaisesRegex(StructuralPriorShadowError, "snapshot"):
            to_forecast_observation(forecast(live=live(snapshot_id=1)))


if __name__ == "__main__":
    unittest.main()
