import unittest
from datetime import datetime, timezone

from ml.demand_engine.live_trajectory_feature_store import LiveTrajectoryFeatures
from ml.demand_engine.trajectory_gap import (
    StructuralPriorAnchor,
    TrajectoryReferenceRow,
    evaluate_trajectory_gap,
)

UTC = timezone.utc


def live(**overrides):
    values = dict(
        feature_version="live-trajectory-v1.1",
        signal_readiness="ready",
        feature_quality="sector_matched_plus_raw",
        inventory_interpretation="demand_proxy_not_confirmed_sales",
        point_in_time_validated=True,
        as_of=datetime(2026, 10, 17, 17, 0, tzinfo=UTC),
        kickoff_at=datetime(2026, 10, 31, 16, 30, tzinfo=UTC),
        hours_to_kickoff=335.5,
        days_to_kickoff=335.5 / 24,
        checkpoint_label="T-14",
        checkpoint_distance_hours=0.5,
        checkpoint_ready=True,
        available_index=0.80,
        velocity_24h_pct_of_first_per_hour=0.10,
        velocity_6h_pct_of_first_per_hour=0.15,
    )
    values.update(overrides)
    return LiveTrajectoryFeatures(**values)


def prior(**overrides):
    values = dict(
        status="ready",
        source_prior_id=1,
        horizon="T-30",
        p50=31832.0,
        stadium_capacity=43269,
        expected_occupancy=0.7357,
        point_in_time_validated=True,
    )
    values.update(overrides)
    return StructuralPriorAnchor(**values)


def reference(event_id, club, available_index, *, v24=0.08, v6=0.10):
    return TrajectoryReferenceRow(
        ticket_event_id=event_id,
        club_slug=club,
        horizon="T-14",
        as_of_at=datetime(2026, 10, 10, 12, 0, tzinfo=UTC),
        feature_version="live-trajectory-v1.1",
        training_eligible=True,
        point_in_time_validated=True,
        signal_readiness="ready",
        available_index=available_index,
        velocity_24h_pct_of_first_per_hour=v24,
        velocity_6h_pct_of_first_per_hour=v6,
    )


class TrajectoryGapTest(unittest.TestCase):
    def test_fail_closed_outside_checkpoint_window(self):
        result = evaluate_trajectory_gap(
            ticket_event_id=6,
            club_slug="lech",
            live=live(checkpoint_label=None, checkpoint_ready=False, hours_to_kickoff=388.0),
            prior=prior(),
            references=[],
        )
        self.assertEqual(result.status, "INSUFFICIENT_SIGNAL")
        self.assertEqual(result.reason_code, "outside_reference_checkpoint_window")
        self.assertAlmostEqual(result.observed_progress, 0.20)
        self.assertIsNone(result.expected_progress)

    def test_requires_genuine_ready_prior(self):
        result = evaluate_trajectory_gap(
            ticket_event_id=6,
            club_slug="lech",
            live=live(),
            prior=prior(status="missing_prior", source_prior_id=None, p50=None),
            references=[],
        )
        self.assertEqual(result.status, "INSUFFICIENT_SIGNAL")
        self.assertEqual(result.reason_code, "structural_prior_not_ready")

    def test_requires_minimum_reference_diversity(self):
        result = evaluate_trajectory_gap(
            ticket_event_id=6,
            club_slug="lech",
            live=live(),
            prior=prior(),
            references=[
                reference(1, "lech", 0.90),
                reference(2, "lech", 0.80),
                reference(3, "lech", 0.70),
            ],
        )
        self.assertEqual(result.status, "INSUFFICIENT_SIGNAL")
        self.assertEqual(result.reason_code, "insufficient_reference_pool")
        self.assertEqual(result.reference_event_count, 3)
        self.assertEqual(result.reference_club_count, 1)

    def test_classifies_progress_against_empirical_iqr(self):
        refs = [
            reference(1, "lech", 0.90),  # progress .10
            reference(2, "pogon", 0.80), # progress .20
            reference(3, "gks", 0.70),   # progress .30
        ]
        on_track = evaluate_trajectory_gap(
            ticket_event_id=6,
            club_slug="lech",
            live=live(available_index=0.80),
            prior=prior(),
            references=refs,
        )
        self.assertEqual(on_track.status, "ON_TRACK")
        self.assertAlmostEqual(on_track.expected_progress, 0.20)
        self.assertAlmostEqual(on_track.level_gap, 0.0)
        self.assertEqual(on_track.confidence, "LOW")

        under = evaluate_trajectory_gap(
            ticket_event_id=6,
            club_slug="lech",
            live=live(available_index=0.97),
            prior=prior(),
            references=refs,
        )
        self.assertEqual(under.status, "UNDERPERFORMING")

        over = evaluate_trajectory_gap(
            ticket_event_id=6,
            club_slug="lech",
            live=live(available_index=0.55),
            prior=prior(),
            references=refs,
        )
        self.assertEqual(over.status, "OUTPERFORMING")

    def test_excludes_target_event_and_future_reference(self):
        refs = [
            reference(6, "lech", 0.40),
            reference(1, "lech", 0.90),
            reference(2, "pogon", 0.80),
            reference(3, "gks", 0.70),
            TrajectoryReferenceRow(
                ticket_event_id=4,
                club_slug="legia",
                horizon="T-14",
                as_of_at=datetime(2026, 10, 18, 12, 0, tzinfo=UTC),
                feature_version="live-trajectory-v1.1",
                training_eligible=True,
                point_in_time_validated=True,
                signal_readiness="ready",
                available_index=0.1,
            ),
        ]
        result = evaluate_trajectory_gap(
            ticket_event_id=6,
            club_slug="lech",
            live=live(available_index=0.80),
            prior=prior(),
            references=refs,
        )
        self.assertEqual(result.reference_event_count, 3)
        self.assertEqual(result.reference_club_count, 3)
        self.assertAlmostEqual(result.expected_progress, 0.20)


if __name__ == "__main__":
    unittest.main()
