from unittest.mock import MagicMock
from src.config import BOOK_INDEX, MEMORY_INDEX
from src.memory import delete_memory, reset_memories, retrieve_memories, save_memory


def test_reset_memories_deletes_only_memory_documents():
    es = MagicMock()
    es.indices.exists.return_value = True
    es.delete_by_query.return_value = {"deleted": 3}

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
    es = MagicMock()
    es.indices.exists.return_value = True
    es.delete_by_query.return_value = {"deleted": 0}

    assert reset_memories(es) == 0
    assert reset_memories(es) == 0


def test_reset_memories_handles_missing_index():
    es = MagicMock()
    es.indices.exists.return_value = False

    assert reset_memories(es) == 0
    es.delete_by_query.assert_not_called()

def test_save_memory_writes_user_scoped_doc():
    es = MagicMock()
    mem_id = save_memory(es, "alumno-01", "Prefiero PowerShell")
    assert mem_id
    doc = es.index.call_args.kwargs["document"]
    assert doc["user_id"] == "alumno-01"
    assert doc["text"] == "Prefiero PowerShell"

def test_cross_user_delete_denied():
    es = MagicMock()
    es.get.return_value = {"found": True, "_source": {"user_id": "alumno-02"}}
    assert delete_memory(es, "alumno-01", "abc") is False
    es.delete.assert_not_called()

def test_retrieval_user_filter():
    es = MagicMock()
    es.search.return_value = {"hits": {"hits": []}}
    retrieve_memories(es, "alumno-01", "branch")
    query = es.search.call_args.kwargs["query"]
    assert query["bool"]["filter"] == [{"term": {"user_id": "alumno-01"}}]
