"""Clonar Pro Git en español e indexar capítulos seleccionados en Elasticsearch.

Uso: python -m scripts.load_book --chapters 02 03
Regeneración: python -m scripts.load_book --recreate --confirm
"""
import argparse
import hashlib
import re
import subprocess
from pathlib import Path
from src.store import client, ensure_indices
from src.config import BOOK_INDEX

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT / "data" / "progit2-es"
GIT_URL = "https://github.com/progit/progit2-es.git"
CHAPTERS = {"02": "02-git-basics", "03": "03-git-branching"}


def download_book():
    if REPO.exists() and (REPO / ".git").is_dir():
        return
    if REPO.exists():
        raise RuntimeError(f"Existe {REPO} pero no parece un repositorio Git.")
    REPO.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "clone", "--depth", "1", GIT_URL, str(REPO)], check=True)


def select_files(repo, chapters):
    """Selecciona los .asc por el nombre de la carpeta, sin depender de una ruta fija."""
    targets = {CHAPTERS[c] for c in chapters}
    result = []
    for f in sorted(repo.rglob("*.asc")):
        if any(part in targets for part in f.parts):
            result.append(f)
    return result


def sanitize_asciidoc(source):
    """Limpieza deliberadamente ligera: conserva comandos Git y párrafos."""
    text = source.replace("\ufeff", "")
    text = re.sub(r"(?m)^\s*(?:image::|include::|ifdef::|ifndef::|endif::).*?$", "", text)
    text = re.sub(r"(?m)^\s*:[a-zA-Z][\w-]*:.*?$", "", text)
    text = re.sub(r"(?m)^\s*//.*?$", "", text)
    text = re.sub(r"(?m)^\s*(?:\[\[.*?\]\]|\[source.*?\]|\[NOTE\]|\[TIP\]|\[WARNING\])\s*$", "", text)
    text = re.sub(r"(?m)^\s*={1,5}\s+", "", text)
    text = re.sub(r"link:([^\[]+)\[([^]]+)\]", r"\2 (\1)", text)
    text = re.sub(r"(?m)^\s*\|===\s*$", "", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extract_section_title(source, fallback):
    """Obtiene el primer encabezado traducido del documento AsciiDoc."""
    match = re.search(r"(?m)^={2,5}\s+(.+?)\s*$", source)
    return match.group(1).strip() if match else fallback


def split_chunks(text, max_chars=1300):
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    chunks, current = [], ""
    for paragraph in paragraphs:
        # No descartar párrafos grandes: dividir en segmentos de caracteres.
        segments = [paragraph[i:i+max_chars] for i in range(0, len(paragraph), max_chars)]
        for seg in segments:
            if current and len(current) + len(seg) + 2 > max_chars:
                chunks.append(current)
                current = ""
            current = (current + "\n\n" + seg).strip()
    if current:
        chunks.append(current)
    return chunks


def actions(repo, chapters):
    selected = select_files(repo, chapters)
    if not selected:
        raise RuntimeError("No se encontraron archivos .asc para esos capítulos. Revisa la estructura de progit2-es.")
    for path in selected:
        rel = path.relative_to(repo)
        chapter = next((c for c, folder in CHAPTERS.items() if folder in rel.parts), "??")
        source = path.read_text(encoding="utf-8")
        section = extract_section_title(source, path.stem.replace("-", " "))
        cleaned = sanitize_asciidoc(source)
        for i, chunk in enumerate(split_chunks(cleaned)):
            if len(chunk) < 90:
                continue
            key = hashlib.sha256(f"{rel}:{i}".encode()).hexdigest()[:24]
            yield {"_op_type": "index", "_index": BOOK_INDEX, "_id": key,
                   "_source": {"title": "Pro Git en español — capítulo " + chapter,
                               "section": section,
                               "chapter": chapter, "chunk": i,
                               "source": f"https://github.com/progit/progit2-es/blob/master/{rel.as_posix()}",
                               "content": chunk}}


def prepare_book_index(es, recreate=False):
    """Prepara el índice documental; nunca modifica el índice de memorias."""
    if recreate and es.indices.exists(index=BOOK_INDEX):
        es.indices.delete(index=BOOK_INDEX)
    ensure_indices(es)


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--chapters", nargs="+", choices=list(CHAPTERS), default=["02", "03"])
    parser.add_argument(
        "--recreate",
        action="store_true",
        help="Elimina y recrea únicamente el índice documental antes de cargarlo",
    )
    parser.add_argument(
        "--confirm",
        action="store_true",
        help="Confirma la regeneración del índice documental",
    )
    args = parser.parse_args(argv)
    if args.recreate and not args.confirm:
        parser.error("Añade --confirm para regenerar el índice documental.")
    download_book()
    es = client()
    prepare_book_index(es, recreate=args.recreate)
    from elasticsearch.helpers import streaming_bulk
    ok = 0
    for success, result in streaming_bulk(es, actions(REPO, args.chapters), raise_on_error=False):
        if not success:
            print("Error al indexar:", result)
        else:
            ok += 1
    es.indices.refresh(index=BOOK_INDEX)
    print(f"Indexados {ok} fragmentos en '{BOOK_INDEX}'.")
    print("Fuente: Pro Git 2 en español (CC BY-NC-SA 3.0), proyecto progit2-es.")

if __name__ == "__main__":
    main()
