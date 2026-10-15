from datetime import datetime, timedelta, timezone
import unittest

from ml.demand_engine.live_trajectory_feature_store import (
    SectorInventoryRecord,
    SnapshotRecord,
    build_live_trajectory_features,
)

UTC = timezone.utc


class LiveTrajectoryFeatureStoreTest(unittest.TestCase):
    def setUp(self) -> None:
        self.kickoff = datetime(2026, 12, 10, 20, 0, tzinfo=UTC)
        self.as_of = self.kickoff - timedelta(days=14)

    def _snap(self, snapshot_id: int, hours_before_asof: float, available: int) -> SnapshotRecord:
        return SnapshotRecord(
            snapshot_id=snapshot_id,
            captured_at=self.as_of - timedelta(hours=hours_before_asof),
            available_total=available,
        )

    def test_point_in_time_excludes_future_snapshot(self) -> None:
        snapshots = [
            self._snap(1, 24, 10000),
            self._snap(2, 6, 9500),
            self._snap(3, 0, 9200),
            SnapshotRecord(4, self.as_of + timedelta(hours=1), 100),
        ]

        features = build_live_trajectory_features(
            snapshots,
            [],
            as_of=self.as_of,
            kickoff_at=self.kickoff,
            stadium_capacity=20000,
        )

        self.assertEqual(features.snapshot_id, 3)
        self.assertEqual(features.available_total, 9200)
        self.assertEqual(features.raw_snapshot_count, 3)
        self.assertTrue(features.point_in_time_validated)
        self.assertEqual(features.checkpoint_label, "T-14")
        self.assertTrue(features.checkpoint_ready)

    def test_builds_6h_24h_72h_and_7d_velocity(self) -> None:
        snapshots = [
            self._snap(1, 168, 12000),
            self._snap(2, 72, 11000),
            self._snap(3, 24, 10000),
            self._snap(4, 6, 9400),
            self._snap(5, 0, 9100),
        ]

        features = build_live_trajectory_features(
            snapshots,
            [],
            as_of=self.as_of,
            kickoff_at=self.kickoff,
            stadium_capacity=20000,
        )

        self.assertEqual(features.net_removed_6h, 300)
        self.assertAlmostEqual(features.velocity_6h or 0, 50.0)
        self.assertEqual(features.net_removed_24h, 900)
        self.assertAlmostEqual(features.velocity_24h or 0, 37.5)
        self.assertEqual(features.net_removed_72h, 1900)
        self.assertAlmostEqual(features.velocity_72h or 0, 1900 / 72)
        self.assertEqual(features.net_removed_7d, 2900)
        self.assertAlmostEqual(features.velocity_7d or 0, 2900 / 168)
        self.assertAlmostEqual(features.available_share_of_capacity or 0, 0.455)
        self.assertGreater(features.acceleration_6h_vs_24h or 0, 0)

    def test_stale_anchor_is_not_mislabeled_as_short_window(self) -> None:
        snapshots = [
            self._snap(1, 40, 10000),
            self._snap(2, 0, 9000),
        ]
        features = build_live_trajectory_features(
            snapshots,
            [],
            as_of=self.as_of,
            kickoff_at=self.kickoff,
        )
        self.assertIsNone(features.velocity_6h)
        self.assertIsNone(features.velocity_24h)

    def test_sector_release_is_separated_from_absorption(self) -> None:
        snapshots = [
            self._snap(1, 6, 1000),
            self._snap(2, 0, 1050),
        ]
        sectors = [
            SectorInventoryRecord(1, "A", 500),
            SectorInventoryRecord(1, "B", 500),
            SectorInventoryRecord(2, "A", 450),
            SectorInventoryRecord(2, "B", 550),
            SectorInventoryRecord(2, "C", 50),
        ]
        features = build_live_trajectory_features(
            snapshots,
            sectors,
            as_of=self.as_of,
            kickoff_at=self.kickoff,
        )

        self.assertEqual(features.matched_sector_count, 2)
        self.assertEqual(features.entered_sector_count, 1)
        self.assertEqual(features.left_sector_count, 0)
        self.assertEqual(features.matched_absorption, 50)
        self.assertEqual(features.matched_release, 50)
        self.assertEqual(features.coverage_inventory_effect, 50)
        self.assertTrue(features.sector_coverage_change_flag)
        self.assertTrue(features.release_activity_flag)
        self.assertFalse(features.unexplained_inventory_increase_flag)
        self.assertEqual(features.feature_quality, "sector_matched_plus_raw")

    def test_material_unexplained_inventory_increase_degrades_readiness(self) -> None:
        snapshots = [
            self._snap(1, 36, 1000),
            self._snap(2, 24, 950),
            self._snap(3, 12, 900),
            self._snap(4, 0, 1100),
        ]
        features = build_live_trajectory_features(
            snapshots,
            [],
            as_of=self.as_of,
            kickoff_at=self.kickoff,
        )
        self.assertTrue(features.unexplained_inventory_increase_flag)
        self.assertEqual(features.signal_readiness, "partial")

    def test_duplicate_and_invalid_snapshots_are_counted_not_used(self) -> None:
        same_time = self.as_of - timedelta(hours=24)
        snapshots = [
            SnapshotRecord(1, same_time, 1000),
            SnapshotRecord(2, same_time, 900),
            SnapshotRecord(3, self.as_of - timedelta(hours=12), -1),
            SnapshotRecord(4, self.as_of, 800),
        ]
        features = build_live_trajectory_features(
            snapshots,
            [],
            as_of=self.as_of,
            kickoff_at=self.kickoff,
        )
        self.assertEqual(features.raw_snapshot_count, 4)
        self.assertEqual(features.clean_snapshot_count, 2)
        self.assertEqual(features.duplicate_timestamp_count, 1)
        self.assertEqual(features.invalid_snapshot_count, 1)
        self.assertEqual(features.excluded_anomaly_count, 2)
        self.assertEqual(features.first_available_total, 900)

    def test_checkpoint_window_is_one_sided(self) -> None:
        after_t14 = self.kickoff - timedelta(days=13, hours=23)
        features = build_live_trajectory_features(
            [SnapshotRecord(1, after_t14, 1000)],
            [],
            as_of=after_t14,
            kickoff_at=self.kickoff,
        )
        self.assertIsNone(features.checkpoint_label)
        self.assertFalse(features.checkpoint_ready)

    def test_ready_requires_history_and_no_large_gap(self) -> None:
        snapshots = [
            self._snap(1, 30, 1000),
            self._snap(2, 20, 950),
            self._snap(3, 10, 900),
            self._snap(4, 0, 850),
        ]
        features = build_live_trajectory_features(
            snapshots,
            [],
            as_of=self.as_of,
            kickoff_at=self.kickoff,
        )
        self.assertFalse(features.data_gap_detected)
        self.assertEqual(features.signal_readiness, "ready")

    def test_timezone_naive_asof_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            build_live_trajectory_features(
                [],
                [],
                as_of=datetime(2026, 10, 1, 12, 0),
                kickoff_at=self.kickoff,
            )


if __name__ == "__main__":
    unittest.main()
