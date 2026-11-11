"""Clonar Pro Git en español e indexar capítulos seleccionados en Elasticsearch.

Uso: python -m scripts.load_book --chapters 02 03
Regeneración: python -m scripts.load_book --recreate --confirm
"""
import argparse
import hashlib
import re
import subprocess
from pathlib import Path

from src.config import BOOK_INDEX
from src.store import client, ensure_indices

# Rutas y fuente del corpus. ``ROOT`` se calcula desde este archivo para que el
# comando funcione sin depender del directorio personal de cada estudiante.
ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT / "data" / "progit2-es"
GIT_URL = "https://github.com/progit/progit2-es.git"

# Solo se cargan dos capítulos para mantener rápida y comprensible la demo.
# La clave es la opción de CLI y el valor, la carpeta real del repositorio.
CHAPTERS = {"02": "02-git-basics", "03": "03-git-branching"}


def download_book():
    """Clona una copia ligera del libro si todavía no existe localmente.

    ``--depth 1`` descarga solo la revisión más reciente: basta para indexar el
    texto y evita transferir todo el historial de Git durante una clase.
    """
    # Reutilizar el clon permite repetir la carga sin depender de Internet.
    if REPO.exists() and (REPO / ".git").is_dir():
        return

    # No sobrescribimos una carpeta desconocida; podría contener datos del alumno.
    if REPO.exists():
        raise RuntimeError(f"Existe {REPO} pero no parece un repositorio Git.")

    REPO.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "clone", "--depth", "1", GIT_URL, str(REPO)], check=True)


def select_files(repo, chapters):
    """Selecciona los AsciiDoc pertenecientes a los capítulos solicitados.

    Buscar por componentes de ruta tolera pequeños cambios en la profundidad de
    carpetas del repositorio de la traducción.
    """
    targets = {CHAPTERS[c] for c in chapters}
    result = []
    for path in sorted(repo.rglob("*.asc")):
        if any(part in targets for part in path.parts):
            result.append(path)
    return result


def sanitize_asciidoc(source):
    """Retira marcas de AsciiDoc sin intentar construir un parser completo.

    La limpieza conserva párrafos y ejemplos de comandos, que son la información
    útil para recuperar. Cada expresión regular elimina una familia concreta de
    directivas editoriales.
    """
    # Algunos archivos traducidos comienzan con BOM, invisible pero problemático
    # al imprimirlo en ciertas consolas de Windows.
    text = source.replace("\ufeff", "")

    # Imágenes, includes y condicionales no aportan texto autocontenido al índice.
    text = re.sub(r"(?m)^\s*(?:image::|include::|ifdef::|ifndef::|endif::).*?$", "", text)
    # Atributos globales de AsciiDoc, por ejemplo ``:imagesdir:``.
    text = re.sub(r"(?m)^\s*:[a-zA-Z][\w-]*:.*?$", "", text)
    # Comentarios editoriales de una línea.
    text = re.sub(r"(?m)^\s*//.*?$", "", text)
    # Anclas y etiquetas de presentación; su contenido no es lenguaje natural.
    text = re.sub(r"(?m)^\s*(?:\[\[.*?\]\]|\[source.*?\]|\[NOTE\]|\[TIP\]|\[WARNING\])\s*$", "", text)
    # Conservamos el título, pero retiramos sus caracteres ``===``.
    text = re.sub(r"(?m)^\s*={1,5}\s+", "", text)
    # Transformamos enlaces AsciiDoc en texto legible más su URL.
    text = re.sub(r"link:([^\[]+)\[([^]]+)\]", r"\2 (\1)", text)
    # Quitamos delimitadores de tabla, no necesariamente el texto de sus celdas.
    text = re.sub(r"(?m)^\s*\|===\s*$", "", text)
    # Normalizamos bloques de líneas vacías para facilitar el troceado posterior.
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extract_section_title(source, fallback):
    """Obtiene el primer encabezado traducido o usa un nombre alternativo."""
    match = re.search(r"(?m)^={2,5}\s+(.+?)\s*$", source)
    return match.group(1).strip() if match else fallback


def split_chunks(text, max_chars=1300):
    """Agrupa párrafos en fragmentos de hasta ``max_chars`` caracteres.

    Fragmentos pequeños mejoran la precisión de recuperación; un límite por
    caracteres mantiene el ejemplo sencillo y determinista para el alumnado.
    """
    # Los párrafos son la unidad preferida porque conservan ideas completas.
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    chunks, current = [], ""

    for paragraph in paragraphs:
        # Un párrafo excepcionalmente grande también debe respetar el límite.
        segments = [
            paragraph[start:start + max_chars]
            for start in range(0, len(paragraph), max_chars)
        ]
        for segment in segments:
            # ``+ 2`` representa las dos líneas nuevas entre párrafos.
            if current and len(current) + len(segment) + 2 > max_chars:
                chunks.append(current)
                current = ""
            current = (current + "\n\n" + segment).strip()

    # Al terminar el bucle queda un último fragmento aún no añadido.
    if current:
        chunks.append(current)
    return chunks


def actions(repo, chapters):
    """Genera operaciones de indexación para ``streaming_bulk``.

    Es un generador: produce un documento cada vez y evita guardar todo el libro
    procesado simultáneamente en memoria.
    """
    selected = select_files(repo, chapters)
    if not selected:
        raise RuntimeError("No se encontraron archivos .asc para esos capítulos. Revisa la estructura de progit2-es.")

    for path in selected:
        rel = path.relative_to(repo)
        # Recuperamos el número lógico a partir de la carpeta del archivo.
        chapter = next((c for c, folder in CHAPTERS.items() if folder in rel.parts), "??")
        source = path.read_text(encoding="utf-8")
        section = extract_section_title(source, path.stem.replace("-", " "))
        cleaned = sanitize_asciidoc(source)

        for i, chunk in enumerate(split_chunks(cleaned)):
            # Textos muy cortos suelen ser títulos sueltos o ruido editorial.
            if len(chunk) < 90:
                continue

            # Ruta + posición produce un ID estable: repetir la carga actualiza el
            # mismo documento en vez de crear un duplicado.
            key = hashlib.sha256(f"{rel}:{i}".encode()).hexdigest()[:24]
            yield {
                "_op_type": "index",
                "_index": BOOK_INDEX,
                "_id": key,
                "_source": {
                    "title": "Pro Git en español — capítulo " + chapter,
                    "section": section,
                    "chapter": chapter,
                    "chunk": i,
                    # La fuente hace trazable cada respuesta hasta el texto original.
                    "source": (
                        "https://github.com/progit/progit2-es/blob/master/"
                        f"{rel.as_posix()}"
                    ),
                    "content": chunk,
                },
            }


def prepare_book_index(es, recreate=False):
    """Prepara el índice documental; nunca elimina el índice de memorias."""
    # Recrear es necesario cuando cambia un analyzer, porque Elasticsearch no
    # permite sustituir el analyzer de un campo existente en el mismo índice.
    if recreate and es.indices.exists(index=BOOK_INDEX):
        es.indices.delete(index=BOOK_INDEX)

    # Además de crear ``progit``, esta función asegura que el índice de memoria
    # exista; si ya existe, no lo modifica.
    ensure_indices(es)


def main(argv=None):
    """Procesa opciones, prepara el índice y carga los fragmentos del libro."""
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

    # La combinación de dos flags hace difícil borrar el índice por accidente.
    if args.recreate and not args.confirm:
        parser.error("Añade --confirm para regenerar el índice documental.")

    download_book()
    es = client()
    prepare_book_index(es, recreate=args.recreate)

    # Importación local: el helper solo se necesita durante una carga real, no
    # cuando las pruebas importan funciones de limpieza o troceado.
    from elasticsearch.helpers import streaming_bulk

    ok = 0
    # ``streaming_bulk`` envía lotes eficientes sin construir una petición enorme.
    for success, result in streaming_bulk(es, actions(REPO, args.chapters), raise_on_error=False):
        if not success:
            print("Error al indexar:", result)
        else:
            ok += 1

    # Un refresh final garantiza que ``status`` y ``search`` vean toda la carga.
    es.indices.refresh(index=BOOK_INDEX)
    print(f"Indexados {ok} fragmentos en '{BOOK_INDEX}'.")
    print("Fuente: Pro Git 2 en español (CC BY-NC-SA 3.0), proyecto progit2-es.")


if __name__ == "__main__":
    main()
