#!/usr/bin/env python3
import unittest

import pandas as pd

from ml.d2_prospective_evidence_class_v1 import (
    EVIDENCE_DELAYED_LABEL,
    EVIDENCE_TRUE_PROSPECTIVE,
)
from ml.d2_prospective_tag_scoring_evidence_v1 import tag_scoring_evidence


class D2ProspectiveTagScoringEvidenceV1Test(unittest.TestCase):
    def _readiness(self):
        return {
            "stage2_freeze_cutoff_at": "2026-10-19T19:11:01+00:00",
            "events": [
                {
                    "ticket_event_id": 15,
                    "evidence_class": EVIDENCE_DELAYED_LABEL,
                    "counts_toward_true_prospective_promotion_evidence": False,
                    "readiness_status": "READY_FOR_PROSPECTIVE_SCORE",
                    "final24_snapshot_count": 96,
                },
                {
                    "ticket_event_id": 10,
                    "evidence_class": EVIDENCE_TRUE_PROSPECTIVE,
                    "counts_toward_true_prospective_promotion_evidence": True,
                    "readiness_status": "READY_FOR_PROSPECTIVE_SCORE",
                    "final24_snapshot_count": 80,
                },
            ],
        }

    def test_scored_events_and_rows_receive_frozen_evidence_class(self) -> None:
        scoring = {
            "status": "COMPLETED_PROSPECTIVE_SCORING",
            "scored_events": [
                {"ticket_event_id": 15, "scores": {}},
                {"ticket_event_id": 10, "scores": {}},
            ],
            "blocked_events": [],
        }
        rows = pd.DataFrame({
            "ticket_event_id": [15, 15, 10],
            "p2_p50": [1.0, 2.0, 3.0],
        })
        tagged, tagged_rows = tag_scoring_evidence(scoring, self._readiness(), rows)
        self.assertEqual(tagged["delayed_label_scored_event_ids"], [15])
        self.assertEqual(tagged["true_prospective_scored_event_ids"], [10])
        self.assertEqual(tagged["delayed_label_scored_event_count"], 1)
        self.assertEqual(tagged["true_prospective_scored_event_count"], 1)
        by_id = {row["ticket_event_id"]: row for row in tagged["scored_events"]}
        self.assertFalse(by_id[15]["counts_toward_true_prospective_promotion_evidence"])
        self.assertTrue(by_id[10]["counts_toward_true_prospective_promotion_evidence"])
        self.assertEqual(
            tagged_rows["evidence_class"].tolist(),
            [EVIDENCE_DELAYED_LABEL, EVIDENCE_DELAYED_LABEL, EVIDENCE_TRUE_PROSPECTIVE],
        )
        self.assertEqual(
            tagged_rows["counts_toward_true_prospective_promotion_evidence"].tolist(),
            [False, False, True],
        )

    def test_blocked_scoring_event_is_also_tagged(self) -> None:
        scoring = {
            "status": "NEW_EVENTS_BLOCKED_NO_SCORES",
            "scored_events": [],
            "blocked_events": [
                {"ticket_event_id": 15, "reason": "RuntimeError"},
            ],
        }
        tagged, _ = tag_scoring_evidence(scoring, self._readiness(), pd.DataFrame())
        self.assertEqual(tagged["blocked_events"][0]["evidence_class"], EVIDENCE_DELAYED_LABEL)
        self.assertFalse(
            tagged["blocked_events"][0]["counts_toward_true_prospective_promotion_evidence"]
        )

    def test_scoring_event_missing_readiness_evidence_is_hard_failure(self) -> None:
        scoring = {
            "status": "COMPLETED_PROSPECTIVE_SCORING",
            "scored_events": [{"ticket_event_id": 999, "scores": {}}],
            "blocked_events": [],
        }
        with self.assertRaises(RuntimeError):
            tag_scoring_evidence(scoring, self._readiness(), pd.DataFrame())

    def test_invalid_readiness_evidence_class_is_hard_failure(self) -> None:
        readiness = self._readiness()
        readiness["events"][0]["evidence_class"] = "UNKNOWN"
        scoring = {
            "status": "COMPLETED_PROSPECTIVE_SCORING",
            "scored_events": [{"ticket_event_id": 15, "scores": {}}],
            "blocked_events": [],
        }
        with self.assertRaises(RuntimeError):
            tag_scoring_evidence(scoring, readiness, pd.DataFrame())


if __name__ == "__main__":
    unittest.main()
