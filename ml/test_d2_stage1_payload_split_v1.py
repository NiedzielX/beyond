#!/usr/bin/env python3
import unittest

import pandas as pd

from ml.d2_stage1_payload_split_v1 import split_payload


class D2Stage1PayloadSplitV1Test(unittest.TestCase):
    def _fixture(self):
        frozen_ids = [1, 3, 4, 8, 9, 12, 13, 14, 17]
        contract_rows = []
        live_rows = []
        events = []
        # 30 exact frozen rows: first three events have 4 rows, remaining six 3.
        row_counts = {event_id: (4 if event_id in {1, 3, 4} else 3) for event_id in frozen_ids}
        kickoff_base = pd.Timestamp("2026-10-01T12:00:00Z")
        for event_pos, event_id in enumerate(frozen_ids):
            kickoff = kickoff_base + pd.Timedelta(days=event_pos)
            events.append({
                "ticket_event_id": event_id,
                "club_slug": f"club-{event_id}",
                "home_team": f"Home {event_id}",
                "away_team": f"Away {event_id}",
                "kickoff_at": kickoff.isoformat(),
            })
            for index in range(row_counts[event_id]):
                as_of = kickoff - pd.Timedelta(hours=18 - index * 6)
                contract_rows.append({
                    "ticket_event_id": event_id,
                    "as_of_at": as_of.isoformat(),
                })
                live_rows.append({
                    "ticket_event_id": event_id,
                    "features": {"as_of_at": as_of.isoformat()},
                })

        self.assertEqual(len(contract_rows), 30)
        holdout_kickoff = kickoff_base + pd.Timedelta(days=20)
        events.append({
            "ticket_event_id": 5,
            "club_slug": "lech",
            "home_team": "Lech Poznań",
            "away_team": "Korona Kielce",
            "kickoff_at": holdout_kickoff.isoformat(),
            "actual_attendance": 37407,
            "stadium_capacity": 43269,
        })
        for index in range(4):
            live_rows.append({
                "ticket_event_id": 5,
                "features": {
                    "as_of_at": (holdout_kickoff - pd.Timedelta(hours=18 - index * 6)).isoformat()
                },
            })

        max_frozen = max(pd.Timestamp(row["kickoff_at"]) for row in events if row["ticket_event_id"] != 5)
        attendance = [
            {"club_slug": "lech", "kickoff_at": (max_frozen - pd.Timedelta(days=3)).isoformat(), "actual_attendance": 20000},
            {"club_slug": "lech", "kickoff_at": holdout_kickoff.isoformat(), "actual_attendance": 37407},
        ]
        return {
            "events_export": {"ok": True, "eventCount": 10, "events": events},
            "attendance_export": {"ok": True, "attendance": attendance},
            "sporting_export": {"ok": True, "sportingMatches": []},
            "aliases_export": {"ok": True, "aliases": {}},
            "live_export": {
                "ok": True,
                "eventCount": 10,
                "liveRowCount": 34,
                "liveRows": live_rows,
                "sampling": {"mode": "fixture"},
            },
            "training_contract": {"rows": contract_rows},
        }

    def test_dynamic_export_is_split_into_exact_frozen_development_and_holdout(self) -> None:
        frozen, manifest = split_payload(**self._fixture())
        self.assertEqual(frozen["eventCount"], 9)
        self.assertEqual(frozen["liveRowCount"], 30)
        self.assertEqual(
            sorted(row["ticket_event_id"] for row in frozen["events"]),
            [1, 3, 4, 8, 9, 12, 13, 14, 17],
        )
        self.assertEqual(manifest["new_holdout_candidates"]["event_ids"], [5])
        self.assertEqual(manifest["new_holdout_candidates"]["live_rows_by_event"], {5: 4})
        self.assertFalse(manifest["rules"]["new_holdouts_used_for_stage1_selection"])

    def test_future_attendance_is_not_in_frozen_stage0_payload(self) -> None:
        frozen, _ = split_payload(**self._fixture())
        kickoffs = [pd.Timestamp(row["kickoff_at"]) for row in frozen["attendance"]]
        self.assertEqual(len(kickoffs), 1)
        self.assertLessEqual(max(kickoffs), pd.Timestamp(frozen["events"][-1]["kickoff_at"]))

    def test_missing_committed_live_row_is_hard_failure(self) -> None:
        fixture = self._fixture()
        fixture["live_export"]["liveRows"].pop(0)
        with self.assertRaises(RuntimeError):
            split_payload(**fixture)

    def test_new_event_does_not_change_frozen_row_identity(self) -> None:
        frozen, _ = split_payload(**self._fixture())
        frozen_keys = {
            (int(row["ticket_event_id"]), str((row.get("features") or {})["as_of_at"]))
            for row in frozen["liveRows"]
        }
        self.assertEqual(len(frozen_keys), 30)
        self.assertTrue(all(event_id != 5 for event_id, _ in frozen_keys))


if __name__ == "__main__":
    unittest.main()
