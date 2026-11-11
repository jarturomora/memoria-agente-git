"""Recuperación léxica en español de fragmentos de Pro Git (BM25)."""
from src.config import BOOK_INDEX

def search_book(es, question, size=3):
    response = es.search(index=BOOK_INDEX, size=size, query={
        "multi_match": {"query": question, "fields": ["title^3", "section^2", "content"]}
    })
    return [{"score": x["_score"], **x["_source"]} for x in response["hits"]["hits"]]
