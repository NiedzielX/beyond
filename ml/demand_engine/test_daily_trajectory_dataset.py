from datetime import datetime, timedelta, timezone
import unittest

from ml.demand_engine.daily_trajectory_dataset import (
    DATASET_VERSION,
    build_daily_trajectory_dataset,
    select_structural_prior_at_cutoff,
)
from ml.demand_engine.live_trajectory_feature_store import SnapshotRecord
from ml.demand_engine.structural_prior import StructuralPrior

UTC = timezone.utc


class DailyTrajectoryDatasetTest(unittest.TestCase):
    def setUp(self) -> None:
        self.kickoff = datetime(2026, 12, 10, 20, 0, tzinfo=UTC)

    def _prior(
        self,
        *,
        source_id: int,
        target_days: int,
        requested_days: int | None = None,
        generated_offset_hours: float = 0,
        event_id: int = 101,
    ) -> StructuralPrior:
        target = self.kickoff - timedelta(days=target_days)
        requested = self.kickoff - timedelta(days=requested_days or target_days)
        return StructuralPrior(
            ticket_event_id=event_id,
            horizon="T-3",
            requested_as_of_at=requested,
            target_as_of_at=target,
            kickoff_at=self.kickoff,
            model_spec_id="test-structural",
            model_family="test-family",
            feature_contract="test-contract",
            p50=15000.0,
            p10=14000.0,
            p90=16000.0,
            stadium_capacity=20000,
            point_in_time_validated=True,
            source_prior_id=source_id,
            generated_at=requested + timedelta(hours=generated_offset_hours),
        )

    def test_builds_exact_daily_cutoffs_and_keeps_missing_rows(self) -> None:
        snapshot = SnapshotRecord(
            snapshot_id=1,
            captured_at=self.kickoff - timedelta(days=2, hours=12),
            available_total=8000,
        )

        rows = build_daily_trajectory_dataset(
            ticket_event_id=101,
            club_slug="lech",
            kickoff_at=self.kickoff,
            snapshots=[snapshot],
            stadium_capacity=20000,
            start_days=3,
            end_days=1,
        )

        self.assertEqual([row.days_to_event for row in rows], [3, 2, 1])
        self.assertEqual(rows[0].as_of_at, self.kickoff - timedelta(days=3))
        self.assertEqual(rows[1].as_of_at, self.kickoff - timedelta(days=2))
        self.assertEqual(rows[2].as_of_at, self.kickoff - timedelta(days=1))
        self.assertEqual(rows[0].trajectory.feature_quality, "no_usable_snapshot")
        self.assertIsNone(rows[0].trajectory.available_total)
        self.assertEqual(rows[1].trajectory.available_total, 8000)
        self.assertEqual(rows[2].trajectory.available_total, 8000)
        self.assertEqual(rows[0].dataset_version, DATASET_VERSION)

    def test_future_snapshot_never_enters_earlier_daily_row(self) -> None:
        snapshots = [
            SnapshotRecord(
                snapshot_id=1,
                captured_at=self.kickoff - timedelta(days=3),
                available_total=9000,
            ),
            SnapshotRecord(
                snapshot_id=2,
                captured_at=self.kickoff - timedelta(days=1, hours=12),
                available_total=100,
            ),
        ]

        rows = build_daily_trajectory_dataset(
            ticket_event_id=101,
            club_slug="lech",
            kickoff_at=self.kickoff,
            snapshots=snapshots,
            start_days=2,
            end_days=1,
        )

        p2, p1 = rows
        self.assertEqual(p2.trajectory.snapshot_id, 1)
        self.assertEqual(p2.trajectory.available_total, 9000)
        self.assertEqual(p2.trajectory.raw_snapshot_count, 1)
        self.assertEqual(p1.trajectory.snapshot_id, 2)
        self.assertEqual(p1.trajectory.available_total, 100)
        self.assertFalse(p2.target_future_points_used)

    def test_structural_prior_must_have_been_generated_by_cutoff(self) -> None:
        # T-3 checkpoint is requested at P-3 but persisted one hour later.
        prior = self._prior(
            source_id=10,
            target_days=3,
            requested_days=3,
            generated_offset_hours=1,
        )

        rows = build_daily_trajectory_dataset(
            ticket_event_id=101,
            club_slug="lech",
            kickoff_at=self.kickoff,
            snapshots=[],
            structural_priors=[prior],
            start_days=3,
            end_days=2,
        )

        self.assertIsNone(rows[0].structural_prior)
        self.assertFalse(rows[0].structural_prior_available)
        self.assertEqual(rows[1].structural_prior, prior)
        self.assertTrue(rows[1].structural_prior_available)

    def test_later_requested_prior_is_not_backfilled_into_earlier_cutoff(self) -> None:
        future_prior = self._prior(
            source_id=11,
            target_days=3,
            requested_days=1,
            generated_offset_hours=0,
        )

        selected = select_structural_prior_at_cutoff(
            [future_prior],
            ticket_event_id=101,
            as_of_at=self.kickoff - timedelta(days=2),
        )

        self.assertIsNone(selected)

    def test_latest_eligible_structural_prior_is_selected_deterministically(self) -> None:
        older = self._prior(source_id=10, target_days=3, requested_days=3)
        newer = self._prior(source_id=12, target_days=3, requested_days=2)

        selected = select_structural_prior_at_cutoff(
            [older, newer],
            ticket_event_id=101,
            as_of_at=self.kickoff - timedelta(days=2),
        )

        self.assertEqual(selected, newer)

    def test_capacity_minus_available_is_explicitly_only_a_proxy(self) -> None:
        snapshot = SnapshotRecord(
            snapshot_id=1,
            captured_at=self.kickoff - timedelta(days=2),
            available_total=7000,
        )

        row = build_daily_trajectory_dataset(
            ticket_event_id=101,
            club_slug="lech",
            kickoff_at=self.kickoff,
            snapshots=[snapshot],
            stadium_capacity=20000,
            start_days=2,
            end_days=2,
        )[0]

        self.assertEqual(row.occupied_capacity_proxy, 13000)
        self.assertEqual(row.inventory_interpretation, "demand_proxy_not_confirmed_sales")

    def test_residual_input_ready_requires_both_trajectory_and_prior(self) -> None:
        prior = self._prior(source_id=10, target_days=3, requested_days=3)
        snapshot = SnapshotRecord(
            snapshot_id=1,
            captured_at=self.kickoff - timedelta(days=3),
            available_total=9000,
        )

        row = build_daily_trajectory_dataset(
            ticket_event_id=101,
            club_slug="lech",
            kickoff_at=self.kickoff,
            snapshots=[snapshot],
            structural_priors=[prior],
            start_days=2,
            end_days=2,
        )[0]

        self.assertTrue(row.residual_model_input_ready)
        self.assertTrue(row.point_in_time_validated)

    def test_timezone_naive_kickoff_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            build_daily_trajectory_dataset(
                ticket_event_id=101,
                club_slug="lech",
                kickoff_at=datetime(2026, 12, 10, 20, 0),
                snapshots=[],
                start_days=2,
                end_days=1,
            )

    def test_invalid_daily_range_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            build_daily_trajectory_dataset(
                ticket_event_id=101,
                club_slug="lech",
                kickoff_at=self.kickoff,
                snapshots=[],
                start_days=1,
                end_days=2,
            )


if __name__ == "__main__":
    unittest.main()
