import json
import logging
import os
import sys
from typing import List
from elasticsearch import Elasticsearch
from arxivdigest.connector import ArxivdigestConnector

from index import run_indexing
from init_index import init_index
from semantic_scholar import SemanticScholar


file_locations = [
    os.path.expanduser("~") + "/arxivdigest/system_config.json",
    "/etc/arxivdigest/system_config.json",
    os.curdir + "/system_config.json",
]


def get_config_from_file(file_paths: List[str]):
    """Checks the given list of file paths for a config file,
    returns None if not found."""
    for file_location in file_paths:
        if os.path.isfile(file_location):
            print("Found config file at: {}".format(os.path.abspath(file_location)))
            with open(file_location) as file:
                return json.load(file)
    return {}


config_file = get_config_from_file(file_locations)

ARXIVDIGEST_CONFIG = config_file.get("arxivdigest", {})
ARXIVDIGEST_BASE_URL = ARXIVDIGEST_CONFIG.get(
    "base_url", "https://api.arxivdigest.org/"
)
ARXIVDIGEST_API_KEY = ARXIVDIGEST_CONFIG.get(
    "api_key", "4c02e337-c94b-48b6-b30e-0c06839c81e6"
)
S2_CONFIG = config_file.get("semantic_scholar", {})
S2_API_KEY = S2_CONFIG.get("api_key")
S2_MAX_REQUESTS = S2_CONFIG.get("max_requests", 100)
S2_WINDOW_SIZE = S2_CONFIG.get("window_size", 300)
ELASTICSEARCH_CONFIG = config_file.get("elasticsearch", {})
ELASTICSEARCH_INDEX = ELASTICSEARCH_CONFIG.get("index", "arxivdigest_articles")
ELASTICSEARCH_HOST = ELASTICSEARCH_CONFIG.get(
    "host", {"host": "127.0.0.1", "port": 9200}
)


def make_recommendation(es: Elasticsearch, topics, index, n_topics_explanation=3):
    pass


def create_explanation(es: Elasticsearch, topics):
    pass


def make_recommendations(
    es: Elasticsearch, user_info, interleaved_articles, index, n_articles=10
):
    pass


def recommend(
    es: Elasticsearch, arxivdigest_connector: ArxivdigestConnector, index: str
):
    """Generate and send recommendations for all users."""
    total_users = arxivdigest_connector.get_number_of_users()
    logger.info(f"Starting recommending articles for {total_users} users")
    recommendation_count = 0
    while recommendation_count < total_users:
        user_ids = arxivdigest_connector.get_user_ids(recommendation_count)
        user_info = arxivdigest_connector.get_user_info(user_ids)
        interleaved = arxivdigest_connector.get_interleaved_articles(user_ids)

        recommendations = make_recommendations(es, user_info, interleaved, index)

        if recommendations:
            arxivdigest_connector.send_article_recommendations(recommendations)
        recommendation_count += len(user_ids)
        logger.info(f"Processed {recommendation_count} users")


def run():
    """Run the recommender system:
    - Update index with new articles
    - Fetch user info for all users
    - Create and send recommendations for each user
    """
    es = Elasticsearch(hosts=[ELASTICSEARCH_HOST])
    arxivdigest_connector = ArxivdigestConnector(
        ARXIVDIGEST_API_KEY, ARXIVDIGEST_BASE_URL
    )
    s2 = SemanticScholar(S2_API_KEY, S2_MAX_REQUESTS, S2_WINDOW_SIZE)
    if not es.indices.exists(index=ELASTICSEARCH_INDEX):
        logger.info("Creating index.")
        init_index(es, ELASTICSEARCH_INDEX)
    logger.info("Indexing articles from arXivDigest API.")
    run_indexing(es, ELASTICSEARCH_INDEX, arxivdigest_connector, s2)
    recommend(es, arxivdigest_connector, ELASTICSEARCH_INDEX)
    logger.info("\nFinished recommending articles.")


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
    log_level = config_file.get("log_level", "INFO").upper()
    logger.setLevel(log_levels.get(log_level, 20))

    run()
