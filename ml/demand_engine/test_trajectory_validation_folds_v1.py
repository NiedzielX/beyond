from datetime import datetime, timedelta, timezone
import unittest

from ml.demand_engine.trajectory_validation_folds_v1 import (
    FOLD_CONTRACT_ID,
    TrajectoryEventIdentityV1,
    build_trajectory_forward_folds_v1,
)

UTC = timezone.utc


class TrajectoryValidationFoldsV1Test(unittest.TestCase):
    def _event(self, event_id: int, club: str, day: int, hour: int = 18):
        return TrajectoryEventIdentityV1(
            ticket_event_id=event_id,
            club_slug=club,
            kickoff_at=datetime(2026, 1, day, hour, 0, tzinfo=UTC),
        )

    def test_first_fold_requires_five_prior_events_and_four_clubs(self) -> None:
        events = [
            self._event(1, "a", 1),
            self._event(2, "b", 2),
            self._event(3, "c", 3),
            self._event(4, "d", 4),
            self._event(5, "a", 5),
            self._event(6, "e", 6),
        ]
        registry = build_trajectory_forward_folds_v1(events)
        self.assertEqual(registry.contract_id, FOLD_CONTRACT_ID)
        self.assertEqual(len(registry.folds), 1)
        fold = registry.folds[0]
        self.assertEqual(fold.train_event_ids, (1, 2, 3, 4, 5))
        self.assertEqual(fold.test_event_ids, (6,))
        self.assertEqual(fold.train_event_count, 5)
        self.assertEqual(fold.train_club_count, 4)

    def test_same_kickoff_events_never_train_one_another(self) -> None:
        kickoff = datetime(2026, 1, 6, 18, 0, tzinfo=UTC)
        events = [
            self._event(1, "a", 1),
            self._event(2, "b", 2),
            self._event(3, "c", 3),
            self._event(4, "d", 4),
            self._event(5, "a", 5),
            TrajectoryEventIdentityV1(6, "e", kickoff),
            TrajectoryEventIdentityV1(7, "f", kickoff),
        ]
        registry = build_trajectory_forward_folds_v1(events)
        self.assertEqual(len(registry.folds), 1)
        fold = registry.folds[0]
        self.assertEqual(fold.test_event_ids, (6, 7))
        self.assertNotIn(6, fold.train_event_ids)
        self.assertNotIn(7, fold.train_event_ids)

    def test_later_fold_expands_training_only_with_earlier_events(self) -> None:
        events = [
            self._event(1, "a", 1),
            self._event(2, "b", 2),
            self._event(3, "c", 3),
            self._event(4, "d", 4),
            self._event(5, "a", 5),
            self._event(6, "e", 6),
            self._event(7, "f", 7),
        ]
        registry = build_trajectory_forward_folds_v1(events)
        self.assertEqual(len(registry.folds), 2)
        self.assertEqual(registry.folds[0].train_event_ids, (1, 2, 3, 4, 5))
        self.assertEqual(registry.folds[0].test_event_ids, (6,))
        self.assertEqual(registry.folds[1].train_event_ids, (1, 2, 3, 4, 5, 6))
        self.assertEqual(registry.folds[1].test_event_ids, (7,))

    def test_manifest_is_deterministic_under_input_order(self) -> None:
        events = [
            self._event(1, "a", 1),
            self._event(2, "b", 2),
            self._event(3, "c", 3),
            self._event(4, "d", 4),
            self._event(5, "a", 5),
            self._event(6, "e", 6),
        ]
        a = build_trajectory_forward_folds_v1(events)
        b = build_trajectory_forward_folds_v1(reversed(events))
        self.assertEqual(a.manifest_sha256, b.manifest_sha256)
        self.assertEqual(len(a.manifest_sha256), 64)

    def test_conflicting_duplicate_event_identity_is_rejected(self) -> None:
        event = self._event(1, "a", 1)
        conflict = TrajectoryEventIdentityV1(
            ticket_event_id=1,
            club_slug="other",
            kickoff_at=event.kickoff_at + timedelta(hours=1),
        )
        with self.assertRaises(ValueError):
            build_trajectory_forward_folds_v1([event, conflict])

    def test_timezone_naive_kickoff_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            build_trajectory_forward_folds_v1(
                [TrajectoryEventIdentityV1(1, "a", datetime(2026, 1, 1, 18, 0))],
                min_train_events=1,
                min_train_clubs=1,
            )


if __name__ == "__main__":
    unittest.main()
