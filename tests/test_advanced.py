"""Advanced-tier fidelity transitions with fake converters (no docling/tesseract)."""

from __future__ import annotations

import json

import pytest

import fux.ingest.advanced as advanced
from fux.cli import main
from fux.config import load
from fux.errors import FuxError
from fux.frontmatter import parse as fm_parse
from fux.ingest.manifest import read as manifest_read

from test_convert import tiny_png


def project(tmp_path):
    (tmp_path / "img").mkdir()
    (tmp_path / "docs").mkdir()
    (tmp_path / "img/diagram.png").write_bytes(tiny_png())
    (tmp_path / "docs/note.md").write_text("# Note\n\nplain\n", encoding="utf-8")
    (tmp_path / "fux.toml").write_text(
        '[sources]\ndocs = ["docs"]\nimages = ["img"]\n', encoding="utf-8"
    )
    return tmp_path


def run(tmp_path, monkeypatch, *argv):
    monkeypatch.chdir(tmp_path)
    return main(list(argv))


@pytest.fixture
def fake_ocr(monkeypatch):
    monkeypatch.setattr(
        advanced,
        "_tesseract_convert",
        lambda path, entry: f"Image file `{entry['source']}`.\n\n## Extracted text (OCR)\n\nARCHITECTURE DIAGRAM shows the ingest pipeline",
    )


def test_upgrade_flips_fidelity_everywhere(tmp_path, monkeypatch, capsys, fake_ocr):
    project(tmp_path)
    run(tmp_path, monkeypatch, "ingest")
    capsys.readouterr()

    assert run(tmp_path, monkeypatch, "ingest", "--advanced", "img/diagram.png") == 0
    assert "fidelity: advanced" in capsys.readouterr().out

    fm = fm_parse((tmp_path / ".fux/cache/img/diagram.png.md").read_text(encoding="utf-8"))
    assert fm.meta["fidelity"] == "advanced"
    assert fm.meta["converter"] == "tesseract"
    assert "ARCHITECTURE DIAGRAM" in fm.body

    entry = manifest_read(tmp_path)["img/diagram.png"]
    assert entry["fidelity"] == "advanced"

    # the OCR text is searchable: index was rebuilt despite unchanged source sha
    run(tmp_path, monkeypatch, "ask", "architecture diagram ingest pipeline", "--json")
    payload = json.loads(capsys.readouterr().out)
    assert payload["results"][0]["path"] == "img/diagram.png"
    assert payload["results"][0]["fidelity"] == "advanced"


def test_upgrade_survives_reingest_until_source_changes(tmp_path, monkeypatch, capsys, fake_ocr):
    project(tmp_path)
    run(tmp_path, monkeypatch, "ingest")
    run(tmp_path, monkeypatch, "ingest", "--advanced", "img/diagram.png")

    run(tmp_path, monkeypatch, "ingest")  # plain re-ingest: no downgrade
    assert manifest_read(tmp_path)["img/diagram.png"]["fidelity"] == "advanced"

    (tmp_path / "img/diagram.png").write_bytes(tiny_png(5, 5))  # source changed
    run(tmp_path, monkeypatch, "ingest")
    assert manifest_read(tmp_path)["img/diagram.png"]["fidelity"] == "inferred"  # honest reset


def test_list_inferred_shows_candidates_not_upgraded(tmp_path, monkeypatch, capsys, fake_ocr):
    project(tmp_path)
    run(tmp_path, monkeypatch, "ingest")
    run(tmp_path, monkeypatch, "ingest", "--advanced", "img/diagram.png")
    capsys.readouterr()
    run(tmp_path, monkeypatch, "ingest", "--list-inferred")
    out = capsys.readouterr().out
    assert "docs/note.md" in out
    assert "img/diagram.png" not in out  # advanced entries are no longer candidates


def test_unknown_target_and_wrong_kind(tmp_path, monkeypatch, capsys):
    project(tmp_path)
    run(tmp_path, monkeypatch, "ingest")
    capsys.readouterr()
    assert run(tmp_path, monkeypatch, "ingest", "--advanced", "nope.pdf") == 1
    assert "not in the manifest" in capsys.readouterr().err
    assert run(tmp_path, monkeypatch, "ingest", "--advanced", "docs/note.md") == 1
    assert "no advanced converter" in capsys.readouterr().err


def test_missing_tesseract_binary_has_actionable_error(tmp_path, monkeypatch, capsys):
    project(tmp_path)
    run(tmp_path, monkeypatch, "ingest")
    monkeypatch.setattr(advanced.shutil, "which", lambda name: None)
    capsys.readouterr()
    assert run(tmp_path, monkeypatch, "ingest", "--advanced", "img/diagram.png") == 1
    assert "tesseract" in capsys.readouterr().err


def test_basename_resolution(tmp_path, monkeypatch, capsys, fake_ocr):
    project(tmp_path)
    run(tmp_path, monkeypatch, "ingest")
    capsys.readouterr()
    assert run(tmp_path, monkeypatch, "ingest", "--advanced", "diagram.png") == 0
    assert manifest_read(tmp_path)["img/diagram.png"]["fidelity"] == "advanced"
