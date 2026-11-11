"""Operaciones de memoria explícita, individual y editable.

La aplicación nunca guarda automáticamente el chat. Un recuerdo solo se crea
cuando el usuario ejecuta ``remember``; esta decisión hace visible el control y
el consentimiento en una demo educativa.
"""

from datetime import datetime, timezone
from uuid import uuid4

from src.config import MEMORY_INDEX


def reset_memories(es):
    """Elimina todos los recuerdos sin borrar ni recrear su índice.

    Devuelve la cantidad eliminada. Un índice ausente equivale a una memoria
    vacía, lo que permite ejecutar el comando repetidamente sin error.
    """
    if not es.indices.exists(index=MEMORY_INDEX):
        return 0

    # ``delete_by_query`` elimina documentos, pero conserva mapping y ajustes.
    # La espera y el refresh garantizan que el contador posterior ya vea el
    # resultado antes de que la CLI informe al usuario.
    result = es.delete_by_query(
        index=MEMORY_INDEX,
        query={"match_all": {}},
        wait_for_completion=True,
        refresh=True,
    )
    return result.get("deleted", 0)


def save_memory(es, user_id, text):
    """Guarda un recuerdo asociado a un usuario y devuelve su identificador."""
    # Rechazar cadenas vacías evita documentos inútiles difíciles de recuperar.
    if not user_id or not user_id.strip() or not text or not text.strip():
        raise ValueError("El usuario y el recuerdo no pueden estar vacíos.")

    # UUID permite crear IDs localmente sin pedir primero un contador al índice.
    memory_id = str(uuid4())
    es.index(
        index=MEMORY_INDEX,
        id=memory_id,
        document={
            "user_id": user_id,
            "text": text.strip(),
            # UTC evita ambigüedades si la demo se ejecuta en otra zona horaria.
            "created_at": datetime.now(timezone.utc).isoformat(),
        },
        # Esperar al refresh hace visible el recuerdo en la consulta siguiente.
        refresh="wait_for",
    )
    return memory_id


def list_memories(es, user_id, size=100):
    """Lista los recuerdos de un usuario, empezando por los más recientes."""
    response = es.search(
        index=MEMORY_INDEX,
        size=size,
        # ``term`` exige coincidencia exacta porque ``user_id`` es keyword.
        query={"term": {"user_id": user_id}},
        sort=[{"created_at": "desc"}],
    )
    return [
        {"id": hit["_id"], **hit["_source"]}
        for hit in response["hits"]["hits"]
    ]


def retrieve_memories(es, user_id, question, size=5):
    """Recupera preferencias del usuario relacionadas con una pregunta.

    El filtro por usuario es obligatorio. La coincidencia léxica solo ordena:
    una preferencia general puede seguir apareciendo por su recencia aunque no
    comparta palabras exactas con la pregunta.
    """
    response = es.search(
        index=MEMORY_INDEX,
        size=size,
        query={
            "bool": {
                # ``filter`` no altera el score y aísla los datos del usuario.
                "filter": [{"term": {"user_id": user_id}}],
                # ``should`` aumenta la puntuación de recuerdos relacionados.
                "should": [{"match": {"text": question}}],
            }
        },
        # Primero relevancia; después recencia para resolver empates.
        sort=[{"_score": "desc"}, {"created_at": "desc"}],
    )
    return [
        {"id": hit["_id"], **hit["_source"]}
        for hit in response["hits"]["hits"]
    ]


def delete_memory(es, user_id, memory_id):
    """Elimina un recuerdo solo si pertenece al usuario indicado."""
    # ``ignore_status=404`` convierte "no existe" en una respuesta comprobable
    # en lugar de lanzar una excepción desde el cliente.
    result = es.options(ignore_status=404).get(index=MEMORY_INDEX, id=memory_id)

    # Esta comprobación evita que conocer un UUID permita borrar datos ajenos.
    if not result.get("found") or result.get("_source", {}).get("user_id") != user_id:
        return False

    es.delete(index=MEMORY_INDEX, id=memory_id, refresh="wait_for")
    return True
