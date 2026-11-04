from copy import deepcopy
import unittest
from ml.verify_blocked_outcome445_composite_v1 import verify,OFFICIAL


def inputs():
    primary={'http_status':200,'url':'https://www.frekwencyjny.pl/','text_truncated':False,'sha256':'a'*64,
        'retrieved_at':'2026-11-04T13:45:00+00:00','text':'02.11 18:10 02.11.2026 18:10 Zagłębie L. 1:0 Korona 3 396'}
    official={'http_status':200,'url':OFFICIAL,'final_url':OFFICIAL,'text_truncated':False,'sha256':'b'*64,
        'retrieved_at':'2026-11-04T18:24:00+00:00',
        'text':'Zagłębie\nLubin\nEkstraklasa / 13\n02 lis 2026 godz. 18:00\nvs\n1 : 0\n1 : 0\nPodsumowanie\nKorona\nKielce\nKGHM Zagłębie Lubin 1-0 Korona Kielce'}
    event={'id':445,'club_slug':'zaglebie_lubin','home_team':'KGHM Zagłębie Lubin','away_team':'Korona Kielce',
        'competition':'Ekstraklasa','kickoff_at':'2026-11-02T17:00:00+00:00'}
    return primary,official,event


class CompositeVerificationTests(unittest.TestCase):
    def test_exact_official_schedule_anchors_identity_without_guessing_primary_clock_cause(self):
        primary,official,event=inputs();before=deepcopy((primary,official,event))
        row=verify(primary,official,event,[event],'2026-11-04T18:30:00+00:00')
        self.assertEqual(row['actual_attendance'],3396);self.assertEqual(row['kickoff_at'],event['kickoff_at'])
        self.assertEqual(row['source_payload']['primary_reported_kickoff_at'],'2026-11-02T17:10:00+00:00')
        self.assertFalse(row['source_payload']['official_attendance_corroborated'])
        self.assertFalse(row['source_payload']['cause_of_time_discrepancy_verified'])
        self.assertEqual((primary,official,event),before)

    def test_wrong_official_clock_or_result_cannot_create_a_tolerance_join(self):
        for old,new in [('18:00','18:10'),('1-0','2-0')]:
            p,o,e=inputs();o['text']=o['text'].replace(old,new)
            with self.assertRaisesRegex(ValueError,'not proven'):verify(p,o,e,[e],'2026-11-04T18:30:00+00:00')

    def test_ambiguous_fixture_and_backdated_verification_are_rejected(self):
        p,o,e=inputs()
        with self.assertRaisesRegex(ValueError,'Ambiguous'):verify(p,o,e,[e,{**e,'id':999}],'2026-11-04T18:30:00+00:00')
        with self.assertRaisesRegex(ValueError,'backdate'):verify(p,o,e,[e],'2026-11-04T18:20:00+00:00')

    def test_other_fixture_or_incomplete_receipts_do_not_authorize_import(self):
        p,o,e=inputs()
        with self.assertRaises(ValueError):verify(p,{**o,'text_truncated':True},e,[e],'2026-11-04T18:30:00+00:00')
        with self.assertRaisesRegex(ValueError,'limited'):verify(p,o,{**e,'id':446},[e],'2026-11-04T18:30:00+00:00')
        p['text']=p['text'].replace('1:0','2:0')
        with self.assertRaisesRegex(ValueError,'not unique or supported'):verify(p,o,e,[e],'2026-11-04T18:30:00+00:00')


if __name__=='__main__':unittest.main()
