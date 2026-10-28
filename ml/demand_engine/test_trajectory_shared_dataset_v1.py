from datetime import datetime, timedelta, timezone
import unittest

from ml.demand_engine.live_trajectory_feature_store import SnapshotRecord
from ml.demand_engine.structural_prior import StructuralPrior
from ml.demand_engine.trajectory_shared_dataset_v1 import (
    DATASET_CONTRACT_ID,
    TrajectoryEventBundleV1,
    TrajectoryOutcomeV1,
    materialize_event_examples_v1,
    materialize_shared_dataset_v1,
)

UTC = timezone.utc


class TrajectorySharedDatasetV1Test(unittest.TestCase):
    def setUp(self) -> None:
        self.kickoff = datetime(2026, 10, 25, 18, 0, tzinfo=UTC)

    def _prior(self, *, event_id: int = 101, days: int = 7) -> StructuralPrior:
        target = self.kickoff - timedelta(days=days)
        return StructuralPrior(
            ticket_event_id=event_id,
            horizon=f"T-{days}",
            requested_as_of_at=target,
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
            source_prior_id=1,
            generated_at=target,
        )

    def _snapshots(self) -> tuple[SnapshotRecord, ...]:
        # Enough history for multiple later daily cutoffs to become ready.
        start = self.kickoff - timedelta(days=8)
        rows = []
        available = 10000
        snapshot_id = 1
        for hour in range(0, 8 * 24, 6):
            rows.append(
                SnapshotRecord(
                    snapshot_id=snapshot_id,
                    captured_at=start + timedelta(hours=hour),
                    available_total=available,
                )
            )
            available -= 40
            snapshot_id += 1
        return tuple(rows)

    def _bundle(self, *, event_id: int = 101, actual: int = 16000) -> TrajectoryEventBundleV1:
        return TrajectoryEventBundleV1(
            ticket_event_id=event_id,
            club_slug=f"club-{event_id}",
            kickoff_at=self.kickoff + timedelta(days=event_id - 101),
            snapshots=self._shift_snapshots(event_id - 101),
            sectors=(),
            structural_priors=(self._shift_prior(event_id - 101, event_id),),
            outcome=TrajectoryOutcomeV1(
                actual_attendance=actual,
                confirmed_at=self.kickoff + timedelta(days=event_id - 101, hours=4),
                attendance_definition="official_attendance",
                source_name="test",
            ),
            stadium_capacity=20000,
        )

    def _shift_snapshots(self, days: int) -> tuple[SnapshotRecord, ...]:
        return tuple(
            SnapshotRecord(
                snapshot_id=row.snapshot_id,
                captured_at=row.captured_at + timedelta(days=days),
                available_total=row.available_total,
            )
            for row in self._snapshots()
        )

    def _shift_prior(self, days: int, event_id: int) -> StructuralPrior:
        prior = self._prior(event_id=event_id)
        return StructuralPrior(
            ticket_event_id=event_id,
            horizon=prior.horizon,
            requested_as_of_at=prior.requested_as_of_at + timedelta(days=days),
            target_as_of_at=prior.target_as_of_at + timedelta(days=days),
            kickoff_at=prior.kickoff_at + timedelta(days=days),
            model_spec_id=prior.model_spec_id,
            model_family=prior.model_family,
            feature_contract=prior.feature_contract,
            p50=prior.p50,
            p10=prior.p10,
            p90=prior.p90,
            stadium_capacity=prior.stadium_capacity,
            point_in_time_validated=prior.point_in_time_validated,
            source_prior_id=prior.source_prior_id,
            generated_at=(prior.generated_at + timedelta(days=days)) if prior.generated_at else None,
        )

    def test_event_materializer_builds_both_lanes_from_same_cutoff(self) -> None:
        examples = materialize_event_examples_v1(
            self._bundle(),
            start_days=7,
            end_days=1,
        )
        self.assertGreater(len(examples), 0)
        for example in examples:
            self.assertEqual(example.dataset_contract_id, DATASET_CONTRACT_ID)
            self.assertEqual(example.lane_b_sequence.as_of_at, example.as_of_at)
            self.assertEqual(example.residual_target, 1000.0)
            self.assertFalse(example.target_values_used_in_features)
            self.assertFalse(example.production_change)

    def test_event_weights_sum_to_one_per_event(self) -> None:
        examples = materialize_event_examples_v1(
            self._bundle(),
            start_days=7,
            end_days=1,
        )
        self.assertAlmostEqual(sum(row.event_row_weight for row in examples), 1.0)

    def test_shared_dataset_has_deterministic_identity_hash(self) -> None:
        bundles = [self._bundle(event_id=101), self._bundle(event_id=102)]
        a = materialize_shared_dataset_v1(bundles, start_days=7, end_days=1)
        b = materialize_shared_dataset_v1(reversed(bundles), start_days=7, end_days=1)
        self.assertEqual(a.identity_manifest_sha256, b.identity_manifest_sha256)
        self.assertEqual(len(a.identity_manifest_sha256), 64)
        self.assertEqual(a.event_ids, (101, 102))

    def test_outcome_must_be_confirmed_after_kickoff(self) -> None:
        bundle = self._bundle()
        invalid = TrajectoryEventBundleV1(
            ticket_event_id=bundle.ticket_event_id,
            club_slug=bundle.club_slug,
            kickoff_at=bundle.kickoff_at,
            snapshots=bundle.snapshots,
            sectors=bundle.sectors,
            structural_priors=bundle.structural_priors,
            outcome=TrajectoryOutcomeV1(
                actual_attendance=16000,
                confirmed_at=bundle.kickoff_at - timedelta(minutes=1),
                attendance_definition="official_attendance",
                source_name="test",
            ),
            stadium_capacity=bundle.stadium_capacity,
        )
        with self.assertRaises(ValueError):
            materialize_event_examples_v1(invalid, start_days=7, end_days=1)

    def test_duplicate_event_bundle_is_rejected(self) -> None:
        bundle = self._bundle()
        with self.assertRaises(ValueError):
            materialize_shared_dataset_v1([bundle, bundle], start_days=7, end_days=1)


if __name__ == "__main__":
    unittest.main()
