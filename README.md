# ArXivDigest recommender

Third-party recommender system for arXivDigest. Based on the [sample system](https://github.com/iai-group/arXivDigest/tree/master/sample) in the arXivDigest repo.

## Usage

1. Fetch the arXivDigest repository submodule:
   ```sh
   git submodule --init --recursive
   ```
2. Install the `arxivdigest` Python package:
   ```sh
   cd arxivdigest && pip install .
   ```
1. Run `python system.py`.

### Config

It is possible to override the default settings of the system by creating a config file in one of the following locations:
* `~/arxivdigest/system_config.json`
* `/etc/arxivdigest/system_config.json`
* `%cwd%/system_config.json`
 
The file should be in JSON format and include the following keys:   
* `api_url`: Address of the arXivdigest API 
* `api_key`: An active API key for the arXivDigest API
* `elasticsearch_host`: Address and port of the Elasticsearch server
* `index_name`: Name of the index that will be used
* `log_level`: Level of messages to log accepts: 'FATAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG'

Example:

```json
{
   "api_url": "https://api.arxivdigest.org/",
   "api_key" : "4c02e337-c94b-48b6-b30e-0c06839c81e6",
   "elasticsearch_host": {"host": "127.0.0.1", "port": 9200},
   "index_name": "main_index"
}
```
