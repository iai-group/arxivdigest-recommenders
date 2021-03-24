INDEX_SETTINGS = {
    "settings": {
        "index": {"number_of_shards": 1, "number_of_replicas": 0},
    },
    "mappings": {
        "properties": {
            "title": {
                "type": "text",
                "term_vector": "with_positions",
                "analyzer": "english",
            },
            "abstract": {
                "type": "text",
                "term_vector": "with_positions",
                "analyzer": "english",
            },
            "authors": {
                "type": "nested",
                "properties": {
                    "firstname": {"type": "keyword"},
                    "lastname": {"type": "keyword"},
                    "affiliations": {"type": "keyword"},
                },
            },
            "categories": {
                "type": "keyword",
            },
            "comments": {
                "type": "text",
                "term_vector": "with_positions",
                "analyzer": "english",
            },
            "doi": {
                "type": "keyword",
            },
            "journal": {
                "type": "keyword",
            },
            "license": {
                "type": "keyword",
            },
            "date": {"type": "date", "format": "date"},
            "catch_all": {
                "type": "text",
                "term_vector": "with_positions",
                "analyzer": "english",
            },
        }
    },
}


def init_index(es, index):
    es.indices.create(index=index, body=INDEX_SETTINGS)
