from copy import deepcopy
from pathlib import Path
import unittest

from ml.daily_path_coefficient_audit_v1 import build_audit, coefficient_blocks, explain_point
from ml.demand_engine.daily_inventory_path_model_v1 import artifact_sha256, load_model, predict_path
from ml.demand_engine.test_daily_inventory_path_model_v1 import issue


def artifact(coefficients=None):
    result=load_model(Path(__file__).parent/'artifacts/daily_inventory_path_v1.json')
    result['coefficients']=[0.]*250
    for index,value in (coefficients or {}).items():result['coefficients'][index]=value
    result['model_sha256']=artifact_sha256(result)
    return result


class CoefficientAuditTests(unittest.TestCase):
    def test_linear_quadratic_and_scale_reconcile_exactly(self):
        model=artifact({0:-.07,125:-.49})
        current=issue(days=4)
        point=predict_path(current,model)[0]
        result=explain_point(current,point,model)
        self.assertEqual(result['prefix_scale'],1060)
        self.assertAlmostEqual(result['additive_contributions_places']['linear_constant'],-10.6)
        self.assertAlmostEqual(result['additive_contributions_places']['quadratic_constant'],-10.6)
        self.assertAlmostEqual(result['issued_predicted_available_total'],978.8)
        self.assertLess(result['reconstruction_absolute_difference'],1e-9)

    def test_relative_values_and_masks_are_separate_blocks(self):
        model=artifact({6:.7,65:7})
        current=issue(days=4);point=predict_path(current,model)[0]
        result=explain_point(current,point,model)
        self.assertAlmostEqual(result['additive_contributions_places']['linear_relative_inventory_values'],2)
        self.assertAlmostEqual(result['additive_contributions_places']['linear_observed_bin_masks'],1060)
        blocks=coefficient_blocks(model)
        self.assertEqual(blocks['linear_relative_inventory_values']['nonzero_coefficient_count'],1)
        self.assertEqual(blocks['quadratic_relative_inventory_values']['coefficient_count'],60)

    def test_clipped_zero_retains_unclipped_decline_and_adjustment(self):
        model=artifact({0:-1000})
        current=issue(days=4);point=predict_path(current,model)[0]
        result=explain_point(current,point,model)
        self.assertEqual(result['issued_predicted_available_total'],0)
        self.assertLess(result['unclipped_available_total'],0)
        self.assertAlmostEqual(result['zero_clip_adjustment'],-result['unclipped_available_total'])

    def test_mismatched_issued_prediction_or_lineage_is_rejected(self):
        model=artifact();current=issue(days=4);point=predict_path(current,model)[0]
        for key,value in [('predicted_available_total',999),('baseline_available_total',999),
                          ('model_sha256','wrong'),('prefix_sha256','wrong'),('target_at',current['issued_as_of_at'])]:
            bad=deepcopy(point);bad[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):explain_point(current,bad,model)

    def test_corrupt_model_is_not_explained_as_valid(self):
        model=artifact();model['coefficients'][0]=1
        with self.assertRaisesRegex(ValueError,'hash mismatch'):coefficient_blocks(model)

    def test_report_does_not_read_scores_as_explanatory_inputs_or_mutate_inputs(self):
        model=artifact();current=issue(days=4)
        attempt={'attempt_id':1,'artifact':model,'issue':current}
        points=[{**point,'attempt_id':1,'score':{'target_available_total':'DO_NOT_USE'}} for point in predict_path(current,model)]
        before=deepcopy((attempt,points,model))
        report=build_audit([attempt],points,model)
        self.assertEqual(report['prediction_count'],3)
        self.assertEqual(report['independent_event_count'],1)
        self.assertFalse(report['target_values_used']);self.assertFalse(report['accuracy_evaluated'])
        self.assertEqual((attempt,points,model),before)
        with self.assertRaisesRegex(ValueError,'Orphan'):build_audit([],points,model)


if __name__=='__main__':unittest.main()
