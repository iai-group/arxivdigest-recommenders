import asyncio
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk
from arxivdigest.connector import ArxivdigestConnector
from collections import defaultdict
from typing import DefaultDict, List, Sequence

from arxivdigest_recommenders.recommender import ArxivdigestRecommender
from arxivdigest_recommenders.semantic_scholar import SemanticScholar
from arxivdigest_recommenders import config


def explanation(author: dict, num_cites: int, topics: Sequence[str]) -> str:
    topics = [f"**{topic}**" for topic in topics]
    if len(topics) > 1:
        topics[-1] = "and " + topics[-1]
    return (
        f"This article seems to be about {(' ' if len(topics) < 3 else ', ').join(topics)}, "
        f"and is authored by {author['name']}, who you have cited {num_cites} "
        f"{'time' if num_cites == 1 else 'times'} in the last {config.MAX_PAPER_AGE} years."
    )


class HybridRecommender(ArxivdigestRecommender):
    """Recommender system that recommends papers published by authors that the user has previously cited and that are
    relevant to the user's topics of interest."""

    def __init__(self):
        super().__init__(config.HYBRID_API_KEY, "HybridRecommender")
        self._citation_counts: DefaultDict[str, DefaultDict[str, int]] = defaultdict(
            lambda: defaultdict(int)
        )
        self._indexing_run = False
        self._es = Elasticsearch(hosts=[config.ELASTICSEARCH_HOST])
        if not self._es.indices.exists(config.HYBRID_INDEX):
            self._es.indices.create(config.HYBRID_INDEX)

    async def index_papers(self, paper_ids: Sequence[str]):
        self._logger.info("Indexing candidate papers in Elasticsearch.")
        async with SemanticScholar() as s2:
            papers = await asyncio.gather(
                *[s2.paper(arxiv_id=paper_id) for paper_id in paper_ids],
                return_exceptions=True,
            )
        paper_data = ArxivdigestConnector(config.HYBRID_API_KEY).get_article_data(
            paper_ids
        )
        bulk(
            self._es,
            (
                {
                    "_index": config.HYBRID_INDEX,
                    "_id": paper_id,
                    "_source": {
                        "title": paper["title"],
                        "abstract": paper["abstract"],
                        "fieldsOfStudy": paper["fieldsOfStudy"],
                        "topics": [t["topic"] for t in paper["topics"]],
                        "date": paper_data[paper_id]["date"],
                    },
                }
                for paper_id, paper in zip(paper_ids, papers)
                if not isinstance(paper, BaseException)
            ),
            request_timeout=10,
        )
        self._indexing_run = True

    def topic_search(self, topic: str):
        query = {
            "query": {
                "bool": {
                    "must": [
                        {"simple_query_string": {"query": topic}},
                    ],
                    "filter": {"range": {"date": {"gte": "now-7d"}}},
                }
            }
        }
        return self._es.search(
            index=config.HYBRID_INDEX, body=query, size=10000, _source=False
        )["hits"]["hits"]

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
        if not self._indexing_run:
            await self.index_papers(paper_ids)
        topic_scores = {
            topic: defaultdict(
                int,
                {paper["_id"]: paper["_score"] for paper in self.topic_search(topic)},
            )
            for topic in user["topics"]
        }
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
            top_topics = sorted(
                [
                    (topic, paper_scores[paper_id])
                    for topic, paper_scores in topic_scores.items()
                ],
                key=lambda t: t[1],
                reverse=True,
            )[: config.MAX_EXPLANATION_TOPICS]
            most_cited_author = max(
                paper["authors"], key=lambda a: citation_counts[a["authorId"]]
            )
            num_cites = citation_counts[most_cited_author["authorId"]]
            score = sum(topic_score for _, topic_score in top_topics) * num_cites
            results.append(
                {
                    "article_id": paper_id,
                    "score": score,
                    "explanation": explanation(
                        most_cited_author, num_cites, [topic for topic, _ in top_topics]
                    )
                    if score > 0
                    else "",
                }
            )
        return results


if __name__ == "__main__":
    recommender = HybridRecommender()
    asyncio.run(recommender.recommend())
