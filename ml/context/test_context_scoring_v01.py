from __future__ import annotations

import unittest

from ml.context.context_scoring_v01 import (
    LeagueStakesInput,
    absence_demand_shock_v01,
    european_league_phase_stakes_v01,
    league_match_stakes_v01,
)


class ContextScoringV01Tests(unittest.TestCase):
    def test_lech_korona_stakes_example(self):
        result = league_match_stakes_v01(
            LeagueStakesInput(
                home_rank=2,
                away_rank=8,
                home_points=22,
                away_points=15,
                home_played=9,
                away_played=10,
            )
        )
        self.assertEqual(result["score"], 42.0)
        self.assertEqual(result["status"], "research_heuristic_not_model_active")

    def test_lech_leverkusen_matchday_two_pressure(self):
        result = european_league_phase_stakes_v01(matchday=2, home_points_before=0)
        self.assertEqual(result["score"], 54.4)

    def test_absence_refuses_to_invent_player_salience(self):
        result = absence_demand_shock_v01(
            player_salience=None,
            absence_certainty=0.99,
            novelty=0.1,
        )
        self.assertIsNone(result["score"])
        self.assertEqual(result["status"], "insufficient_evidence_player_salience")

    def test_new_star_absence_can_generate_large_demand_shock(self):
        result = absence_demand_shock_v01(
            player_salience=0.9,
            absence_certainty=1.0,
            novelty=1.0,
        )
        self.assertEqual(result["score"], 90.0)


if __name__ == "__main__":
    unittest.main()
