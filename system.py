import logging
import sys
import asyncio
from datetime import date
from typing import List
from arxivdigest.connector import ArxivdigestConnector

from semantic_scholar import SemanticScholar
from util import extract_s2_id, padded_cosine_sim
import config


class RecommenderSystem:
    """ArXivDigest recommender system based on venue co-publishing."""

    def __init__(
        self,
        arxivdigest_connector: ArxivdigestConnector,
    ):
        self._connector = arxivdigest_connector
        self._article_ids = self._connector.get_article_ids()
        self._venues: List[str] = []

    async def get_author_representation(self, s2_id: str, max_paper_age=5) -> List[int]:
        """Get the vector representation of an author.

        The returned vector is N-dimensional, where N is the number of venues that have been discovered by the
        recommender thus far. Each value in the vector corresponds to a certain venue and represents the number of
        times the author has published there.

        :param s2_id: S2 author ID.
        :param max_paper_age: Max age (in years) of papers to be considered.
        :return: Author vector representation.
        """
        year_cutoff = date.today().year - max_paper_age
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
            if venue not in self._venues:
                self._venues.append(venue)

        return [author_venues.count(venue) for venue in self._venues]

    async def gen_user_ranking(self, s2_id: str) -> List[dict]:
        """Generate article ranking for a single user.

        The score assigned to each article is the cosine similarity between the user and the article author that is
        most similar to the user.

        :param s2_id: S2 author ID of the user.
        :return: Ranking of candidate articles.
        """
        user = await self.get_author_representation(s2_id)
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
            # TODO: add recommendation explanation
            authors = await asyncio.gather(
                *[
                    self.get_author_representation(author["authorId"])
                    for author in article["authors"]
                    if author["authorId"]
                ],
                return_exceptions=True,
            )
            authors = [
                author for author in authors if not isinstance(author, Exception)
            ]
            results.append(
                {
                    "article_id": article["arxivId"],
                    "score": max(padded_cosine_sim(user, author) for author in authors),
                    "explanation": "",
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
            user_recommendations = await self.gen_user_ranking(s2_id)
            user_recommendations = [
                recommendation
                for recommendation in user_recommendations
                if recommendation["article_id"] not in interleaved_articles[user_id]
            ]
            user_recommendations = sorted(
                user_recommendations, key=lambda r: r["score"], reverse=True
            )
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
    log_levels = {
        "FATAL": 50,
        "ERROR": 40,
        "WARNING": 30,
        "INFO": 20,
        "DEBUG": 10,
    }
    logger = logging.getLogger(__name__)
    logging.basicConfig(
        level=logging.ERROR,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )
    log_level = config.LOG_LEVEL
    logger.setLevel(log_levels.get(log_level, 20))

    arxivdigest_connector = ArxivdigestConnector(
        config.ARXIVDIGEST_API_KEY, config.ARXIVDIGEST_BASE_URL
    )
    recommender = RecommenderSystem(arxivdigest_connector)
    asyncio.run(recommender.recommend())
    logger.info("\nFinished recommending articles.")
