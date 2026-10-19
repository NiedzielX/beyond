#!/usr/bin/env python3
import json
import unittest
from pathlib import Path

AUDIT_PATH = Path("ml/artifacts/d2_prospective_capacity_audit_v1.json")
EXPECTED_VERSION = "d2-prospective-capacity-audit-2026-10-19-v1"
EXPECTED_TRACKED = {
    "cracovia": 15016,
    "gkskatowice": 15048,
    "gornikzabrze": 28236,
    "jagiellonia": 22372,
    "lech": 43269,
    "legia": 31006,
    "pogonszczecin": 21163,
    "slaskwroclaw": 43708,
    "wisla_plock": 15004,
    "wislakrakow": 33130,
    "zaglebie_lubin": 16086,
}


class D2ProspectiveCapacityAuditV1Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.audit = json.loads(AUDIT_PATH.read_text())

    def test_audit_version_scope_and_season_are_frozen(self) -> None:
        self.assertEqual(self.audit["audit_version"], EXPECTED_VERSION)
        self.assertEqual(self.audit["competition_key"], "ekstraklasa")
        self.assertEqual(self.audit["season"], "2026/2027")

    def test_all_current_tracked_home_clubs_are_explicit(self) -> None:
        clubs = self.audit["clubs"]
        self.assertEqual(set(clubs), set(EXPECTED_TRACKED))
        for club_slug, expected_capacity in EXPECTED_TRACKED.items():
            with self.subTest(club_slug=club_slug):
                row = clubs[club_slug]
                self.assertEqual(int(row["capacity"]), expected_capacity)
                self.assertEqual(row["valid_from"], "2026-07-01")
                self.assertIsNone(row["valid_to"])
                self.assertIn(row["verification_status"], {"verified", "carry_forward"})
                self.assertTrue(str(row["source_name"]).strip())
                self.assertTrue(str(row["source_url"]).strip())

    def test_new_delayed_label_clubs_are_verified_not_silent_fallbacks(self) -> None:
        clubs = self.audit["clubs"]
        self.assertEqual(clubs["gornikzabrze"]["verification_status"], "verified")
        self.assertEqual(clubs["gornikzabrze"]["capacity"], 28236)
        self.assertEqual(clubs["zaglebie_lubin"]["verification_status"], "verified")
        self.assertEqual(clubs["zaglebie_lubin"]["capacity"], 16086)
        self.assertEqual(clubs["wisla_plock"]["verification_status"], "verified")
        self.assertEqual(clubs["wisla_plock"]["capacity"], 15004)

    def test_legacy_stage0_audit_is_not_replaced(self) -> None:
        rules = " ".join(self.audit["rules"])
        self.assertIn("does not replace", rules)
        self.assertIn("d2_stage0_capacity_audit_v1.json", rules)


if __name__ == "__main__":
    unittest.main()
