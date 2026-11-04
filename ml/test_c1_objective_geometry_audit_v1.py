import unittest

import pandas as pd

from ml.c1_objective_geometry_audit_v1 import objective_geometry


class ObjectiveGeometryTests(unittest.TestCase):
    def test_identical_person_error_has_different_occupancy_loss(self):
        r = objective_geometry(pd.DataFrame({'ticket_event_id': [1, 2], 'stadium_capacity': [10000, 40000]}))
        self.assertEqual(r['same_seat_error_small_vs_large_capacity_squared_loss_ratio'], 16)
        self.assertEqual(r['same_seat_error_small_vs_large_capacity_absolute_occupancy_loss_ratio'], 4)
        self.assertEqual(r['same_seat_error_small_vs_large_capacity_absolute_seat_loss_ratio'], 1)
        self.assertFalse(r['mae_improvement_proven'])

    def test_multiple_prefixes_do_not_increase_one_events_total_weight(self):
        r = objective_geometry(pd.DataFrame({'ticket_event_id': [1, 2, 2, 2], 'stadium_capacity': [10000, 40000, 40000, 40000]}))
        self.assertAlmostEqual(r['event_weight_mass'], 2)
        self.assertEqual(r['independent_training_events'], 2)

    def test_capacity_rescaling_preserves_relative_geometry(self):
        frame = pd.DataFrame({'ticket_event_id': [1, 2], 'stadium_capacity': [10000, 40000]})
        a = objective_geometry(frame); frame.stadium_capacity *= 3; b = objective_geometry(frame)
        self.assertEqual(a['same_seat_error_small_vs_large_capacity_squared_loss_ratio'], b['same_seat_error_small_vs_large_capacity_squared_loss_ratio'])

    def test_conflicting_capacity_for_one_event_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'conflicting'):
            objective_geometry(pd.DataFrame({'ticket_event_id': [1, 1], 'stadium_capacity': [10000, 40000]}))

    def test_invalid_capacity_or_identity_fails_closed(self):
        for field, value in [('stadium_capacity', 0), ('stadium_capacity', float('nan')),
                             ('stadium_capacity', float('inf')), ('ticket_event_id', 1.5)]:
            frame = pd.DataFrame({'ticket_event_id': [1], 'stadium_capacity': [10000]}); frame[field] = value
            with self.subTest(field=field, value=value), self.assertRaises(ValueError): objective_geometry(frame)

    def test_geometry_is_target_independent_and_does_not_mutate_frame(self):
        frame = pd.DataFrame({'ticket_event_id': [1, 2], 'stadium_capacity': [10000, 40000], 'actual_attendance': ['not parsed', object()]})
        before = frame.copy(deep=True); report = objective_geometry(frame)
        pd.testing.assert_frame_equal(frame, before)
        self.assertFalse(report['predictions_computed']); self.assertFalse(report['target_values_parsed'])
        self.assertFalse(report['training_mae_computed']); self.assertFalse(report['model_fitted'])


if __name__ == '__main__': unittest.main()
