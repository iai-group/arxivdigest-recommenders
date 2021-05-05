import unittest
from typing import List
from arxivdigest_recommenders.venue_based_recommender import VenueBasedRecommender
from arxivdigest_recommenders import config


authors = [
    {
        "author": {},
        "papers": [
            {"venue": venue} for venue in ("a", "a", "b", "c", "d", "e", "f", "b")
        ],
    },
    {"author": {}, "papers": [{"venue": "g"}]},
]
user_representations = [[4, 2, 0, 0, 3, 1], [1, 1, 0, 0, 0, 0]]


class TestVenueBasedRecommender(unittest.TestCase):
    recommender: VenueBasedRecommender = None
    author_representations: List[List[int]] = None

    @classmethod
    def setUpClass(cls):
        cls.recommender = VenueBasedRecommender()
        cls.author_representations = [
            cls.recommender.author_representation(a["author"], a["papers"])
            for a in authors
        ]

    def test_venues(self):
        self.assertEqual(self.recommender.venues, ["a", "b", "c", "d", "e", "f", "g"])

    def test_author_representation(self):
        self.assertEqual(self.author_representations[0], [2, 2, 1, 1, 1, 1])
        self.assertEqual(self.author_representations[1], [0, 0, 0, 0, 0, 0, 1])

    def test_explanation(self):
        explanations = [
            self.recommender.explanation(
                u, self.author_representations[0], "Author McAuthor"
            )
            for u in user_representations
        ]
        self.assertEqual(
            explanations[0],
            f"You have published 4 times at **a**, 3 times at **e**, and 2 times at **b** during the last "
            f"{config.MAX_PAPER_AGE} years. Author McAuthor has also published at these venues in the same time "
            f"period.",
        )
        self.assertIn(
            explanations[1],
            (
                f"You and Author McAuthor have both published at **a** and **b** during the last "
                f"{config.MAX_PAPER_AGE} years.",
                "You and Author McAuthor have both published at **b** and **a** during the last "
                f"{config.MAX_PAPER_AGE} years.",
            ),
        )


if __name__ == "__main__":
    unittest.main()
