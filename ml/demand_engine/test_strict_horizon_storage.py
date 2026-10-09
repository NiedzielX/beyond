from datetime import datetime, timezone
import unittest

from ml.demand_engine.contracts import (
    EngineForecast,
    ForecastRequest,
    LiveCorrection,
    LiveFeatures,
    QuantileForecast,
)
from ml.demand_engine.storage import canonical_horizon, engine_forecast_to_shadow_observation


class StrictHorizonStorageTest(unittest.TestCase):
    def test_t7_requires_pre_or_exact_checkpoint_timestamp(self) -> None:
        self.assertEqual(canonical_horizon(168.0), "T-7")
        self.assertEqual(canonical_horizon(168.01), "T-7")
        self.assertEqual(canonical_horizon(167.99), "continuous")

    def test_canonical_execution_audit_is_persisted_separately(self) -> None:
        request = ForecastRequest(
            ticket_event_id=5,
            club_slug="lech",
            home_team="Lech Poznań",
            away_team="Korona Kielce",
            competition="Ekstraklasa",
            kickoff_at=datetime(2026, 10, 18, 15, 30, tzinfo=timezone.utc),
            forecast_generated_at=datetime(2026, 10, 11, 15, 30, tzinfo=timezone.utc),
            source_snapshot_id=100,
            source_snapshot_captured_at=datetime(2026, 10, 11, 15, 25, tzinfo=timezone.utc),
            stadium_capacity=43269,
            static_features={
                "effective_forecast_at": "2026-10-11T15:30:00+00:00",
                "shadow_executed_at": "2026-10-11T15:35:00+00:00",
                "source_snapshot_asof_cutoff": "2026-10-11T15:30:00+00:00",
            },
        )
        historical = QuantileForecast(
            p10=20000,
            p50=28000,
            p90=36000,
            model_name="Lech Early Demand Model v1.7",
            model_version="lech-v17-t7-recovered-exact",
            feature_set_version="v17-t7-recovered-exact-v1",
            interval_method="split_conformal_absolute_residual_80:horizon:T-7",
            calibration_version="v17-split-conformal-80-v1:T-7",
        )
        forecast = EngineForecast(
            engine_version="beyond-demand-engine-v1-v17-t7-shadow",
            request=request,
            historical=historical,
            live_features=LiveFeatures(
                feature_version="live-features-v1",
                signal_readiness="partial",
                available_total=2200,
            ),
            correction=LiveCorrection(
                adjustment=0,
                correction_version="live-correction-noop-v1",
                status="shadow",
                reason="test",
            ),
            final_p10=20000,
            final_p50=28000,
            final_p90=36000,
        )

        row = engine_forecast_to_shadow_observation(forecast)
        self.assertEqual(row["horizon"], "T-7")
        self.assertEqual(row["hours_to_kickoff"], 168.0)
        state = row["payload"]["historical_state"]
        self.assertEqual(
            state["effective_forecast_at"],
            "2026-10-11T15:30:00+00:00",
        )
        self.assertEqual(
            state["shadow_executed_at"],
            "2026-10-11T15:35:00+00:00",
        )


if __name__ == "__main__":
    unittest.main()
