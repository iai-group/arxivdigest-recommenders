import asyncio
import random
import numpy as np
from typing import List, Dict

from arxivdigest_recommenders.recommender import ArxivdigestRecommender
from arxivdigest_recommenders.semantic_scholar import SemanticScholar
from arxivdigest_recommenders.author_representation import venue_author_representation
from arxivdigest_recommenders.util import pad_shortest, padded_cosine_sim
from arxivdigest_recommenders import config


def explanation(
    venues: List[str], user: np.ndarray, author: np.ndarray, author_name: str
) -> str:
    """Generate a recommendation explanation.

    :param venues: List of venues.
    :param user: User.
    :param author: Author.
    :param author_name: Author name.
    :return: Explanation.
    """
    user, author = pad_shortest(user, author)
    common_venue_indexes = [
        i for i, user_count in enumerate(user) if user_count > 0 and author[i] > 0
    ]
    if max([user[i] for i in common_venue_indexes]) == 1:
        common_venues = [
            f"**{venues[i]}**"
            for i in random.sample(common_venue_indexes, len(common_venue_indexes))
        ][: config.MAX_EXPLANATION_VENUES]
        if len(common_venues) > 1:
            common_venues[-1] = "and " + common_venues[-1]
        return (
            f"You and {author_name} have both published at "
            f"{(' ' if len(common_venues) < 3 else ', ').join(common_venues)} in the last "
            f"{config.MAX_PAPER_AGE} years."
        )
    else:
        frequent_venue_indexes = sorted(
            [i for i in common_venue_indexes if user[i] > 1],
            key=lambda i: user[i],
            reverse=True,
        )[: config.MAX_EXPLANATION_VENUES]
        frequent_venues = [
            f"{user[i]} times at **{venues[i]}**" for i in frequent_venue_indexes
        ]
        if len(frequent_venues) > 1:
            frequent_venues[-1] = "and " + frequent_venues[-1]
        return (
            f"You have published {(' ' if len(frequent_venues) < 3 else ', ').join(frequent_venues)} in "
            f"the last {config.MAX_PAPER_AGE} years. {author_name} has also published at "
            f"{'this venue' if len(frequent_venues) == 1 else 'these venues'} in the same time period."
        )


class VenueCoPubRecommender(ArxivdigestRecommender):
    """Recommender system based on venue co-publishing."""

    def __init__(self):
        super().__init__(config.VENUE_COPUB_API_KEY, "VenueCoPubRecommender")
        self._venues: List[str] = []
        self._authors: Dict[str, np.ndarray] = {}

    async def author_representation(self, s2_id: str) -> np.ndarray:
        if s2_id not in self._authors:
            async with SemanticScholar() as s2:
                papers = await s2.author_papers(s2_id=s2_id)
            self._authors[s2_id] = venue_author_representation(self._venues, papers)
        return self._authors[s2_id]

    async def score_paper(self, user, user_s2_id, paper_id):
        async with SemanticScholar() as s2:
            paper = await s2.paper(arxiv_id=paper_id)
        if user_s2_id in [a["authorId"] for a in paper["authors"]]:
            return
        author_representations = await asyncio.gather(
            *[
                self.author_representation(a["authorId"])
                for a in paper["authors"]
                if a["authorId"]
            ],
            return_exceptions=True,
        )
        if not any(isinstance(a, np.ndarray) for a in author_representations):
            return
        user_representation = await self.author_representation(user_s2_id)
        similar_author, similar_author_name, score = max(
            [
                (
                    author_representation,
                    a["name"],
                    padded_cosine_sim(user_representation, author_representation),
                )
                for a, author_representation in zip(
                    paper["authors"], author_representations
                )
                if isinstance(author_representation, np.ndarray)
            ],
            key=lambda t: t[2],
        )
        return {
            "article_id": paper_id,
            "score": score,
            "explanation": explanation(
                self._venues,
                user_representation,
                similar_author,
                similar_author_name,
            )
            if score > 0
            else "",
        }


if __name__ == "__main__":
    recommender = VenueCoPubRecommender()
    asyncio.run(recommender.recommend())
