import asyncio
from collections import defaultdict
from typing import DefaultDict

from arxivdigest_recommenders.recommender import ArxivdigestRecommender
from arxivdigest_recommenders.semantic_scholar import SemanticScholar
from arxivdigest_recommenders import config


def explanation(author: dict, num_cites: int) -> str:
    return (
        f"This article is authored by {author['name']}, who you have cited {num_cites} "
        f"{'time' if num_cites == 1 else 'times'} in the last {config.MAX_PAPER_AGE} years."
    )


class PrevCitedRecommender(ArxivdigestRecommender):
    """Recommender system that recommends papers published by authors that the user has previously cited."""

    def __init__(self):
        super().__init__(config.PREV_CITED_API_KEY, "PrevCitedRecommender")
        self._citation_counts: DefaultDict[str, DefaultDict[str, int]] = defaultdict(
            lambda: defaultdict(int)
        )

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

    async def user_ranking(self, user, user_s2_id, paper_ids):
        citation_counts = await self.citation_counts(user_s2_id)
        results = []
        for paper_id in paper_ids:
            try:
                async with SemanticScholar() as s2:
                    paper = await s2.paper(arxiv_id=paper_id)
            except Exception:
                continue
            if len(paper["authors"]) == 0 or user_s2_id in [
                a["authorId"] for a in paper["authors"]
            ]:
                continue
            most_cited_author = max(
                paper["authors"], key=lambda a: citation_counts[a["authorId"]]
            )
            score = citation_counts[most_cited_author["authorId"]]
            results.append(
                {
                    "article_id": paper_id,
                    "score": score,
                    "explanation": explanation(most_cited_author, score)
                    if score > 0
                    else "",
                }
            )
        return results


if __name__ == "__main__":
    recommender = PrevCitedRecommender()
    asyncio.run(recommender.recommend())
