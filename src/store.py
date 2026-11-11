"""Cliente de Elasticsearch y creación de índices de demostración."""
from elasticsearch import Elasticsearch
from src.config import ES_URL, BOOK_INDEX, MEMORY_INDEX

BOOK_MAPPING = {
    "mappings": {"properties": {
        "title": {"type": "text", "analyzer": "spanish"},
        "section": {"type": "text", "analyzer": "spanish"},
        "content": {"type": "text", "analyzer": "spanish"},
        "source": {"type": "keyword"}, "chapter": {"type": "keyword"},
        "chunk": {"type": "integer"}
    }}
}
MEMORY_MAPPING = {
    "mappings": {"properties": {
        "user_id": {"type": "keyword"}, "text": {"type": "text", "analyzer": "spanish"},
        "created_at": {"type": "date"}
    }}
}

def client():
    return Elasticsearch(ES_URL, request_timeout=30)

def ensure_indices(es):
    if not es.indices.exists(index=BOOK_INDEX):
        es.indices.create(index=BOOK_INDEX, body=BOOK_MAPPING)
    if not es.indices.exists(index=MEMORY_INDEX):
        es.indices.create(index=MEMORY_INDEX, body=MEMORY_MAPPING)
