import asyncio
import numpy as np
from typing import List, Dict

from arxivdigest_recommenders.recommender import ArxivdigestRecommender
from arxivdigest_recommenders.semantic_scholar import SemanticScholar
from arxivdigest_recommenders.author_representation import venue_author_representation
from arxivdigest_recommenders.util import pad_shortest
from arxivdigest_recommenders import config


def explanation(
    venues: List[str],
    user: List[int],
    paper: List[int],
) -> str:
    venue_index = paper.index(1)
    return (
        f"This article is published at **{venues[venue_index]}**, where you have published {user[venue_index]} "
        f"{'paper' if user[venue_index] == 1 else 'papers'} in the last {config.MAX_PAPER_AGE} years."
    )


class FrequentVenuesRecommender(ArxivdigestRecommender):
    """Recommender system that recommends papers published at venues that the user has published papers at."""

    def __init__(self):
        super().__init__(config.FREQUENT_VENUES_API_KEY, "FrequentVenuesRecommender")
        self._venues: List[str] = []
        self._authors: Dict[str, np.ndarray] = {}

    async def author_representation(self, s2_id: str) -> np.ndarray:
        if s2_id not in self._authors:
            async with SemanticScholar() as s2:
                papers = await s2.author_papers(s2_id)
            self._authors[s2_id] = venue_author_representation(self._venues, papers)
        return self._authors[s2_id]

    async def score_paper(self, user, user_s2_id, paper_id):
        async with SemanticScholar() as s2:
            paper = await s2.paper(arxiv_id=paper_id)
        user_representation = await self.author_representation(user_s2_id)
        if not paper["venue"] or paper["venue"] not in self._venues:
            return
        paper_representation, user_representation = pad_shortest(
            [int(v == paper["venue"]) for v in self._venues], user_representation
        )
        score = int(np.dot(paper_representation, user_representation))
        return {
            "article_id": paper_id,
            "score": score,
            "explanation": explanation(
                self._venues, user_representation, paper_representation
            )
            if score > 0
            else "",
        }


if __name__ == "__main__":
    recommender = FrequentVenuesRecommender()
    asyncio.run(recommender.recommend())
