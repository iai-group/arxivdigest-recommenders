import asyncio
from collections import defaultdict
from typing import List, Dict, DefaultDict
import numpy as np

from arxivdigest_recommenders.recommender import ArxivdigestRecommender
from arxivdigest_recommenders.semantic_scholar import SemanticScholar
from arxivdigest_recommenders.author_representation import venue_author_representation
from arxivdigest_recommenders.util import pad_shortest, padded_cosine_sim
from arxivdigest_recommenders import config


def explanation(
    venues: List[str],
    user: np.ndarray,
    author: np.ndarray,
    author_name: str,
    author_influence: DefaultDict[int, int],
) -> str:
    user, author = pad_shortest(user, author)
    common_venue_indexes = sorted(
        [i for i, user_count in enumerate(user) if user_count > 0 and author[i] > 0],
        key=lambda i: author_influence[i],
        reverse=True,
    )[: config.MAX_EXPLANATION_VENUES]
    common_venues = [f"**{venues[i]}**" for i in common_venue_indexes]
    if len(common_venues) > 1:
        common_venues[-1] = "and " + common_venues[-1]
    return (
        f"{author_name} has had influential publications at "
        f"{(' ' if len(common_venues) < 3 else ', ').join(common_venues)} in the last {config.MAX_PAPER_AGE} years. "
        f"You have also published at {'this venue' if len(common_venues) == 1 else 'these venues'} in the same time "
        f"period."
    )


class WeightedInfRecommender(ArxivdigestRecommender):
    """Recommender system based on venue co-publishing and author influence."""

    def __init__(self):
        super().__init__(config.WEIGHTED_INF_API_KEY, "WeightedInfRecommender")
        self._venues: List[str] = []
        self._authors: Dict[str, np.ndarray] = {}
        self._influence: Dict[str, DefaultDict[int, int]] = {}

    async def author_representation(self, s2_id: str) -> np.ndarray:
        if s2_id not in self._authors:
            async with SemanticScholar() as s2:
                papers = await s2.author_papers(s2_id)
            self._authors[s2_id] = venue_author_representation(self._venues, papers)
        return self._authors[s2_id]

    async def author_influence(self, s2_id: str) -> DefaultDict[int, int]:
        if s2_id not in self._influence:
            async with SemanticScholar() as s2:
                papers = await s2.author_papers(s2_id)
            self._authors[s2_id] = venue_author_representation(self._venues, papers)
            author_influence = defaultdict(int)
            for paper in papers:
                if paper["venue"] and paper["venue"] in self._venues:
                    author_influence[self._venues.index(paper["venue"])] += paper[
                        "influentialCitationCount"
                    ]
            self._influence[s2_id] = defaultdict(
                int,
                {
                    venue_index: venue_influence
                    for venue_index, venue_influence in author_influence.items()
                    if venue_influence >= config.WEIGHTED_INF_MIN_INFLUENCE
                },
            )
        return self._influence[s2_id]

    async def score_paper(self, user, user_s2_id, paper_id):
        async with SemanticScholar() as s2:
            paper = await s2.paper(arxiv_id=paper_id)
        if user_s2_id in [a["authorId"] for a in paper["authors"]]:
            return
        user_representation = await self.author_representation(user_s2_id)
        user_venue_indexes = np.nonzero(user_representation)[0]
        similar_author = None
        similar_author_name = None
        similar_author_influence = None
        score = 0
        for author in paper["authors"]:
            if not author["authorId"]:
                continue
            try:
                author_representation = await self.author_representation(
                    author["authorId"]
                )
                author_influence = await self.author_influence(author["authorId"])
            except Exception:
                continue
            author_score = np.sum(
                np.vectorize(author_influence.get)(user_venue_indexes)
            ) * padded_cosine_sim(user_representation, author_representation)
            if author_score > score:
                similar_author = author_representation
                similar_author_name = author["name"]
                similar_author_influence = author_influence
                score = author_score
        return {
            "article_id": paper_id,
            "score": score,
            "explanation": explanation(
                self._venues,
                user_representation,
                similar_author,
                similar_author_name,
                similar_author_influence,
            )
            if score > 0
            else "",
        }


if __name__ == "__main__":
    recommender = WeightedInfRecommender()
    asyncio.run(recommender.recommend())
