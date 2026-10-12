from __future__ import annotations

import unittest

from ml.context.gdelt_ngram_sample_v01 import (
    build_candidate_docs,
    contains_token,
    is_polish_lang,
    normalize,
)


class GdeltNgramSampleV01Tests(unittest.TestCase):
    def test_normalizes_polish_team_names(self):
        self.assertEqual(normalize("Lech Poznań"), "lech poznan")
        self.assertEqual(normalize("Górnik Zabrze"), "gornik zabrze")

    def test_token_matching_respects_word_boundaries(self):
        self.assertTrue(contains_token("lech zagra z leverkusen", "lech"))
        self.assertTrue(contains_token("bayer 04 leverkusen przyjedzie", "leverkusen"))
        self.assertFalse(contains_token("kolechowski tekst", "lech"))

    def test_same_document_can_match_teams_in_different_ngrams(self):
        events = [
            {
                "id": 7,
                "homeTeam": "Lech Poznań",
                "awayTeam": "Bayer 04 Leverkusen",
            }
        ]
        team_docs = {
            "Lech Poznań": {10, 20},
            "Bayer 04 Leverkusen": {20, 30},
        }
        by_event, union = build_candidate_docs(events, team_docs)
        self.assertEqual(by_event[7], {20})
        self.assertEqual(union, {20})

    def test_polish_language_variants(self):
        for value in ("pl", "POL", "Polish"):
            self.assertTrue(is_polish_lang(value))
        self.assertFalse(is_polish_lang("en"))


if __name__ == "__main__":
    unittest.main()
