import tempfile
from pathlib import Path
import unittest

from ml.public_attendance_source_audit_v1 import extract, fetch, MAX_TEXT


class PublicSourceAuditTests(unittest.TestCase):
    def test_text_keeps_fixture_row_context_without_script_content(self):
        result = extract(b'<title>Public fixture</title><script>ignore these numbers 99999</script><table><tr><td>2026-10-18</td><td>Club A</td><td>Club B</td><td>12345</td></tr></table>')
        self.assertEqual(result['title'], 'Public fixture')
        self.assertIn('2026-10-18 Club A Club B 12345', result['text'])
        self.assertNotIn('99999', result['text'])

    def test_large_extracted_text_is_explicitly_truncated(self):
        result = extract(('<p>'+'a'*(MAX_TEXT+100)+'</p>').encode())
        self.assertEqual(len(result['text']), MAX_TEXT); self.assertTrue(result['text_truncated'])

    def test_arbitrary_url_is_rejected_before_network_or_file_write(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaisesRegex(ValueError, 'fixed declared'): fetch('https://example.invalid/', Path(d), 0)
            self.assertFalse(list(Path(d).iterdir()))


if __name__ == '__main__': unittest.main()
