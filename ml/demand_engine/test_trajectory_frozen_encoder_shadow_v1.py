import unittest

from ml.run_trajectory_frozen_encoder_shadow_v1 import (
    DATASET_VERSION,
    MODEL_VERSION,
    PRECOMMIT_ID,
    SUPPORTED_DAYS,
)


class FrozenEncoderShadowV1Test(unittest.TestCase):
    def test_candidate_identity_is_frozen(self) -> None:
        self.assertEqual(MODEL_VERSION, "trajectory-frozen-encoder-ridge-ratio-head-v1")
        self.assertEqual(PRECOMMIT_ID, MODEL_VERSION)
        self.assertEqual(DATASET_VERSION, "trajectory-frozen-encoder-shadow-input-v1")
        self.assertEqual(SUPPORTED_DAYS, (7, 3, 1))


if __name__ == "__main__":
    unittest.main()
