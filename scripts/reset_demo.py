"""Elimina únicamente los índices de laboratorio; no borra el volumen de Docker."""
import argparse
from src.store import client
from src.config import BOOK_INDEX, MEMORY_INDEX

p = argparse.ArgumentParser()
p.add_argument("--confirm", action="store_true", help="Confirmar borrado irreversible de los índices")
a = p.parse_args()
if not a.confirm:
    p.error("Añade --confirm para eliminar los índices de la demo.")
es = client()
for name in [BOOK_INDEX, MEMORY_INDEX]:
    if es.indices.exists(index=name):
        es.indices.delete(index=name)
        print("Eliminado:", name)
