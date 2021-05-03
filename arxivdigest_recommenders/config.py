import os
import json
from typing import List


file_locations = [
    os.path.expanduser("~") + "/arxivdigest-recommenders/config.json",
    "/etc/arxivdigest-recommenders/config.json",
    os.curdir + "/config.json",
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
S2_CONFIG = config_file.get("semantic_scholar", {})
S2_API_KEY = S2_CONFIG.get("api_key")
S2_MAX_REQUESTS = S2_CONFIG.get("max_requests", 100)
S2_WINDOW_SIZE = S2_CONFIG.get("window_size", 300)
S2_CACHE_PATH = S2_CONFIG.get("cache_path", "aiohttp-cache.sqlite")
MAX_PAPER_AGE = config_file.get("max_paper_age", 5)
VENUE_CONFIG = config_file.get("venue_based_recommender", {})
VENUE_BASED_RECOMMENDER_API_KEY = VENUE_CONFIG.get("arxivdigest_api_key", "")
VENUE_BLACKLIST = [
    venue.lower() for venue in VENUE_CONFIG.get("venue_blacklist", ["arxiv"])
]
MAX_EXPLANATION_VENUES = VENUE_CONFIG.get("max_explanation_venues", 3)
