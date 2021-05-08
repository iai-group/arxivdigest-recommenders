# ArXivDigest Recommenders

Recommender systems for arXivDigest.

The author details and paper metadata used by the recommender systems are retrieved from the [Semantic Scholar API](https://api.semanticscholar.org/). 

## Available Recommenders

At the moment, there is only one recommender available.

### Venue Co-Publishing Recommender

Based on the assumption that a paper's relevance to a user is tied to the degree of venue co-publishing between the paper's authors and the user: a paper is relevant to a user if the authors of the paper publish at the same venues as the user. 

## Requirements

* Python 3.7+

## Setup

Install the `arxivdigest_recommenders` package and its dependencies with `pip install .`.

## Usage

### Venue Co-Publishing Recommender

Run `python -m arxivdigest_recommenders.venue_copub` to generate and submit recommendations for all arXivDigest users with known Semantic Scholar author IDs.

## Configuration

It is possible to override the default settings of the recommender systems by creating a config file in one of the following locations:
* `~/arxivdigest-recommenders/config.json`
* `/etc/arxivdigest-recommenders/config.json`
* `%cwd%/config.json`

### Structure

* `arxivdigest_base_url`
* `semantic_scholar`: Semantic Scholar API config
  * `api_key`
  * `max_requests`: max number of requests per window
  * `window_size`: window size in seconds
  * `cache_path`: path to SQLite database used to cache responses
* `max_paper_age`: max age (in years) of papers published by an author to consider when generating the author's vector representation
* `venue_blacklist`: (case-insensitive) list of venues that will be when creating venue author vectors
* `venue_copub_recommender`: venue co-publishing recommender config
  * `arxivdigest_api_key`
  * `max_explanation_venues`: max number of venues to include in explanations
* `log_level`: either "FATAL", "ERROR", "WARNING", "INFO", or "DEBUG"

### Example

```json
{
  "arxivdigest_base_url": "https://api.arxivdigest.org/",
  "semantic_scholar": {
    "api_key": "873gd987h3d92873hd9283bnd92",
    "max_requests": 100,
    "window_size": 1,
    "cache_path": "~/.cache/s2-aiohttp-cache.sqlite"
  },
  "max_paper_age": 5,
  "venue_blacklist": ["arxiv"],
  "venue_copub_recommender":  {
    "arxivdigest_api_key": "4c02e337-c94b-48b6-b30e-0c06839c81e6",
    "max_explanation_venues": 3
  },
  "log_level": "FATAL"
}
```
