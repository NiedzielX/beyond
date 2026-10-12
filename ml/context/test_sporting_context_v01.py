from __future__ import annotations

import unittest

from ml.context.sporting_context_v01 import ApiFootball, _norm


class FakeApiFootball(ApiFootball):
    def __init__(self, fixtures):
        self.key = "test"
        self._team_cache = {}
        self._league_cache = {}
        self.fixtures = fixtures

    def get(self, endpoint: str, **params):
        if endpoint == "fixtures":
            return self.fixtures
        return []


class SportingContextTests(unittest.TestCase):
    def test_normalizes_polish_team_name(self):
        self.assertEqual(_norm("Lech Poznań"), "lech poznan")

    def test_last_five_calculates_points_and_goal_difference(self):
        team_id = 1
        fixtures = [
            {"fixture": {"id": 1, "date": "2026-10-01"}, "teams": {"home": {"id": 1}, "away": {"id": 2}}, "goals": {"home": 2, "away": 0}},
            {"fixture": {"id": 2, "date": "2026-10-02"}, "teams": {"home": {"id": 3}, "away": {"id": 1}}, "goals": {"home": 1, "away": 1}},
            {"fixture": {"id": 3, "date": "2026-10-03"}, "teams": {"home": {"id": 1}, "away": {"id": 4}}, "goals": {"home": 0, "away": 1}},
            {"fixture": {"id": 4, "date": "2026-10-04"}, "teams": {"home": {"id": 5}, "away": {"id": 1}}, "goals": {"home": 0, "away": 3}},
            {"fixture": {"id": 5, "date": "2026-10-05"}, "teams": {"home": {"id": 1}, "away": {"id": 6}}, "goals": {"home": 2, "away": 2}},
        ]
        result = FakeApiFootball(fixtures).last_five(team_id)
        self.assertEqual(result["matches"], 5)
        self.assertEqual(result["wins"], 2)
        self.assertEqual(result["draws"], 2)
        self.assertEqual(result["losses"], 1)
        self.assertEqual(result["points"], 8)
        self.assertEqual(result["goal_difference"], 4)


if __name__ == "__main__":
    unittest.main()
