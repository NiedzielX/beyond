from copy import deepcopy
import unittest

from ml.collect_c1_training_expansion_v1 import enrich_anchor
from ml.test_c1_training_expansion_v1 import candidate


class ExactAnchorEnrichmentTests(unittest.TestCase):
    def fixture(self):
        c = candidate(); c['prior'].update(model_spec_id='synthetic', feature_contract='synthetic-contract')
        resolved = {**c['prior'], 'status': 'ready'}
        del c['prior']['target_as_of_at']
        return c, [resolved]

    def test_actual_rpc_missing_field_is_resolved_without_input_mutation(self):
        c, resolved = self.fixture(); before = deepcopy(c)
        enriched = enrich_anchor(c, resolved)
        self.assertEqual(c, before)
        self.assertNotIn('target_as_of_at', c['prior'])
        self.assertEqual(enriched['prior']['target_as_of_at'], resolved[0]['target_as_of_at'])

    def test_changed_anchor_or_values_are_not_silently_substituted(self):
        for field in ['source_prior_id', 'p50', 'stadium_capacity', 'horizon', 'generated_at', 'feature_contract']:
            c, rows = self.fixture(); rows[0][field] = 999 if field in ['source_prior_id', 'p50', 'stadium_capacity'] else 'changed'
            with self.subTest(field=field), self.assertRaises(ValueError): enrich_anchor(c, rows)

    def test_missing_or_ambiguous_resolution_fails_closed(self):
        c, rows = self.fixture()
        for resolved in [[], rows*2]:
            with self.subTest(resolved=resolved), self.assertRaises(ValueError): enrich_anchor(c, resolved)


if __name__ == '__main__': unittest.main()
