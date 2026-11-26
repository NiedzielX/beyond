import unittest

from ml.rolling72_damped_trend_v1 import damped_available_total


class DampedTrendTests(unittest.TestCase):
    def test_fixed_daily_decay(self):
        for horizon, expected in [(24, 524), (48, 543.2), (72, 558.56)]:
            with self.subTest(horizon=horizon):
                self.assertAlmostEqual(damped_available_total(
                    origin_available_total=500, slope24=1,
                    projection_age_hours=0, horizon_hours=horizon,
                ), expected)

    def test_missing_slope_preserves_true_zero(self):
        self.assertEqual(damped_available_total(
            origin_available_total=0, slope24=None,
            projection_age_hours=0.5, horizon_hours=72,
        ), 0)

    def test_projection_age_and_zero_floor(self):
        inputs = dict(origin_available_total=1, slope24=-1, horizon_hours=24)
        self.assertEqual(damped_available_total(**inputs, projection_age_hours=0.5), 0)
        inputs["slope24"] = 1
        self.assertGreater(
            damped_available_total(**inputs, projection_age_hours=0.5), 25
        )

    def test_invalid_or_overflow_values_fail(self):
        defaults = dict(origin_available_total=1, slope24=1,
                        projection_age_hours=0, horizon_hours=24)
        for change in ({"slope24": float("inf")}, {"slope24": 1e308},
                       {"projection_age_hours": 1.1}, {"horizon_hours": 24.0}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                damped_available_total(**(defaults | change))


if __name__ == "__main__":
    unittest.main()
