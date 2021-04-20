from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk
from arxivdigest.connector import ArxivdigestConnector
from typing import List

from semantic_scholar import SemanticScholar


def bulk_insert_articles(es: Elasticsearch, index: str, articles: List[dict]):
    """Bulk insert article data into the Elasticsearch index."""
    bulk_docs = []
    for article in articles:
        doc = {
            "_index": index,
            "_id": article.pop("arxivId"),
            "_source": article,
        }
        bulk_docs.append(doc)
    bulk(es, bulk_docs, request_timeout=10)


def run_indexing(
    es: Elasticsearch,
    index: str,
    arxivdigest_connector: ArxivdigestConnector,
    s2: SemanticScholar,
):
    """Get new additions to the arXivDigest database, fetch information about them from Semantic Scholar,
    and index them in Elasticsearch."""
    article_ids = arxivdigest_connector.get_article_ids()
    article_data = [s2.get_paper(arxiv_id=article_id) for article_id in article_ids]
    bulk_insert_articles(es, index, article_data)
