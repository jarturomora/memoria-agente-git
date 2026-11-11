from pathlib import Path
from scripts.load_book import split_chunks, sanitize_asciidoc, select_files

def test_chunking_respects_limit():
    txt = "first paragraph\n\n" + ("word " * 400)
    chunks = split_chunks(txt, max_chars=100)
    assert len(chunks) > 3
    assert all(len(c) <= 100 for c in chunks)

def test_sanitize():
    cleaned = sanitize_asciidoc("== Title\n\ninclude::other.asc[]\n\nSome text")
    assert "Title" in cleaned
    assert "include::" not in cleaned

def test_select_files(tmp_path):
    folder = tmp_path / "book" / "02-git-basics" / "sections"
    folder.mkdir(parents=True)
    (folder / "a.asc").write_text("Hello")
    assert len(select_files(tmp_path, ["02"])) == 1
    assert not select_files(tmp_path, ["03"])
