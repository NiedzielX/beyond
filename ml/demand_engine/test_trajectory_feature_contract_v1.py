from datetime import datetime, timedelta, timezone
import unittest

from ml.demand_engine.daily_trajectory_dataset import build_daily_trajectory_dataset
from ml.demand_engine.live_trajectory_feature_store import SnapshotRecord
from ml.demand_engine.structural_prior import StructuralPrior
from ml.demand_engine.trajectory_feature_contract_v1 import (
    CONTRACT_ID,
    LANE_A_NUMERIC_FEATURES,
    LANE_A_QUALITY_FEATURES,
    LANE_B_GLOBAL_FIELDS,
    LANE_B_SEQUENCE_FIELDS,
    SequenceInputInsufficientError,
    build_lane_b_sequence_v1,
    lane_a_features_v1,
    lane_b_global_features_v1,
    shared_eligibility_v1,
)

UTC = timezone.utc


class TrajectoryFeatureContractV1Test(unittest.TestCase):
    def setUp(self) -> None:
        self.kickoff = datetime(2026, 12, 10, 20, 0, tzinfo=UTC)
        self.as_of = self.kickoff - timedelta(days=2)

    def _prior(self) -> StructuralPrior:
        return StructuralPrior(
            ticket_event_id=101,
            horizon="T-3",
            requested_as_of_at=self.as_of - timedelta(hours=1),
            target_as_of_at=self.as_of - timedelta(hours=1),
            kickoff_at=self.kickoff,
            model_spec_id="test-structural",
            model_family="test-family",
            feature_contract="test-contract",
            p50=15000.0,
            p10=14000.0,
            p90=16000.0,
            stadium_capacity=20000,
            point_in_time_validated=True,
            source_prior_id=10,
            generated_at=self.as_of - timedelta(minutes=30),
        )

    def _ready_snapshots(self) -> list[SnapshotRecord]:
        return [
            SnapshotRecord(1, self.as_of - timedelta(hours=30), 9000),
            SnapshotRecord(2, self.as_of - timedelta(hours=20), 8800),
            SnapshotRecord(3, self.as_of - timedelta(hours=10), 8500),
            SnapshotRecord(4, self.as_of, 8100),
        ]

    def _row(self):
        return build_daily_trajectory_dataset(
            ticket_event_id=101,
            club_slug="lech",
            kickoff_at=self.kickoff,
            snapshots=self._ready_snapshots(),
            structural_priors=[self._prior()],
            stadium_capacity=20000,
            start_days=2,
            end_days=2,
        )[0]

    def test_shared_gate_accepts_ready_row(self) -> None:
        row = self._row()
        self.assertEqual(row.trajectory.signal_readiness, "ready")
        eligibility = shared_eligibility_v1(row)
        self.assertTrue(eligibility.eligible)
        self.assertEqual(eligibility.reasons, ())

    def test_shared_gate_rejects_short_prefix(self) -> None:
        row = build_daily_trajectory_dataset(
            ticket_event_id=101,
            club_slug="lech",
            kickoff_at=self.kickoff,
            snapshots=[SnapshotRecord(1, self.as_of, 9000)],
            structural_priors=[self._prior()],
            stadium_capacity=20000,
            start_days=2,
            end_days=2,
        )[0]
        eligibility = shared_eligibility_v1(row)
        self.assertFalse(eligibility.eligible)
        self.assertIn("INSUFFICIENT_CLEAN_SNAPSHOTS", eligibility.reasons)
        self.assertIn("INSUFFICIENT_OBSERVATION_WINDOW", eligibility.reasons)
        self.assertIn("SIGNAL_NOT_READY", eligibility.reasons)

    def test_lane_a_feature_names_are_exact(self) -> None:
        features = lane_a_features_v1(self._row())
        self.assertEqual(
            set(features),
            set(LANE_A_NUMERIC_FEATURES) | set(LANE_A_QUALITY_FEATURES),
        )
        self.assertEqual(features["structural_incumbent_p50"], 15000.0)
        self.assertEqual(features["structural_incumbent_p50_share_of_capacity"], 0.75)

    def test_sequence_uses_only_visible_genuine_observations(self) -> None:
        future = SnapshotRecord(99, self.as_of + timedelta(hours=1), 1)
        seq = build_lane_b_sequence_v1(
            self._ready_snapshots() + [future],
            as_of_at=self.as_of,
            kickoff_at=self.kickoff,
            stadium_capacity=20000,
        )
        self.assertEqual(seq.contract_id, CONTRACT_ID)
        self.assertNotIn(99, [step.snapshot_id for step in seq.steps])
        self.assertFalse(seq.target_future_points_used)
        self.assertTrue(seq.point_in_time_validated)
        self.assertEqual(len(seq.steps), 4)

    def test_sequence_dedupes_exact_timestamp_by_highest_snapshot_id(self) -> None:
        ts = self.as_of - timedelta(hours=5)
        seq = build_lane_b_sequence_v1(
            [
                SnapshotRecord(1, ts, 9000),
                SnapshotRecord(2, ts, 8000),
            ],
            as_of_at=self.as_of,
            kickoff_at=self.kickoff,
            stadium_capacity=20000,
        )
        self.assertEqual(seq.sequence_length, 1)
        self.assertEqual(seq.steps[0].snapshot_id, 2)
        self.assertEqual(seq.first_available_total, 8000)

    def test_sequence_keeps_latest_genuine_observation_per_hour_bucket(self) -> None:
        # Both observations are in the same integer hour-to-kickoff bucket.
        first = SnapshotRecord(1, self.as_of - timedelta(minutes=40), 9000)
        later = SnapshotRecord(2, self.as_of - timedelta(minutes=10), 8500)
        seq = build_lane_b_sequence_v1(
            [first, later],
            as_of_at=self.as_of,
            kickoff_at=self.kickoff,
            stadium_capacity=20000,
        )
        self.assertEqual(seq.sequence_length, 1)
        self.assertEqual(seq.steps[0].snapshot_id, 2)

    def test_sequence_has_no_forward_fill(self) -> None:
        seq = build_lane_b_sequence_v1(
            [
                SnapshotRecord(1, self.as_of - timedelta(hours=30), 9000),
                SnapshotRecord(2, self.as_of, 8100),
            ],
            as_of_at=self.as_of,
            kickoff_at=self.kickoff,
            stadium_capacity=20000,
        )
        self.assertEqual(seq.sequence_length, 2)
        self.assertAlmostEqual(seq.steps[1].delta_hours_since_previous or 0, 30.0)
        self.assertAlmostEqual(seq.steps[0].available_index, 1.0)
        self.assertAlmostEqual(seq.steps[1].available_index, 0.9)
        self.assertAlmostEqual(seq.steps[1].delta_available_index or 0, -0.1)

    def test_zero_first_inventory_fails_closed(self) -> None:
        with self.assertRaises(SequenceInputInsufficientError):
            build_lane_b_sequence_v1(
                [SnapshotRecord(1, self.as_of, 0)],
                as_of_at=self.as_of,
                kickoff_at=self.kickoff,
                stadium_capacity=20000,
            )

    def test_lane_b_global_feature_names_are_exact(self) -> None:
        row = self._row()
        seq = build_lane_b_sequence_v1(
            self._ready_snapshots(),
            as_of_at=self.as_of,
            kickoff_at=self.kickoff,
            stadium_capacity=20000,
        )
        features = lane_b_global_features_v1(row, seq)
        self.assertEqual(set(features), set(LANE_B_GLOBAL_FIELDS))
        self.assertEqual(features["sequence_length"], 4)
        self.assertEqual(features["verified_capacity_available"], True)

    def test_model_sequence_field_order_is_frozen(self) -> None:
        seq = build_lane_b_sequence_v1(
            self._ready_snapshots(),
            as_of_at=self.as_of,
            kickoff_at=self.kickoff,
            stadium_capacity=20000,
        )
        self.assertEqual(len(seq.steps[0].model_values()), len(LANE_B_SEQUENCE_FIELDS))

    def test_timezone_naive_cutoff_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            build_lane_b_sequence_v1(
                self._ready_snapshots(),
                as_of_at=datetime(2026, 12, 8, 20, 0),
                kickoff_at=self.kickoff,
            )


if __name__ == "__main__":
    unittest.main()
