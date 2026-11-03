from copy import deepcopy
from datetime import datetime, timedelta, timezone
import unittest

from ml.mae03_context_evidence_audit_v1 import audit, feature_status


CHECKED = "2026-11-03T20:00Z"
KICKOFF = datetime(2026, 10, 25, 16, tzinfo=timezone.utc)


def snapshot(event=1, checkpoint="T-24h", value=0):
    hours = {"T-24h": 24, "T-3d": 72}[checkpoint]
    cutoff = KICKOFF-timedelta(hours=hours)
    return {"id": event*10+hours, "ticket_event_id": event, "checkpoint_code": checkpoint,
            "checkpoint_at": cutoff.isoformat(), "captured_at": (cutoff+timedelta(minutes=5)).isoformat(),
            "created_at": (cutoff+timedelta(minutes=5)).isoformat(), "capture_mode": "prospective",
            "metadata": {"kickoff_at": KICKOFF.isoformat(), "club_slug": "club"+str(event % 5)},
            "baseline_historical_p50": 1000, "baseline_forecast_id": event,
            "baseline_forecast_generated_at": (cutoff-timedelta(hours=1)).isoformat(),
            "baseline_model_version": "baseline-v1", "baseline_historical_model": "structural-v1",
            "context_features": {"hype.media_attention": {"status": "observed", "numeric_value": value,
                "observed_at": cutoff.isoformat(), "source_observed_at": cutoff.isoformat(),
                "source_name": "source-v2", "source_record_key": str(event)}}}


def outcome(event=1):
    # No attendance values are required or supplied to the audit.
    return {"ticket_event_id": event, "confirmed_at": (KICKOFF+timedelta(hours=4)).isoformat()}


class ContextEvidenceTests(unittest.TestCase):
    def test_many_events_with_zero_feature_have_no_variance(self):
        report = audit([snapshot(n) for n in range(1, 9)], [outcome(n) for n in range(1, 9)], CHECKED)
        group = report["feature_source_checkpoint_groups"][0]
        self.assertEqual(group["paired_event_count"], 8)
        self.assertEqual(group["paired_zero_count"], 8)
        self.assertEqual(group["screening_status"], "NO_VARIANCE")
        self.assertFalse(report["model_fit_performed"])

    def test_unknown_or_blocked_numeric_zero_is_not_an_observed_zero(self):
        rows = [snapshot(1), snapshot(2), snapshot(3)]
        rows[1]["context_features"]["hype.media_attention"]["status"] = "unknown"
        rows[2]["context_features"]["hype.media_attention"]["status"] = "blocked_external_access"
        report = audit(rows, [outcome(n) for n in range(1, 4)], CHECKED)
        self.assertEqual(report["feature_source_checkpoint_groups"][0]["paired_zero_count"], 1)
        self.assertEqual(report["feature_status_counts"]["unknown"], 1)
        self.assertEqual(report["feature_status_counts"]["blocked_external_access"], 1)

    def test_multiple_checkpoints_do_not_create_independent_events(self):
        report = audit([snapshot(), snapshot(checkpoint="T-3d")], [outcome()], CHECKED)
        self.assertEqual(report["distinct_paired_events_any_checkpoint"], 1)
        self.assertEqual(len(report["feature_source_checkpoint_groups"]), 2)

    def test_duplicate_checkpoint_and_outcome_rejected(self):
        with self.assertRaisesRegex(ValueError, "Duplicate event/checkpoint"):
            audit([snapshot(), snapshot()], [outcome()], CHECKED)
        with self.assertRaisesRegex(ValueError, "Duplicate confirmed outcome"):
            audit([snapshot()], [outcome(), outcome()], CHECKED)

    def test_late_or_premature_capture_is_not_prospective(self):
        for minutes in (-1, 31):
            row = snapshot()
            row["captured_at"] = (KICKOFF-timedelta(hours=24)+timedelta(minutes=minutes)).isoformat()
            report = audit([row], [outcome()], CHECKED)
            self.assertEqual(report["capture_counts"]["OUTSIDE_PROSPECTIVE_CAPTURE_WINDOW"], 1)
            self.assertEqual(report["distinct_paired_events_any_checkpoint"], 0)

    def test_retrospective_rows_remain_separate(self):
        row = snapshot(); row["capture_mode"] = "retrospective_point_in_time"
        report = audit([row], [outcome()], CHECKED)
        self.assertEqual(report["capture_counts"]["RETROSPECTIVE_EXCLUDED"], 1)
        self.assertEqual(report["feature_source_checkpoint_groups"], [])

    def test_future_context_source_time_rejected_at_exact_boundary(self):
        row = snapshot(); feature = row["context_features"]["hype.media_attention"]
        cutoff = KICKOFF-timedelta(hours=24)
        self.assertEqual(feature_status(feature, cutoff), "OBSERVED_NUMERIC_CAPTURE_TIME_VALID")
        feature["source_observed_at"] = (cutoff+timedelta(microseconds=1)).isoformat()
        self.assertEqual(feature_status(feature, cutoff), "OBSERVATION_AFTER_CUTOFF")

    def test_future_baseline_and_missing_lineage_do_not_form_pairs(self):
        for change in ({"baseline_forecast_generated_at": KICKOFF.isoformat()}, {"baseline_forecast_id": None}):
            row = snapshot(); row.update(change)
            report = audit([row], [outcome()], CHECKED)
            self.assertEqual(report["distinct_paired_events_any_checkpoint"], 0)
            self.assertEqual(report["feature_source_checkpoint_groups"], [])

    def test_source_and_baseline_versions_are_not_pooled(self):
        rows = [snapshot(n, value=n) for n in range(1, 9)]
        for row in rows[4:]:
            row["context_features"]["hype.media_attention"]["source_name"] = "other-source"
        report = audit(rows, [outcome(n) for n in range(1, 9)], CHECKED)
        self.assertEqual(len(report["feature_source_checkpoint_groups"]), 2)
        self.assertTrue(all(g["screening_status"] == "INSUFFICIENT_EVENTS" for g in report["feature_source_checkpoint_groups"]))
        for row in rows[2:4]: row["baseline_model_version"] = "other-baseline"
        report = audit(rows, [outcome(n) for n in range(1, 9)], CHECKED)
        self.assertEqual(len(report["feature_source_checkpoint_groups"]), 3)

    def test_screening_pass_is_not_model_permission_or_ingestion_proof(self):
        report = audit([snapshot(n, value=n) for n in range(1, 9)], [outcome(n) for n in range(1, 9)], CHECKED)
        group = report["feature_source_checkpoint_groups"][0]
        self.assertEqual(group["screening_status"], "CANDIDATE_FOR_PRECOMMIT_ONLY")
        self.assertFalse(group["model_fit_authorized"])
        self.assertFalse(group["independent_original_ingestion_time_proven"])

    def test_unconfirmed_or_too_early_outcome_is_not_a_label_pair(self):
        for when in ("2026-11-04T20:00Z", KICKOFF.isoformat(), "invalid"):
            report = audit([snapshot()], [{"ticket_event_id": 1, "confirmed_at": when}], CHECKED)
            self.assertEqual(report["feature_source_checkpoint_groups"][0]["paired_event_count"], 0)

    def test_genuine_post_match_confirmation_before_sync_wait_is_retained(self):
        confirmed = (KICKOFF+timedelta(hours=2, minutes=57)).isoformat()
        report = audit([snapshot()], [{"ticket_event_id": 1, "confirmed_at": confirmed}], CHECKED)
        self.assertEqual(report["feature_source_checkpoint_groups"][0]["paired_event_count"], 1)

    def test_one_nonzero_event_does_not_supply_every_training_fold(self):
        rows = [snapshot(n, value=int(n == 1)) for n in range(1, 9)]
        report = audit(rows, [outcome(n) for n in range(1, 9)], CHECKED)
        group = report["feature_source_checkpoint_groups"][0]
        self.assertEqual(group["paired_distinct_values"], 2)
        self.assertEqual(group["loeo_min_training_distinct_values"], 1)
        self.assertEqual(group["screening_status"], "INSUFFICIENT_GROUPED_VARIATION")

    def test_nonfinite_or_boolean_numeric_value_rejected(self):
        cutoff = KICKOFF-timedelta(hours=24)
        for value in (True, float("nan"), float("inf")):
            feature = snapshot(value=value)["context_features"]["hype.media_attention"]
            self.assertEqual(feature_status(feature, cutoff), "INVALID_NUMERIC_VALUE")

    def test_input_snapshots_remain_unchanged(self):
        rows = [snapshot()]; original = deepcopy(rows)
        audit(rows, [outcome()], CHECKED)
        self.assertEqual(rows, original)


if __name__ == "__main__":
    unittest.main()
