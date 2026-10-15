from datetime import datetime, timezone
import unittest

from ml.demand_engine.contracts import ForecastRequest
from ml.demand_engine.live_features import LIVE_FEATURE_VERSION, RowLiveFeatureProvider


class LiveContractRegistryTest(unittest.TestCase):
    def test_row_provider_fallback_uses_current_feature_version(self) -> None:
        request = ForecastRequest(
            ticket_event_id=999,
            club_slug="test",
            home_team="Home",
            away_team="Away",
            competition="Test",
            kickoff_at=datetime(2026, 12, 1, 18, 0, tzinfo=timezone.utc),
            forecast_generated_at=datetime(2026, 11, 1, 18, 0, tzinfo=timezone.utc),
        )
        provider = RowLiveFeatureProvider(lambda _event_id: None)
        features = provider.features(request)

        self.assertEqual(LIVE_FEATURE_VERSION, "live-trajectory-v1.1")
        self.assertEqual(features.feature_version, "live-trajectory-v1.1")
        self.assertEqual(features.signal_readiness, "not_ready")


if __name__ == "__main__":
    unittest.main()
