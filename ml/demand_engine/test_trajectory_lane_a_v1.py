from datetime import datetime, timedelta, timezone
import unittest

from ml.demand_engine.live_trajectory_feature_store import SnapshotRecord
from ml.demand_engine.structural_prior import StructuralPrior
from ml.demand_engine.trajectory_lane_a_v1 import (
    PRECOMMIT_ID,
    RIDGE_ALPHA,
    evaluate_lane_a_forward_v1,
    fit_preprocessor_v1,
)
from ml.demand_engine.trajectory_shared_dataset_v1 import (
    TrajectoryEventBundleV1,
    TrajectoryOutcomeV1,
    materialize_shared_dataset_v1,
)
from ml.demand_engine.trajectory_validation_folds_v1 import (
    TrajectoryEventIdentityV1,
    build_trajectory_forward_folds_v1,
)

UTC = timezone.utc


class TrajectoryLaneAV1Test(unittest.TestCase):
    def _bundle(self, event_id: int, day_offset: int, club: str) -> TrajectoryEventBundleV1:
        kickoff = datetime(2026, 10, 10, 18, 0, tzinfo=UTC) + timedelta(days=day_offset)
        start = kickoff - timedelta(days=8)
        snapshots = []
        available = 10000 - event_id * 20
        for idx, hour in enumerate(range(0, 8 * 24, 6), start=1):
            snapshots.append(
                SnapshotRecord(
                    snapshot_id=event_id * 1000 + idx,
                    captured_at=start + timedelta(hours=hour),
                    available_total=available,
                )
            )
            available -= 35 + event_id
        prior_at = kickoff - timedelta(days=7)
        prior = StructuralPrior(
            ticket_event_id=event_id,
            horizon="T-7",
            requested_as_of_at=prior_at,
            target_as_of_at=prior_at,
            kickoff_at=kickoff,
            model_spec_id="test-structural",
            model_family="test",
            feature_contract="test",
            p50=12000 + event_id * 500,
            p10=None,
            p90=None,
            stadium_capacity=30000,
            point_in_time_validated=True,
            source_prior_id=event_id,
            generated_at=prior_at,
        )
        actual = int(prior.p50 + 300 + event_id * 10)
        return TrajectoryEventBundleV1(
            ticket_event_id=event_id,
            club_slug=club,
            kickoff_at=kickoff,
            snapshots=tuple(snapshots),
            sectors=(),
            structural_priors=(prior,),
            outcome=TrajectoryOutcomeV1(
                actual_attendance=actual,
                confirmed_at=kickoff + timedelta(hours=3),
                attendance_definition="official_attendance",
                source_name="test",
            ),
            stadium_capacity=30000,
        )

    def _dataset_and_folds(self):
        clubs = ["a", "b", "c", "d", "e", "f"]
        bundles = [self._bundle(i + 1, i, clubs[i]) for i in range(6)]
        dataset = materialize_shared_dataset_v1(bundles, start_days=7, end_days=1)
        identities = [
            TrajectoryEventIdentityV1(
                ticket_event_id=b.ticket_event_id,
                club_slug=b.club_slug,
                kickoff_at=b.kickoff_at,
            )
            for b in bundles
        ]
        folds = build_trajectory_forward_folds_v1(identities).folds
        return dataset, folds

    def test_lane_a_uses_fixed_precommit_and_alpha(self) -> None:
        dataset, folds = self._dataset_and_folds()
        score = evaluate_lane_a_forward_v1(dataset.examples, folds)
        self.assertEqual(score.precommit_id, PRECOMMIT_ID)
        self.assertEqual(score.alpha, RIDGE_ALPHA)
        self.assertEqual(score.independent_test_events, 1)
        self.assertGreater(score.test_rows, 0)

    def test_only_test_event_is_predicted(self) -> None:
        dataset, folds = self._dataset_and_folds()
        score = evaluate_lane_a_forward_v1(dataset.examples, folds)
        self.assertEqual({row.ticket_event_id for row in score.predictions}, {6})

    def test_event_weights_sum_to_one_before_fit(self) -> None:
        dataset, _ = self._dataset_and_folds()
        for event_id in dataset.event_ids:
            total = sum(
                row.event_row_weight
                for row in dataset.examples
                if row.ticket_event_id == event_id
            )
            self.assertAlmostEqual(total, 1.0)

    def test_preprocessor_fits_from_supplied_rows_only(self) -> None:
        dataset, _ = self._dataset_and_folds()
        train = [row for row in dataset.examples if row.ticket_event_id <= 5]
        pre = fit_preprocessor_v1(train)
        self.assertEqual(len(pre.numeric_medians), 16)
        self.assertEqual(len(pre.numeric_means), 16)
        self.assertEqual(len(pre.numeric_stds), 16)


if __name__ == "__main__":
    unittest.main()
