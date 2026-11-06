from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock

from ml.watch_structural_history_refresh_v1 import run_once


class ClockRetryTests(unittest.TestCase):
    def test_only_actual_new_evidence_clock_failure_allows_one_unchanged_retry(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);folder=root/'evidence';folder.mkdir();calls=[]
            def cycle(*args):
                calls.append(1)
                if len(calls)==1:
                    (folder/'new.json').write_text('{"issued_at":"actual"}')
                    raise ValueError('New actual forecast clock invalid')
                return {'status':'CYCLE_VERIFIED'}
            result=run_once(root,None,None,cycle)
            self.assertEqual(len(calls),2);self.assertTrue(result['unchanged_later_clock_retry'])
            self.assertEqual(result['new_evidence_first_pass'],1)

    def test_without_new_evidence_or_with_another_error_there_is_no_retry(self):
        for message in ['New actual forecast clock invalid','Different source hash']:
            with tempfile.TemporaryDirectory() as temp:
                cycle=Mock(side_effect=ValueError(message))
                with self.assertRaises(ValueError):run_once(Path(temp),None,None,cycle)
                cycle.assert_called_once()

    def test_changed_evidence_on_retry_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);folder=root/'evidence';folder.mkdir();calls=[]
            def cycle(*args):
                calls.append(1);(folder/'new.json').write_text(str(len(calls)))
                if len(calls)==1:raise ValueError('New actual forecast clock invalid')
                return {}
            with self.assertRaisesRegex(ValueError,'Evidence changed'):run_once(root,None,None,cycle)


if __name__=='__main__':unittest.main()
