from copy import deepcopy
from datetime import datetime,timezone
import json
from pathlib import Path
import tempfile
import unittest

from ml.test_structural_known_at_inputs_v1 import fixture,seal
from ml.archive_structural_known_at_inputs_v1 import VERSION as ARCHIVE_VERSION
from ml.select_structural_known_at_snapshot_v1 import select_snapshot

NOW=datetime(2026,11,4,18,tzinfo=timezone.utc)


def save(root,value):
    directory=root/('capture-'+value['export_sha256']);directory.mkdir()
    (directory/'inputs.json').write_text(json.dumps(value))
    (directory/'receipt.json').write_text(json.dumps({'version':ARCHIVE_VERSION,'status':'SOURCE_ARCHIVED_AND_RESTORED',
        'restore_verified':True,'capture_completed_at':value['completed_at'],'source_export_sha256':value['export_sha256'],
        'private_backup':{'key':'structural-known-at-inputs-v1/'+'a'*64+'.json','sha256':'a'*64,
                          'read_back_verified':True},'forecast_created':False,'official_database_write':False}))
    return directory


class AsOfArchiveTests(unittest.TestCase):
    def test_current_row_revision_does_not_replace_the_genuinely_earlier_captured_value(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);old=fixture();save(root,old)
            revised=deepcopy(old);revised['parts']['history'][0]['actual_attendance']=26000
            revised['parts']['history'][0]['updated_at']='2026-11-04T16:40:00Z';revised=seal(revised['parts'])
            revised['requested_at']='2026-11-04T16:41:00Z';revised['completed_at']='2026-11-04T16:41:10Z'
            from ml.export_structural_known_at_inputs_v1 import digest
            revised['export_sha256']=digest({k:v for k,v in revised.items() if k!='export_sha256'});save(root,revised)
            result=select_snapshot(root,'2026-11-04T16:35:00Z',now=NOW)
            self.assertEqual(result['source']['parts']['history'][0]['actual_attendance'],25000)
            later=select_snapshot(root,'2026-11-04T16:42:00Z',now=NOW)
            self.assertEqual(later['source']['parts']['history'][0]['actual_attendance'],26000)

    def test_pre_activation_missing_stale_and_future_cutoffs_do_not_fabricate_history(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);save(root,fixture())
            for cutoff in ['2026-11-04T16:30:00Z','2026-11-04T17:35:00Z']:
                result=select_snapshot(root,cutoff,now=NOW);self.assertIsNone(result['source'])
                self.assertEqual(result['status'],'NO_GENUINE_PRE_CUTOFF_SNAPSHOT')
            with self.assertRaisesRegex(ValueError,'future availability'):select_snapshot(root,'2026-11-04T19:00:00Z',now=NOW)

    def test_tampered_captured_value_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);value=fixture();directory=save(root,value)
            value['parts']['history'][0]['actual_attendance']=1
            (directory/'inputs.json').write_text(json.dumps(value))
            with self.assertRaisesRegex(ValueError,'hash mismatch'):select_snapshot(root,'2026-11-04T16:35:00Z',now=NOW)

    def test_failed_partial_archive_without_verified_receipt_is_ineligible(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);directory=save(root,fixture());(directory/'receipt.json').unlink()
            self.assertIsNone(select_snapshot(root,'2026-11-04T16:35:00Z',now=NOW)['source'])

    def test_other_experiment_recovery_cannot_be_selected_as_an_attendance_archive(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);directory=save(root,fixture());file=directory/'receipt.json';receipt=json.loads(file.read_text())
            receipt['private_backup']['key']='c1-seat-median-v1/'+'a'*64+'.json';file.write_text(json.dumps(receipt))
            with self.assertRaisesRegex(ValueError,'namespace'):select_snapshot(root,'2026-11-04T16:35:00Z',now=NOW)


if __name__=='__main__':unittest.main()
