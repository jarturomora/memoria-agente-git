"""Pruebas unitarias de aislamiento, recuperación y borrado de memoria.

``MagicMock`` registra las llamadas que recibiría Elasticsearch. Así se valida
la consulta exacta sin modificar los datos locales de la demostración.
"""

from unittest.mock import MagicMock

from src.config import BOOK_INDEX, MEMORY_INDEX
from src.memory import delete_memory, reset_memories, retrieve_memories, save_memory


def test_reset_memories_deletes_only_memory_documents():
    """El reset usa delete-by-query solo sobre ``agent-memories``."""
    es = MagicMock()
    es.indices.exists.return_value = True
    es.delete_by_query.return_value = {"deleted": 3}

    # Además del contador, verificamos los parámetros de consistencia elegidos.
    assert reset_memories(es) == 3
    es.delete_by_query.assert_called_once_with(
        index=MEMORY_INDEX,
        query={"match_all": {}},
        wait_for_completion=True,
        refresh=True,
    )
    es.indices.delete.assert_not_called()
    es.indices.create.assert_not_called()


def test_reset_memories_keeps_mapping_and_book_index_untouched():
    """El reset no recrea índices, cambia mappings ni apunta a ``progit``."""
    es = MagicMock()
    es.indices.exists.return_value = True
    es.delete_by_query.return_value = {"deleted": 1}

    reset_memories(es)

    assert MEMORY_INDEX != BOOK_INDEX
    assert es.delete_by_query.call_args.kwargs["index"] == MEMORY_INDEX
    es.indices.put_mapping.assert_not_called()
    es.indices.delete.assert_not_called()
    es.indices.create.assert_not_called()


def test_reset_memories_is_idempotent_when_index_is_empty():
    """Repetir el reset sobre memoria vacía debe devolver cero sin fallar."""
    es = MagicMock()
    es.indices.exists.return_value = True
    es.delete_by_query.return_value = {"deleted": 0}

    assert reset_memories(es) == 0
    assert reset_memories(es) == 0


def test_reset_memories_handles_missing_index():
    """Un índice de memoria ausente se interpreta como una memoria vacía."""
    es = MagicMock()
    es.indices.exists.return_value = False

    assert reset_memories(es) == 0
    es.delete_by_query.assert_not_called()


def test_save_memory_writes_user_scoped_doc():
    """Cada documento guardado conserva usuario, texto e ID propio."""
    es = MagicMock()
    mem_id = save_memory(es, "alumno-01", "Prefiero PowerShell")

    assert mem_id
    doc = es.index.call_args.kwargs["document"]
    assert doc["user_id"] == "alumno-01"
    assert doc["text"] == "Prefiero PowerShell"

def test_cross_user_delete_denied():
    """Un usuario no puede borrar un recuerdo perteneciente a otro."""
    es = MagicMock()
    es.get.return_value = {"found": True, "_source": {"user_id": "alumno-02"}}
    assert delete_memory(es, "alumno-01", "abc") is False
    es.delete.assert_not_called()

def test_retrieval_user_filter():
    """Toda recuperación incluye obligatoriamente un filtro exacto de usuario."""
    es = MagicMock()
    es.search.return_value = {"hits": {"hits": []}}
    retrieve_memories(es, "alumno-01", "branch")
    query = es.search.call_args.kwargs["query"]
    assert query["bool"]["filter"] == [{"term": {"user_id": "alumno-01"}}]
