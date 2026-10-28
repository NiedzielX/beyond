from datetime import datetime, timedelta, timezone
import unittest

from ml.demand_engine.trajectory_self_supervised_v1 import (
    EPOCHS,
    HIDDEN_DIM,
    PRECOMMIT_ID,
    SEED,
    TRAIN_EVENT_IDS,
    VALIDATION_EVENT_IDS,
    TargetFreeEventV1,
    TargetFreeObservationV1,
    build_target_free_pairs_v1,
)

UTC = timezone.utc


class TrajectorySelfSupervisedV1Test(unittest.TestCase):
    def _event(self) -> TargetFreeEventV1:
        kickoff = datetime(2026, 11, 1, 18, 0, tzinfo=UTC)
        start = kickoff - timedelta(days=4)
        observations = []
        available = 1000
        for idx, hours in enumerate(range(0, 73, 6), start=1):
            captured = start + timedelta(hours=hours)
            observations.append(
                TargetFreeObservationV1(
                    snapshot_id=idx,
                    captured_at=captured,
                    hours_to_kickoff=(kickoff-captured).total_seconds()/3600.0,
                    available_total=available,
                )
            )
            available -= 10
        return TargetFreeEventV1(999, "test", kickoff, tuple(observations))

    def test_protocol_constants_are_frozen(self) -> None:
        self.assertEqual(PRECOMMIT_ID, "trajectory-self-supervised-24h-delta-v1")
        self.assertEqual(HIDDEN_DIM, 8)
        self.assertEqual(EPOCHS, 100)
        self.assertEqual(SEED, 17)
        self.assertEqual(len(TRAIN_EVENT_IDS), 21)
        self.assertEqual(VALIDATION_EVENT_IDS, (447, 449, 450, 451, 452))

    def test_pairs_are_target_free_and_about_24h(self) -> None:
        pairs = build_target_free_pairs_v1(self._event())
        self.assertGreater(len(pairs), 0)
        for pair in pairs:
            self.assertGreaterEqual(pair.elapsed_hours, 18.0)
            self.assertLessEqual(pair.elapsed_hours, 30.0)
            self.assertEqual(pair.sequence.shape[1], 4)
            self.assertLessEqual(pair.sequence.shape[0], 29)

    def test_event_pair_weights_sum_to_one(self) -> None:
        pairs = build_target_free_pairs_v1(self._event())
        self.assertAlmostEqual(sum(pair.event_pair_weight for pair in pairs), 1.0)

    def test_short_prefixes_are_not_used(self) -> None:
        kickoff = datetime(2026, 11, 1, 18, 0, tzinfo=UTC)
        observations = (
            TargetFreeObservationV1(1, kickoff-timedelta(hours=30), 30.0, 1000),
            TargetFreeObservationV1(2, kickoff-timedelta(hours=24), 24.0, 990),
            TargetFreeObservationV1(3, kickoff-timedelta(hours=6), 6.0, 980),
        )
        event = TargetFreeEventV1(1000, "short", kickoff, observations)
        self.assertEqual(build_target_free_pairs_v1(event), ())


if __name__ == "__main__":
    unittest.main()
