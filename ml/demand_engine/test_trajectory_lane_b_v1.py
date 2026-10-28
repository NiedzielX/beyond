from datetime import datetime, timezone
import unittest

from ml.demand_engine.trajectory_feature_contract_v1 import LaneBSequenceV1, SequenceStepV1
from ml.demand_engine.trajectory_lane_b_v1 import (
    GRAD_CLIP,
    HIDDEN_DIM,
    LEARNING_RATE,
    MAX_EPOCHS,
    PRECOMMIT_ID,
    SEEDS,
    WEIGHT_DECAY,
    fit_global_preprocessor_v1,
    transform_global_v1,
    transform_sequence_v1,
)
from ml.demand_engine.trajectory_shared_dataset_v1 import TrajectoryDevelopmentExampleV1

UTC = timezone.utc


class TrajectoryLaneBV1ProtocolTest(unittest.TestCase):
    def _example(self) -> TrajectoryDevelopmentExampleV1:
        kickoff = datetime(2026, 10, 25, 18, 0, tzinfo=UTC)
        sequence = LaneBSequenceV1(
            contract_id="trajectory-feature-contract-v1",
            as_of_at=datetime(2026, 10, 24, 18, 0, tzinfo=UTC),
            kickoff_at=kickoff,
            steps=(
                SequenceStepV1(1, datetime(2026, 10, 23, 18, 0, tzinfo=UTC), 48.0, 1.0, None, None, None),
                SequenceStepV1(2, datetime(2026, 10, 24, 18, 0, tzinfo=UTC), 24.0, 0.8, None, 24.0, -0.2),
            ),
            first_available_total=1000,
            verified_capacity=20000,
        )
        return TrajectoryDevelopmentExampleV1(
            dataset_contract_id="trajectory-shared-development-dataset-v1",
            feature_contract_id="trajectory-feature-contract-v1",
            ticket_event_id=1,
            club_slug="test",
            kickoff_at=kickoff,
            days_to_event=1,
            as_of_at=datetime(2026, 10, 24, 18, 0, tzinfo=UTC),
            incumbent_p50=15000.0,
            actual_attendance=16000,
            residual_target=1000.0,
            lane_a_features={},
            lane_b_sequence=sequence,
            lane_b_global_features={
                "days_to_event": 1,
                "snapshot_age_minutes": 10.0,
                "clean_snapshot_count": 10,
                "observation_window_hours": 48.0,
                "max_visible_gap_hours": 24.0,
                "structural_incumbent_p50": 15000.0,
                "structural_incumbent_p50_share_of_capacity": 0.75,
                "verified_capacity_available": True,
                "sequence_length": 2,
            },
            event_row_weight=1.0,
        )

    def test_frozen_hyperparameters_match_precommit(self) -> None:
        self.assertEqual(PRECOMMIT_ID, "trajectory-lane-b-small-gru-residual-v1")
        self.assertEqual(SEEDS, (17, 29, 41))
        self.assertEqual(HIDDEN_DIM, 8)
        self.assertEqual(MAX_EPOCHS, 200)
        self.assertEqual(LEARNING_RATE, 0.001)
        self.assertEqual(WEIGHT_DECAY, 0.01)
        self.assertEqual(GRAD_CLIP, 1.0)

    def test_sequence_transform_preserves_genuine_two_step_shape(self) -> None:
        transformed = transform_sequence_v1(self._example())
        self.assertEqual(transformed.shape, (2, 5))
        self.assertAlmostEqual(float(transformed[0, 0]), 48.0 / 1440.0)
        self.assertAlmostEqual(float(transformed[1, 0]), 24.0 / 1440.0)
        self.assertAlmostEqual(float(transformed[1, 1]), 0.8)
        self.assertAlmostEqual(float(transformed[1, 3]), 1.0)
        self.assertAlmostEqual(float(transformed[1, 4]), -0.2)

    def test_global_preprocessing_is_train_fitted_and_finite(self) -> None:
        example = self._example()
        pre = fit_global_preprocessor_v1([example])
        transformed = transform_global_v1([example], pre)
        self.assertEqual(transformed.shape[0], 1)
        self.assertTrue((transformed == transformed).all())


if __name__ == "__main__":
    unittest.main()
