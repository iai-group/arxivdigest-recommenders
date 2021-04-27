import os
import json
from typing import List


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

LOG_LEVEL = config_file.get("log_level", "INFO").upper()
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
VENUE_BLACKLIST = [venue.lower() for venue in config_file.get("venue_blacklist", ["arxiv"])]
