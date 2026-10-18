#!/usr/bin/env python3
import unittest

import numpy as np
import pandas as pd

from ml.context_extension_v2 import (
    ALL_CONTEXT_COLUMNS,
    CANDIDATES,
    SEQUENCE_COLUMNS,
    STAKES_COLUMNS,
    build_context_store,
    points_acceleration3,
    streak_features,
)


class ContextExtensionV2Test(unittest.TestCase):
    def test_context_groups_are_disjoint_and_candidate_contract_is_small(self) -> None:
        self.assertTrue(set(SEQUENCE_COLUMNS).isdisjoint(set(STAKES_COLUMNS)))
        self.assertEqual(set(ALL_CONTEXT_COLUMNS), set(SEQUENCE_COLUMNS) | set(STAKES_COLUMNS))
        self.assertEqual(
            [candidate.id for candidate in CANDIDATES],
            ["NO_CONTEXT", "sequence_only", "stakes_only", "sequence_stakes"],
        )

    def test_streak_features_are_sequence_aware(self) -> None:
        self.assertEqual(streak_features(["W", "D", "W"]), {"win": 1, "unbeaten": 3, "loss": 0})
        self.assertEqual(streak_features(["W", "L", "L"]), {"win": 0, "unbeaten": 0, "loss": 2})
        self.assertEqual(streak_features([]), {"win": 0, "unbeaten": 0, "loss": 0})

    def test_points_acceleration_requires_six_completed_matches(self) -> None:
        self.assertTrue(np.isnan(points_acceleration3([3, 3, 0, 3, 1])))
        # recent 3 = 7, previous 3 = 4
        self.assertEqual(points_acceleration3([3, 1, 0, 3, 3, 1]), 3.0)

    def test_snapshot_before_completion_cannot_see_result_but_later_snapshot_can(self) -> None:
        matches = pd.DataFrame({
            "match_key": ["m1", "m2"],
            "season": ["2025/2026", "2025/2026"],
            "home_club_key": ["a", "a"],
            "away_club_key": ["b", "c"],
            "home_goals": [2, 0],
            "away_goals": [0, 0],
            "kickoff_at": pd.to_datetime([
                "2026-01-10T12:00:00Z",
                "2026-01-20T12:00:00Z",
            ]),
            "completed_at": pd.to_datetime([
                "2026-01-10T15:00:00Z",
                "2026-01-20T15:00:00Z",
            ]),
        })
        snapshots = pd.DataFrame({
            "match_key": ["m1", "m2", "m2"],
            "season": ["2025/2026"] * 3,
            "horizon": ["T-1", "T-14", "T-7"],
            "as_of_at": pd.to_datetime([
                "2026-01-09T12:00:00Z",
                "2026-01-10T14:00:00Z",
                "2026-01-10T16:00:00Z",
            ]),
            "kickoff_at": pd.to_datetime([
                "2026-01-10T12:00:00Z",
                "2026-01-20T12:00:00Z",
                "2026-01-20T12:00:00Z",
            ]),
            "home_club_key": ["a", "a", "a"],
            "away_club_key": ["b", "c", "c"],
            "season_progress": [0.20, 0.20, 0.20],
        })

        context = build_context_store(matches, snapshots)
        before_self = context[(context["match_key"] == "m1") & (context["horizon"] == "T-1")].iloc[0]
        before_completion = context[(context["match_key"] == "m2") & (context["horizon"] == "T-14")].iloc[0]
        after_completion = context[(context["match_key"] == "m2") & (context["horizon"] == "T-7")].iloc[0]

        self.assertEqual(int(before_self["ctx_home_win_streak"]), 0)
        self.assertEqual(int(before_completion["ctx_home_win_streak"]), 0)
        self.assertEqual(int(after_completion["ctx_home_win_streak"]), 1)

        # Before m1 completes every participant has zero points, so c is tied
        # with the leader. After m1 completes, c trails leader a by 3 points.
        self.assertAlmostEqual(float(before_completion["ctx_away_title_pressure"]), 0.20)
        self.assertLess(float(after_completion["ctx_away_title_pressure"]), 0.20)

    def test_no_context_column_uses_target_attendance_or_future_label_name(self) -> None:
        forbidden_fragments = ("attendance", "target", "final", "future_result")
        for column in ALL_CONTEXT_COLUMNS:
            for fragment in forbidden_fragments:
                self.assertNotIn(fragment, column)


if __name__ == "__main__":
    unittest.main()
