import asyncio
import random
from datetime import date
from collections import defaultdict
from typing import List, Dict, Any
from arxivdigest.connector import ArxivdigestConnector

from semantic_scholar import SemanticScholar
from util import (
    extract_s2_id,
    padded_cosine_sim,
    pad_shortest,
    gather_exclude_exceptions,
)
from log import logger
import config


class RecommenderSystem:
    """ArXivDigest recommender system based on venue co-publishing."""

    def __init__(self, max_paper_age=5):
        """
        :param max_paper_age: Max age (in years) of papers to consider when when generating author vector
        representations.
        """
        self._connector = ArxivdigestConnector(
            config.ARXIVDIGEST_API_KEY, config.ARXIVDIGEST_BASE_URL
        )
        self._max_paper_age = max_paper_age

        # Stores the names of all discovered venues.
        self._venues: List[str] = []

        # Stores the vector representations of the papers (their authors) that are candidate for recommendation.
        self._papers: Dict[str, List[Dict[str, Any]]] = {}

        # Used as a cache for the vector representations of authors.
        self._authors: Dict[str, List[int]] = {}

        # Locks used to ensure that the vector representation of an author is created only once if missing.
        self._author_locks = defaultdict(asyncio.Lock)

    async def get_author_representation(self, s2_id: str) -> List[int]:
        """Get the vector representation of an author.

        The returned vector is N-dimensional, where N is the number of venues that have been discovered by the
        recommender thus far. Each value in the vector corresponds to a certain venue and represents the number of
        times the author has published there.

        :param s2_id: S2 author ID.
        :return: Author vector representation.
        """
        async with self._author_locks[s2_id]:
            if s2_id not in self._authors:
                year_cutoff = date.today().year - self._max_paper_age
                async with SemanticScholar() as s2:
                    author = await s2.get_author(s2_id)
                    papers = await gather_exclude_exceptions(
                        *[
                            s2.get_paper(s2_id=paper["paperId"])
                            for paper in author["papers"]
                            if paper["year"] is None or paper["year"] >= year_cutoff
                        ]
                    )
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

    async def gen_paper_representations(self):
        """Generate author representations for each author of each paper that is candidate for recommendation."""

        async def get_author_representations(paper: dict):
            authors = await gather_exclude_exceptions(
                *[
                    self.get_author_representation(author["authorId"])
                    for author in paper["authors"]
                    if author["authorId"]
                ]
            )
            return [
                {"name": paper["authors"][i]["name"], "representation": author}
                for i, author in enumerate(authors)
            ]

        paper_ids = self._connector.get_article_ids()
        logger.info(
            f"Generating vector representations of {len(paper_ids)} candidate papers and their authors."
        )
        async with SemanticScholar() as s2:
            papers = await gather_exclude_exceptions(
                *[s2.get_paper(arxiv_id=paper_id) for paper_id in paper_ids]
            )
        paper_authors = await asyncio.gather(
            *[get_author_representations(paper) for paper in papers]
        )
        self._papers = {
            paper["arxivId"]: authors for paper, authors in zip(papers, paper_authors)
        }

    def gen_explanation(
        self, user: List[int], author: List[int], author_name: str, max_venues=3
    ) -> str:
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

    async def gen_user_ranking(self, s2_id: str) -> List[Dict[str, Any]]:
        """Generate paper ranking for a single user.

        The score assigned to each paper is the cosine similarity between the user and the paper author that is
        most similar to the user.

        :param s2_id: S2 author ID of the user.
        :return: Ranking of candidate papers.
        """
        try:
            user = await self.get_author_representation(s2_id)
        except Exception:
            logger.error(f"S2 ID {s2_id}: unable to generate author representation.")
            return []
        results = []
        for paper_id, authors in self._papers.items():
            similar_author, score = max(
                [
                    (author, padded_cosine_sim(user, author["representation"]))
                    for author in authors
                ],
                key=lambda t: t[1],
            )
            results.append(
                {
                    "article_id": paper_id,
                    "score": score,
                    "explanation": self.gen_explanation(
                        user, similar_author["representation"], similar_author["name"]
                    )
                    if score > 0
                    else "",
                }
            )
        return results

    async def gen_recommendations(
        self, users: dict, interleaved_papers: dict, max_recommendations=10
    ) -> Dict[str, Dict[str, Any]]:
        """Generate recommendations for a user batch.

        :param users: Users.
        :param interleaved_papers: Interleaved papers that will be excluded from the generated recommendations
        before submission.
        :param max_recommendations: Max number of recommendations per user.
        :return: Recommendations.
        """

        async def gen_user_recommendations(user_id: str, user_data: dict):
            s2_id = extract_s2_id(user_data)
            if s2_id is None:
                logger.info(f"User {user_id}: skipped (no S2 ID provided).")
                return []
            user_ranking = await self.gen_user_ranking(s2_id)
            user_ranking = [
                recommendation
                for recommendation in user_ranking
                if recommendation["article_id"] not in interleaved_papers[user_id]
                and recommendation["score"] > 0
            ]
            user_recommendations = sorted(
                user_ranking, key=lambda r: r["score"], reverse=True
            )[:max_recommendations]
            logger.info(
                f"User {user_id}: recommended {len(user_recommendations)} papers."
            )
            return user_recommendations

        recommendations = await asyncio.gather(
            *[
                gen_user_recommendations(user_id, user_data)
                for user_id, user_data in users.items()
            ]
        )
        return {
            user_id: user_recommendations
            for user_id, user_recommendations in zip(users.keys(), recommendations)
            if len(user_recommendations) > 0
        }

    async def recommend(self):
        """Generate and submit recommendations for all users."""
        total_users = self._connector.get_number_of_users()
        logger.info(f"Recommending papers for {total_users} users.")
        await self.gen_paper_representations()
        recommendation_count = 0
        while recommendation_count < total_users:
            user_ids = self._connector.get_user_ids(recommendation_count)
            users = self._connector.get_user_info(user_ids)
            interleaved = self._connector.get_interleaved_articles(user_ids)

            recommendations = await self.gen_recommendations(users, interleaved)

            if recommendations:
                self._connector.send_article_recommendations(recommendations)
            recommendation_count += len(user_ids)
            logger.info(f"Processed {recommendation_count} users.")
        logger.info("Finished recommending.")


if __name__ == "__main__":
    recommender = RecommenderSystem()
    asyncio.run(recommender.recommend())
