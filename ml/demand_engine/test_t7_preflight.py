from datetime import datetime
import unittest
from zoneinfo import ZoneInfo

from ml.demand_engine.t7_preflight import T7EvidenceError, validate_t7_evidence

WARSAW = ZoneInfo("Europe/Warsaw")


def evidence_fixture() -> dict:
    teams = [
        "lech", "korona", "gornik_zabrze", "legia", "wisla_krakow",
        "pogon", "zaglebie_lubin", "piast", "gks_katowice", "jagiellonia",
        "wisla_plock", "widzew", "wieczysta", "cracovia", "radomiak",
        "slask", "motor", "rakow",
    ]
    return {
        "ticket_event_id": 5,
        "season": "2026/2027",
        "home_team": "Lech Poznań",
        "away_team": "Korona Kielce",
        "competition": "Ekstraklasa",
        "target_kickoff_at": "2026-10-18T17:30:00+02:00",
        "home_team_key": "lech",
        "opponent_key": "korona",
        "target_round_no": 11,
        "total_rounds": 34,
        "league_team_keys": teams,
        "completed_results": [
            {
                "kickoff_at": "2026-10-10T17:30:00+02:00",
                "home_team_key": "slask",
                "away_team_key": "lech",
                "home_goals": 0,
                "away_goals": 1,
            }
        ],
        "current_season_home_attendance": [
            {
                "season": "2026/2027",
                "match_date": "2026-09-20T20:15:00+02:00",
                "opponent_key": "radomiak",
                "attendance": 19478,
                "capacity_constrained_for_model": False,
            }
        ],
        "expected_visible_league_results": 1,
        "expected_visible_home_attendance_rows": 1,
        "sources": {
            "schedule": ["https://example.com/schedule"],
            "league_results": ["https://example.com/results"],
            "home_attendance": ["https://example.com/attendance"],
            "verified_at": "2026-10-11T17:31:00+02:00",
        },
    }


class T7PreflightTest(unittest.TestCase):
    def setUp(self) -> None:
        self.kickoff = datetime(2026, 10, 18, 17, 30, tzinfo=WARSAW)

    def validate(self, evidence: dict, persist: bool = True):
        return validate_t7_evidence(
            evidence=evidence,
            ticket_event_id=5,
            home_team="Lech Poznań",
            away_team="Korona Kielce",
            competition="Ekstraklasa",
            kickoff_at=self.kickoff,
            persist=persist,
        )

    def test_complete_persistence_evidence_passes(self) -> None:
        result = self.validate(evidence_fixture())
        self.assertEqual(result["persistence_preflight"], "passed")
        self.assertEqual(result["cutoff_local_date"], "2026-10-11")
        self.assertEqual(result["visible_league_results"], 1)
        self.assertEqual(result["visible_home_attendance_rows"], 1)

    def test_persistence_requires_independently_expected_counts(self) -> None:
        evidence = evidence_fixture()
        del evidence["expected_visible_league_results"]
        with self.assertRaisesRegex(T7EvidenceError, "expected_visible_league_results"):
            self.validate(evidence)

    def test_persistence_requires_source_audit_block(self) -> None:
        evidence = evidence_fixture()
        del evidence["sources"]
        with self.assertRaisesRegex(T7EvidenceError, "sources audit block"):
            self.validate(evidence)

    def test_result_on_t7_calendar_date_is_rejected(self) -> None:
        evidence = evidence_fixture()
        evidence["completed_results"][0]["kickoff_at"] = "2026-10-11T12:00:00+02:00"
        with self.assertRaisesRegex(T7EvidenceError, "strict T-7 calendar-date semantics"):
            self.validate(evidence)

    def test_home_attendance_at_or_after_exact_t7_is_rejected(self) -> None:
        evidence = evidence_fixture()
        evidence["current_season_home_attendance"][0]["match_date"] = (
            "2026-10-11T17:30:00+02:00"
        )
        with self.assertRaisesRegex(T7EvidenceError, "not known before exact T-7"):
            self.validate(evidence)

    def test_dry_run_can_omit_source_manifest_and_expected_counts(self) -> None:
        evidence = evidence_fixture()
        del evidence["sources"]
        del evidence["expected_visible_league_results"]
        del evidence["expected_visible_home_attendance_rows"]
        result = self.validate(evidence, persist=False)
        self.assertEqual(result["persistence_preflight"], "dry_run_passed")


if __name__ == "__main__":
    unittest.main()
