import unittest

from ml.watch_c1_training_expansion_v1 import ExpansionStorage, validate_bounds


class ExpansionWorkerBoundsTests(unittest.TestCase):
    def test_deadline_and_polling_are_explicit_and_bounded(self):
        validate_bounds('2026-11-06T20:30:00Z', 900, '2026-11-04T13:00:00Z')
        for until, interval in [('2026-11-08T13:00:00Z', 900), ('2026-11-04T12:00:00Z', 900),
                                ('2026-11-05T13:00:00Z', 1), ('2026-11-05T13:00:00Z', 3600)]:
            with self.subTest(until=until, interval=interval), self.assertRaises(ValueError):
                validate_bounds(until, interval, '2026-11-04T13:00:00Z')

    def test_backup_cannot_write_original_lane_or_latest_manifest(self):
        self.assertEqual(ExpansionStorage._key('c1-expansion-v1/'+'a'*64+'.json'), 'c1-expansion-v1/'+'a'*64+'.json')
        for path in ['manifests/'+'a'*64+'.json', 'drift-v1/'+'a'*64+'.json', 'c1-expansion-v1/../../latest.json']:
            with self.subTest(path=path), self.assertRaises(ValueError): ExpansionStorage._key(path)


if __name__ == '__main__': unittest.main()
