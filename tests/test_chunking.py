"""Pruebas del pipeline que transforma *Pro Git* en documentos indexables.

Estas pruebas no descargan el libro ni conectan con Elasticsearch. Utilizan
texto y carpetas temporales para comprobar cada transformación de forma aislada.
"""

from unittest.mock import MagicMock, patch

import pytest

from scripts import load_book
from scripts.load_book import (
    extract_section_title,
    prepare_book_index,
    sanitize_asciidoc,
    select_files,
    split_chunks,
)
from src.config import BOOK_INDEX
from src.store import BOOK_MAPPING

def test_chunking_respects_limit():
    """Ningún fragmento debe superar el tamaño configurado."""
    txt = "first paragraph\n\n" + ("word " * 400)
    chunks = split_chunks(txt, max_chars=100)

    assert len(chunks) > 3
    assert all(len(c) <= 100 for c in chunks)


def test_sanitize():
    """La limpieza conserva texto útil y elimina marcas editoriales y BOM."""
    cleaned = sanitize_asciidoc("\ufeff== Título\n\ninclude::other.asc[]\n\nContenido")

    assert "Título" in cleaned
    assert "include::" not in cleaned
    assert "\ufeff" not in cleaned


def test_extract_section_title_in_spanish():
    """El encabezado traducido debe convertirse en el campo ``section``."""
    source = "[[ramas]]\n=== Gestión de Ramas\n\nContenido"

    assert extract_section_title(source, "branch management") == "Gestión de Ramas"


def test_select_files(tmp_path):
    """La selección incluye solo archivos de los capítulos solicitados."""
    # ``tmp_path`` es una carpeta desechable creada por pytest para esta prueba.
    folder = tmp_path / "book" / "02-git-basics" / "sections"
    folder.mkdir(parents=True)
    (folder / "a.asc").write_text("Hello")

    assert len(select_files(tmp_path, ["02"])) == 1
    assert not select_files(tmp_path, ["03"])


def test_recreate_deletes_only_book_index():
    """Regenerar el corpus nunca debe borrar el índice de memoria."""
    es = MagicMock()
    es.indices.exists.return_value = True

    # Se sustituye ``ensure_indices`` para observar la coordinación sin crear
    # un cliente ni índices reales.
    with patch("scripts.load_book.ensure_indices") as ensure_indices:
        prepare_book_index(es, recreate=True)

    es.indices.delete.assert_called_once_with(index=BOOK_INDEX)
    ensure_indices.assert_called_once_with(es)


def test_recreate_requires_explicit_confirmation():
    """El flag destructivo aislado debe terminar antes de descargar o borrar."""
    with patch.object(load_book, "download_book") as download_book:
        with pytest.raises(SystemExit) as exit_info:
            load_book.main(["--recreate"])

    assert exit_info.value.code == 2
    download_book.assert_not_called()


def test_book_fields_use_spanish_analyzer():
    """Los campos buscables deben aplicar análisis lingüístico español."""
    properties = BOOK_MAPPING["mappings"]["properties"]

    for field in ["title", "section", "content"]:
        assert properties[field]["analyzer"] == "spanish"
