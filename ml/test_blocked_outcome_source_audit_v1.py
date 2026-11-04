import tempfile
import unittest
from pathlib import Path
from ml.blocked_outcome_source_audit_v1 import Links,fetch,normalized


class OfficialSourceAuditTests(unittest.TestCase):
    def test_only_official_https_article_links_are_exposed(self):
        p=Links('https://www.zaglebie.com/aktualnosci');p.feed('<a href="/aktualnosci/zaglebie-korona-raport">Zagłębie – Korona</a>'
            '<a href="https://evil.invalid/zaglebie-korona">outside</a><a href="http://www.zaglebie.com/zaglebie-korona">http</a>'
            '<a href="https://user:pass@www.zaglebie.com/zaglebie-korona">credentials</a>')
        self.assertEqual(len(p.links),1);self.assertEqual(p.links[0]['url'],'https://www.zaglebie.com/aktualnosci/zaglebie-korona-raport')

    def test_unknown_public_hosts_are_rejected_before_network(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaisesRegex(ValueError,'official hosts'):fetch('https://evil.invalid/',Path(d),0)

    def test_polish_source_terms_can_be_matched_without_changing_original_evidence(self):
        self.assertEqual(normalized('ZAGŁĘBIE – Koroną'),'zaglebie – korona')


if __name__=='__main__':unittest.main()
