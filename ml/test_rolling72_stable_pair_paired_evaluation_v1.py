import unittest
from datetime import datetime, timedelta, timezone

from ml.rolling72_stable_pair_paired_evaluation_v1 import analyze


def rows(events=30):
    output = []
    label = 1
    for event in range(1, events + 1):
        for horizon in (24, 48, 72):
            issued = datetime(2026, 11, 1, tzinfo=timezone.utc)
            target = issued + timedelta(hours=horizon)
            output.append({
                "issue_id": f"issue-{event}",
                "pers_issue_id": f"issue-{event}",
                "drift24_issue_id": f"issue-{event}",
                "stable_pair_issue_id": f"issue-{event}",
                "label_issue_id": f"issue-{event}",
                "label_id": label,
                "label_status": "SCORED",
                "bundle_id": event,
                "ticket_event_id": event,
                "club_id": f"club-{(event - 1) % 8 + 1}",
                "horizon_hours": horizon,
                "issued_at": issued.isoformat().replace("+00:00", "Z"),
                "target_at": target.isoformat().replace("+00:00", "Z"),
                "label_target_at": target.isoformat().replace("+00:00", "Z"),
                "target_seal_id": 1000 + label,
                "actual": 100,
                "pers_prediction": 110,
                "drift24_prediction": 110,
                "drift24_status": "FALLBACK_PERS",
                "parent_fallback_reason": "SCOPE_MISMATCH",
                "stable_pair_status": "STABLE_PAIR_OVERRIDE",
                "stable_pair_prediction": 105,
                "stable_pair_support_reason": "SUPPORTED",
            })
            label += 1
    return output


class StablePairPairedEvaluationTests(unittest.TestCase):
    def test_scored_cohort_is_identical_and_policy_gate_is_applied(self):
        facts = rows()
        # Parent READY rows are inherited unchanged by the composed policy.
        facts[0].update(drift24_status="READY", parent_fallback_reason=None,
                        drift24_prediction=108,
                        stable_pair_status="INHERITED_DRIFT24",
                        stable_pair_prediction=108, stable_pair_support_reason=None)
        result = analyze(facts)
        self.assertEqual(result["evidence_claim"], "OFFLINE_PAIRED_LABEL_AUDIT_ONLY")
        self.assertFalse(result["prospective_claim"])
        self.assertEqual(result["runtime_coverage"], "UNKNOWN")
        primary = result["primary_stable_pair_vs_pers"]
        secondary = result["secondary_stable_pair_vs_drift24"]
        self.assertEqual(primary["horizons"]["72"]["accepted_shared_labels"], 30)
        self.assertEqual(secondary["horizons"]["72"]["accepted_shared_labels"], 30)
        self.assertEqual(primary["support"], secondary["support"])
        self.assertEqual(primary["horizons"]["72"]["candidate_method"]["event_balanced_mae"], 5)
        self.assertEqual(primary["horizons"]["72"]["delta_candidate_minus_baseline"]["event_balanced_mae"], -5)
        self.assertEqual(result["parent_drift24_vs_pers"]["pair_roles"]["candidate"], "DRIFT24")
        self.assertEqual(result["policy_status_counts"]["STABLE_PAIR_OVERRIDE"], 89)
        self.assertEqual(result["policy_status_counts"]["INHERITED_DRIFT24"], 1)

    def test_unsupported_fallback_retains_exact_pers(self):
        fact = rows(events=1)[0]
        fact.update(stable_pair_status="INHERITED_PERS", stable_pair_prediction=110,
                    stable_pair_support_reason="INSUFFICIENT_SUPPORT")
        result = analyze([fact])
        self.assertEqual(result["policy_status_counts"]["INHERITED_PERS"], 1)

    def test_rejects_override_without_scope_mismatch(self):
        fact = rows(events=1)[0]
        fact["parent_fallback_reason"] = "SOURCE_BREAK"
        with self.assertRaisesRegex(ValueError, "override requires supported SCOPE_MISMATCH"):
            analyze([fact])

    def test_rejects_override_without_explicit_positive_support(self):
        fact = rows(events=1)[0]
        fact["stable_pair_support_reason"] = "INSUFFICIENT_SUPPORT"
        with self.assertRaisesRegex(ValueError, "override requires supported SCOPE_MISMATCH"):
            analyze([fact])

    def test_rejects_parent_ready_drift_not_inherited_exactly(self):
        fact = rows(events=1)[0]
        fact.update(drift24_status="READY", parent_fallback_reason=None)
        with self.assertRaisesRegex(ValueError, "READY DRIFT24 must be inherited exactly"):
            analyze([fact])

    def test_rejects_method_or_label_issue_mismatch(self):
        fact = rows(events=1)[0]
        fact["stable_pair_issue_id"] = "another-issue"
        with self.assertRaisesRegex(ValueError, "share the exact issue_id"):
            analyze([fact])

    def test_rejects_target_seal_or_target_clock_mismatch(self):
        fact = rows(events=1)[0]
        fact["target_seal_id"] = 0
        with self.assertRaisesRegex(ValueError, "target_seal_id"):
            analyze([fact])
        fact = rows(events=1)[0]
        fact["label_target_at"] = "2026-11-03T00:00:00Z"
        with self.assertRaisesRegex(ValueError, "label_target_at"):
            analyze([fact])
        fact = rows(events=1)[0]
        fact["target_at"] = "2026-11-02T01:00:00Z"
        with self.assertRaisesRegex(ValueError, "target_at must equal"):
            analyze([fact])

    def test_rejects_unaccepted_or_outside_kickoff_label(self):
        fact = rows(events=1)[0]
        fact["label_status"] = "WAITING"
        with self.assertRaisesRegex(ValueError, "only accepted SCORED"):
            analyze([fact])
        fact = rows(events=1)[0]
        fact["stable_pair_status"] = "OUTSIDE_KICKOFF"
        with self.assertRaisesRegex(ValueError, "outside-kickoff"):
            analyze([fact])

    def test_rejects_duplicate_label_or_coordinate(self):
        pair = rows(events=1)
        with self.assertRaisesRegex(ValueError, "duplicate label_id"):
            analyze([pair[0], dict(pair[0], bundle_id=2, horizon_hours=48)])
        with self.assertRaisesRegex(ValueError, "duplicate bundle_id/horizon"):
            analyze([pair[0], dict(pair[0], label_id=999)])

    def test_requires_two_way_issue_bundle_relation_across_horizons(self):
        pair = rows(events=1)
        pair[1]["issue_id"] = pair[1]["pers_issue_id"] = "different-issue"
        pair[1]["drift24_issue_id"] = pair[1]["stable_pair_issue_id"] = "different-issue"
        pair[1]["label_issue_id"] = "different-issue"
        with self.assertRaisesRegex(ValueError, "bundle/event must bind to exactly one issue_id"):
            analyze(pair)

    def test_requires_common_issue_clock_across_horizons(self):
        pair = rows(events=1)
        pair[1]["issued_at"] = "2026-11-01T01:00:00Z"
        pair[1]["target_at"] = "2026-11-03T01:00:00Z"
        pair[1]["label_target_at"] = "2026-11-03T01:00:00Z"
        with self.assertRaisesRegex(ValueError, "issued_at must be common across horizons"):
            analyze(pair)


if __name__ == "__main__":
    unittest.main()
