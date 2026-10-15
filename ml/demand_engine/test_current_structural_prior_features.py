import unittest

import pandas as pd

from ml.demand_engine.current_structural_prior_features import (
    CurrentStructuralPriorEvent,
    build_current_structural_prior_row,
)


class CurrentStructuralPriorFeaturesTest(unittest.TestCase):
    def setUp(self):
        self.historical = pd.DataFrame(
            [
                {
                    "season": "2025/2026",
                    "date": "2025-08-01",
                    "kickoff_time_local": "18:00",
                    "home_club_key": "home",
                    "away_club_key": "alpha",
                    "attendance": 10000,
                },
                {
                    "season": "2025/2026",
                    "date": "2025-09-01",
                    "kickoff_time_local": "18:00",
                    "home_club_key": "home",
                    "away_club_key": "away",
                    "attendance": 12000,
                },
                {
                    "season": "2025/2026",
                    "date": "2025-10-01",
                    "kickoff_time_local": "18:00",
                    "home_club_key": "home",
                    "away_club_key": "beta",
                    "attendance": 14000,
                },
            ]
        )
        self.current_attendance = pd.DataFrame(
            [
                {
                    "club_slug": "home",
                    "kickoff_at": "2026-08-01T16:00:00Z",
                    "opponent_key": "away",
                    "actual_attendance": 20000,
                },
                {
                    "club_slug": "home",
                    "kickoff_at": "2026-09-15T16:00:00Z",
                    "opponent_key": "gamma",
                    "actual_attendance": 22000,
                },
                {
                    "club_slug": "home",
                    "kickoff_at": "2026-10-05T16:00:00Z",
                    "opponent_key": "future_should_be_ignored",
                    "actual_attendance": 40000,
                },
            ]
        )
        as_of = pd.Timestamp("2026-10-01T16:30:00Z")
        self.sporting = pd.DataFrame(
            [
                {
                    "club_key": "home",
                    "as_of_at": as_of,
                    "matches_played": 8,
                    "points": 18,
                    "ppg": 2.25,
                    "gdpg": 1.0,
                    "form5_points": 11,
                    "form5_gd": 4,
                    "last_kickoff_at": "2026-09-20T18:00:00Z",
                    "matches_last14": 1,
                    "position": 3,
                },
                {
                    "club_key": "away",
                    "as_of_at": as_of,
                    "matches_played": 9,
                    "points": 16,
                    "ppg": 16 / 9,
                    "gdpg": 0.4,
                    "form5_points": 10,
                    "form5_gd": 2,
                    "last_kickoff_at": "2026-09-18T18:30:00Z",
                    "matches_last14": 1,
                    "position": 5,
                },
            ]
        )
        self.event = CurrentStructuralPriorEvent(
            ticket_event_id=99,
            season="2026/2027",
            round_no=13,
            kickoff_at=pd.Timestamp("2026-10-31T16:30:00Z"),
            home_club_key="home",
            away_club_key="away",
            stadium_capacity=43000,
        )

    def test_builds_exact_t30_row_and_ignores_future_attendance(self):
        row = build_current_structural_prior_row(
            historical_matches=self.historical,
            current_attendance=self.current_attendance,
            sporting_state=self.sporting,
            event=self.event,
            horizon="T-30",
        ).iloc[0]

        self.assertEqual(row["as_of_at"], pd.Timestamp("2026-10-01T16:30:00Z"))
        self.assertEqual(row["horizon"], "T-30")
        self.assertEqual(row["season_home_n"], 2)
        self.assertAlmostEqual(row["baseline_season"], 21000.0)
        self.assertEqual(row["home_attendance_last"], 22000.0)
        self.assertEqual(row["capacity"], 43000.0)
        self.assertEqual(row["home_position"], 3)
        self.assertEqual(row["away_position"], 5)
        self.assertEqual(row["position_gap"], 2)
        self.assertFalse(bool(row["training_eligible"]))
        self.assertFalse(bool(row["target_eligible"]))

    def test_builds_exact_t7_cutoff(self):
        sporting = self.sporting.copy()
        sporting["as_of_at"] = pd.Timestamp("2026-10-24T16:30:00Z")
        row = build_current_structural_prior_row(
            historical_matches=self.historical,
            current_attendance=self.current_attendance,
            sporting_state=sporting,
            event=self.event,
            horizon="T-7",
        ).iloc[0]

        self.assertEqual(row["as_of_at"], pd.Timestamp("2026-10-24T16:30:00Z"))
        self.assertEqual(row["horizon"], "T-7")
        self.assertEqual(row["capacity"], 43000.0)

    def test_rejects_sporting_state_from_future(self):
        sporting = self.sporting.copy()
        sporting.loc[sporting["club_key"] == "away", "as_of_at"] = pd.Timestamp(
            "2026-10-02T00:00:00Z"
        )
        with self.assertRaisesRegex(ValueError, "from the future"):
            build_current_structural_prior_row(
                historical_matches=self.historical,
                current_attendance=self.current_attendance,
                sporting_state=sporting,
                event=self.event,
                horizon="T-30",
            )


if __name__ == "__main__":
    unittest.main()
