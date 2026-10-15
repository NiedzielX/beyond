from datetime import datetime, timedelta, timezone
import unittest

from ml.demand_engine.live_trajectory_feature_store import (
    SnapshotRecord,
    build_live_trajectory_features,
)

UTC = timezone.utc


class LiveTrajectoryQualityTest(unittest.TestCase):
    def setUp(self) -> None:
        self.kickoff = datetime(2026, 12, 10, 20, 0, tzinfo=UTC)
        self.as_of = self.kickoff - timedelta(days=14)

    def test_old_collector_gap_does_not_permanently_block_current_signal(self) -> None:
        snapshots = [
            SnapshotRecord(1, self.as_of - timedelta(hours=300), 12000),
            SnapshotRecord(2, self.as_of - timedelta(hours=250), 11900),
            SnapshotRecord(3, self.as_of - timedelta(hours=174), 11800),
        ]
        # Last seven days are healthy at a six-hour cadence. The older outage is
        # retained in all-history telemetry but must not block today's signal.
        for index, hours_before in enumerate(range(168, -1, -6), start=4):
            snapshots.append(
                SnapshotRecord(
                    index,
                    self.as_of - timedelta(hours=hours_before),
                    11800 - index * 15,
                )
            )

        features = build_live_trajectory_features(
            snapshots,
            [],
            as_of=self.as_of,
            kickoff_at=self.kickoff,
        )

        self.assertGreater(features.max_visible_gap_hours or 0, 12)
        self.assertFalse(features.data_gap_detected)
        self.assertEqual(features.signal_readiness, "ready")

    def test_timezone_naive_snapshot_is_rejected_explicitly(self) -> None:
        snapshot = SnapshotRecord(
            1,
            datetime(2026, 11, 20, 12, 0),
            10000,
        )
        with self.assertRaisesRegex(ValueError, "snapshot.captured_at must be timezone-aware"):
            build_live_trajectory_features(
                [snapshot],
                [],
                as_of=self.as_of,
                kickoff_at=self.kickoff,
            )


if __name__ == "__main__":
    unittest.main()
