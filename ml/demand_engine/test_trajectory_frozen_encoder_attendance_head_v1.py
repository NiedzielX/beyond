import unittest

import numpy as np

from ml.demand_engine.trajectory_frozen_encoder_attendance_head_v1 import (
    CORRECTION_RATIO_CAP,
    PRECOMMIT_ID,
    RIDGE_ALPHA,
    build_encoder_sequence_from_pairs_v1,
    fit_attendance_head_v1,
)


class FrozenEncoderAttendanceHeadV1Test(unittest.TestCase):
    def test_protocol_is_frozen(self) -> None:
        self.assertEqual(PRECOMMIT_ID, "trajectory-frozen-encoder-ridge-ratio-head-v1")
        self.assertEqual(RIDGE_ALPHA, 10.0)
        self.assertEqual(CORRECTION_RATIO_CAP, 0.10)

    def test_sequence_uses_last_168h_context_without_forward_fill(self) -> None:
        # Chronological earliest -> latest, represented as decreasing hours-to-kickoff.
        pairs = [
            [400.0, 1000],
            [330.0, 950],
            [300.0, 930],
            [250.0, 900],
            [220.0, 880],
            [190.0, 860],
            [170.0, 840],
            [168.0, 830],
        ]
        sequence = build_encoder_sequence_from_pairs_v1(pairs, horizon="T-7")
        # T-7 source is 168h; context includes only <=336h-to-kickoff.
        self.assertEqual(sequence.shape[1], 4)
        self.assertEqual(sequence.shape[0], 7)
        self.assertAlmostEqual(float(sequence[0, 1]), 0.95)
        self.assertAlmostEqual(float(sequence[-1, 0]), 168.0 / 1440.0)

    def test_fit_requires_exact_10_event_19_row_cohort(self) -> None:
        rng = np.random.default_rng(17)
        event_ids = np.asarray([1,2,3,4,5,6,7,8,9] + [10]*10, dtype=int)
        embeddings = rng.normal(size=(19, 8))
        structural = np.full(19, 10000.0)
        actual = np.linspace(9000, 11000, 19)
        identities = [{"ticket_event_id": int(event_ids[i]), "horizon": "T-1"} for i in range(19)]
        head = fit_attendance_head_v1(
            embeddings=embeddings,
            structural_p50=structural,
            actual_attendance=actual,
            event_ids=event_ids,
            fit_identities=identities,
            encoder_artifact_sha256="a"*64,
            encoder_source_pt_sha256="b"*64,
        )
        self.assertEqual(head.fit_row_count, 19)
        self.assertEqual(len(head.fit_event_ids), 10)
        self.assertEqual(len(head.ridge_coef), 8)

    def test_prediction_is_capped(self) -> None:
        from ml.demand_engine.trajectory_frozen_encoder_attendance_head_v1 import FrozenAttendanceHeadV1
        head = FrozenAttendanceHeadV1(
            precommit_id=PRECOMMIT_ID,
            encoder_artifact_sha256="a"*64,
            encoder_source_pt_sha256="b"*64,
            fit_manifest_sha256="c"*64,
            alpha=RIDGE_ALPHA,
            correction_ratio_cap=CORRECTION_RATIO_CAP,
            scaler_mean=(0.0,)*8,
            scaler_std=(1.0,)*8,
            ridge_coef=(10.0,)*8,
            ridge_intercept=0.0,
            fit_event_ids=tuple(range(1,11)),
            fit_row_count=19,
        )
        self.assertEqual(head.predict_ratio(np.ones(8)), 0.10)
        self.assertEqual(head.predict_ratio(-np.ones(8)), -0.10)


if __name__ == "__main__":
    unittest.main()
