# ArXivDigest recommender (WIP)

Third-party recommender system for arXivDigest. Based on the [sample system](https://github.com/iai-group/arXivDigest/tree/master/sample) in the arXivDigest repo.

## Usage

1. Install dependencies with `pip install -r requirements.txt`
1. Fetch the arXivDigest submodule and install the `arxivdigest` package:
   ```sh
   git submodule update --init --recursive
   cd arxivdigest && pip install .
   ```
1. Run `python system.py`.

### Config

It is possible to override the default settings of the system by creating a config file in one of the following locations:
* `~/arxivdigest/system_config.json`
* `/etc/arxivdigest/system_config.json`
* `%cwd%/system_config.json`

#### Example

```json
{
   "arxivdigest": {
      "base_url": "https://api.arxivdigest.org/",
      "api_key": "4c02e337-c94b-48b6-b30e-0c06839c81e6"
   },
   "semantic_scholar": {
      "api_key": "873gd987h3d92873hd9283bnd92"
   },
   "elasticsearch": {
      "host": {"host": "127.0.0.1", "port": 9200},
      "index": "arxivdigest_articles"
   },
   "log_level": "FATAL"
}
```

`log_level` can be set to either "FATAL", "ERROR", "WARNING", "INFO", or "DEBUG".