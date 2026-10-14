from __future__ import annotations

import unittest

from ml.context.gdelt_ngram_sample_v02 import (
    build_event_doc_sets,
    contains_token,
    is_polish_lang,
    normalize,
)


class GdeltNgramSampleV02Tests(unittest.TestCase):
    def test_normalizes_polish_names(self):
        self.assertEqual(normalize("Pogoń Szczecin"), "pogon szczecin")
        self.assertEqual(normalize("Raków Częstochowa"), "rakow czestochowa")

    def test_word_boundaries(self):
        self.assertTrue(contains_token("lech poznan gra dzis", "lech poznan"))
        self.assertFalse(contains_token("kolechowski tekst", "lech"))

    def test_broad_union_is_distinct_from_exact_pair(self):
        events = [{"id": 7, "homeTeam": "Lech Poznań", "awayTeam": "Bayer 04 Leverkusen"}]
        all_docs = {
            "Lech Poznań": {1, 2},
            "Bayer 04 Leverkusen": {2, 3},
        }
        strong_docs = {
            "Lech Poznań": {1},
            "Bayer 04 Leverkusen": {3},
        }
        result = build_event_doc_sets(events, all_docs, strong_docs)[7]
        self.assertEqual(result["pair"], {2})
        self.assertEqual(result["union"], {1, 3})
        self.assertEqual(result["home"], {1})
        self.assertEqual(result["away"], {3})

    def test_polish_language_variants(self):
        for value in ("pl", "POL", "Polish"):
            self.assertTrue(is_polish_lang(value))
        self.assertFalse(is_polish_lang("en"))


if __name__ == "__main__":
    unittest.main()
