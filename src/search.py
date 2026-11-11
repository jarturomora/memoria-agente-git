"""Recuperación léxica en español de fragmentos de *Pro Git*.

Elasticsearch utiliza BM25 para ordenar los documentos según su relevancia.
No hay embeddings ni llamadas a modelos en este módulo.
"""

from src.config import BOOK_INDEX


def search_book(es, question, size=3):
    """Devuelve los fragmentos del libro más relevantes para una pregunta.

    ``title^3`` y ``section^2`` son *boosts*: una coincidencia en el título
    pesa tres veces y una coincidencia en la sección dos veces. El contenido
    conserva el peso base. Esto suele priorizar capítulos temáticamente útiles.
    """
    response = es.search(
        index=BOOK_INDEX,
        size=size,
        query={
            "multi_match": {
                "query": question,
                "fields": ["title^3", "section^2", "content"],
            }
        },
    )

    # La CLI no necesita la estructura completa de Elasticsearch. Aplanamos
    # cada hit y conservamos ``_score`` para poder explicar la relevancia.
    return [
        {"score": hit["_score"], **hit["_source"]}
        for hit in response["hits"]["hits"]
    ]
