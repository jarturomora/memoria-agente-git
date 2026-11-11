"""Clonar Pro Git e indexar capítulos seleccionados en Elasticsearch.

Uso: python -m scripts.load_book --chapters 02 03
"""
import argparse
import hashlib
import re
import subprocess
from pathlib import Path
from src.store import client, ensure_indices
from src.config import BOOK_INDEX

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT / "data" / "progit2"
GIT_URL = "https://github.com/progit/progit2.git"
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
    text = re.sub(r"(?m)^\s*(?:image::|include::|ifdef::|ifndef::|endif::).*?$", "", source)
    text = re.sub(r"(?m)^\s*:[a-zA-Z][\w-]*:.*?$", "", text)
    text = re.sub(r"(?m)^\s*//.*?$", "", text)
    text = re.sub(r"(?m)^\s*(?:\[\[.*?\]\]|\[source.*?\]|\[NOTE\]|\[TIP\]|\[WARNING\])\s*$", "", text)
    text = re.sub(r"(?m)^\s*={1,5}\s+", "", text)
    text = re.sub(r"link:([^\[]+)\[([^]]+)\]", r"\2 (\1)", text)
    text = re.sub(r"(?m)^\s*\|===\s*$", "", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


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
        raise RuntimeError("No se encontraron archivos .asc para esos capítulos. Revisa la estructura de progit2.")
    for path in selected:
        rel = path.relative_to(repo)
        chapter = next((c for c, folder in CHAPTERS.items() if folder in rel.parts), "??")
        cleaned = sanitize_asciidoc(path.read_text(encoding="utf-8"))
        for i, chunk in enumerate(split_chunks(cleaned)):
            if len(chunk) < 90:
                continue
            key = hashlib.sha256(f"{rel}:{i}".encode()).hexdigest()[:24]
            yield {"_op_type": "index", "_index": BOOK_INDEX, "_id": key,
                   "_source": {"title": "Pro Git — capítulo " + chapter,
                               "section": path.stem.replace("-", " "),
                               "chapter": chapter, "chunk": i,
                               "source": f"https://github.com/progit/progit2/blob/main/{rel.as_posix()}",
                               "content": chunk}}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--chapters", nargs="+", choices=list(CHAPTERS), default=["02", "03"])
    args = parser.parse_args()
    download_book()
    es = client()
    ensure_indices(es)
    from elasticsearch.helpers import streaming_bulk
    ok = 0
    for success, result in streaming_bulk(es, actions(REPO, args.chapters), raise_on_error=False):
        if not success:
            print("Error al indexar:", result)
        else:
            ok += 1
    es.indices.refresh(index=BOOK_INDEX)
    print(f"Indexados {ok} fragmentos en '{BOOK_INDEX}'.")
    print("Fuente: Pro Git 2 (CC BY-NC-SA 3.0), Scott Chacon y Ben Straub.")

if __name__ == "__main__":
    main()
