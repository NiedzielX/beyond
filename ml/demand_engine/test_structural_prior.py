from datetime import datetime, timedelta, timezone
import unittest

from ml.demand_engine.contracts import ForecastRequest
from ml.demand_engine.structural_prior import (
    CURRENT_STRUCTURAL_PRIOR_SPECS,
    RowStructuralPriorAdapter,
    StructuralPriorError,
    StructuralPriorNotDueError,
    StructuralPriorUnavailableError,
    resolve_structural_prior_spec,
)

UTC = timezone.utc


class StructuralPriorAdapterTest(unittest.TestCase):
    def setUp(self) -> None:
        self.kickoff = datetime(2026, 12, 10, 20, 0, tzinfo=UTC)

    def _request(self, days_before: float) -> ForecastRequest:
        return ForecastRequest(
            ticket_event_id=24,
            club_slug="jagiellonia",
            home_team="Jagiellonia Bialystok",
            away_team="Crystal Palace",
            competition="UEFA Conference League",
            kickoff_at=self.kickoff,
            forecast_generated_at=self.kickoff - timedelta(days=days_before),
            stadium_capacity=22372,
        )

    def _row(self, horizon: str) -> dict:
        spec = CURRENT_STRUCTURAL_PRIOR_SPECS[horizon]
        target = self.kickoff - timedelta(days=spec.target_days_before)
        return {
            "status": "ready",
            "source_prior_id": 17,
            "ticket_event_id": 24,
            "horizon": horizon,
            "requested_as_of_at": (self.kickoff - timedelta(days=10)).isoformat(),
            "target_as_of_at": target.isoformat(),
            "kickoff_at": self.kickoff.isoformat(),
            "model_spec_id": spec.model_spec_id,
            "model_family": spec.model_family,
            "feature_contract": spec.feature_contract,
            "p50": 18000,
            "p10": None,
            "p90": None,
            "stadium_capacity": 22372,
            "expected_occupancy": None,
            "point_in_time_validated": True,
            "generated_at": datetime(2026, 10, 15, 9, 0, tzinfo=UTC).isoformat(),
            "metadata": {"source": "test"},
        }

    def test_before_t30_is_not_due(self) -> None:
        with self.assertRaises(StructuralPriorNotDueError):
            resolve_structural_prior_spec(
                kickoff_at=self.kickoff,
                requested_as_of_at=self.kickoff - timedelta(days=31),
            )

    def test_t10_carries_forward_t14_not_future_t7(self) -> None:
        spec, target = resolve_structural_prior_spec(
            kickoff_at=self.kickoff,
            requested_as_of_at=self.kickoff - timedelta(days=10),
        )
        self.assertEqual(spec.horizon, "T-14")
        self.assertEqual(target, self.kickoff - timedelta(days=14))

    def test_boundaries_switch_to_newly_due_checkpoint(self) -> None:
        cases = [
            (30, "T-30"),
            (14, "T-14"),
            (7, "T-7"),
            (3, "T-3"),
            (1, "T-1"),
        ]
        for days, expected in cases:
            with self.subTest(days=days):
                spec, _ = resolve_structural_prior_spec(
                    kickoff_at=self.kickoff,
                    requested_as_of_at=self.kickoff - timedelta(days=days),
                )
                self.assertEqual(spec.horizon, expected)

    def test_adapter_exposes_current_champion_and_computes_occupancy(self) -> None:
        row = self._row("T-14")
        adapter = RowStructuralPriorAdapter(lambda _event_id, _asof: row)
        prior = adapter.prior(self._request(10))

        self.assertEqual(prior.horizon, "T-14")
        self.assertEqual(prior.model_spec_id, CURRENT_STRUCTURAL_PRIOR_SPECS["T-14"].model_spec_id)
        self.assertAlmostEqual(prior.expected_occupancy or 0, 18000 / 22372)
        self.assertIsNone(prior.p10)
        self.assertIsNone(prior.p90)

    def test_adapter_never_silently_accepts_legacy_model(self) -> None:
        row = self._row("T-14")
        row["model_spec_id"] = "lech-v13-early-seasonality"
        adapter = RowStructuralPriorAdapter(lambda _event_id, _asof: row)
        with self.assertRaisesRegex(StructuralPriorError, "Wrong model spec"):
            adapter.prior(self._request(10))

    def test_adapter_rejects_future_or_wrong_checkpoint(self) -> None:
        row = self._row("T-14")
        row["target_as_of_at"] = (self.kickoff - timedelta(days=7)).isoformat()
        adapter = RowStructuralPriorAdapter(lambda _event_id, _asof: row)
        with self.assertRaisesRegex(StructuralPriorError, "Wrong target cutoff"):
            adapter.prior(self._request(10))

    def test_adapter_rejects_non_pit_prior(self) -> None:
        row = self._row("T-14")
        row["point_in_time_validated"] = False
        adapter = RowStructuralPriorAdapter(lambda _event_id, _asof: row)
        with self.assertRaisesRegex(StructuralPriorError, "not point-in-time validated"):
            adapter.prior(self._request(10))

    def test_missing_materialized_prior_is_explicit(self) -> None:
        adapter = RowStructuralPriorAdapter(lambda _event_id, _asof: None)
        with self.assertRaises(StructuralPriorUnavailableError):
            adapter.prior(self._request(10))


if __name__ == "__main__":
    unittest.main()
