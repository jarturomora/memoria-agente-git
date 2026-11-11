"""Elimina los dos índices para reiniciar completamente el laboratorio.

Este script es más destructivo que ``src.cli reset-memory``: borra tanto el
libro como los recuerdos. No elimina el volumen de Docker, de modo que los
índices podrán crearse y cargarse de nuevo.
"""

import argparse

from src.config import BOOK_INDEX, MEMORY_INDEX
from src.store import client

# La confirmación mediante flag permite usar el script en automatizaciones sin
# convertir una ejecución accidental en un borrado silencioso.
p = argparse.ArgumentParser()
p.add_argument("--confirm", action="store_true", help="Confirmar borrado irreversible de los índices")
a = p.parse_args()
if not a.confirm:
    p.error("Añade --confirm para eliminar los índices de la demo.")

es = client()

# La lista es explícita: nunca se utiliza un comodín como ``*`` que pudiera
# alcanzar índices ajenos al laboratorio.
for name in [BOOK_INDEX, MEMORY_INDEX]:
    if es.indices.exists(index=name):
        es.indices.delete(index=name)
        print("Eliminado:", name)
