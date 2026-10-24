"""`fux register [--json]` as a user runs it — the real CLI via subprocess.

SR-INGEST decision 22d (W-279): the verb prints the committed register's rows
FROM the index, so on a current index its text output is the file's bytes and
`--json` is one object per document. `fux doctor`'s `register` row names its
three states — missing, old format, drift.

⚠ **Named `test_register_verb.py`** for the reason `test_inspect_verb.py` gives:
`tests/ingest/test_register.py` exists and neither tree has an `__init__.py`.
"""

from __future__ import annotations

from l12_fixtures import config_file
import json
import subprocess
import sys
from pathlib import Path

from l12_fixtures import write_config


def _fux(root: Path, *argv: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "fux.cli", *argv],
        capture_output=True, text=True, encoding="utf-8", cwd=root,
    )


def _repo(tmp_path: Path) -> Path:
    (tmp_path / ".git").mkdir()
    (tmp_path / "fux.toml").write_text("[sources]\n", encoding="utf-8")
    fux = tmp_path / ".fux"
    (fux / "sources").mkdir(parents=True)
    (fux / "sources" / "dirs").write_text("docs\nold archived=true\n", encoding="utf-8")
    (config_file(fux.parent, "pii")).write_text("", encoding="utf-8")
    write_config(tmp_path)
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "rota.md").write_text("# Rota\n\nthe rota hands over Monday\n", encoding="utf-8")
    (tmp_path / "old").mkdir()
    (tmp_path / "old" / "cold.md").write_text("# Cold store\n\nretired in March\n", encoding="utf-8")
    ingest = _fux(tmp_path, "ingest", "--no-accelerator", "--no-progress")
    assert ingest.returncode == 0, ingest.stderr
    return tmp_path


def test_register_prints_the_file_bytes_on_a_current_index(tmp_path):
    root = _repo(tmp_path)
    out = _fux(root, "register")
    assert out.returncode == 0, out.stderr
    assert out.stdout == (root / ".fux" / "index" / "REGISTER").read_text(encoding="utf-8")
    lines = out.stdout.splitlines()
    assert lines[0].startswith("# fux.register.v2\trules=")
    assert lines[1] == "# loc\tsha\tdecoder\t[k=v ...]"
    assert lines[2].startswith("docs/rota.md\t") and lines[2].endswith("\tprose")
    assert lines[3].startswith("old/cold.md\t") and lines[3].endswith("\tprose\tarchived=true")


def test_register_json_is_one_object_per_document(tmp_path):
    root = _repo(tmp_path)
    out = _fux(root, "register", "--json")
    assert out.returncode == 0, out.stderr
    rows = [json.loads(line) for line in out.stdout.splitlines()]
    assert [r["loc"] for r in rows] == ["docs/rota.md", "old/cold.md"]
    assert rows[0]["decoder"] == {"name": "prose", "digest": None}
    assert "archived" not in rows[0] and rows[1]["archived"] is True
    assert all(isinstance(r["rules"], int) and len(r["sha"]) == 40 for r in rows)


def test_register_writes_nothing(tmp_path):
    root = _repo(tmp_path)
    index = root / ".fux" / "index"
    before = {p.name: p.read_bytes() for p in index.iterdir()}
    assert _fux(root, "register").returncode == 0
    assert _fux(root, "register", "--json").returncode == 0
    assert {p.name: p.read_bytes() for p in index.iterdir()} == before


def test_doctor_names_the_three_register_states(tmp_path):
    root = _repo(tmp_path)
    path = root / ".fux" / "index" / "REGISTER"

    def row() -> dict:
        out = _fux(root, "doctor", "--json", "--no-progress")
        return next(c for c in json.loads(out.stdout)["checks"] if c["name"] == "register")

    assert row()["ok"] is True
    current = path.read_text(encoding="utf-8")

    path.write_text("# loc\tkind\tsha\tdecoder\tfetcher\ndocs/rota.md\tfile\tabc\tprose\t-\n", encoding="utf-8")
    old = row()
    assert old["ok"] is False and old["level"] == "warn" and "old format" in old["detail"]

    path.unlink()
    missing = row()
    assert missing["ok"] is False and "no REGISTER beside the index" in missing["detail"]

    path.write_text(current.replace("docs/rota.md\t", "docs/gone.md\t"), encoding="utf-8")
    drift = row()
    assert drift["ok"] is False and "docs/gone.md" in drift["detail"] and "docs/rota.md" in drift["detail"]

    # The next ingest rewrites it, and then the verb and the file agree again.
    assert _fux(root, "ingest", "--no-accelerator", "--no-progress").returncode == 0
    assert row()["ok"] is True
    assert _fux(root, "register").stdout == path.read_text(encoding="utf-8")
