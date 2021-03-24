import json
import logging
import os
import sys
from elasticsearch import Elasticsearch
from arxivdigest.connector import ArxivdigestConnector

from index import run_indexing
from init_index import init_index


file_locations = [
    os.path.expanduser("~") + "/arxivdigest/system_config.json",
    "/etc/arxivdigest/system_config.json",
    os.curdir + "/system_config.json",
]


def get_config_from_file(file_paths):
    """Checks the given list of file paths for a config file,
    returns None if not found."""
    for file_location in file_paths:
        if os.path.isfile(file_location):
            print("Found config file at: {}".format(os.path.abspath(file_location)))
            with open(file_location) as file:
                return json.load(file)
    return {}


config_file = get_config_from_file(file_locations)

API_KEY = config_file.get("api_key", "4c02e337-c94b-48b6-b30e-0c06839c81e6")
API_URL = config_file.get("api_url", "https://api.arxivdigest.org/")
INDEX = config_file.get("index_name", "main_index")
ELASTICSEARCH_HOST = config_file.get(
    "elasticsearch_host", {"host": "127.0.0.1", "port": 9200}
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
    """Makes and sends recommendations to all users."""
    total_users = arxivdigest_connector.get_number_of_users()
    logger.info("Starting recommending articles for {} users".format(total_users))
    recommendation_count = 0
    while recommendation_count < total_users:
        user_ids = arxivdigest_connector.get_user_ids(recommendation_count)
        user_info = arxivdigest_connector.get_user_info(user_ids)
        interleaved = arxivdigest_connector.get_interleaved_articles(user_ids)

        recommendations = make_recommendations(es, user_info, interleaved, index)

        if recommendations:
            arxivdigest_connector.send_article_recommendations(recommendations)
        recommendation_count += len(user_ids)
        logger.info("Processed {} users".format(recommendation_count))


def run(api_key, api_url, index):
    """Runs the recommender system:
    - Updates index with new articles
    - Fetches user info for all users
    - Creates and sends recommendations for each user
    """
    es = Elasticsearch(hosts=[ELASTICSEARCH_HOST])
    arxivdigest_connector = ArxivdigestConnector(api_key, api_url)
    if not es.indices.exists(index=index):
        logger.info("Creating index.")
        init_index(es, index)
    logger.info("Indexing articles from arXivDigest API.")
    run_indexing(es, index, arxivdigest_connector)
    #recommend(es, arxivdigest_connector, index)
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

    run(API_KEY, API_URL, INDEX)
