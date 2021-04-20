INDEX_SETTINGS = {
    "settings": {
        "index": {"number_of_shards": 1, "number_of_replicas": 0},
    }
}


def init_index(es, index):
    es.indices.create(index=index, body=INDEX_SETTINGS)
