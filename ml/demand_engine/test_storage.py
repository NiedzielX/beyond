from datetime import datetime, timezone
import unittest

from ml.demand_engine.contracts import (
    EngineForecast,
    ForecastRequest,
    LiveCorrection,
    LiveFeatures,
    QuantileForecast,
)
from ml.demand_engine.storage import (
    ForecastPersistenceError,
    SupabaseForecastStore,
    engine_forecast_to_shadow_observation,
)


class FakeStore(SupabaseForecastStore):
    def __init__(self) -> None:
        super().__init__("https://example.supabase.co", "test-secret")
        self.last_observation = None

    def _post(self, observation):
        self.last_observation = observation
        return 12345


def example_forecast() -> EngineForecast:
    kickoff = datetime(2026, 10, 18, 15, 30, tzinfo=timezone.utc)
    generated = datetime(2026, 10, 11, 15, 30, tzinfo=timezone.utc)
    request = ForecastRequest(
        ticket_event_id=5,
        club_slug="lech",
        home_team="Lech Poznań",
        away_team="Korona Kielce",
        competition="Ekstraklasa",
        kickoff_at=kickoff,
        forecast_generated_at=generated,
        source_snapshot_id=9975,
        source_snapshot_captured_at=datetime(
            2026, 10, 11, 15, 29, tzinfo=timezone.utc
        ),
        stadium_capacity=43269,
        static_features={
            "season": "2026/2027",
            "opponent_key": "korona",
            "target_round_no": 11,
            "target_season_progress": 10 / 34,
            "target_matches_remaining": 23,
            "lech_position_at_t7": 3,
            "opponent_position_at_t7": 8,
            "lech_matches_played_at_t7": 10,
            "opponent_matches_played_at_t7": 10,
            "league_team_count": 18,
            "t7_state_cutoff_local_date": "2026-10-11",
            "t7_visible_league_results": 90,
        },
    )
    historical = QuantileForecast(
        p10=21000.4,
        p50=29337.2,
        p90=37673.8,
        model_name="lech-v17-horizon-specific",
        model_version="lech-v17-t7-recovered-exact",
        feature_set_version="v17-t7-recovered-exact-v1",
        interval_method="split_conformal_absolute_residual_80:horizon:T-7",
        calibration_version="v17-split-conformal-80-v1:T-7",
    )
    live = LiveFeatures(
        feature_version="live-features-v1",
        signal_readiness="partial",
        available_total=2000,
        first_available_total=5000,
        available_index=0.4,
        velocity_6h=12.5,
        velocity_24h=8.0,
        acceleration_6h_vs_24h=4.5,
        raw_snapshot_count=20,
        clean_snapshot_count=19,
        excluded_anomaly_count=1,
    )
    correction = LiveCorrection(
        adjustment=0.0,
        correction_version="live-correction-noop-v1",
        status="shadow",
        reason="Historical champion shadow; live correction not promoted.",
    )
    return EngineForecast(
        engine_version="beyond-demand-engine-v1-v17-t7-shadow",
        request=request,
        historical=historical,
        live_features=live,
        correction=correction,
        final_p10=historical.p10,
        final_p50=historical.p50,
        final_p90=historical.p90,
    )


class StorageTest(unittest.TestCase):
    def test_maps_t7_shadow_with_full_lineage(self) -> None:
        row = engine_forecast_to_shadow_observation(example_forecast())
        self.assertEqual(row["forecast_status"], "shadow")
        self.assertEqual(row["horizon"], "T-7")
        self.assertEqual(row["model_version"], "beyond-demand-engine-v1-v17-t7-shadow")
        self.assertEqual(row["historical_model"], "lech-v17-t7-recovered-exact")
        self.assertEqual(row["historical_p50"], 29337)
        self.assertEqual(row["final_p90"], 37674)
        self.assertEqual(
            row["payload"]["engine"]["historical_calibration_version"],
            "v17-split-conformal-80-v1:T-7",
        )
        self.assertEqual(
            row["payload"]["live"]["inventory_interpretation"],
            "demand_proxy_not_confirmed_sales",
        )
        self.assertEqual(
            row["payload"]["historical_state"]["t7_state_cutoff_local_date"],
            "2026-10-11",
        )

    def test_store_uses_shadow_rpc_and_returns_observation_id(self) -> None:
        store = FakeStore()
        persisted = store.insert(example_forecast())
        self.assertEqual(persisted["id"], 12345)
        self.assertEqual(persisted["forecast_status"], "shadow")
        self.assertEqual(store.last_observation["ticket_event_id"], 5)

    def test_persistence_refuses_forecast_without_snapshot_lineage(self) -> None:
        forecast = example_forecast()
        request = ForecastRequest(
            **{
                **forecast.request.__dict__,
                "source_snapshot_id": None,
                "source_snapshot_captured_at": None,
            }
        )
        broken = EngineForecast(
            **{**forecast.__dict__, "request": request}
        )
        with self.assertRaises(ForecastPersistenceError):
            engine_forecast_to_shadow_observation(broken)


if __name__ == "__main__":
    unittest.main()
