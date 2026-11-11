"""CLI de la demo. Ejecutar con: python -m src.cli ..."""
import argparse
from src.store import client, ensure_indices
from src.config import BOOK_INDEX, MEMORY_INDEX
from src.search import search_book
from src.memory import save_memory, list_memories, delete_memory
from src.agent import answer


def main(argv=None):
    p = argparse.ArgumentParser(description="Laboratorio: conocimiento y memoria con Elasticsearch")
    sub = p.add_subparsers(dest="command", required=True)
    sub.add_parser("status")
    q = sub.add_parser("search", help="Busca pasajes del libro sin LLM")
    q.add_argument("question")
    r = sub.add_parser("remember", help="Guarda un recuerdo explícito")
    r.add_argument("text")
    ls = sub.add_parser("memories", help="Muestra los recuerdos")
    delete = sub.add_parser("forget", help="Elimina un recuerdo propio")
    delete.add_argument("memory_id")
    a = sub.add_parser("ask", help="Muestra contexto; --llm genera respuesta")
    a.add_argument("question")
    a.add_argument("--llm", action="store_true")
    for cmd in [r, ls, delete, a]:
        cmd.add_argument("--user", default="alumno-01")
    args = p.parse_args(argv)
    es = client()
    try:
        if not es.ping():
            p.error("Elasticsearch no responde. Inicia Docker y revisa http://localhost:9200")
        ensure_indices(es)
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
            if not ms: print("Sin recuerdos.")
            for m in ms:
                print(f"{m['id']} | {m['text']}")
        elif args.command == "forget":
            print("Recuerdo eliminado." if delete_memory(es, args.user, args.memory_id)
                  else "No existe o pertenece a otro usuario.")
        elif args.command == "ask":
            passages, memories, output = answer(es, args.user, args.question, args.llm)
            print("\n=== CONOCIMIENTO RECUPERADO ===")
            show_passages(passages)
            print("\n=== MEMORIA RECUPERADA ===")
            for m in memories: print("-", m["text"])
            if not memories: print("(ninguna)")
            print("\n=== RESPUESTA ===")
            print(output if output is not None else "Modo local: sin LLM. Ejecuta con --llm para generar una respuesta.")
    except Exception as exc:
        p.exit(1, f"Error: {exc}\n")


def show_passages(passages):
    if not passages:
        print("Sin resultados. ¿Has ejecutado python -m scripts.load_book?")
    for i, item in enumerate(passages, 1):
        print(f"[{i}] {item['title']} · {item['section']} | {item['source']}")
        print(item["content"][:350].replace("\n", " "), "...\n")

if __name__ == "__main__":
    main()
