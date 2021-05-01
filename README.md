# ArXivDigest Recommenders

Recommender systems for arXivDigest.

Paper and author metadata are retrieved from Semantic Scholar. 

## Recommenders

There is currently only one recommender available.

### Venue-Based

Recommender based on the assumption that a paper's relevance to a user is tied to the degree of venue co-publishing between the paper's authors and the user: a paper is relevant to a user if the authors of the paper publish at the same venues as the user. 

## Requirements

* Python 3.7+

## Setup

Install the `arxivdigest_recommenders` package and its dependencies with `pip install .`.

## Usage

Run `python -m arxivdigest_recommenders.venue_based_recommender` to run the venue-based recommender. This will generate and submit recommendations for all arXivDigest users with known Semantic Scholar author IDs.

### Configuration

It is possible to override the default settings of the recommender systems by creating a config file in one of the following locations:
* `~/arxivdigest/system_config.json`
* `/etc/arxivdigest/system_config.json`
* `%cwd%/system_config.json`

#### Structure

* `arxivdigest`: arXivDigest API config
   * `base_url`
   * `api_key`
* `semantic_scholar`: Semantic Scholar API config
   * `api_key`
   * `max_requests`: max number of requests per window
   * `window_size`: window size in seconds
   * `cache_path`: path to SQLite database used to cache responses
* `venue_blacklist`: (case-insensitive) list of venues that will be ignored by the venue-based recommender
* `log_level`: either "FATAL", "ERROR", "WARNING", "INFO", or "DEBUG"

#### Example

```json
{
   "arxivdigest": {
      "base_url": "https://api.arxivdigest.org/",
      "api_key": "4c02e337-c94b-48b6-b30e-0c06839c81e6"
   },
   "semantic_scholar": {
      "api_key": "873gd987h3d92873hd9283bnd92",
      "max_requests": 100,
      "window_size": 1,
      "cache_path": "~/.cache/s2-aiohttp-cache.sqlite"
   },
   "venue_blacklist": ["arxiv"],
   "log_level": "FATAL"
}
```
