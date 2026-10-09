from datetime import datetime, timezone
import unittest

from ml.demand_engine.contracts import ForecastRequest, LiveFeatures, QuantileForecast
from ml.demand_engine.engine import DemandEngine
from ml.demand_engine.live_features import RowLiveFeatureProvider
from ml.demand_engine.storage import to_forecast_observation


class HistoricalStub:
    def forecast(self, request: ForecastRequest) -> QuantileForecast:
        return QuantileForecast(
            p10=25000,
            p50=30000,
            p90=35000,
            model_name="historical-stub",
            model_version="test-v1",
            feature_set_version="features-test-v1",
        )


class LiveStub:
    def features(self, request: ForecastRequest) -> LiveFeatures:
        return LiveFeatures(
            feature_version="live-test-v1",
            signal_readiness="ready",
            available_total=10000,
            available_index=0.42,
            velocity_6h=21.0,
            velocity_24h=15.0,
            acceleration_6h_vs_24h=6.0,
            raw_snapshot_count=20,
            clean_snapshot_count=19,
            excluded_anomaly_count=1,
        )


def request_fixture() -> ForecastRequest:
    return ForecastRequest(
        ticket_event_id=123,
        club_slug="test-club",
        home_team="Home",
        away_team="Away",
        competition="League",
        kickoff_at=datetime(2026, 11, 1, 18, 0, tzinfo=timezone.utc),
        forecast_generated_at=datetime(2026, 10, 25, 18, 0, tzinfo=timezone.utc),
        source_snapshot_id=456,
        source_snapshot_captured_at=datetime(2026, 10, 25, 17, 55, tzinfo=timezone.utc),
        stadium_capacity=40000,
    )


class DemandEngineTest(unittest.TestCase):
    def test_noop_live_correction_preserves_historical_forecast(self) -> None:
        result = DemandEngine(HistoricalStub(), LiveStub()).forecast(request_fixture())

        self.assertEqual(result.historical.p50, 30000)
        self.assertEqual(result.correction.adjustment, 0)
        self.assertEqual(result.correction.status, "shadow")
        self.assertEqual(result.final_p10, 25000)
        self.assertEqual(result.final_p50, 30000)
        self.assertEqual(result.final_p90, 35000)

        row = to_forecast_observation(result)
        self.assertEqual(row["historical_p50"], 30000)
        self.assertEqual(row["final_p50"], 30000)
        self.assertEqual(row["live_adjustment"], 0)
        self.assertEqual(
            row["payload"]["live"]["inventory_interpretation"],
            "demand_proxy_not_confirmed_sales",
        )
        self.assertEqual(row["payload"]["engine"]["live_feature_version"], "live-test-v1")

    def test_live_feature_row_adapter_defaults_to_partial_not_ready(self) -> None:
        provider = RowLiveFeatureProvider(
            lambda event_id: {
                "available_total": "2361",
                "first_available_total": "8222",
                "available_index": "0.287156",
                "net_removed_since_first": "5861",
                "net_removed_since_previous": "-5",
                "velocity_since_previous": "-19.991",
                "net_removed_6h": "173",
                "velocity_6h": "28.813",
                "net_removed_24h": "387",
                "velocity_24h": "16.106",
                "acceleration_6h_vs_24h": "12.708",
            }
        )

        features = provider.features(request_fixture())

        self.assertEqual(features.signal_readiness, "partial")
        self.assertEqual(features.available_total, 2361)
        self.assertAlmostEqual(features.available_index or 0, 0.287156)
        self.assertAlmostEqual(features.velocity_6h or 0, 28.813)
        self.assertAlmostEqual(features.acceleration_6h_vs_24h or 0, 12.708)

    def test_live_feature_row_adapter_is_not_ready_without_data(self) -> None:
        provider = RowLiveFeatureProvider(lambda event_id: None)
        features = provider.features(request_fixture())
        self.assertEqual(features.signal_readiness, "not_ready")


if __name__ == "__main__":
    unittest.main()
