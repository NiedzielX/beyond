from datetime import datetime
import unittest
from zoneinfo import ZoneInfo

from ml.demand_engine.t7_state import LeagueResult, build_t7_static_features

WARSAW = ZoneInfo("Europe/Warsaw")


class T7StateBuilderTest(unittest.TestCase):
    def test_excludes_matches_on_t7_calendar_date(self) -> None:
        kickoff = datetime(2026, 10, 18, 17, 30, tzinfo=WARSAW)
        results = [
            LeagueResult(
                datetime(2026, 10, 9, 20, 30, tzinfo=WARSAW),
                "lech",
                "korona",
                2,
                0,
            ),
            LeagueResult(
                datetime(2026, 10, 10, 18, 0, tzinfo=WARSAW),
                "legia",
                "rakow",
                1,
                1,
            ),
            # Even though this result is earlier than the exact 17:30 T-7 clock
            # time, recovered v1.7 uses the calendar checkpoint and excludes it.
            LeagueResult(
                datetime(2026, 10, 11, 12, 0, tzinfo=WARSAW),
                "korona",
                "legia",
                5,
                0,
            ),
        ]

        state = build_t7_static_features(
            season="2026/2027",
            target_kickoff_at=kickoff,
            home_team_key="lech",
            opponent_key="korona",
            target_round_no=11,
            total_rounds=34,
            league_team_keys=["lech", "korona", "legia", "rakow"],
            completed_results=results,
        )

        self.assertEqual(state["t7_state_cutoff_local_date"], "2026-10-11")
        self.assertEqual(state["t7_visible_league_results"], 2)
        self.assertEqual(state["lech_matches_played_at_t7"], 1)
        self.assertEqual(state["opponent_matches_played_at_t7"], 1)
        self.assertEqual(state["target_round_no"], 11)
        self.assertAlmostEqual(state["target_season_progress"], 10 / 34)
        self.assertEqual(state["target_matches_remaining"], 23)

    def test_ranking_uses_points_goal_difference_goals_for_then_team_key(self) -> None:
        kickoff = datetime(2026, 10, 18, 17, 30, tzinfo=WARSAW)
        results = [
            LeagueResult(
                datetime(2026, 10, 1, 18, 0, tzinfo=WARSAW),
                "lech",
                "korona",
                2,
                1,
            ),
            LeagueResult(
                datetime(2026, 10, 2, 18, 0, tzinfo=WARSAW),
                "legia",
                "rakow",
                3,
                2,
            ),
        ]
        state = build_t7_static_features(
            season="2026/2027",
            target_kickoff_at=kickoff,
            home_team_key="lech",
            opponent_key="korona",
            target_round_no=11,
            total_rounds=34,
            league_team_keys=["lech", "korona", "legia", "rakow"],
            completed_results=results,
        )
        # Lech and Legia both have three points and +1 GD; Legia has 3 GF vs
        # Lech's 2, so Legia ranks first and Lech second.
        self.assertEqual(state["lech_position_at_t7"], 2)
        # Korona and Raków have equal points; Korona has -1 GD, same as Raków,
        # but Korona has 1 GF vs Raków's 2, so Korona ranks fourth.
        self.assertEqual(state["opponent_position_at_t7"], 4)


if __name__ == "__main__":
    unittest.main()
