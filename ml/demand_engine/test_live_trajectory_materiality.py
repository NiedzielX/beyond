from datetime import datetime, timedelta, timezone
import unittest

from ml.demand_engine.live_trajectory_feature_store import (
    SectorInventoryRecord,
    SnapshotRecord,
    build_live_trajectory_features,
)

UTC = timezone.utc


class LiveTrajectoryMaterialityTest(unittest.TestCase):
    def setUp(self) -> None:
        self.kickoff = datetime(2026, 12, 10, 20, 0, tzinfo=UTC)
        self.as_of = self.kickoff - timedelta(days=14)

    def _base_snapshots(self, previous_total: int, current_total: int):
        return [
            SnapshotRecord(1, self.as_of - timedelta(hours=30), 10000),
            SnapshotRecord(2, self.as_of - timedelta(hours=24), 9900),
            SnapshotRecord(3, self.as_of - timedelta(hours=6), previous_total),
            SnapshotRecord(4, self.as_of, current_total),
        ]

    def test_small_sector_reavailability_is_not_material_release(self) -> None:
        sectors = [
            SectorInventoryRecord(3, "A", 500),
            SectorInventoryRecord(3, "B", 500),
            SectorInventoryRecord(4, "A", 507),
            SectorInventoryRecord(4, "B", 506),
        ]
        features = build_live_trajectory_features(
            self._base_snapshots(1000, 1013),
            sectors,
            as_of=self.as_of,
            kickoff_at=self.kickoff,
        )
        self.assertEqual(features.feature_version, "live-trajectory-v1.1")
        self.assertEqual(features.matched_release, 13)
        self.assertFalse(features.release_activity_flag)
        self.assertFalse(features.unexplained_inventory_increase_flag)

    def test_material_matched_release_is_flagged(self) -> None:
        sectors = [
            SectorInventoryRecord(3, "A", 500),
            SectorInventoryRecord(3, "B", 500),
            SectorInventoryRecord(4, "A", 530),
            SectorInventoryRecord(4, "B", 530),
        ]
        features = build_live_trajectory_features(
            self._base_snapshots(1000, 1060),
            sectors,
            as_of=self.as_of,
            kickoff_at=self.kickoff,
        )
        self.assertEqual(features.matched_release, 60)
        self.assertTrue(features.release_activity_flag)
        self.assertFalse(features.unexplained_inventory_increase_flag)

    def test_sector_entry_is_coverage_change_not_release(self) -> None:
        sectors = [
            SectorInventoryRecord(3, "A", 1000),
            SectorInventoryRecord(4, "A", 1000),
            SectorInventoryRecord(4, "C", 200),
        ]
        features = build_live_trajectory_features(
            self._base_snapshots(1000, 1200),
            sectors,
            as_of=self.as_of,
            kickoff_at=self.kickoff,
        )
        self.assertTrue(features.sector_coverage_change_flag)
        self.assertFalse(features.release_activity_flag)
        self.assertFalse(features.unexplained_inventory_increase_flag)

    def test_material_raw_increase_without_sector_explanation_is_anomaly(self) -> None:
        features = build_live_trajectory_features(
            self._base_snapshots(1000, 1060),
            [],
            as_of=self.as_of,
            kickoff_at=self.kickoff,
        )
        self.assertTrue(features.unexplained_inventory_increase_flag)
        self.assertEqual(features.signal_readiness, "partial")


if __name__ == "__main__":
    unittest.main()
