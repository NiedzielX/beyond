from datetime import datetime, timedelta, timezone
import unittest

from ml.demand_engine.contracts import ForecastRequest
from ml.demand_engine.v17_t7 import (
    CALIBRATION_VERSION,
    CONFORMAL_RADIUS,
    MODEL_VERSION,
    RecoveredV17T7Forecaster,
    V17T7StateError,
)


class RecoveredV17T7ForecasterTest(unittest.TestCase):
    def setUp(self) -> None:
        self.forecaster = RecoveredV17T7Forecaster()
        kickoff = datetime(2024, 11, 10, 16, 30, tzinfo=timezone.utc)
        self.request = ForecastRequest(
            ticket_event_id=999,
            club_slug="lech",
            home_team="Lech Poznań",
            away_team="Legia Warszawa",
            competition="Ekstraklasa",
            kickoff_at=kickoff,
            forecast_generated_at=kickoff - timedelta(days=7),
            stadium_capacity=43269,
            static_features={
                "season": "2024/2025",
                "opponent_key": "legia",
                "target_round_no": 15,
                "target_season_progress": 0.41176,
                "target_matches_remaining": 19,
                "lech_position_at_t7": 1,
                "opponent_position_at_t7": 5,
                "lech_matches_played_at_t7": 14,
                "opponent_matches_played_at_t7": 13,
                "league_team_count": 18,
            },
        )

    def test_reproduces_preserved_legia_t7_prediction(self) -> None:
        result = self.forecaster.forecast(self.request)

        self.assertEqual(result.model_version, MODEL_VERSION)
        self.assertEqual(result.calibration_version, CALIBRATION_VERSION)
        self.assertAlmostEqual(result.p50, 42811.25523882332, places=6)
        self.assertAlmostEqual(
            result.p10,
            42811.25523882332 - CONFORMAL_RADIUS,
            places=6,
        )
        self.assertEqual(result.p90, 43269)

    def test_rejects_use_before_canonical_t7_checkpoint(self) -> None:
        too_early = ForecastRequest(
            **{
                **self.request.__dict__,
                "forecast_generated_at": self.request.kickoff_at - timedelta(days=8),
            }
        )
        self.assertFalse(self.forecaster.supports(too_early))
        with self.assertRaises(V17T7StateError):
            self.forecaster.forecast(too_early)


if __name__ == "__main__":
    unittest.main()
