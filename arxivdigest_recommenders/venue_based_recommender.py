import asyncio
import random
from typing import List

from arxivdigest_recommenders.recommender import ArxivdigestRecommender
from arxivdigest_recommenders import config
from arxivdigest_recommenders.util import pad_shortest


class VenueBasedRecommender(ArxivdigestRecommender):
    """Recommender system based on venue co-publishing."""

    def __init__(self):
        super().__init__(config.VENUE_BASED_RECOMMENDER_API_KEY)

        # Stores the names of all discovered venues.
        self._venues: List[str] = []

    @property
    def venues(self):
        return self._venues

    def gen_author_representation(
        self, author: dict, published_papers: List[dict]
    ) -> List[int]:
        author_venues = [paper["venue"] for paper in published_papers if paper["venue"]]
        for venue in author_venues:
            if (
                venue.lower() not in config.VENUE_BLACKLIST
                and venue not in self._venues
            ):
                self._venues.append(venue)
        return [author_venues.count(venue) for venue in self._venues]

    def gen_explanation(
        self, user: List[int], author: List[int], author_name: str
    ) -> str:
        user, author = pad_shortest(user, author)
        common_venue_indexes = [
            i for i, user_count in enumerate(user) if user_count > 0 and author[i] > 0
        ]
        if max([user[i] for i in common_venue_indexes]) == 1:
            common_venues = [
                f"**{self._venues[i]}**"
                for i in random.sample(common_venue_indexes, len(common_venue_indexes))
            ][: config.MAX_EXPLANATION_VENUES]
            if len(common_venues) > 1:
                common_venues[-1] = "and " + common_venues[-1]
            return (
                f"You and {author_name} have both published at "
                f"{(' ' if len(common_venues) < 3 else ', ').join(common_venues)} during the last "
                f"{config.MAX_PAPER_AGE} years."
            )
        else:
            frequent_venue_indexes = sorted(
                [i for i in common_venue_indexes if user[i] > 1],
                key=lambda i: user[i],
                reverse=True,
            )[: config.MAX_EXPLANATION_VENUES]
            frequent_venues = [
                f"{user[i]} times at **{self._venues[i]}**"
                for i in frequent_venue_indexes
            ]
            if len(frequent_venues) > 1:
                frequent_venues[-1] = "and " + frequent_venues[-1]
            return (
                f"You have published {(' ' if len(frequent_venues) < 3 else ', ').join(frequent_venues)} during "
                f"the last {config.MAX_PAPER_AGE} years. {author_name} has also published at "
                f"{'this venue' if len(frequent_venues) == 1 else 'these venues'} in the same time period."
            )


if __name__ == "__main__":
    recommender = VenueBasedRecommender()
    asyncio.run(recommender.recommend())
