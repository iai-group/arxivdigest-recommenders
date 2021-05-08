import unittest
from arxivdigest_recommenders.venue_copub import explanation
from arxivdigest_recommenders import config


authors = [
    {"name": "Author McAuthor", "representation": [2, 2, 1, 1, 1, 1]},
    {"name": "Author McAuthor", "representation": [0, 0, 0, 0, 0, 0, 1]},
]

users = [{"representation": [4, 2, 0, 0, 3, 1]}, {"representation": [1, 1, 0, 0, 0, 0]}]
venues = ["a", "b", "c", "d", "e", "f", "g"]


class TestVenueCoPubRecommender(unittest.TestCase):
    def test_explanation(self):
        explanations = [explanation(venues, u, authors[0]) for u in users]
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
