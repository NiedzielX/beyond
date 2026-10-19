#!/usr/bin/env python3
import json
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from ml.d2_prospective_outcome_readiness_v1 import (
    STATUS_FUTURE,
    STATUS_GRACE,
    STATUS_MISSING_CAPACITY,
    STATUS_MISSING_LIVE,
    STATUS_MISSING_OUTCOME,
    STATUS_READY,
    build_readiness_report,
    classify_events,
)
from ml.d2_prospective_score_v1 import (
    EXPECTED_DEVELOPMENT_EVENT_IDS,
    EXPECTED_REGISTRY_VERSION,
    EXPECTED_STAGE2_PACKAGE,
)


class D2ProspectiveOutcomeReadinessV1Test(unittest.TestCase):
    def _event(self, event_id, kickoff, actual=12000, capacity=20000):
        return {
            "ticket_event_id": event_id,
            "club_slug": f"club-{event_id}",
            "home_team": f"Home {event_id}",
            "away_team": f"Away {event_id}",
            "kickoff_at": kickoff,
            "actual_attendance": actual,
            "stadium_capacity": capacity,
        }

    def test_completed_missing_outcome_is_visible_blocker(self) -> None:
        rows = classify_events(
            events=[self._event(20, "2026-10-19T17:00:00Z", actual=None)],
            live_rows=[{"ticket_event_id": 20}] * 4,
            scored_ids={5},
            as_of_at=pd.Timestamp("2026-10-19T20:30:00Z"),
        )
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["readiness_status"], STATUS_MISSING_OUTCOME)
        self.assertEqual(rows[0]["final24_live_row_count"], 4)
        self.assertFalse(rows[0]["actual_attendance_present"])

    def test_verified_outcome_and_live_rows_is_ready(self) -> None:
        rows = classify_events(
            events=[self._event(20, "2026-10-19T17:00:00Z", actual=13456)],
            live_rows=[{"ticket_event_id": 20}] * 4,
            scored_ids=set(),
            as_of_at=pd.Timestamp("2026-10-19T20:30:00Z"),
        )
        self.assertEqual(rows[0]["readiness_status"], STATUS_READY)

    def test_completed_outcome_without_live_rows_is_blocked(self) -> None:
        rows = classify_events(
            events=[self._event(20, "2026-10-19T17:00:00Z", actual=13456)],
            live_rows=[],
            scored_ids=set(),
            as_of_at=pd.Timestamp("2026-10-19T20:30:00Z"),
        )
        self.assertEqual(rows[0]["readiness_status"], STATUS_MISSING_LIVE)

    def test_missing_capacity_is_blocked_after_other_prerequisites(self) -> None:
        rows = classify_events(
            events=[self._event(20, "2026-10-19T17:00:00Z", actual=13456, capacity=None)],
            live_rows=[{"ticket_event_id": 20}] * 4,
            scored_ids=set(),
            as_of_at=pd.Timestamp("2026-10-19T20:30:00Z"),
        )
        self.assertEqual(rows[0]["readiness_status"], STATUS_MISSING_CAPACITY)

    def test_future_and_grace_events_are_not_false_blockers(self) -> None:
        events = [
            self._event(20, "2026-10-20T17:00:00Z", actual=None),
            self._event(21, "2026-10-19T19:00:00Z", actual=None),
        ]
        rows = classify_events(
            events=events,
            live_rows=[{"ticket_event_id": 20}, {"ticket_event_id": 21}],
            scored_ids=set(),
            as_of_at=pd.Timestamp("2026-10-19T20:30:00Z"),
        )
        by_id = {row["ticket_event_id"]: row for row in rows}
        self.assertEqual(by_id[20]["readiness_status"], STATUS_FUTURE)
        self.assertEqual(by_id[21]["readiness_status"], STATUS_GRACE)

    def test_development_and_registered_events_are_excluded(self) -> None:
        dev_id = EXPECTED_DEVELOPMENT_EVENT_IDS[0]
        rows = classify_events(
            events=[
                self._event(dev_id, "2026-10-01T10:00:00Z"),
                self._event(5, "2026-10-18T15:30:00Z"),
                self._event(20, "2026-10-19T17:00:00Z", actual=None),
            ],
            live_rows=[
                {"ticket_event_id": dev_id},
                {"ticket_event_id": 5},
                {"ticket_event_id": 20},
            ],
            scored_ids={5},
            as_of_at=pd.Timestamp("2026-10-19T21:00:00Z"),
        )
        self.assertEqual([row["ticket_event_id"] for row in rows], [20])

    def test_report_never_estimates_attendance(self) -> None:
        registry = {
            "registry_version": EXPECTED_REGISTRY_VERSION,
            "frozen_package_id": EXPECTED_STAGE2_PACKAGE,
            "development_event_ids": list(EXPECTED_DEVELOPMENT_EVENT_IDS),
            "scored_prospective_events": [{"ticket_event_id": 5}],
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "registry.json"
            path.write_text(json.dumps(registry))
            report = build_readiness_report(
                events_export={
                    "events": [self._event(20, "2026-10-19T17:00:00Z", actual=None)]
                },
                live_export={"liveRows": [{"ticket_event_id": 20}] * 4},
                registry_path=path,
                as_of_at=pd.Timestamp("2026-10-19T21:00:00Z"),
            )
        self.assertFalse(report["attendance_estimation_performed"])
        self.assertEqual(report["blocked_completed_event_ids"], [20])
        self.assertEqual(report["ready_event_ids"], [])
        self.assertEqual(report["events"][0]["readiness_status"], STATUS_MISSING_OUTCOME)


if __name__ == "__main__":
    unittest.main()
