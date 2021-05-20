from abc import ABC, abstractmethod
from collections import defaultdict
from typing import List, Dict, Any, Sequence
from arxivdigest.connector import ArxivdigestConnector

from arxivdigest_recommenders import config
from arxivdigest_recommenders.semantic_scholar import SemanticScholar
from arxivdigest_recommenders.util import extract_s2_id, chunks
from arxivdigest_recommenders.log import logger


class ArxivdigestRecommender(ABC):
    """Base class for arXivDigest recommender systems."""

    def __init__(self, arxivdigest_api_key: str):
        self._arxivdigest_api_key = arxivdigest_api_key

    @abstractmethod
    async def user_ranking(
        self, user: dict, user_s2_id: str, paper_ids: Sequence[str]
    ) -> List[dict]:
        """Generate ranking of papers for a user.

        :param user: User data.
        :param user_s2_id: S2 author ID of the user.
        :param paper_ids: arXiv IDs of papers.
        :return: Ranking of candidate papers.
        """
        pass

    async def recommendations(
        self,
        users: dict,
        interleaved_papers: dict,
        paper_ids: Sequence[str],
        max_recommendations=10,
        batch_size=50,
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Generate recommendations for a user batch.

        :param users: Users.
        :param interleaved_papers: Interleaved papers that will be excluded from the generated recommendations
        before submission.
        :param paper_ids: arXiv IDs of candidate papers.
        :param max_recommendations: Max number of recommendations per user.
        :param batch_size: User recommendations are generated in batches of candidate papers. This is the number of
        papers used in each batch.
        :return: Recommendations.
        """
        user_rankings = defaultdict(list)
        for user_id, user_data in users.items():
            s2_id = extract_s2_id(user_data)
            if s2_id is None:
                logger.info(f"User {user_id}: skipped (no S2 ID provided).")
                continue
            try:
                # Validate the user's S2 ID.
                async with SemanticScholar() as s2:
                    await s2.author(s2_id)
            except Exception:
                logger.error(
                    f"User {user_id}: unable to get author details for S2 ID {s2_id}."
                )
                continue
            for batch in chunks(paper_ids, batch_size):
                batch_user_ranking = await self.user_ranking(user_data, s2_id, batch)
                batch_user_ranking = [
                    r
                    for r in batch_user_ranking
                    if r["article_id"] not in interleaved_papers[user_id]
                    and r["score"] > 0
                ]
                user_rankings[user_id].extend(batch_user_ranking)
        recommendations = {
            user_id: sorted(user_ranking, key=lambda r: r["score"], reverse=True)[
                :max_recommendations
            ]
            for user_id, user_ranking in user_rankings.items()
        }
        for user_id, user_recommendations in recommendations.items():
            logger.info(
                f"User {user_id}: recommended {len(user_recommendations)} papers."
            )
        return {
            user_id: user_recommendations
            for user_id, user_recommendations in recommendations.items()
            if len(user_recommendations) > 0
        }

    async def recommend(
        self, submit_recommendations=True
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Generate and submit recommendations for all users.

        :param submit_recommendations: Submit recommendations to arXivDigest.
        :return: Recommendations.
        """
        connector = ArxivdigestConnector(
            self._arxivdigest_api_key, config.ARXIVDIGEST_BASE_URL
        )
        paper_ids = connector.get_article_ids()
        logger.info(f"{len(paper_ids)} candidate papers.")
        total_users = connector.get_number_of_users()
        logger.info(f"Recommending papers for {total_users} users.")
        recommendation_count = 0
        recommendations = {}
        while recommendation_count < total_users:
            user_ids = connector.get_user_ids(recommendation_count)
            users = connector.get_user_info(user_ids)
            interleaved = connector.get_interleaved_articles(user_ids)
            batch_recommendations = await self.recommendations(
                users, interleaved, paper_ids
            )
            recommendations.update(batch_recommendations)
            if batch_recommendations and submit_recommendations:
                connector.send_article_recommendations(batch_recommendations)
            recommendation_count += len(user_ids)
            logger.info(f"Processed {recommendation_count} users.")
        logger.info("Finished recommending.")
        logger.info(
            f"Semantic Scholar API: {SemanticScholar.cache_hits} cache hits, "
            f"{SemanticScholar.cache_misses} cache misses, and {SemanticScholar.errors} errors."
        )
        return recommendations
