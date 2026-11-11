"""Interfaz de línea de comandos del laboratorio.

Se ejecuta desde la raíz con ``python -m src.cli <comando>``. La CLI contiene
solo orquestación y presentación; las operaciones viven en módulos pequeños
para poder probarlas sin conectar a Elasticsearch.
"""

import argparse

from src.agent import answer
from src.config import BOOK_INDEX, MEMORY_INDEX
from src.memory import delete_memory, list_memories, reset_memories, save_memory
from src.search import search_book
from src.store import client, ensure_indices


def main(argv=None):
    """Analiza argumentos, ejecuta el comando elegido y muestra su resultado.

    ``argv`` permite que las pruebas pasen una lista controlada. Cuando vale
    ``None``, argparse usa los argumentos escritos en la terminal.
    """
    p = argparse.ArgumentParser(description="Laboratorio: conocimiento y memoria con Elasticsearch")
    sub = p.add_subparsers(dest="command", required=True)

    # Cada subparser representa un verbo visible de la aplicación.
    sub.add_parser("status")
    q = sub.add_parser("search", help="Busca pasajes del libro sin LLM")
    q.add_argument("question")
    r = sub.add_parser("remember", help="Guarda un recuerdo explícito")
    r.add_argument("text")
    ls = sub.add_parser("memories", help="Muestra los recuerdos")
    delete = sub.add_parser("forget", help="Elimina un recuerdo propio")
    delete.add_argument("memory_id")
    reset = sub.add_parser(
        "reset-memory",
        help="Elimina todos los recuerdos sin modificar el índice de Pro Git",
    )
    reset.add_argument(
        "--confirm",
        action="store_true",
        help="Confirma el borrado sin solicitar entrada interactiva",
    )
    a = sub.add_parser("ask", help="Muestra contexto; --llm genera respuesta")
    a.add_argument("question")
    a.add_argument("--llm", action="store_true")

    # Estos comandos operan en el ámbito de un usuario de demostración.
    for cmd in [r, ls, delete, a]:
        cmd.add_argument("--user", default="alumno-01")

    args = p.parse_args(argv)

    # Pedimos confirmación antes de crear siquiera el cliente. Una cancelación
    # no establece conexión ni ejecuta operaciones en Elasticsearch.
    if args.command == "reset-memory" and not args.confirm:
        confirmation = input(
            "Esta operación eliminará todos los recuerdos. "
            "Escribe BORRAR para confirmar: "
        )
        if confirmation != "BORRAR":
            print("Operación cancelada; no se ha eliminado ningún recuerdo.")
            return

    es = client()
    try:
        # ``ping`` ofrece un error claro si Docker todavía no está listo.
        if not es.ping():
            p.error("Elasticsearch no responde. Inicia Docker y revisa http://localhost:9200")

        # reset-memory no crea, elimina ni modifica ningún índice: solo borra
        # documentos del índice de memoria si este ya existe.
        if args.command != "reset-memory":
            ensure_indices(es)

        # A partir de aquí se delega la lógica en funciones de store, search,
        # memory y agent. La CLI se limita a formatear sus respuestas.
        if args.command == "status":
            print("Elasticsearch OK:", es.info()["version"]["number"])
            for index in [BOOK_INDEX, MEMORY_INDEX]:
                print(f"  {index}: {es.count(index=index)['count']} documentos")
        elif args.command == "search":
            show_passages(search_book(es, args.question))
        elif args.command == "remember":
            print("Recuerdo guardado:", save_memory(es, args.user, args.text))
        elif args.command == "memories":
            ms = list_memories(es, args.user)
            if not ms:
                print("Sin recuerdos.")
            for memory in ms:
                print(f"{memory['id']} | {memory['text']}")
        elif args.command == "forget":
            deleted = delete_memory(es, args.user, args.memory_id)
            print(
                "Recuerdo eliminado."
                if deleted
                else "No existe o pertenece a otro usuario."
            )
        elif args.command == "reset-memory":
            deleted = reset_memories(es)
            print(f"Recuerdos eliminados: {deleted}")
        elif args.command == "ask":
            passages, memories, output = answer(es, args.user, args.question, args.llm)
            print("\n=== CONOCIMIENTO RECUPERADO ===")
            show_passages(passages)
            print("\n=== MEMORIA RECUPERADA ===")
            for memory in memories:
                print("-", memory["text"])
            if not memories:
                print("(ninguna)")
            print("\n=== RESPUESTA ===")
            print(
                output
                if output is not None
                else "Modo local: sin LLM. Ejecuta con --llm para generar una respuesta."
            )
    except Exception as exc:
        # Centralizar errores mantiene mensajes breves y evita trazas intimidantes
        # durante la demo. El código de salida 1 permite detectar el fallo.
        p.exit(1, f"Error: {exc}\n")


def show_passages(passages):
    """Imprime fragmentos recuperados con su sección y fuente original."""
    if not passages:
        print("Sin resultados. ¿Has ejecutado python -m scripts.load_book?")

    for position, item in enumerate(passages, 1):
        print(f"[{position}] {item['title']} · {item['section']} | {item['source']}")
        # El recorte mantiene legible la terminal; el documento completo sigue
        # disponible en Elasticsearch y mediante el enlace de origen.
        print(item["content"][:350].replace("\n", " "), "...\n")


if __name__ == "__main__":
    # Este bloque solo se ejecuta con ``python -m src.cli`` y no al importar el
    # módulo desde las pruebas.
    main()
