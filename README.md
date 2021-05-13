# ArXivDigest Recommenders

Recommender systems for arXivDigest.

The author details and paper metadata used by the recommender systems are retrieved from the [Semantic Scholar API](https://api.semanticscholar.org/). 

## Available Recommenders

At the moment, there is only one recommender available.

### Venue Co-Publishing Recommender

Based on the assumption that a paper's relevance to a user is tied to the degree of venue co-publishing between the paper's authors and the user: a paper is relevant to a user if the authors of the paper publish at the same venues as the user. 

## Requirements

* Python 3.7+
* MongoDB &mdash; Used to cache responses from the Semantic Scholar API

## Setup

### Development

Install the `arxivdigest_recommenders` package and its dependencies with `pip install -e .`. The `-e` flag makes the installation editable.

### Production

Install the `arxivdigest_recommenders` package directly from the master branch of this repository:
```shell
pip install git+https://github.com/olafapl/arxivdigest_recommenders.git
```

Updates can be installed with:
```shell
pip install --upgrade git+https://github.com/olafapl/arxivdigest_recommenders.git
```

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
* `mongodb`
  * `host`
  * `port`
* `semantic_scholar`: Semantic Scholar API config
  * `api_key`
  * `max_requests`: max number of requests per window
  * `window_size`: window size in seconds
  * `cache_db`: MongoDB database used for caching
  * `paper_cache_expiration`: expiration time (in days) for paper data
  * `author_cache_expiration`: expiration time (in days) for author data
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
  "mongodb": {
    "host": "127.0.0.1",
    "port": 27017
  },
  "semantic_scholar": {
    "api_key": "873gd987h3d92873hd9283bnd92",
    "max_requests": 100,
    "window_size": 1,
    "cache_db": "s2cache",
    "paper_cache_expiration": 30,
    "author_cache_expiration": 7
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
