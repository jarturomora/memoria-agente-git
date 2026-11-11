"""Conexión a Elasticsearch y definición del esquema de los índices.

Un *mapping* cumple un papel parecido al esquema de una tabla: indica cómo se
interpreta cada campo. Esta demo mantiene dos mappings separados para reforzar
la diferencia entre conocimiento documental y memoria del usuario.
"""

from elasticsearch import Elasticsearch

from src.config import ES_URL, BOOK_INDEX, MEMORY_INDEX

# Mapping del conocimiento documental. Los campos de texto usan el analizador
# español para normalizar palabras y mejorar las coincidencias lingüísticas.
BOOK_MAPPING = {
    "mappings": {
        "properties": {
            # ``text`` se analiza y puede participar en búsquedas BM25.
            "title": {"type": "text", "analyzer": "spanish"},
            "section": {"type": "text", "analyzer": "spanish"},
            "content": {"type": "text", "analyzer": "spanish"},
            # ``keyword`` conserva el valor exacto para filtros y trazabilidad.
            "source": {"type": "keyword"},
            "chapter": {"type": "keyword"},
            "chunk": {"type": "integer"},
        }
    }
}

# Mapping de los recuerdos. ``user_id`` es ``keyword`` porque se filtra por
# igualdad exacta; no queremos que Elasticsearch analice o divida ese valor.
MEMORY_MAPPING = {
    "mappings": {
        "properties": {
            "user_id": {"type": "keyword"},
            "text": {"type": "text", "analyzer": "spanish"},
            "created_at": {"type": "date"},
        }
    }
}


def client():
    """Construye el cliente oficial apuntando al Elasticsearch configurado.

    El timeout evita que la CLI quede esperando indefinidamente si Docker está
    detenido o la máquina está bajo mucha carga.
    """
    return Elasticsearch(ES_URL, request_timeout=30)


def ensure_indices(es):
    """Crea los índices que falten sin reemplazar los que ya existen.

    Esta función es idempotente: puede llamarse varias veces y nunca borra
    documentos ni cambia mappings existentes.
    """
    # Cada comprobación nombra el índice explícitamente para impedir que una
    # operación sobre memoria afecte por accidente al corpus del libro.
    if not es.indices.exists(index=BOOK_INDEX):
        es.indices.create(index=BOOK_INDEX, body=BOOK_MAPPING)
    if not es.indices.exists(index=MEMORY_INDEX):
        es.indices.create(index=MEMORY_INDEX, body=MEMORY_MAPPING)
