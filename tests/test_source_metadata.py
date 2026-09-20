"""Regression tests for metadata propagation from add-source to the daemon.

Explicit --type/--title/--date used to be discarded: the watcher inferred
source_type purely from file extensions (Markdown always became "url").
Citation metadata travels via the .bib sidecar; the .meta.json sidecar
carries only what BibTeX cannot round-trip (source type, full ISO date).
"""
import json
from datetime import date

import duckdb

from lacuna_wiki.cli.add_source import _write_bib_sidecar, _write_metadata_sidecar
from lacuna_wiki.daemon.watcher import RawSourceHandler
from lacuna_wiki.db.schema import init_db


def _register(vault, source):
    db = duckdb.connect(":memory:")
    init_db(db)
    handler = RawSourceHandler(db, vault, lambda texts: [[0.0] * 768 for _ in texts])
    handler._register(source)
    row = db.execute(
        "SELECT slug, title, authors, source_type, published_date FROM sources"
    ).fetchone()
    db.close()
    return row


def test_metadata_sidecar_carries_only_non_bib_fields(tmp_path):
    _write_metadata_sidecar(tmp_path, "note", "session", date(2026, 9, 20))
    metadata = json.loads((tmp_path / "note.meta.json").read_text())
    assert metadata == {"source_type": "session", "published_date": "2026-09-20"}


def test_watcher_combines_bib_and_metadata_sidecars(tmp_path):
    raw = tmp_path / "raw" / "project"
    raw.mkdir(parents=True)
    (raw / "session.md").write_text("# Session\n\nA research session.")
    _write_bib_sidecar(raw, "session", "My session", "Hal", date(2026, 9, 20), "session")
    _write_metadata_sidecar(raw, "session", "session", date(2026, 9, 20))

    row = _register(tmp_path, raw / "session.md")
    assert row == ("session", "My session", "Hal", "session", date(2026, 9, 20))


def test_watcher_full_date_beats_bib_year(tmp_path):
    raw = tmp_path / "raw" / "project"
    raw.mkdir(parents=True)
    (raw / "post.md").write_text("# Post\n\nBody.")
    _write_bib_sidecar(raw, "post", "A post", None, date(2026, 1, 1), "blog")
    _write_metadata_sidecar(raw, "post", "blog", date(2026, 9, 20))

    row = _register(tmp_path, raw / "post.md")
    assert row[3] == "blog"
    assert row[4] == date(2026, 9, 20)


def test_watcher_falls_back_to_inference_without_sidecars(tmp_path):
    raw = tmp_path / "raw" / "project"
    raw.mkdir(parents=True)
    (raw / "page.md").write_text("# Page\n\nBody.")

    row = _register(tmp_path, raw / "page.md")
    assert row[3] == "url"


def test_watcher_tolerates_corrupt_metadata_sidecar(tmp_path):
    raw = tmp_path / "raw" / "project"
    raw.mkdir(parents=True)
    (raw / "page.md").write_text("# Page\n\nBody.")
    (raw / "page.meta.json").write_text("{not json")

    row = _register(tmp_path, raw / "page.md")
    assert row[3] == "url"
