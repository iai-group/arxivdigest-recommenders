import asyncio
from collections import defaultdict
from typing import DefaultDict, Dict, Any

from arxivdigest_recommenders.recommender import ArxivdigestRecommender
from arxivdigest_recommenders.semantic_scholar import SemanticScholar
from arxivdigest_recommenders import config


def explanation(author: dict, collaborator: dict, num_cites: int) -> str:
    return (
        f"This article is authored by {author['name']}, who has been cited by your previous collaborator "
        f"{collaborator['name']} {num_cites} {'time' if num_cites == 1 else 'times'} in the last "
        f"{config.MAX_PAPER_AGE} years."
    )


class PrevCitedCollabRecommender(ArxivdigestRecommender):
    """Recommender system that recommends papers published by authors that have been cited by the user's previous
    collaborators."""

    def __init__(self):
        super().__init__(config.PREV_CITED_COLLAB_API_KEY, "PrevCitedCollabRecommender")
        self._citation_counts: DefaultDict[str, DefaultDict[str, int]] = defaultdict(
            lambda: defaultdict(int)
        )
        self._collaborators: DefaultDict[str, Dict[str, Any]] = defaultdict(dict)

    async def citation_counts(self, s2_id: str) -> DefaultDict[str, int]:
        if s2_id not in self._citation_counts:
            async with SemanticScholar() as s2:
                papers = await s2.author_papers(s2_id=s2_id)
            for paper in papers:
                for reference in paper["references"]:
                    for author in reference["authors"]:
                        if author["authorId"]:
                            self._citation_counts[s2_id][author["authorId"]] += 1
        return self._citation_counts[s2_id]

    async def collaborators(self, s2_id: str) -> Dict[str, Any]:
        if s2_id not in self._collaborators:
            async with SemanticScholar() as s2:
                papers = await s2.author_papers(s2_id=s2_id)
            for paper in papers:
                for author in paper["authors"]:
                    if author["authorId"] and author["authorId"] != s2_id:
                        self._collaborators[s2_id][author["authorId"]] = author
        return self._collaborators[s2_id]

    async def user_ranking(self, user, user_s2_id, paper_ids):
        collaborators = await self.collaborators(user_s2_id)
        results = []
        for paper_id in paper_ids:
            try:
                async with SemanticScholar() as s2:
                    paper = await s2.paper(arxiv_id=paper_id)
            except Exception:
                continue
            if len(paper["authors"]) == 0:
                continue
            score = 0
            most_cited_author = None
            citer = None
            for collaborator_id, collaborator in collaborators.items():
                citation_counts = await self.citation_counts(collaborator_id)
                authors = [
                    a
                    for a in paper["authors"]
                    if a["authorId"] != collaborator["authorId"]
                ]
                if len(authors) == 0:
                    continue
                collaborator_most_cited_author = max(
                    authors,
                    key=lambda a: citation_counts[a["authorId"]],
                )
                collaborator_score = citation_counts[
                    collaborator_most_cited_author["authorId"]
                ]
                if collaborator_score > score:
                    score = collaborator_score
                    most_cited_author = collaborator_most_cited_author
                    citer = collaborator
            results.append(
                {
                    "article_id": paper_id,
                    "score": score,
                    "explanation": explanation(most_cited_author, citer, score)
                    if score > 0
                    else "",
                }
            )
        return results


if __name__ == "__main__":
    recommender = PrevCitedCollabRecommender()
    asyncio.run(recommender.recommend())
