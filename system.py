import asyncio
import random
from datetime import date
from typing import List, Dict
from arxivdigest.connector import ArxivdigestConnector

from semantic_scholar import SemanticScholar
from util import extract_s2_id, padded_cosine_sim, pad_shortest
from log import logger
import config


class RecommenderSystem:
    """ArXivDigest recommender system based on venue co-publishing."""

    def __init__(self, arxivdigest_connector: ArxivdigestConnector, max_paper_age=5):
        """
        :param arxivdigest_connector: ArXivDigest connector.
        :param max_paper_age: Max age (in years) of papers to consider when when generating author vector
        representations.
        """
        self._connector = arxivdigest_connector
        self._max_paper_age = max_paper_age
        self._article_ids = self._connector.get_article_ids()
        self._venues: List[str] = []
        self._authors: Dict[str, List[int]] = {}

    async def get_author_representation(self, s2_id: str) -> List[int]:
        """Get the vector representation of an author.

        The returned vector is N-dimensional, where N is the number of venues that have been discovered by the
        recommender thus far. Each value in the vector corresponds to a certain venue and represents the number of
        times the author has published there.

        :param s2_id: S2 author ID.
        :return: Author vector representation.
        """
        if s2_id not in self._authors:
            year_cutoff = date.today().year - self._max_paper_age
            async with SemanticScholar() as s2:
                author = await s2.get_author(s2_id)
                papers = await asyncio.gather(
                    *[
                        s2.get_paper(s2_id=paper["paperId"])
                        for paper in author["papers"]
                        if paper["year"] is None or paper["year"] >= year_cutoff
                    ],
                    return_exceptions=True,
                )
            papers = [paper for paper in papers if not isinstance(paper, Exception)]
            author_venues = [paper["venue"] for paper in papers if paper["venue"]]

            for venue in author_venues:
                if (
                    venue.lower() not in config.VENUE_BLACKLIST
                    and venue not in self._venues
                ):
                    self._venues.append(venue)

            self._authors[s2_id] = [
                author_venues.count(venue) for venue in self._venues
            ]
        return self._authors[s2_id]

    def gen_explanation(
        self, user: List[int], author: List[int], author_name: str, max_venues=3
    ):
        """Generate a recommendation explanation based on the vector representations of a user and an author.

        :param user: User vector representation.
        :param author: Author vector representation.
        :param author_name: Author name.
        :param max_venues: Max number of venues to include in explanation.
        :return: Explanation.
        """
        user, author = pad_shortest(user, author)
        common_venue_indexes = [
            i for i, user_count in enumerate(user) if user_count > 0 and author[i] > 0
        ]
        if max([user[i] for i in common_venue_indexes]) == 1:
            common_venues = [
                f"**{self._venues[i]}**"
                for i in random.sample(common_venue_indexes, len(common_venue_indexes))
            ][:max_venues]
            if len(common_venues) > 1:
                common_venues[-1] = "and " + common_venues[-1]
            return (
                f"You and {author_name} have both published at "
                f"{(' ' if len(common_venues) < 3 else ', ').join(common_venues)} during the last "
                f"{self._max_paper_age} years."
            )
        else:
            frequent_venue_indexes = sorted(
                [i for i in common_venue_indexes if user[i] > 1],
                key=lambda i: user[i],
                reverse=True,
            )[:max_venues]
            frequent_venues = [
                f"{user[i]} times at **{self._venues[i]}**"
                for i in frequent_venue_indexes
            ]
            if len(frequent_venues) > 1:
                frequent_venues[-1] = "and " + frequent_venues[-1]
            return (
                f"You have published {(' ' if len(frequent_venues) < 3 else ', ').join(frequent_venues)} during "
                f"the last {self._max_paper_age} years. {author_name} has also published at "
                f"{'this venue' if len(frequent_venues) == 1 else 'these venues'} in the same time period."
            )

    async def gen_user_ranking(self, s2_id: str) -> List[dict]:
        """Generate article ranking for a single user.

        The score assigned to each article is the cosine similarity between the user and the article author that is
        most similar to the user.

        :param s2_id: S2 author ID of the user.
        :return: Ranking of candidate articles.
        """
        try:
            user = await self.get_author_representation(s2_id)
        except Exception:
            logger.error(f"S2 ID {s2_id}: unable to generate author representation.")
            return []
        async with SemanticScholar() as s2:
            articles = await asyncio.gather(
                *[
                    s2.get_paper(arxiv_id=article_id)
                    for article_id in self._article_ids
                ],
                return_exceptions=True,
            )
        articles = [
            article for article in articles if not isinstance(article, Exception)
        ]
        results = []
        for article in articles:
            authors = await asyncio.gather(
                *[
                    self.get_author_representation(author["authorId"])
                    for author in article["authors"]
                    if author["authorId"]
                ],
                return_exceptions=True,
            )
            authors = [
                (author, article["authors"][i]["name"])
                for i, author in enumerate(authors)
                if not isinstance(author, Exception)
            ]
            (similar_author, similar_author_name), score = max(
                [(author, padded_cosine_sim(user, author[0])) for author in authors],
                key=lambda t: t[1],
            )
            results.append(
                {
                    "article_id": article["arxivId"],
                    "score": score,
                    "explanation": self.gen_explanation(
                        user, similar_author, similar_author_name
                    )
                    if score > 0
                    else "",
                }
            )
        return results

    async def gen_recommendations(
        self, users: dict, interleaved_articles: dict, max_recommendations=10
    ) -> dict:
        """Generate recommendations for a user batch.

        :param users: Users.
        :param interleaved_articles: Interleaved articles that will be excluded from the generated recommendations
        before submission.
        :param max_recommendations: Max number of recommendations per user.
        :return: Recommendations.
        """
        recommendations = {}
        for user_id, user in users.items():
            s2_id = extract_s2_id(user)
            if s2_id is None:
                logger.info(f"User {user_id}: skipped (no S2 ID provided).")
                continue
            logger.debug(f"User {user_id} S2 ID: {s2_id}.")
            user_ranking = await self.gen_user_ranking(s2_id)
            user_ranking = [
                recommendation
                for recommendation in user_ranking
                if recommendation["article_id"] not in interleaved_articles[user_id]
                and recommendation["score"] > 0
            ]
            user_recommendations = sorted(
                user_ranking, key=lambda r: r["score"], reverse=True
            )
            if len(user_recommendations) > 0:
                recommendations[user_id] = user_recommendations[:max_recommendations]
            logger.info(
                f"User {user_id}: recommended {len(recommendations[user_id])} articles."
            )
        return recommendations

    async def recommend(self):
        """Generate and submit recommendations for all users."""
        total_users = self._connector.get_number_of_users()
        logger.info(f"Starting recommending articles for {total_users} users")
        recommendation_count = 0
        while recommendation_count < total_users:
            user_ids = self._connector.get_user_ids(recommendation_count)
            users = self._connector.get_user_info(user_ids)
            interleaved = self._connector.get_interleaved_articles(user_ids)

            recommendations = await self.gen_recommendations(users, interleaved)

            if recommendations:
                self._connector.send_article_recommendations(recommendations)
            recommendation_count += len(user_ids)
            logger.info(f"Processed {recommendation_count} users")


if __name__ == "__main__":
    arxivdigest_connector = ArxivdigestConnector(
        config.ARXIVDIGEST_API_KEY, config.ARXIVDIGEST_BASE_URL
    )
    recommender = RecommenderSystem(arxivdigest_connector)
    asyncio.run(recommender.recommend())
    logger.info("\nFinished recommending articles.")
