# arXivDigest Recommenders

Recommender systems for [arXivDigest](https://github.com/iai-group/arXivDigest).

The author details and paper metadata used by the recommender systems are retrieved from the [Semantic Scholar API](https://api.semanticscholar.org/). 

## Available Recommenders

| **Recommender system** | **Module**           | **Class**                   |
|------------------------|----------------------|-----------------------------|
| Frequent Venues        | `frequent_venues.py` | `FrequentVenuesRecommender` |
| Venue Co-Publishing    | `venue_copub.py`     | `VenueCoPubRecommender`     |

### Frequent Venues

It is not uncommon for researchers to publish numerous papers at the same venue over time. This recommender is based on the assumption that a paper published at a venue that a user frequently publishes at is more relevant to the user than other papers.

### Venue Co-Publishing

This recommender is based on the assumption that a paper's relevance to a user is tied to the degree of venue co-publishing between the paper's authors and the user: a paper is relevant to a user if the authors of the paper publish at the same venues as the user. 

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

### Running a Single Recommender

The different recommenders can be run directly by running the modules containing their implementation. As an example, the Frequent Venues recommender can be run by executing `python -m arxivdigest_recommenders.frequent_venues`.

### Running Multiple Recommenders

The Semantic Scholar API rate limit defined in the config file (or the default one of 100 requests per five minute window) works only on a per-process basis, meaning that if two recommenders are run at the same time using the aforementioned method, the effective rate limit will be double that of what we expect. To avoid this problem, run the recommenders in the same process:

```python
import asyncio
from arxivdigest_recommenders.frequent_venues import FrequentVenuesRecommender
from arxivdigest_recommenders.venue_copub import VenueCoPubRecommender


async def main():
    fv = FrequentVenuesRecommender()
    vc = VenueCoPubRecommender()
    await asyncio.gather(*[fv.recommend(), vc.recommend()])


asyncio.run(main())
```

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
* `frequent_venues_recommender`: Frequent Venues recomender config
  * `arxivdigest_api_key`
* `venue_copub_recommender`: Venue Co-Publishing recommender config
  * `arxivdigest_api_key`
  * `max_explanation_venues`: max number of venues to include in explanations
* `log_level`: either "FATAL", "ERROR", "WARNING", "INFO", or "DEBUG"

### Defaults

```json
{
  "arxivdigest_base_url": "https://api.arxivdigest.org/",
  "mongodb": {
    "host": "127.0.0.1",
    "port": 27017
  },
  "semantic_scholar": {
    "api_key": null,
    "max_requests": 100,
    "window_size": 300,
    "cache_db": "s2cache",
    "paper_cache_expiration": 30,
    "author_cache_expiration": 7
  },
  "max_paper_age": 5,
  "venue_blacklist": ["arxiv"],
  "frequent_venues_recommender": {
    "arxivdigest_api_key": null
  },
  "venue_copub_recommender":  {
    "arxivdigest_api_key": null,
    "max_explanation_venues": 3
  },
  "log_level": "INFO"
}
```
