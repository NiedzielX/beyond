"""Source-state-only synthetic checks, after the v1 contract scaffolding is applied."""
from datetime import datetime, timedelta
import json
import os
from pathlib import Path
import unittest
from urllib.parse import urlparse

import psycopg
from psycopg.types.json import Jsonb


class SourceStateContract(unittest.TestCase):
    counter = 50000

    @classmethod
    def setUpClass(cls):
        dsn = os.environ.get('DAILY_PATH_TEST_DSN', '')
        target = urlparse(dsn)
        if target.hostname not in {'127.0.0.1','localhost'} or target.path != '/daily_path_contract':
            raise RuntimeError('Only isolated localhost daily_path_contract is allowed')
        cls.db = psycopg.connect(dsn, autocommit=True)
        cls.db.execute("""
          alter table public.ticket_events add column if not exists club_slug text;
          alter table public.ticket_events add column if not exists external_event_id text;
          alter table public.ticket_events add column if not exists created_at timestamptz;
          create table private.stellis_raw_observations_v1 (
            id bigint generated always as identity primary key,
            club_slug text not null, external_event_id text not null,
            captured_at timestamptz not null, created_at timestamptz not null,
            kickoff_at timestamptz, availability_exposed boolean not null,
            available_total integer, source_version text not null, raw_metadata jsonb not null,
            promoted_ticket_event_id bigint, promoted_snapshot_id bigint, promoted_at timestamptz
          );
        """)
        root = Path(__file__).resolve().parents[2]
        cls.db.execute((root/'supabase/sql/daily_inventory_source_state_as_known_v2.sql').read_text())

    @classmethod
    def tearDownClass(cls):
        cls.db.close()

    def fixture(self, *, metadata=None, available=0, exposed=True, late_created=False,
                future_capture=False, event_late=False, promoted=False, promotion_late=False, provider='stellis'):
        type(self).counter += 1
        event = self.counter
        now = self.db.execute('select clock_timestamp()').fetchone()[0]
        cutoff, kickoff = now-timedelta(hours=1), now+timedelta(days=3)
        created = now if event_late else now-timedelta(days=5)
        self.db.execute('insert into public.ticket_events(id,kickoff_at,provider,club_slug,external_event_id,created_at) values(%s,%s,%s,%s,%s,%s)',
                        (event,kickoff,provider,'synthetic',str(event),created))
        captured = now if future_capture else cutoff-timedelta(hours=1)
        received = now if late_created else cutoff-timedelta(minutes=30)
        snapshot = event*100 if promoted else None
        promotion = (now if promotion_late else cutoff-timedelta(minutes=10)) if promoted else None
        if promoted:
            self.db.execute("insert into public.snapshots values(%s,%s,%s,%s,'stellis_visible_available')",(snapshot,event,captured,available))
        raw = self.db.execute("""insert into private.stellis_raw_observations_v1
          (club_slug,external_event_id,captured_at,created_at,kickoff_at,availability_exposed,available_total,source_version,raw_metadata,
           promoted_ticket_event_id,promoted_snapshot_id,promoted_at)
          values('synthetic',%s,%s,%s,%s,%s,%s,'synthetic-source-v2',%s,%s,%s,%s) returning id""",
          (str(event),captured,received,kickoff,exposed,available,Jsonb(metadata or {}),event if promoted else None,snapshot,promotion)).fetchone()[0]
        return event, cutoff, raw, snapshot

    def read(self, event, cutoff, role='service_role'):
        self.db.execute('set role '+role)
        try:
            return self.db.execute('select public.daily_inventory_source_state_as_known_v2(%s,%s)',(event,cutoff)).fetchone()[0]
        finally:self.db.execute('reset role')

    def test_explicit_visible_zero_and_unknown_legacy_stage_remain_zero(self):
        event,cutoff,raw,_ = self.fixture()
        row = self.read(event,cutoff)['observations'][0]
        self.assertEqual(row['raw_observation_id'],raw)
        self.assertEqual(row['available_total'],0)
        self.assertTrue(row['source_visible'])
        self.assertIsNone(row['source_active'])
        self.assertEqual(row['status'],'VISIBLE_LEGACY_STAGE_UNKNOWN')

    def test_active_visible_zero_remains_zero(self):
        event,cutoff,_,_ = self.fixture(metadata={'has_active_stage':True,'show_available_tickets_count':True})
        row = self.read(event,cutoff)['observations'][0]
        self.assertEqual(row['status'],'VISIBLE_ACTIVE');self.assertEqual(row['available_total'],0)

    def test_hidden_and_inactive_counts_are_not_model_usable_zeros(self):
        for metadata,exposed,status in [({'has_active_stage':False},True,'INACTIVE_STAGE'),
                                        ({'show_available_tickets_count':False},True,'HIDDEN_SOURCE'),
                                        ({},False,'HIDDEN_SOURCE')]:
            event,cutoff,_,_ = self.fixture(metadata=metadata,exposed=exposed)
            row = self.read(event,cutoff)['observations'][0]
            self.assertEqual(row['raw_available_total'],0)
            self.assertIsNone(row['available_total']);self.assertEqual(row['status'],status)

    def test_null_or_string_booleans_fail_closed(self):
        for metadata in ({'has_active_stage':'false'},{'show_available_tickets_count':None},['unexpected']):
            event,cutoff,_,_ = self.fixture(metadata=metadata)
            row = self.read(event,cutoff)['observations'][0]
            self.assertEqual(row['status'],'INVALID_SOURCE_METADATA');self.assertIsNone(row['available_total'])

    def test_source_capture_and_receipt_both_must_exist_by_cutoff(self):
        for options in ({'late_created':True},{'future_capture':True}):
            event,cutoff,_,_ = self.fixture(**options)
            self.assertEqual(self.read(event,cutoff)['observations'],[])

    def test_event_created_after_cutoff_is_not_historically_known(self):
        event,cutoff,_,_ = self.fixture(event_late=True)
        result = self.read(event,cutoff)
        self.assertEqual(result['status'],'EVENT_NOT_KNOWN_AS_OF');self.assertEqual(result['observations'],[])

    def test_promotion_link_created_later_is_not_backprojected(self):
        event,cutoff,_,snapshot = self.fixture(promoted=True,promotion_late=True)
        row = self.read(event,cutoff)['observations'][0]
        self.assertIsNone(row['public_snapshot_id']);self.assertIsNone(row['promotion_known_at'])
        event,cutoff,_,snapshot = self.fixture(promoted=True)
        row = self.read(event,cutoff)['observations'][0]
        self.assertEqual(row['public_snapshot_id'],snapshot)

    def test_wrong_snapshot_lineage_does_not_form_link(self):
        event,cutoff,_,snapshot = self.fixture(promoted=True)
        self.db.execute('update public.snapshots set available_total=123 where id=%s',(snapshot,))
        self.assertIsNone(self.read(event,cutoff)['observations'][0]['public_snapshot_id'])

    def test_future_and_post_kickoff_cutoffs_are_rejected(self):
        event,cutoff,_,_ = self.fixture()
        now = self.db.execute('select clock_timestamp()').fetchone()[0]
        with self.assertRaisesRegex(psycopg.Error,'INVALID_CUTOFF'):self.read(event,now+timedelta(days=1))
        self.db.execute('update public.ticket_events set kickoff_at=%s where id=%s',(now-timedelta(hours=2),event))
        with self.assertRaisesRegex(psycopg.Error,'PREMATCH'):self.read(event,cutoff)

    def test_browser_roles_are_denied_and_other_provider_is_not_reinterpreted(self):
        event,cutoff,_,_ = self.fixture(provider='roboticket')
        for role in ['anon','authenticated']:
            with self.assertRaises(psycopg.errors.InsufficientPrivilege):self.read(event,cutoff,role)
        result = self.read(event,cutoff)
        self.assertEqual(result['status'],'UNSUPPORTED_PROVIDER');self.assertEqual(result['observations'],[])

    def test_read_only_provenance_and_non_mutation(self):
        event,cutoff,raw,_ = self.fixture(promoted=True)
        before = self.db.execute('select to_jsonb(r) from private.stellis_raw_observations_v1 r where id=%s',(raw,)).fetchone()[0]
        snapshots = self.db.execute('select count(*) from public.snapshots').fetchone()[0]
        result = self.read(event,cutoff);row=result['observations'][0]
        self.assertEqual(before,self.db.execute('select to_jsonb(r) from private.stellis_raw_observations_v1 r where id=%s',(raw,)).fetchone()[0])
        self.assertEqual(snapshots,self.db.execute('select count(*) from public.snapshots').fetchone()[0])
        self.assertLessEqual(datetime.fromisoformat(row['known_at']),cutoff)
        self.assertFalse(result['production_change']);self.assertFalse(result['target_values_used'])
        self.assertFalse(result['raw_table_immutability_independently_proven'])
        directory=os.environ.get('DAILY_PATH_TEST_FEED_DIR')
        if directory:
            output=Path(directory);output.mkdir(parents=True,exist_ok=True)
            (output/'source-state.json').write_text(json.dumps(result,sort_keys=True)+'\n')


if __name__=='__main__':unittest.main()
