"""Regression tests for local-source key collisions (same basename)."""
from lacuna_wiki.cli.add_source import _disambiguate_on_disk


def _setup(tmp_path):
    raw = tmp_path / "raw"
    (raw / "project-a").mkdir(parents=True)
    (raw / "project-b").mkdir(parents=True)
    return raw


def test_first_file_keeps_base_key(tmp_path):
    raw = _setup(tmp_path)
    src = tmp_path / "README.md"
    src.write_text("# Project A")
    assert _disambiguate_on_disk("readme", raw, src) == "readme"


def test_same_basename_different_content_gets_suffix(tmp_path):
    raw = _setup(tmp_path)
    (raw / "project-a" / "readme.md").write_text("# Project A")
    src = tmp_path / "README.md"
    src.write_text("# Project B — different content")
    assert _disambiguate_on_disk("readme", raw, src) == "readmeb"


def test_readding_identical_file_reuses_key(tmp_path):
    raw = _setup(tmp_path)
    (raw / "project-a" / "readme.md").write_text("# Project A")
    src = tmp_path / "README.md"
    src.write_text("# Project A")
    assert _disambiguate_on_disk("readme", raw, src) == "readme"


def test_suffixes_chain_across_concept_dirs(tmp_path):
    raw = _setup(tmp_path)
    (raw / "project-a" / "readme.md").write_text("# A")
    (raw / "project-b" / "readmeb.md").write_text("# B")
    src = tmp_path / "README.md"
    src.write_text("# C")
    assert _disambiguate_on_disk("readme", raw, src) == "readmec"


def test_sidecar_files_do_not_mask_identity(tmp_path):
    raw = _setup(tmp_path)
    (raw / "project-a" / "readme.md").write_text("# A")
    (raw / "project-a" / "readme.bib").write_text("@misc{readme,\n}")
    src = tmp_path / "README.md"
    src.write_text("# A")
    assert _disambiguate_on_disk("readme", raw, src) == "readme"
