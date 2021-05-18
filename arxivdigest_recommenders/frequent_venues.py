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
        f"{'paper' if user[venue_index] == 1 else 'papers'}."
    )


class FrequentVenuesRecommender(ArxivdigestRecommender):
    def __init__(self):
        super().__init__(config.FREQUENT_VENUES_API_KEY)
        self._venues: List[str] = []
        self._authors: Dict[str, List[int]] = {}

    @property
    def venues(self):
        return self._venues

    async def author_representation(self, s2_id: str) -> List[int]:
        if s2_id not in self._authors:
            async with SemanticScholar() as s2:
                papers = await s2.author_papers(s2_id=s2_id)
            self._authors[s2_id] = venue_author_representation(self._venues, papers)
        return self._authors[s2_id]

    async def user_ranking(self, user, user_s2_id, paper_ids):
        user_representation = await self.author_representation(user_s2_id)
        results = []
        for paper_id in paper_ids:
            try:
                async with SemanticScholar() as s2:
                    paper = await s2.paper(arxiv_id=paper_id)
            except Exception:
                continue
            if not paper["venue"] or paper["venue"] not in self._venues:
                continue
            paper_representation, user_representation = pad_shortest(
                [int(v == paper["venue"]) for v in self._venues], user_representation
            )
            score = np.dot(paper_representation, user_representation)
            results.append(
                {
                    "article_id": paper_id,
                    "score": score,
                    "explanation": explanation(
                        self._venues, user_representation, paper_representation
                    )
                    if score > 0
                    else "",
                }
            )
        return results


if __name__ == "__main__":
    recommender = FrequentVenuesRecommender()
    asyncio.run(recommender.recommend())
