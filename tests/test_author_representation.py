import unittest
from arxivdigest_recommenders.author_representation import venue_author_representation


author_papers = [
    [{"venue": venue} for venue in ("a", "a", "b", "c", "d", "e", "f", "b")],
    [{"venue": "g"}],
]


class TestAuthorRepresentation(unittest.TestCase):
    def test_venue_author_representation(self):
        venues = []
        author_representations = [
            venue_author_representation(venues, papers) for papers in author_papers
        ]
        self.assertEqual(author_representations[0], [2, 2, 1, 1, 1, 1])
        self.assertEqual(author_representations[1], [0, 0, 0, 0, 0, 0, 1])
        self.assertEqual(venues, ["a", "b", "c", "d", "e", "f", "g"])


if __name__ == "__main__":
    unittest.main()
