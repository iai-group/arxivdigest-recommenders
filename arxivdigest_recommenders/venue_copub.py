import asyncio
import random
from typing import List, Dict, Any

from arxivdigest_recommenders.recommender import ArxivdigestRecommender
from arxivdigest_recommenders.author_representation import venue_author_representation
from arxivdigest_recommenders.util import pad_shortest, padded_cosine_sim
from arxivdigest_recommenders import config


def explanation(venues: List[str], user: Dict[str, Any], author: Dict[str, Any]) -> str:
    """Generate a recommendation explanation.

    :param venues: List of venues.
    :param user: User.
    :param author: Author.
    :return: Explanation.
    """
    user_representation, author_representation = pad_shortest(
        user["representation"], author["representation"]
    )
    common_venue_indexes = [
        i
        for i, user_count in enumerate(user_representation)
        if user_count > 0 and author_representation[i] > 0
    ]
    if max([user_representation[i] for i in common_venue_indexes]) == 1:
        common_venues = [
            f"**{venues[i]}**"
            for i in random.sample(common_venue_indexes, len(common_venue_indexes))
        ][: config.MAX_EXPLANATION_VENUES]
        if len(common_venues) > 1:
            common_venues[-1] = "and " + common_venues[-1]
        return (
            f"You and {author['name']} have both published at "
            f"{(' ' if len(common_venues) < 3 else ', ').join(common_venues)} during the last "
            f"{config.MAX_PAPER_AGE} years."
        )
    else:
        frequent_venue_indexes = sorted(
            [i for i in common_venue_indexes if user_representation[i] > 1],
            key=lambda i: user_representation[i],
            reverse=True,
        )[: config.MAX_EXPLANATION_VENUES]
        frequent_venues = [
            f"{user_representation[i]} times at **{venues[i]}**"
            for i in frequent_venue_indexes
        ]
        if len(frequent_venues) > 1:
            frequent_venues[-1] = "and " + frequent_venues[-1]
        return (
            f"You have published {(' ' if len(frequent_venues) < 3 else ', ').join(frequent_venues)} during "
            f"the last {config.MAX_PAPER_AGE} years. {author['name']} has also published at "
            f"{'this venue' if len(frequent_venues) == 1 else 'these venues'} in the same time period."
        )


class VenueCoPubRecommender(ArxivdigestRecommender):
    """Recommender system based on venue co-publishing."""

    def __init__(self):
        super().__init__(config.VENUE_COPUB_API_KEY)

        # Stores the names of all discovered venues.
        self._venues: List[str] = []

    @property
    def venues(self):
        return self._venues

    def author_representation(self, author, published_papers):
        return venue_author_representation(self._venues, published_papers)

    async def user_ranking(self, user, paper_authors):
        results = []
        for paper_id, authors in paper_authors.items():
            similar_author, score = max(
                [
                    (
                        author,
                        padded_cosine_sim(
                            user["representation"], author["representation"]
                        ),
                    )
                    for author in authors
                ],
                key=lambda t: t[1],
            )
            results.append(
                {
                    "article_id": paper_id,
                    "score": score,
                    "explanation": explanation(self._venues, user, similar_author)
                    if score > 0
                    else "",
                }
            )
        return results


if __name__ == "__main__":
    recommender = VenueCoPubRecommender()
    asyncio.run(recommender.recommend())
