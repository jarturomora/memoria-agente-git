"""Memoria explícita, individual y editable: no se guarda automáticamente el chat."""
from datetime import datetime, timezone
from uuid import uuid4
from src.config import MEMORY_INDEX

def save_memory(es, user_id, text):
    if not user_id or not user_id.strip() or not text or not text.strip():
        raise ValueError("El usuario y el recuerdo no pueden estar vacíos.")
    memory_id = str(uuid4())
    es.index(index=MEMORY_INDEX, id=memory_id, document={
        "user_id": user_id, "text": text.strip(),
        "created_at": datetime.now(timezone.utc).isoformat()
    }, refresh="wait_for")
    return memory_id

def list_memories(es, user_id, size=100):
    response = es.search(index=MEMORY_INDEX, size=size,
        query={"term": {"user_id": user_id}}, sort=[{"created_at": "desc"}])
    return [{"id": x["_id"], **x["_source"]} for x in response["hits"]["hits"]]

def retrieve_memories(es, user_id, question, size=5):
    # Filtramos por usuario; los recuerdos cortos se traen todos en esta demo.
    # La selección léxica permite priorizar los relevantes y un pequeño conjunto
    # reciente actúa como fallback para preferencias generales.
    response = es.search(index=MEMORY_INDEX, size=size,
        query={"bool": {"filter": [{"term": {"user_id": user_id}}],
            "should": [{"match": {"text": question}}]}},
        sort=[{"_score": "desc"}, {"created_at": "desc"}])
    return [{"id": x["_id"], **x["_source"]} for x in response["hits"]["hits"]]

def delete_memory(es, user_id, memory_id):
    # Nunca permitir eliminar un recuerdo de otro usuario.
    result = es.options(ignore_status=404).get(index=MEMORY_INDEX, id=memory_id)
    if not result.get("found") or result.get("_source", {}).get("user_id") != user_id:
        return False
    es.delete(index=MEMORY_INDEX, id=memory_id, refresh="wait_for")
    return True
