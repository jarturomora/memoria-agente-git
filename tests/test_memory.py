from unittest.mock import MagicMock
from src.memory import delete_memory, retrieve_memories, save_memory

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
