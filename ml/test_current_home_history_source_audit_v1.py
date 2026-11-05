import hashlib
import tempfile
from pathlib import Path
import unittest
from unittest.mock import Mock
import urllib.error
import urllib.request

from ml.current_home_history_source_audit_v1 import fetch, SOURCES, PublicRedirect, allowed_redirect, MAX_BYTES


class SourceAuditTests(unittest.TestCase):
    def response(self, raw, url=SOURCES[0]):
        response = Mock(status=200, url=url, headers={'Content-Type': 'text/html; charset=utf-8'})
        response.read.return_value = raw
        response.__enter__ = Mock(return_value=response)
        response.__exit__ = Mock(return_value=False)
        opener = Mock(); opener.open.return_value = response
        return opener

    def test_original_bytes_hash_and_actual_receipt_are_preserved_without_verification(self):
        raw = b'<h1>Motor</h1><script>12345</script><p>Public fixture</p>'
        with tempfile.TemporaryDirectory() as temp:
            result = fetch(SOURCES[0], Path(temp), 0, self.response(raw))
            self.assertEqual((Path(temp) / 'source-0.html').read_bytes(), raw)
            self.assertEqual(result['sha256'], hashlib.sha256(raw).hexdigest())
            self.assertLessEqual(result['retrieved_at'], result['receipt_completed_at'])
            self.assertFalse(result['fixture_identity_verified']); self.assertFalse(result['automatic_label_import'])
            self.assertNotIn('12345', result['text'])

    def test_unlisted_original_url_never_opens_network(self):
        opener = Mock()
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaises(ValueError): fetch('https://example.invalid/', Path(temp), 0, opener)
            opener.open.assert_not_called(); self.assertFalse(list(Path(temp).iterdir()))

    def test_cross_host_http_userinfo_and_port_redirects_are_rejected(self):
        for url in ['https://example.invalid/', 'http://frekwencyjny.pl/',
                    'https://user@www.frekwencyjny.pl/', 'https://www.frekwencyjny.pl:8443/']:
            self.assertFalse(allowed_redirect(url))
            with self.assertRaises(ValueError):
                PublicRedirect().redirect_request(urllib.request.Request(SOURCES[0]), None, 302, 'redirect', {}, url)

    def test_oversized_response_has_no_saved_or_successful_source(self):
        with tempfile.TemporaryDirectory() as temp:
            result = fetch(SOURCES[0], Path(temp), 0, self.response(b'x' * (MAX_BYTES + 1)))
            self.assertEqual(result['error_type'], 'ValueError')
            self.assertNotIn('sha256', result); self.assertFalse(list(Path(temp).iterdir()))

    def test_non_html_or_redirected_final_response_stays_unverified(self):
        with tempfile.TemporaryDirectory() as temp:
            for bad in ['content', 'host']:
                opener = self.response(b'public', 'https://example.invalid/' if bad == 'host' else SOURCES[0])
                if bad == 'content': opener.open.return_value.headers = {'Content-Type': 'application/json'}
                result = fetch(SOURCES[0], Path(temp), 0, opener)
                self.assertIn('error_type', result); self.assertNotIn('sha256', result)
            self.assertFalse(list(Path(temp).iterdir()))

    def test_network_failure_is_unknown_and_does_not_become_zero_attendance(self):
        opener = Mock(); opener.open.side_effect = urllib.error.URLError('unavailable')
        with tempfile.TemporaryDirectory() as temp:
            result = fetch(SOURCES[0], Path(temp), 0, opener)
            self.assertEqual(result['error_type'], 'URLError')
            self.assertFalse(result['fixture_identity_verified']); self.assertNotIn('actual_attendance', result)
            self.assertFalse(list(Path(temp).iterdir()))


if __name__ == '__main__': unittest.main()
