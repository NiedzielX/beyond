#!/usr/bin/env python3
import unittest

from ml.pre_live_v2_historical_freeze_v1 import (
    B2_HORIZONS,
    CONTRACT,
    EXPECTED_FINAL_MAE,
    FREEZE_ID,
    HORIZONS,
    MANIFEST_FLOAT_DECIMALS,
    canonical_metric,
)


class PreLiveV2HistoricalFreezeV1Test(unittest.TestCase):
    def test_freeze_id_is_fixed(self) -> None:
        self.assertEqual(
            FREEZE_ID,
            "pre-live-v2-historical-candidate-2026-10-18-v1",
        )

    def test_manifest_metrics_are_canonicalized_to_nine_decimals(self) -> None:
        self.assertEqual(MANIFEST_FLOAT_DECIMALS, 9)
        self.assertEqual(canonical_metric(2157.1473613912335), 2157.147361391)
        self.assertEqual(canonical_metric(1889.3672272292854), 1889.367227229)

    def test_all_five_horizons_are_frozen(self) -> None:
        self.assertEqual(HORIZONS, ["T-30", "T-14", "T-7", "T-3", "T-1"])
        self.assertEqual(set(CONTRACT), set(HORIZONS))
        self.assertEqual(set(EXPECTED_FINAL_MAE), set(HORIZONS))

    def test_only_t7_t3_t1_have_b2(self) -> None:
        self.assertEqual(B2_HORIZONS, {"T-7", "T-3", "T-1"})
        self.assertEqual(CONTRACT["T-30"]["current_season_regime"], "NO_ADJUSTMENT")
        self.assertEqual(CONTRACT["T-14"]["current_season_regime"], "NO_ADJUSTMENT")
        self.assertEqual(CONTRACT["T-7"]["current_season_regime"], "ewma50-resid-k6-cap05-min3")
        self.assertEqual(CONTRACT["T-3"]["current_season_regime"], "ewma50-resid-k2-cap05-min3")
        self.assertEqual(CONTRACT["T-1"]["current_season_regime"], "ewma50-resid-k6-cap05-min3")

    def test_no_historical_c2_context_is_frozen(self) -> None:
        for contract in CONTRACT.values():
            self.assertEqual(contract["historical_context_extension"], "NO_CONTEXT")

    def test_every_horizon_has_four_exact_fold_expectations(self) -> None:
        expected_seasons = {
            "2022/2023",
            "2023/2024",
            "2024/2025",
            "2025/2026",
        }
        for horizon in HORIZONS:
            self.assertEqual(set(EXPECTED_FINAL_MAE[horizon]), expected_seasons)
            for value in EXPECTED_FINAL_MAE[horizon].values():
                self.assertGreater(value, 0.0)


if __name__ == "__main__":
    unittest.main()
