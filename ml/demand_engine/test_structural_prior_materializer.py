import inspect
import unittest

import pandas as pd

import ml.demand_engine.materialize_structural_priors as materializer
from ml.demand_engine.materialize_structural_priors import build_sporting_state


class StructuralPriorMaterializerTest(unittest.TestCase):
    def test_scheduled_materializer_has_no_fit_path(self):
        source = inspect.getsource(materializer)
        self.assertNotIn("fit_structural_prior_runtime", source)
        self.assertNotIn(".fit(", source)

    def test_sporting_state_excludes_same_day_completed_match(self):
        aliases = {
            "Home": "home",
            "Away": "away",
            "Third": "third",
        }
        rows = [
            {
                "season": "2026-2027",
                "event_date": "2026-10-09",
                "home_team": "Home",
                "away_team": "Third",
                "home_score": 2,
                "away_score": 0,
                "completed": True,
            },
            {
                "season": "2026-2027",
                "event_date": "2026-10-09",
                "home_team": "Away",
                "away_team": "Third",
                "home_score": 1,
                "away_score": 1,
                "completed": True,
            },
            {
                # Must be excluded even though the source marks it completed:
                # exact kickoff is not available, so same local date is unsafe.
                "season": "2026-2027",
                "event_date": "2026-10-10",
                "home_team": "Away",
                "away_team": "Home",
                "home_score": 5,
                "away_score": 0,
                "completed": True,
            },
        ]
        state = build_sporting_state(
            rows,
            aliases,
            as_of_at=pd.Timestamp("2026-10-10T15:30:00Z"),
            source_season="2026/2027",
        ).set_index("club_key")

        self.assertEqual(int(state.loc["home", "matches_played"]), 1)
        self.assertEqual(float(state.loc["home", "points"]), 3.0)
        self.assertEqual(int(state.loc["away", "matches_played"]), 1)
        self.assertEqual(float(state.loc["away", "points"]), 1.0)
        self.assertEqual(int(state.loc["home", "position"]), 1)
        self.assertLess(
            pd.Timestamp(state.loc["home", "last_kickoff_at"]),
            pd.Timestamp("2026-10-10T15:30:00Z"),
        )

    def test_ignores_other_seasons_and_unfinished_rows(self):
        aliases = {"Home": "home", "Away": "away"}
        rows = [
            {
                "season": "2025-2026",
                "event_date": "2026-10-01",
                "home_team": "Home",
                "away_team": "Away",
                "home_score": 4,
                "away_score": 0,
                "completed": True,
            },
            {
                "season": "2026-2027",
                "event_date": "2026-10-01",
                "home_team": "Home",
                "away_team": "Away",
                "home_score": 4,
                "away_score": 0,
                "completed": False,
            },
            {
                "season": "2026-2027",
                "event_date": "2026-10-02",
                "home_team": "Home",
                "away_team": "Away",
                "home_score": 1,
                "away_score": 0,
                "completed": True,
            },
        ]
        state = build_sporting_state(
            rows,
            aliases,
            as_of_at=pd.Timestamp("2026-10-10T12:00:00Z"),
            source_season="2026/2027",
        ).set_index("club_key")
        self.assertEqual(int(state.loc["home", "matches_played"]), 1)
        self.assertEqual(float(state.loc["home", "points"]), 3.0)
        self.assertEqual(float(state.loc["away", "points"]), 0.0)


if __name__ == "__main__":
    unittest.main()
