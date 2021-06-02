import os
import json
from typing import List


file_locations = [
    os.curdir + "/config.json",
    os.path.expanduser("~") + "/arxivdigest-recommenders/config.json",
    "/etc/arxivdigest-recommenders/config.json",
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

LOG_LEVEL = config_file.get("log_level", "INFO").upper()
ARXIVDIGEST_BASE_URL = config_file.get(
    "arxivdigest_base_url", "https://api.arxivdigest.org/"
)
MONGODB_CONFIG = config_file.get("mongodb", {})
MONGODB_HOST = MONGODB_CONFIG.get("host", "127.0.0.1")
MONGODB_PORT = MONGODB_CONFIG.get("port", 27017)
ELASTICSEARCH_HOST = config_file.get(
    "elasticsearch", {"host": "127.0.0.1", "port": 9200}
)
S2_CONFIG = config_file.get("semantic_scholar", {})
S2_API_KEY = S2_CONFIG.get("api_key")
S2_MAX_CONCURRENT_REQUESTS = S2_CONFIG.get("max_concurrent_requests", 100)
S2_MAX_REQUESTS = S2_CONFIG.get("max_requests", 100)
S2_WINDOW_SIZE = S2_CONFIG.get("window_size", 300)
S2_CACHE_RESPONSES = S2_CONFIG.get("cache_responses", True)
S2_CACHE_DB = S2_CONFIG.get("cache_db", "s2cache")
S2_PAPER_EXPIRATION = S2_CONFIG.get("paper_cache_expiration", 30)
S2_AUTHOR_EXPIRATION = S2_CONFIG.get("author_cache_expiration", 7)
MAX_PAPER_AGE = config_file.get("max_paper_age", 5)
MAX_EXPLANATION_VENUES = config_file.get("max_explanation_venues", 3)
VENUE_BLACKLIST = [
    venue.lower() for venue in config_file.get("venue_blacklist", ["arxiv"])
]
FREQUENT_VENUES_API_KEY = config_file.get("frequent_venues_recommender", {}).get(
    "arxivdigest_api_key", ""
)
VENUE_COPUB_CONFIG = config_file.get("venue_copub_recommender", {})
VENUE_COPUB_API_KEY = VENUE_COPUB_CONFIG.get("arxivdigest_api_key", "")
WEIGHTED_INF_CONFIG = config_file.get("weighted_inf_recommender", {})
WEIGHTED_INF_API_KEY = WEIGHTED_INF_CONFIG.get("arxivdigest_api_key", "")
WEIGHTED_INF_MIN_INFLUENCE = WEIGHTED_INF_CONFIG.get("min_influence", 20)
PREV_CITED_API_KEY = config_file.get("prev_cited_recommender", {}).get(
    "arxivdigest_api_key", ""
)
PREV_CITED_COLLAB_API_KEY = config_file.get("prev_cited_collab_recommender", {}).get(
    "arxivdigest_api_key", ""
)
HYBRID_CONFIG = config_file.get("hybrid_recommender", {})
HYBRID_API_KEY = HYBRID_CONFIG.get("arxivdigest_api_key", "")
HYBRID_INDEX = HYBRID_CONFIG.get("index", "arxivdigest_papers")
MAX_EXPLANATION_TOPICS = HYBRID_CONFIG.get("max_explanation_topics", 3)
