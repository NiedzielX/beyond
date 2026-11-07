from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock,patch

from ml.c1_history_scoring_adapter_v1 import persist_scores,recover_score_directory
from ml import run_postmatch_outcome_closure_v3 as closure


class ImmutableScorePathTests(unittest.TestCase):
    def row(self,event,snapshot,value=1):
        return {'ticket_event_id':event,'source_snapshot_id':snapshot,'absolute_errors':{'history_policy':value}}

    def test_multiple_events_and_prefixes_get_distinct_immutable_files(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);rows=[self.row(1,10),self.row(1,11),self.row(2,20)]
            persist_scores(root,rows)
            self.assertTrue((root/'scores').is_dir())
            self.assertEqual({p.name for p in (root/'scores').glob('*.json')},
                {'event-1-snapshot-10.json','event-1-snapshot-11.json','event-2-snapshot-20.json'})
            before={p.name:p.read_bytes() for p in (root/'scores').glob('*.json')}
            persist_scores(root,rows)
            self.assertEqual(before,{p.name:p.read_bytes() for p in (root/'scores').glob('*.json')})

    def test_confirmed_score_revision_never_overwrites_original(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);persist_scores(root,[self.row(1,10)])
            path=root/'scores/event-1-snapshot-10.json';before=path.read_bytes()
            with self.assertRaisesRegex(ValueError,'never overwrite'):persist_scores(root,[self.row(1,10,2)])
            self.assertEqual(path.read_bytes(),before)

    def test_preexisting_malformed_directory_path_is_preserved_for_review(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);(root/'scores').write_text('previous evidence')
            with self.assertRaisesRegex(ValueError,'preserve'):persist_scores(root,[self.row(1,10)])
            self.assertEqual((root/'scores').read_text(),'previous evidence')

    def test_missing_and_invalid_ids_cannot_create_score_filenames(self):
        for row in [{},{'ticket_event_id':True,'source_snapshot_id':10},self.row(1,'../x'),self.row(0,1)]:
            with tempfile.TemporaryDirectory() as temp:
                with self.assertRaises(ValueError):persist_scores(Path(temp),[row])
                self.assertEqual(list(Path(temp).iterdir()),[])


class VersionedClosureTests(unittest.TestCase):
    def test_v3_pins_adapter_without_changing_original_source_contract_or_slots(self):
        before=closure.base.contract('branch','a'*40)
        new=closure.contract('branch','a'*40)
        self.assertEqual(new['version'],'postmatch-outcome-closure-v3')
        self.assertEqual(new['slots'],before['slots']);self.assertEqual(new['until'],before['until'])
        self.assertTrue(all(new['source_hashes'][key]==value for key,value in before['source_hashes'].items()))
        self.assertIn('ml/c1_history_scoring_adapter_v1.py',new['source_hashes'])
        self.assertFalse(new['production_change']);self.assertEqual(new['live_adjustment'],0)
        self.assertEqual(closure.base.contract('branch','a'*40),before)

    def test_actual_scoring_routes_history_through_the_explicit_path_adapter(self):
        response=Mock(returncode=0,stdout='{"status":"CYCLE_VERIFIED","synthetic_only":true}')
        with patch('ml.c1_outcome_scoring_bridge_v1.run_scorers',return_value={}),patch.object(closure.base,'score_support_only',return_value={}),patch.object(closure.subprocess,'run',return_value=response) as execute:
            result=closure.score_unchanged()
        modules=[call.args[0][2] for call in execute.call_args_list]
        self.assertEqual(modules,['ml.c1_history_scoring_adapter_v1','ml.run_structural_history_refresh_v1'])
        self.assertEqual(result['history']['status'],'CYCLE_VERIFIED')


class PreservedPartialScoreRecoveryTests(unittest.TestCase):
    def prepare(self,root):
        import hashlib
        row={'ticket_event_id':448,'source_snapshot_id':123,'actual_attendance':31849.0}
        raw=(json.dumps(row,sort_keys=True,indent=2)+'\n').encode();(root/'scores').write_bytes(raw)
        receipt={'original_score_sha256':hashlib.sha256(raw).hexdigest(),'key':'private-verified-original',
                 'independent_remote_decompression_verified':True,'read_back_verified':True}
        return row,raw,receipt

    def test_exact_replayed_original_is_archived_and_relocated_without_changing_bytes(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);row,raw,receipt=self.prepare(root)
            result=recover_score_directory(root,[row],receipt)
            self.assertEqual(result['status'],'RELOCATED_IDENTICALLY')
            self.assertEqual((root/'scores/event-448-snapshot-123.json').read_bytes(),raw)
            self.assertEqual(next(root.glob('score-path-original-*.json')).read_bytes(),raw)
            self.assertEqual(recover_score_directory(root,[row],receipt)['status'],'ALREADY_RELOCATED_IDENTICALLY')

    def test_unverified_backup_unknown_or_duplicate_expected_score_cannot_move_original(self):
        for mode in ['backup','changed','duplicate']:
            with tempfile.TemporaryDirectory() as temp:
                root=Path(temp);row,raw,receipt=self.prepare(root);expected=[row]
                if mode=='backup':receipt['read_back_verified']=False
                if mode=='changed':expected=[{**row,'actual_attendance':1.0}]
                if mode=='duplicate':expected=[row,row]
                with self.assertRaises(ValueError):recover_score_directory(root,expected,receipt)
                self.assertTrue((root/'scores').is_file());self.assertEqual((root/'scores').read_bytes(),raw)

    def test_crash_between_archive_and_directory_swap_resumes_from_verified_prepared_bytes(self):
        import os
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);row,raw,receipt=self.prepare(root);rename=os.rename;calls=[]
            def interrupt(src,dst):
                calls.append(1)
                if len(calls)==2:raise OSError('simulated interruption')
                return rename(src,dst)
            with patch('ml.c1_history_scoring_adapter_v1.os.rename',side_effect=interrupt):
                with self.assertRaises(OSError):recover_score_directory(root,[row],receipt)
            self.assertFalse((root/'scores').exists());self.assertEqual(next(root.glob('score-path-original-*.json')).read_bytes(),raw)
            self.assertEqual(recover_score_directory(root,[row],receipt)['status'],'RELOCATED_IDENTICALLY')
            self.assertEqual((root/'scores/event-448-snapshot-123.json').read_bytes(),raw)

    def test_active_collector_lock_blocks_relocation(self):
        import fcntl
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);row,raw,receipt=self.prepare(root)
            with (root/'watcher.lock').open('a') as lock:
                fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
                with self.assertRaises(BlockingIOError):recover_score_directory(root,[row],receipt)
            self.assertEqual((root/'scores').read_bytes(),raw)


if __name__=='__main__':unittest.main()
